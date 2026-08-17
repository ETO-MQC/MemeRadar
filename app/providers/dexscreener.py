from __future__ import annotations
import asyncio, time
from datetime import datetime, timezone
import httpx

BASE = "https://api.dexscreener.com"

class DexScreenerProvider:
    def __init__(self, timeout=12):
        self.client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent":"MemeRadar-MVP/1.0"})

    async def _get(self, path):
        r = await self.client.get(BASE + path)
        r.raise_for_status(); return r.json()

    async def latest_tokens(self, max_items=24):
        items = []
        for path in ("/token-profiles/latest/v1", "/token-boosts/latest/v1", "/token-boosts/top/v1"):
            try:
                data = await self._get(path)
                if isinstance(data, list): items.extend(data)
                elif isinstance(data, dict) and data.get("chainId") and data.get("tokenAddress"): items.append(data)
            except Exception:
                continue
        seen=set(); out=[]
        for x in items:
            chain=x.get("chainId"); addr=x.get("tokenAddress")
            if chain and addr and (chain,addr) not in seen:
                seen.add((chain,addr)); out.append(x)
            if len(out)>=max_items: break
        return out

    async def token_pairs(self, chain: str, address: str):
        try:
            data = await self._get(f"/token-pairs/v1/{chain}/{address}")
            return data if isinstance(data,list) else []
        except Exception:
            return []

    async def discover(self, supported_chains, max_items=24):
        tokens = [x for x in await self.latest_tokens(max_items*2) if x.get("chainId") in supported_chains][:max_items]
        sem=asyncio.Semaphore(6)
        async def one(t):
            async with sem:
                pairs=await self.token_pairs(t["chainId"],t["tokenAddress"])
                if not pairs: return None
                p=max(pairs,key=lambda z: float(((z.get("liquidity") or {}).get("usd") or 0)))
                created=p.get("pairCreatedAt")
                age=None
                if created:
                    try: age=max(0,(time.time()*1000-float(created))/60000)
                    except: pass
                tx=(p.get("txns") or {}).get("m5") or {}
                pc=p.get("priceChange") or {}; vol=p.get("volume") or {}; liq=p.get("liquidity") or {}
                base=p.get("baseToken") or {}
                return {
                  "token_key":f"{t['chainId']}:{t['tokenAddress']}","chain":t["chainId"],"address":t["tokenAddress"],
                  "symbol":base.get("symbol") or "?","name":base.get("name") or "Unknown","source":"dexscreener",
                  "url":p.get("url") or t.get("url") or "","first_seen":datetime.now(timezone.utc).isoformat(),
                  "updated_at":datetime.now(timezone.utc).isoformat(),"price_usd":float(p.get("priceUsd") or 0),
                  "liquidity_usd":float(liq.get("usd") or 0),"volume_h1":float(vol.get("h1") or 0),
                  "market_cap":float(p.get("marketCap") or p.get("fdv") or 0),"age_minutes":age,
                  "buys_m5":int(tx.get("buys") or 0),"sells_m5":int(tx.get("sells") or 0),
                  "change_m5":float(pc.get("m5") or 0),"change_h1":float(pc.get("h1") or 0),
                  "profile":t,"pair":p
                }
        vals=await asyncio.gather(*(one(t) for t in tokens))
        return [x for x in vals if x and x.get("price_usd",0)>0]

    async def close(self): await self.client.aclose()
