from __future__ import annotations
import httpx

BASE="https://api.gateio.ws/api/v4"
class GatePublicProvider:
    def __init__(self, timeout=10): self.client=httpx.AsyncClient(timeout=timeout,headers={"User-Agent":"MemeRadar-MVP/1.0"})
    async def ticker(self,pair:str):
        r=await self.client.get(BASE+"/spot/tickers",params={"currency_pair":pair}); r.raise_for_status(); data=r.json()
        return data[0] if isinstance(data,list) and data else None
    async def candles(self,pair:str,interval="1m",limit=120):
        r=await self.client.get(BASE+"/spot/candlesticks",params={"currency_pair":pair,"interval":interval,"limit":limit}); r.raise_for_status(); return r.json()
    async def analyze_dip(self,pair:str,lookback=120):
        t=await self.ticker(pair); candles=await self.candles(pair,"1m",min(1000,lookback))
        if not t or not candles: return None
        # Gate candle commonly: [timestamp, quote_volume, close, high, low, open, base_volume, ...]
        parsed=[]
        for row in candles:
            try: parsed.append({"ts":int(float(row[0])),"close":float(row[2]),"high":float(row[3]),"low":float(row[4]),"open":float(row[5])})
            except Exception: continue
        if len(parsed)<3:return None
        parsed=sorted(parsed,key=lambda x:x["ts"])
        price=float(t.get("last") or parsed[-1]["close"]); peak=max(x["high"] for x in parsed)
        dd=(peak-price)/peak*100 if peak else 0
        prev=parsed[-2]["close"]; rebound=(price-prev)/prev*100 if prev else 0
        qv=float(t.get("quote_volume") or t.get("base_volume") or 0)
        return {"pair":pair,"token_key":"gate:"+pair,"chain":"gate","address":pair,"symbol":pair.replace("_USDT",""),"name":pair,
                "source":"gate","url":"","price_usd":price,"peak":peak,"drawdown_pct":dd,"rebound_pct":rebound,
                "quote_volume_24h":qv,"change_24h":float(t.get("change_percentage") or 0)}
    async def close(self): await self.client.aclose()
