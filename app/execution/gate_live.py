from __future__ import annotations
from ..config import env

CONFIRM="I_UNDERSTAND_SPOT_RISK"
class GateLiveExecutor:
    def __init__(self):
        self.enabled=env("LIVE_TRADING_ENABLED","false").lower()=="true" and env("LIVE_ARM_CODE")==CONFIRM
        self.key=env("GATE_API_KEY"); self.secret=env("GATE_API_SECRET")
    def status(self):
        return {"armed":bool(self.enabled and self.key and self.secret),"required_arm_code":CONFIRM,"spot_only":True}
    def _exchange(self):
        if not (self.enabled and self.key and self.secret): raise RuntimeError("Gate实盘未解锁；保持模拟盘是默认行为。")
        import ccxt
        ex=ccxt.gateio({"apiKey":self.key,"secret":self.secret,"enableRateLimit":True})
        ex.load_markets(); return ex
    def market_buy_usdt(self,pair:str,stake_usdt:float):
        ex=self._exchange(); symbol=pair.replace("_","/"); ticker=ex.fetch_ticker(symbol); price=float(ticker["last"])
        amount=float(ex.amount_to_precision(symbol,stake_usdt/price)); return ex.create_order(symbol,"market","buy",amount)
    def market_sell(self,pair:str,amount:float):
        ex=self._exchange(); symbol=pair.replace("_","/"); amount=float(ex.amount_to_precision(symbol,amount)); return ex.create_order(symbol,"market","sell",amount)
