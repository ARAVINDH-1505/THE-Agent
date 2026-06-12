from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AgentProfile


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else project_root() / "config" / "agents.json"
    return json.loads(config_path.read_text(encoding="utf-8-sig"))


def load_agents(path: str | Path | None = None) -> list[AgentProfile]:
    config = load_config(path)
    return [AgentProfile(**item) for item in config["agents"]]

