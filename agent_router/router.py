from __future__ import annotations

from dataclasses import asdict

from .config import load_config, load_agents
from .models import AgentProfile, RouteRequest
from .prompt_optimizer import optimize_prompt
from .security import redact_sensitive_data, scan_for_sensitive_data

TASK_KEYWORDS = {
    "coding": ["code", "bug", "test", "repo", "refactor", "python", "typescript", "api", "compile", "debug", "error", "stack trace"],
    "research": ["paper", "literature", "model", "experiment", "metric", "baseline", "ablation", "dataset", "citation"],
    "writing": ["document", "proposal", "email", "summary", "explain", "write", "draft"],
    "build": ["build", "prototype", "app", "dashboard", "full-stack", "feature", "workflow"],
    "review": ["review", "verify", "audit", "risk", "security", "hallucination", "check"],
}

AGENT_AFFINITY = {
    "codex": {"coding": 6, "review": 4, "build": 3, "research": 1, "writing": 1, "general": 2},
    "claude": {"research": 6, "writing": 5, "review": 5, "build": 2, "coding": 2, "general": 4},
    "cursor": {"coding": 5, "review": 2, "build": 2, "research": 1, "writing": 1, "general": 2},
    "antigravity": {"build": 6, "coding": 3, "review": 2, "research": 1, "writing": 1, "general": 2},
}


def classify_task(task: str) -> str:
    lower = task.lower()
    scores = []
    for task_type, words in TASK_KEYWORDS.items():
        score = sum(1 for word in words if word in lower)
        scores.append((score, task_type))
    score, task_type = max(scores)
    return task_type if score > 0 else "general"


def estimate_risk(request: RouteRequest, task_type: str) -> str:
    text = f"{request.task}\n{request.context or ''}".lower()
    high_risk = ["production", "security", "credential", "payment", "delete", "private key", "medical", "legal", "financial"]
    medium_risk = ["architecture", "migration", "database", "deploy", "benchmark", "experiment", "model evaluation"]
    if request.mode == "careful" or any(term in text for term in high_risk):
        return "high"
    if task_type in {"research", "review"} or any(term in text for term in medium_risk):
        return "medium"
    return "low"


def score_agent(agent: AgentProfile, request: RouteRequest, task_type: str, risk: str) -> float:
    score = AGENT_AFFINITY[agent.id].get(task_type, 1)
    if request.mode == "fast":
        score -= agent.latency * 0.8
        score -= agent.cost * 0.7
    if request.mode == "careful":
        score += 2 if agent.context_window == "very_large" else 0
        score += 2 if task_type == "review" else 0
    if request.mode == "coding" and agent.id in {"codex", "cursor"}:
        score += 3
    if request.mode == "research" and agent.id == "claude":
        score += 4
    if request.mode == "build" and agent.id == "antigravity":
        score += 3
    if request.budget == "low":
        score -= agent.cost
    if risk == "high" and agent.id == "claude":
        score += 2
    if request.preferred_agent == agent.id:
        score += 10
    return round(score, 2)


def choose_verifier(agents: list[AgentProfile], primary: AgentProfile, task_type: str) -> AgentProfile | None:
    by_id = {agent.id: agent for agent in agents}
    if task_type == "coding" and primary.id != "codex":
        return by_id["codex"]
    if primary.id != "claude":
        return by_id["claude"]
    return by_id["codex"]


def create_handoff(primary: AgentProfile, verifier: AgentProfile | None, task_type: str, risk: str, prompt: str) -> str:
    text = (
        f"Recommended agent: {primary.display_name}\n"
        f"Task type: {task_type}\n"
        f"Risk: {risk}\n\n"
        "Paste this optimized prompt into the selected agent:\n"
        "```text\n"
        f"{prompt}\n"
        "```"
    )
    if verifier:
        text += (
            f"\n\nVerification pass:\nAfter {primary.display_name} responds, ask {verifier.display_name} "
            "to review only for correctness, missing assumptions, security issues, and unnecessary token use."
        )
    return text


def route_task(request: RouteRequest) -> dict:
    config = load_config()
    agents = load_agents()
    raw_input = f"{request.task}\n{request.context or ''}"
    findings = scan_for_sensitive_data(raw_input)
    safe_task = redact_sensitive_data(request.task) if findings else request.task
    safe_context = redact_sensitive_data(request.context) if findings and request.context else request.context
    safe_request = RouteRequest(**{**request.__dict__, "task": safe_task, "context": safe_context})
    task_type = classify_task(safe_task)
    risk = estimate_risk(safe_request, task_type)
    max_chars = config["policies"]["max_prompt_characters"][request.budget]
    prompt = optimize_prompt(safe_task, request.mode, request.budget, max_chars, safe_context)

    scored = sorted(
        [(agent, score_agent(agent, request, task_type, risk)) for agent in agents],
        key=lambda item: item[1],
        reverse=True,
    )
    primary = scored[0][0]
    should_verify = request.allow_multi_agent and (risk == "high" or request.mode == "careful")
    verifier = choose_verifier(agents, primary, task_type) if should_verify else None

    return {
        "primary_agent": asdict(primary),
        "verifier_agent": asdict(verifier) if verifier else None,
        "risk": risk,
        "task_type": task_type,
        "score_breakdown": {agent.id: score for agent, score in scored},
        "optimized_prompt": prompt,
        "security_findings": findings,
        "handoff": create_handoff(primary, verifier, task_type, risk, prompt),
        "notes": [
            "This version routes and prepares prompts; it does not secretly control GUI apps.",
            "Paste the handoff prompt into the recommended app, or add a direct adapter later where the app exposes an API/CLI.",
            "Use the verifier only for high-risk or careful-mode work to save tokens.",
        ],
    }
