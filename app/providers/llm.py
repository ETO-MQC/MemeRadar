from __future__ import annotations
import json, re
import httpx
from ..config import env

class LLMProvider:
    def __init__(self):
        self.enabled=env("LLM_ENABLED","false").lower()=="true"; self.base=env("LLM_BASE_URL","http://127.0.0.1:8092/v1").rstrip("/")
        self.key=env("LLM_API_KEY"); self.model=env("LLM_MODEL","local-model"); self.client=httpx.AsyncClient(timeout=45)
    async def narrative_score(self,candidate:dict,social_items:list[dict]):
        if not self.enabled:return 50.0,"LLM未启用；仅使用链上/市场数据评分。"
        related=[]; sym=(candidate.get("symbol") or "").lower(); name=(candidate.get("name") or "").lower()
        for i in social_items:
            txt=(i.get("text") or "").lower()
            if (sym and sym in txt) or (name and len(name)>2 and name in txt): related.append(i.get("text","")[:500])
        context="\n---\n".join(related[:8]) or "暂无直接匹配的社交内容。"
        prompt=f'''你是热点叙事筛选器，不负责下单。评估这个新代币是否存在可验证的现实/网络热点催化，而不是只看币名。\n代币:{candidate.get('name')} ({candidate.get('symbol')}) 链:{candidate.get('chain')}\n1h成交量:{candidate.get('volume_h1')} 流动性:{candidate.get('liquidity_usd')} 1h涨跌:{candidate.get('change_h1')}%\n相关社交内容:\n{context}\n只返回JSON: {{"score":0到100,"summary":"不超过80字","red_flags":["..."]}}。没有证据时分数不得高于55。'''
        headers={"Content-Type":"application/json"};
        if self.key: headers["Authorization"]=f"Bearer {self.key}"
        try:
            r=await self.client.post(self.base+"/chat/completions",headers=headers,json={"model":self.model,"messages":[{"role":"user","content":prompt}],"temperature":0.1,"max_tokens":300}); r.raise_for_status()
            text=r.json()["choices"][0]["message"]["content"]
            m=re.search(r"\{.*\}",text,re.S); obj=json.loads(m.group(0) if m else text)
            return float(obj.get("score",50)), obj.get("summary","") + (("；风险:"+"、".join(obj.get("red_flags") or [])) if obj.get("red_flags") else "")
        except Exception as e:return 50.0,f"LLM调用失败，按中性分处理：{e}"
    async def close(self): await self.client.aclose()
