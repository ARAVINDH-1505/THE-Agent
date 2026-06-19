from __future__ import annotations

MODE_INSTRUCTIONS = {
    "fast": "Be concise. Solve the direct request first. Ask questions only if blocked.",
    "balanced": "Give a practical answer with enough reasoning to verify the approach.",
    "careful": "Prioritize correctness, security, and explicit assumptions. Identify risks before final recommendations.",
    "research": "Separate evidence from inference. Call out uncertainty and avoid unsupported claims.",
    "coding": "Use the existing codebase style. Make scoped changes, run relevant checks, and report verification.",
    "build": "Produce a working MVP path with concrete files, interfaces, and next actions.",
    "learning": "Explain the reasoning while keeping the answer actionable.",
}


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    compact = "\n".join(lines)
    while "\n\n\n\n" in compact:
        compact = compact.replace("\n\n\n\n", "\n\n\n")
    return compact.strip()


def trim_long_logs(text: str, limit: int = 80) -> str:
    lines = text.split("\n")
    if len(lines) <= limit:
        return text
    head = lines[:30]
    tail = lines[-40:]
    removed = len(lines) - len(head) - len(tail)
    return "\n".join(head + ["", f"[...{removed} lines removed by agent-router...]", ""] + tail)


def hard_limit(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    keep_head = int(max_chars * 0.55)
    keep_tail = max_chars - keep_head - 120
    return text[:keep_head] + "\n\n[...middle truncated to respect token budget...]\n\n" + text[-keep_tail:]


def optimize_prompt(task: str, mode: str, budget: str, max_chars: int, context: str | None = None) -> str:
    clean_task = normalize_whitespace(task)
    clean_context = trim_long_logs(normalize_whitespace(context)) if context else ""
    parts = [
        f"Task:\n{clean_task}",
        f"Mode:\n{mode}",
        f"Operating instruction:\n{MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS['balanced'])}",
    ]
    if clean_context:
        parts.append(f"Relevant context:\n{clean_context}")
    parts.append(
        "Response requirements:\n"
        "- Prefer precise, testable steps.\n"
        "- Avoid inventing facts, files, APIs, or experiment results.\n"
        "- Mention assumptions.\n"
        "- If code is changed, include verification steps."
    )
    return hard_limit("\n\n".join(parts), max_chars)
