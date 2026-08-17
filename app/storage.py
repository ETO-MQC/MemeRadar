from __future__ import annotations
import json, sqlite3, threading
from datetime import datetime, timezone
from pathlib import Path
from .config import ROOT

DB_PATH = ROOT / "data" / "memeradar.db"

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

class Storage:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self._init()

    def _init(self):
        with self.lock:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS candidates(
              token_key TEXT PRIMARY KEY, chain TEXT, address TEXT, symbol TEXT, name TEXT,
              source TEXT, url TEXT, first_seen TEXT, updated_at TEXT, score REAL,
              risk_status TEXT, price_usd REAL, liquidity_usd REAL, volume_h1 REAL,
              market_cap REAL, age_minutes REAL, buys_m5 INTEGER, sells_m5 INTEGER,
              change_m5 REAL, change_h1 REAL, narrative TEXT, raw_json TEXT
            );
            CREATE TABLE IF NOT EXISTS price_points(
              id INTEGER PRIMARY KEY AUTOINCREMENT, token_key TEXT, ts TEXT, price REAL
            );
            CREATE INDEX IF NOT EXISTS idx_price_token_ts ON price_points(token_key, ts);
            CREATE TABLE IF NOT EXISTS paper_positions(
              id INTEGER PRIMARY KEY AUTOINCREMENT, token_key TEXT, chain TEXT, symbol TEXT,
              strategy TEXT, entry_price REAL, qty REAL, remaining_qty REAL, stake_usdt REAL,
              opened_at TEXT, closed_at TEXT, status TEXT, highest_price REAL,
              current_price REAL, realized_pnl REAL DEFAULT 0, exit_price REAL,
              exit_reason TEXT, principal_recovered INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, kind TEXT, message TEXT, meta_json TEXT
            );
            CREATE TABLE IF NOT EXISTS social_items(
              item_key TEXT PRIMARY KEY, source TEXT, author TEXT, ts TEXT, text TEXT, url TEXT, raw_json TEXT
            );
            """)
            self.conn.commit()

    def event(self, level: str, kind: str, message: str, meta=None):
        with self.lock:
            self.conn.execute("INSERT INTO events(ts,level,kind,message,meta_json) VALUES(?,?,?,?,?)",
                              (utcnow(), level, kind, message, json.dumps(meta or {}, ensure_ascii=False)))
            self.conn.commit()

    def upsert_candidate(self, c: dict):
        keys = ["token_key","chain","address","symbol","name","source","url","first_seen","updated_at","score",
                "risk_status","price_usd","liquidity_usd","volume_h1","market_cap","age_minutes","buys_m5","sells_m5",
                "change_m5","change_h1","narrative","raw_json"]
        vals = [c.get(k) for k in keys]
        qs = ",".join("?" for _ in keys)
        updates = ",".join(f"{k}=excluded.{k}" for k in keys if k != "token_key")
        with self.lock:
            self.conn.execute(f"INSERT INTO candidates({','.join(keys)}) VALUES({qs}) ON CONFLICT(token_key) DO UPDATE SET {updates}", vals)
            if c.get("price_usd"):
                self.conn.execute("INSERT INTO price_points(token_key,ts,price) VALUES(?,?,?)", (c["token_key"], utcnow(), c["price_usd"]))
            self.conn.commit()

    def list_candidates(self, limit=100):
        with self.lock:
            rows = self.conn.execute("SELECT * FROM candidates ORDER BY score DESC, updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_candidate(self, token_key: str):
        with self.lock:
            r = self.conn.execute("SELECT * FROM candidates WHERE token_key=?", (token_key,)).fetchone()
            return dict(r) if r else None

    def open_position(self, c: dict, strategy: str, stake: float, price: float):
        qty = stake / price
        with self.lock:
            cur = self.conn.execute("""INSERT INTO paper_positions(token_key,chain,symbol,strategy,entry_price,qty,remaining_qty,stake_usdt,
                opened_at,status,highest_price,current_price,realized_pnl) VALUES(?,?,?,?,?,?,?,?,?,'open',?,?,0)""",
                (c["token_key"], c.get("chain","gate"), c.get("symbol","?"), strategy, price, qty, qty, stake, utcnow(), price, price))
            self.conn.commit()
            return cur.lastrowid

    def list_positions(self, open_only=False):
        q = "SELECT * FROM paper_positions" + (" WHERE status='open'" if open_only else "") + " ORDER BY id DESC"
        with self.lock:
            return [dict(r) for r in self.conn.execute(q).fetchall()]

    def get_open_position_for(self, token_key: str, strategy: str | None = None):
        q = "SELECT * FROM paper_positions WHERE token_key=? AND status='open'"
        args = [token_key]
        if strategy:
            q += " AND strategy=?"; args.append(strategy)
        q += " ORDER BY id DESC LIMIT 1"
        with self.lock:
            r = self.conn.execute(q, args).fetchone()
            return dict(r) if r else None

    def update_mark(self, pid: int, price: float):
        with self.lock:
            self.conn.execute("UPDATE paper_positions SET current_price=?, highest_price=MAX(highest_price,?) WHERE id=? AND status='open'", (price, price, pid))
            self.conn.commit()

    def partial_sell(self, pid: int, qty_to_sell: float, price: float, reason: str):
        with self.lock:
            p = self.conn.execute("SELECT * FROM paper_positions WHERE id=?", (pid,)).fetchone()
            if not p or p["status"] != "open": return
            qty_to_sell = min(float(qty_to_sell), float(p["remaining_qty"]))
            pnl = qty_to_sell * (price - float(p["entry_price"]))
            remain = float(p["remaining_qty"]) - qty_to_sell
            self.conn.execute("UPDATE paper_positions SET remaining_qty=?, current_price=?, realized_pnl=realized_pnl+?, principal_recovered=1 WHERE id=?",
                              (remain, price, pnl, pid))
            self.event("info","paper_partial_sell",f"{p['symbol']} 部分止盈：{reason}", {"position_id":pid,"qty":qty_to_sell,"price":price,"pnl":pnl})
            self.conn.commit()

    def close_position(self, pid: int, price: float, reason: str):
        with self.lock:
            p = self.conn.execute("SELECT * FROM paper_positions WHERE id=?", (pid,)).fetchone()
            if not p or p["status"] != "open": return
            remaining = float(p["remaining_qty"])
            pnl = remaining * (price - float(p["entry_price"]))
            total_pnl = float(p["realized_pnl"] or 0) + pnl
            self.conn.execute("""UPDATE paper_positions SET remaining_qty=0,current_price=?,exit_price=?,closed_at=?,status='closed',
                exit_reason=?,realized_pnl=? WHERE id=?""", (price, price, utcnow(), reason, total_pnl, pid))
            self.conn.commit()
            self.event("info","paper_close",f"{p['symbol']} 平仓：{reason}", {"position_id":pid,"price":price,"pnl":total_pnl})

    def add_social(self, item: dict):
        with self.lock:
            self.conn.execute("""INSERT OR IGNORE INTO social_items(item_key,source,author,ts,text,url,raw_json) VALUES(?,?,?,?,?,?,?)""",
                              (item["item_key"],item.get("source"),item.get("author"),item.get("ts"),item.get("text"),item.get("url"),json.dumps(item.get("raw",{}),ensure_ascii=False)))
            self.conn.commit()

    def list_social(self, limit=60):
        with self.lock:
            return [dict(r) for r in self.conn.execute("SELECT * FROM social_items ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()]

    def list_events(self, limit=100):
        with self.lock:
            return [dict(r) for r in self.conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def paper_summary(self, starting_balance: float):
        with self.lock:
            pos = [dict(r) for r in self.conn.execute("SELECT * FROM paper_positions").fetchall()]
        realized = sum(float(p.get("realized_pnl") or 0) for p in pos if p["status"] == "closed")
        # 部分止盈已记在 open 仓 realized_pnl 中，也计入。
        realized += sum(float(p.get("realized_pnl") or 0) for p in pos if p["status"] == "open")
        unrealized = sum(float(p["remaining_qty"]) * (float(p["current_price"] or p["entry_price"]) - float(p["entry_price"])) for p in pos if p["status"] == "open")
        locked = sum(float(p["remaining_qty"]) * float(p["entry_price"]) for p in pos if p["status"] == "open")
        return {"starting_balance":starting_balance,"realized_pnl":realized,"unrealized_pnl":unrealized,
                "equity":starting_balance+realized+unrealized,"locked_cost":locked,
                "open_positions":sum(1 for p in pos if p["status"]=="open")}
