from __future__ import annotations
import json, os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SETTINGS_PATH = ROOT / "config" / "settings.json"

def load_settings() -> dict:
    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data: dict) -> None:
    tmp = SETTINGS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SETTINGS_PATH)

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)
