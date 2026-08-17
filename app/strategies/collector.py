from __future__ import annotations
import json
from datetime import datetime, timezone
from ..scoring import candidate_score

async def enrich_candidate(c, goplus, llm, social_items):
    risk,risk_raw=await goplus.check(c["chain"],c["address"])
    narrative_score,narrative=await llm.narrative_score(c,social_items)
    score,parts=candidate_score(c,narrative_score,risk)
    c.update({"risk_status":risk,"score":score,"narrative":narrative,"updated_at":datetime.now(timezone.utc).isoformat(),
              "raw_json":json.dumps({"score_parts":parts,"risk":risk_raw,"profile":c.pop("profile",{}),"pair":c.pop("pair",{})},ensure_ascii=False)})
    return c

def eligible(c,cfg):
    return (float(c.get("score") or 0)>=float(cfg["min_score"]) and float(c.get("age_minutes") or 999999)<=float(cfg["max_age_minutes"]) and
            float(c.get("liquidity_usd") or 0)>=float(cfg["min_liquidity_usd"]) and float(c.get("volume_h1") or 0)>=float(cfg["min_volume_h1_usd"]) and
            int(c.get("buys_m5") or 0)>=int(cfg["min_buys_m5"]) and c.get("risk_status")!="fail")
