from __future__ import annotations
import asyncio, json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .config import ROOT, load_settings, save_settings
from .storage import Storage, utcnow
from .providers.dexscreener import DexScreenerProvider
from .providers.gate import GatePublicProvider
from .providers.goplus import GoPlusProvider
from .providers.social import SocialProvider
from .providers.llm import LLMProvider
from .strategies.collector import enrich_candidate, eligible as collector_eligible
from .strategies.dip import eligible as dip_eligible
from .execution.paper import PaperExecutor
from .execution.gate_live import GateLiveExecutor

storage=Storage(); settings=load_settings(); dex=DexScreenerProvider(); gate=GatePublicProvider(); gp=GoPlusProvider(); social=SocialProvider(); llm=LLMProvider(); paper=PaperExecutor(storage,settings); live=GateLiveExecutor()
scan_lock=asyncio.Lock(); bg_task=None

async def scan_once():
    if scan_lock.locked(): return {"status":"busy"}
    async with scan_lock:
        fresh_social=await social.collect(settings.get("x_watchlist",[]),settings.get("rss_feeds",[]))
        for i in fresh_social: storage.add_social(i)
        social_items=storage.list_social(80)
        candidates=await dex.discover(settings["app"]["supported_chains"],int(settings["app"]["max_candidates_per_scan"]))
        for c in candidates:
            try:
                c=await enrich_candidate(c,gp,llm,social_items); storage.upsert_candidate(c)
                if settings["collector"].get("auto_paper_buy") and collector_eligible(c,settings["collector"]) and not storage.get_open_position_for(c["token_key"],"collector"):
                    paper.buy(c,"collector",float(settings["collector"]["stake_usdt"]),float(c["price_usd"]))
            except Exception as e: storage.event("warn","candidate_error",str(e),{"token":c.get("token_key")})
        for pair in settings.get("gate_watchlist",[]):
            try:
                d=await gate.analyze_dip(pair,int(settings["dip"]["lookback_minutes"]));
                if not d: continue
                c={"token_key":d["token_key"],"chain":"gate","address":pair,"symbol":d["symbol"],"name":d["name"],"source":"gate",
                   "url":"","first_seen":utcnow(),"updated_at":utcnow(),"score":round(min(100,50+d["rebound_pct"]*5+d["drawdown_pct"]),1),
                   "risk_status":"cex-listed","price_usd":d["price_usd"],"liquidity_usd":0,"volume_h1":0,"market_cap":0,"age_minutes":0,
                   "buys_m5":0,"sells_m5":0,"change_m5":d["rebound_pct"],"change_h1":0,
                   "narrative":f"Gate回撤 {d['drawdown_pct']:.1f}% / 最新反弹 {d['rebound_pct']:.2f}% / 24h量 {d['quote_volume_24h']:.0f}","raw_json":json.dumps(d,ensure_ascii=False)}
                storage.upsert_candidate(c)
                if settings["dip"].get("auto_paper_buy") and dip_eligible(d,settings["dip"]) and not storage.get_open_position_for(d["token_key"],"dip"):
                    paper.buy(c,"dip",float(settings["dip"]["stake_usdt"]),float(d["price_usd"]))
            except Exception as e: storage.event("warn","gate_watch_error",str(e),{"pair":pair})
        # 管理模拟仓：DEX仓使用最新候选价；Gate仓实时再取一次。
        for p in storage.list_positions(open_only=True):
            try:
                c=storage.get_candidate(p["token_key"]); price=float(c["price_usd"]) if c else float(p["current_price"])
                if p["chain"]=="gate":
                    d=await gate.analyze_dip(p["token_key"].split(":",1)[1],10); price=float(d["price_usd"]) if d else price
                paper.mark_and_manage(p,price)
            except Exception as e: storage.event("warn","position_mark_error",str(e),{"position_id":p["id"]})
        storage.event("info","scan","扫描完成",{"candidates":len(candidates),"social":len(fresh_social)})
        return {"status":"ok","candidates":len(candidates),"social":len(fresh_social)}

async def background_loop():
    await asyncio.sleep(2)
    while True:
        try: await scan_once()
        except Exception as e: storage.event("error","scan_error",str(e))
        await asyncio.sleep(max(15,int(settings["app"].get("refresh_seconds",45))))

@asynccontextmanager
async def lifespan(app:FastAPI):
    global bg_task
    bg_task=asyncio.create_task(background_loop())
    yield
    bg_task.cancel()
    for x in (dex,gate,gp,social,llm):
        try: await x.close()
        except: pass

app=FastAPI(title="MemeRadar MVP",version="1.0.0",lifespan=lifespan)

@app.get("/")
def root(): return FileResponse(ROOT/"app"/"static"/"index.html")
@app.get("/api/status")
def status():
    return {"version":"1.0.0","mode":"PAPER" if not live.status()["armed"] else "PAPER + GATE LIVE ARMED","live":live.status(),
            "summary":storage.paper_summary(float(settings["paper"]["starting_balance_usdt"])),"settings":settings}
@app.get("/api/candidates")
def candidates(): return storage.list_candidates(100)
@app.get("/api/positions")
def positions(): return storage.list_positions(False)
@app.get("/api/events")
def events(): return storage.list_events(100)
@app.get("/api/social")
def socials(): return storage.list_social(80)
@app.post("/api/scan")
async def scan(): return await scan_once()

class BuyReq(BaseModel): token_key:str; strategy:str="collector"; stake_usdt:float|None=None
@app.post("/api/paper/buy")
def paper_buy(req:BuyReq):
    c=storage.get_candidate(req.token_key)
    if not c: raise HTTPException(404,"candidate not found")
    cfg=settings[req.strategy] if req.strategy in ("collector","dip") else settings["collector"]
    stake=float(req.stake_usdt or cfg["stake_usdt"])
    try: pid=paper.buy(c,req.strategy,stake,float(c["price_usd"])); return {"ok":True,"position_id":pid}
    except Exception as e: raise HTTPException(400,str(e))
class CloseReq(BaseModel): position_id:int
@app.post("/api/paper/close")
def paper_close(req:CloseReq):
    p=next((x for x in storage.list_positions(True) if x["id"]==req.position_id),None)
    if not p: raise HTTPException(404,"position not found")
    storage.close_position(p["id"],float(p["current_price"] or p["entry_price"]),"manual"); return {"ok":True}

class WatchReq(BaseModel): pair:str
@app.post("/api/watch/gate")
def add_gate_watch(req:WatchReq):
    pair=req.pair.strip().upper().replace("/","_")
    if "_" not in pair: pair += "_USDT"
    if pair not in settings["gate_watchlist"]: settings["gate_watchlist"].append(pair); save_settings(settings)
    return {"ok":True,"watchlist":settings["gate_watchlist"]}
class XReq(BaseModel): username:str
@app.post("/api/watch/x")
def add_x_watch(req:XReq):
    u=req.username.strip().lstrip("@")
    if u and u not in settings["x_watchlist"]: settings["x_watchlist"].append(u); save_settings(settings)
    return {"ok":True,"watchlist":settings["x_watchlist"]}
class RssReq(BaseModel): url:str
@app.post("/api/watch/rss")
def add_rss(req:RssReq):
    u=req.url.strip()
    if u and u not in settings["rss_feeds"]: settings["rss_feeds"].append(u); save_settings(settings)
    return {"ok":True,"feeds":settings["rss_feeds"]}
