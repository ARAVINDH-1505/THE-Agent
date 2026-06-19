from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AgentId = Literal["claude", "cursor", "codex", "antigravity"]
Mode = Literal["fast", "balanced", "careful", "research", "coding", "build", "learning"]
Budget = Literal["low", "medium", "high"]
Risk = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class AgentProfile:
    id: AgentId
    display_name: str
    interface: str
    strengths: list[str]
    avoid_for: list[str]
    cost: int
    latency: int
    context_window: str
    can_execute_directly: bool


@dataclass(frozen=True)
class RouteRequest:
    task: str
    mode: Mode = "balanced"
    budget: Budget = "medium"
    project: str | None = None
    context: str | None = None
    preferred_agent: AgentId | None = None
    allow_multi_agent: bool = True


@dataclass(frozen=True)
class RouteDecision:
    primary_agent: dict[str, Any]
    verifier_agent: dict[str, Any] | None
    risk: Risk
    task_type: str
    score_breakdown: dict[str, float]
    optimized_prompt: str
    security_findings: list[dict[str, str]]
    handoff: str
    notes: list[str]
