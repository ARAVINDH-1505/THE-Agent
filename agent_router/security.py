from __future__ import annotations

import re

SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "possible OpenAI-style API key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "possible AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[\"']?[^\"'\s]{8,}", re.I), "possible secret assignment"),
]


def scan_for_sensitive_data(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append({
                "severity": "high",
                "pattern": label,
                "message": "Sensitive-looking content was detected and should not be sent to external agents.",
            })
    return findings


def redact_sensitive_data(text: str) -> str:
    output = text
    for pattern, label in SECRET_PATTERNS:
        output = pattern.sub(f"[REDACTED: {label}]", output)
    return output
