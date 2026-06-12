from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "router.sqlite3"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS route_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            task TEXT NOT NULL,
            mode TEXT NOT NULL,
            budget TEXT NOT NULL,
            primary_agent TEXT NOT NULL,
            verifier_agent TEXT,
            risk TEXT NOT NULL,
            task_type TEXT NOT NULL,
            score_breakdown TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def log_route(task: str, mode: str, budget: str, decision: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO route_events
            (task, mode, budget, primary_agent, verifier_agent, risk, task_type, score_breakdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task,
                mode,
                budget,
                decision["primary_agent"]["id"],
                decision["verifier_agent"]["id"] if decision.get("verifier_agent") else None,
                decision["risk"],
                decision["task_type"],
                json.dumps(decision["score_breakdown"]),
            ),
        )
        conn.commit()


def dashboard_stats() -> dict[str, Any]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM route_events").fetchone()["count"]
        by_agent = conn.execute("SELECT primary_agent, COUNT(*) AS count FROM route_events GROUP BY primary_agent ORDER BY count DESC").fetchall()
        by_type = conn.execute("SELECT task_type, COUNT(*) AS count FROM route_events GROUP BY task_type ORDER BY count DESC").fetchall()
        recent = conn.execute("SELECT * FROM route_events ORDER BY id DESC LIMIT 20").fetchall()
    return {
        "total": total,
        "by_agent": [dict(row) for row in by_agent],
        "by_type": [dict(row) for row in by_type],
        "recent": [dict(row) for row in recent],
    }
