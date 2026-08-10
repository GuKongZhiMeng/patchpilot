from __future__ import annotations

import json
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from .errors import PatchPilotError


_SECRET = re.compile(r"(?i)(api[_-]?key|token|authorization|password)\s*[:=]|sk-[a-z0-9_-]{8,}")
_WORDS = re.compile(r"[\w-]+", re.UNICODE)


@dataclass(frozen=True)
class Memory:
    kind: str
    text: str
    created_at: float


class MemoryStore:
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(str(path))
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS memory(
          id INTEGER PRIMARY KEY, workspace_id TEXT NOT NULL, kind TEXT NOT NULL,
          text TEXT NOT NULL, created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_event(
          id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, step INTEGER NOT NULL,
          type TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL
        );
        """)
        self.connection.commit()

    def close(self):
        self.connection.close()

    def add(self, workspace_id: str, kind: str, text: str) -> None:
        if kind not in {"convention", "decision", "failure"}:
            raise PatchPilotError("invalid_memory", "Unsupported memory kind")
        if _SECRET.search(text):
            raise PatchPilotError("sensitive_memory", "Secret-like text cannot be stored")
        self.connection.execute(
            "INSERT INTO memory(workspace_id,kind,text,created_at) VALUES(?,?,?,?)",
            (workspace_id, kind, text, time.time()),
        )
        self.connection.commit()

    def search(self, workspace_id: str, query: str, limit: int = 5) -> list[Memory]:
        if limit <= 0:
            return []
        terms = {word.lower() for word in _WORDS.findall(query)}
        rows = self.connection.execute(
            "SELECT kind,text,created_at FROM memory WHERE workspace_id=?", (workspace_id,)
        ).fetchall()
        weights = {"convention": 0.3, "decision": 0.2, "failure": 0.1}
        ranked = []
        for kind, text, created_at in rows:
            overlap = len(terms & {word.lower() for word in _WORDS.findall(text)})
            ranked.append((overlap + weights[kind], created_at, Memory(kind, text, created_at)))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [item[2] for item in ranked[:limit]]

    def record_event(self, run_id: str, step: int, event_type: str, payload: dict) -> None:
        safe = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if _SECRET.search(safe):
            raise PatchPilotError("sensitive_event", "Secret-like event cannot be stored")
        self.connection.execute(
            "INSERT INTO run_event(run_id,step,type,payload,created_at) VALUES(?,?,?,?,?)",
            (run_id, step, event_type, safe, time.time()),
        )
        self.connection.commit()

    def events(self, run_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT step,type,payload,created_at FROM run_event WHERE run_id=? ORDER BY id", (run_id,)
        ).fetchall()
        return [{"step": s, "type": t, "payload": json.loads(p), "created_at": c} for s, t, p, c in rows]
