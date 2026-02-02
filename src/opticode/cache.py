from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class Cache:
    facts: List[str]
    history: Dict[str, str]


def load_cache(facts_path: Path, history_path: Path) -> Cache:
    facts = []
    history = {}
    try:
        data = json.loads(facts_path.read_text(encoding="utf-8"))
        facts = data.get("facts", []) if isinstance(data, dict) else []
    except Exception:
        facts = []
    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
        history = data.get("history", {}) if isinstance(data, dict) else {}
    except Exception:
        history = {}
    facts = [str(f).strip() for f in facts if str(f).strip()]
    history = {str(k): str(v) for k, v in history.items()} if isinstance(history, dict) else {}
    return Cache(facts=facts, history=history)


def save_facts(facts_path: Path, facts: List[str]) -> None:
    facts_path.write_text(json.dumps({"facts": facts}, indent=2), encoding="utf-8")


def save_history(history_path: Path, history: Dict[str, str]) -> None:
    history_path.write_text(json.dumps({"history": history}, indent=2), encoding="utf-8")
