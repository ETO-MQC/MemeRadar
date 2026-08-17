from __future__ import annotations

def eligible(d:dict,cfg:dict)->bool:
    return (float(d.get("drawdown_pct") or 0)>=float(cfg["drawdown_trigger_pct"]) and
            float(d.get("rebound_pct") or 0)>=float(cfg["rebound_confirm_pct"]) and
            float(d.get("quote_volume_24h") or 0)>=float(cfg["min_quote_volume_usdt_24h"]))
