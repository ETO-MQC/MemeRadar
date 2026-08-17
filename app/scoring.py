from __future__ import annotations

def clamp(v, lo=0.0, hi=100.0): return max(lo, min(hi, float(v)))

def candidate_score(c: dict, narrative_score: float = 50.0, risk_status: str = "unverified") -> tuple[float, dict]:
    liq = float(c.get("liquidity_usd") or 0)
    v1 = float(c.get("volume_h1") or 0)
    buys = int(c.get("buys_m5") or 0)
    sells = int(c.get("sells_m5") or 0)
    age = float(c.get("age_minutes") or 99999)
    chg = float(c.get("change_h1") or 0)

    liq_s = clamp((liq / 50000) * 100)
    vol_s = clamp((v1 / 50000) * 100)
    flow = 50 if buys+sells == 0 else clamp(100 * buys / (buys+sells))
    age_s = 100 if age <= 30 else 85 if age <= 120 else 65 if age <= 360 else 30
    momentum = clamp(50 + chg * 0.7)
    risk = {"pass":100,"warn":55,"unverified":45,"fail":0}.get(risk_status,45)
    parts = {"liquidity":liq_s,"volume":vol_s,"buy_flow":flow,"freshness":age_s,"momentum":momentum,"narrative":clamp(narrative_score),"risk":risk}
    score = (0.16*liq_s + 0.18*vol_s + 0.13*flow + 0.12*age_s + 0.10*momentum + 0.16*parts["narrative"] + 0.15*risk)
    if risk_status == "fail": score = min(score, 25)
    return round(clamp(score),1), {k:round(v,1) for k,v in parts.items()}
