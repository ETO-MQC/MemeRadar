from __future__ import annotations
from ..storage import Storage

class PaperExecutor:
    def __init__(self,storage:Storage,settings:dict): self.s=storage; self.cfg=settings
    def can_open(self,stake:float):
        summary=self.s.paper_summary(float(self.cfg["paper"]["starting_balance_usdt"]))
        if summary["open_positions"]>=int(self.cfg["paper"]["max_open_positions"]): return False,"达到最大同时持仓数"
        free=summary["equity"]-summary["locked_cost"]
        if free<stake:return False,"模拟资金不足"
        return True,"ok"
    def buy(self,candidate:dict,strategy:str,stake:float,price:float):
        ok,reason=self.can_open(stake)
        if not ok: raise ValueError(reason)
        if self.s.get_open_position_for(candidate["token_key"],strategy): raise ValueError("该策略已有同币种持仓")
        pid=self.s.open_position(candidate,strategy,stake,price)
        self.s.event("info","paper_buy",f"模拟买入 {candidate.get('symbol')} {stake:.2f}U",{"position_id":pid,"strategy":strategy,"price":price})
        return pid

    def mark_and_manage(self,p:dict,price:float):
        self.s.update_mark(p["id"],price)
        entry=float(p["entry_price"]); gain=(price/entry-1)*100 if entry else 0
        high=max(float(p["highest_price"] or entry),price); draw=(high-price)/high*100 if high else 0
        if p["strategy"]=="collector":
            c=self.cfg["collector"]
            if gain<=-float(c["hard_stop_loss_pct"]): self.s.close_position(p["id"],price,"collector_hard_stop"); return
            if not int(p.get("principal_recovered") or 0) and gain>=float(c["recover_principal_at_pct"]):
                self.s.partial_sell(p["id"],float(p["qty"])*float(c["recover_fraction"]),price,"2x回收本金模式")
                return
            if int(p.get("principal_recovered") or 0) and draw>=float(c["moonbag_trailing_stop_pct"]): self.s.close_position(p["id"],price,"moonbag_trailing_stop"); return
        else:
            c=self.cfg["dip"]
            if gain>=float(c["take_profit_pct"]): self.s.close_position(p["id"],price,"dip_take_profit"); return
            if gain<=-float(c["stop_loss_pct"]): self.s.close_position(p["id"],price,"dip_stop_loss"); return
            if gain>=float(c["trailing_start_pct"]) and draw>=float(c["trailing_stop_pct"]): self.s.close_position(p["id"],price,"dip_trailing_stop"); return
