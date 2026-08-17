from __future__ import annotations
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import httpx
from ..config import env

class SocialProvider:
    def __init__(self):
        self.client=httpx.AsyncClient(timeout=12,headers={"User-Agent":"MemeRadar-MVP/1.0"})
        self.x_token=env("X_BEARER_TOKEN")

    def _parse_feed(self, text:str, url:str):
        out=[]
        try: root=ET.fromstring(text)
        except Exception: return out
        channel=root.find('channel') if root.tag.lower().endswith('rss') else None
        if channel is not None:
            author=(channel.findtext('title') or url).strip()
            for e in channel.findall('item')[:10]:
                title=(e.findtext('title') or '').strip(); desc=(e.findtext('description') or '').strip(); link=(e.findtext('link') or '').strip(); ts=(e.findtext('pubDate') or datetime.now(timezone.utc).isoformat())
                body=(title+' '+desc).strip(); key=hashlib.sha1((url+link+body).encode()).hexdigest(); out.append({"item_key":key,"source":"rss","author":author,"ts":ts,"text":body[:1200],"url":link,"raw":{}})
            return out
        # Atom: namespace tolerant
        def txt(node, suffix):
            for ch in list(node):
                if ch.tag.split('}')[-1]==suffix: return (ch.text or '').strip()
            return ''
        author=txt(root,'title') or url
        for e in [x for x in list(root) if x.tag.split('}')[-1]=='entry'][:10]:
            title=txt(e,'title'); summary=txt(e,'summary') or txt(e,'content'); ts=txt(e,'published') or txt(e,'updated') or datetime.now(timezone.utc).isoformat(); link=''
            for ch in list(e):
                if ch.tag.split('}')[-1]=='link' and ch.attrib.get('href'): link=ch.attrib['href']; break
            body=(title+' '+summary).strip(); key=hashlib.sha1((url+link+body).encode()).hexdigest(); out.append({"item_key":key,"source":"atom","author":author,"ts":ts,"text":body[:1200],"url":link,"raw":{}})
        return out

    async def rss(self,urls):
        out=[]
        for url in urls:
            try:
                r=await self.client.get(url); r.raise_for_status(); out.extend(self._parse_feed(r.text,url))
            except Exception: continue
        return out

    async def x_posts(self,usernames):
        if not self.x_token or not usernames:return []
        headers={"Authorization":f"Bearer {self.x_token}"}; out=[]
        for username in usernames[:20]:
            try:
                u=await self.client.get(f"https://api.x.com/2/users/by/username/{username}",headers=headers); u.raise_for_status(); uid=(u.json().get("data") or {}).get("id")
                if not uid: continue
                p=await self.client.get(f"https://api.x.com/2/users/{uid}/tweets",headers=headers,params={"max_results":10,"tweet.fields":"created_at,public_metrics"}); p.raise_for_status()
                for x in p.json().get("data") or []:
                    out.append({"item_key":"x:"+x["id"],"source":"x","author":"@"+username,"ts":x.get("created_at") or datetime.now(timezone.utc).isoformat(),"text":x.get("text","")[:1200],"url":f"https://x.com/{username}/status/{x['id']}","raw":x})
            except Exception: continue
        return out
    async def collect(self,usernames,rss_urls): return (await self.rss(rss_urls))+(await self.x_posts(usernames))
    async def close(self): await self.client.aclose()
