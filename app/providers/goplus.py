from __future__ import annotations
import httpx
from ..config import env

class GoPlusProvider:
    def __init__(self): self.client=httpx.AsyncClient(timeout=10); self.token=env("GOPLUS_TOKEN")
    async def check(self,chain,address):
        if not self.token: return "unverified", {"reason":"GOPLUS_TOKEN not configured"}
        headers={"Authorization":f"Bearer {self.token}"}
        if chain=="solana": url="https://api.gopluslabs.io/api/v1/solana/token_security"; params={"contract_addresses":address}
        elif chain=="bsc": url="https://api.gopluslabs.io/api/v1/token_security/56"; params={"contract_addresses":address}
        else:return "unverified",{"reason":"unsupported chain"}
        try:
            r=await self.client.get(url,params=params,headers=headers); r.raise_for_status(); data=r.json(); result=data.get("result") or {}
            rec=result.get(address) or result.get(address.lower()) or (next(iter(result.values())) if isinstance(result,dict) and result else {})
            s=str(rec).lower()
            hard_bad = any(flag in s for flag in ["honeypot': '1","is_honeypot\": \"1","malicious_address': '1","cannot_sell_all': '1"])
            warn = any(flag in s for flag in ["is_mintable': '1","is_proxy': '1","hidden_owner': '1"])
            return ("fail" if hard_bad else "warn" if warn else "pass"), rec
        except Exception as e:return "unverified",{"error":str(e)}
    async def close(self): await self.client.aclose()
