from __future__ import annotations
import asyncio, os, sys
import httpx
from .config import env

async def check(name,url,headers=None):
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get(url,headers=headers or {})
            print(f"[OK] {name}: HTTP {r.status_code}")
            return r.is_success
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False

async def main():
    print("MemeRadar MVP 1.0 连接诊断")
    print("Python:",sys.version.split()[0])
    await check("DEX Screener","https://api.dexscreener.com/token-profiles/latest/v1")
    await check("Gate","https://api.gateio.ws/api/v4/spot/tickers?currency_pair=DOGE_USDT")
    if env("LLM_ENABLED","false").lower()=="true":
        try:
            async with httpx.AsyncClient(timeout=8) as c:
                r=await c.get(env("LLM_BASE_URL","http://127.0.0.1:8092/v1").rstrip("/")+"/models",headers={"Authorization":f"Bearer {env('LLM_API_KEY')}"} if env('LLM_API_KEY') else {})
                print(f"[{'OK' if r.is_success else 'FAIL'}] LLM: HTTP {r.status_code}")
        except Exception as e: print("[FAIL] LLM:",e)
    else: print("[SKIP] LLM 未启用")
    if env("X_BEARER_TOKEN"):
        await check("X API","https://api.x.com/2/users/by/username/XDevelopers",{"Authorization":f"Bearer {env('X_BEARER_TOKEN')}"})
    else: print("[SKIP] X_BEARER_TOKEN 未配置")
    print("\n注意：GoPlus 未配置 Token 时主程序会标记 unverified，不会导致启动失败。")

if __name__=='__main__': asyncio.run(main())
