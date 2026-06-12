from __future__ import annotations

import json
import sys
from typing import Any

from .models import RouteRequest
from .router import route_task
from .storage import log_route

SERVER_INFO = {"name": "agent-router-mcp-python", "version": "0.1.0"}

TOOLS = [
    {
        "name": "route_task",
        "description": "Choose Claude, Cursor, Codex, or Antigravity and return an optimized handoff prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "mode": {"type": "string", "enum": ["fast", "balanced", "careful", "research", "coding", "build", "learning"], "default": "balanced"},
                "budget": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                "project": {"type": "string"},
                "context": {"type": "string"},
                "preferred_agent": {"type": "string", "enum": ["claude", "cursor", "codex", "antigravity"]},
                "allow_multi_agent": {"type": "boolean", "default": True},
            },
            "required": ["task"],
        },
    },
    {
        "name": "explain_agents",
        "description": "Explain how the four local applications are used by this router.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def respond(message_id: Any, result: Any) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": message_id, "result": result}) + "\n")
    sys.stdout.flush()


def fail(message_id: Any, code: int, message: str) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}) + "\n")
    sys.stdout.flush()


def explain_agents() -> str:
    return (
        "This MCP is a router, not a hidden remote control for GUI apps.\n\n"
        "Claude: use for research, long reasoning, paper/document synthesis, and careful review.\n"
        "Codex: use for repository edits, terminal work, tests, debugging, and GitHub changes.\n"
        "Cursor: use for focused IDE edits and small code navigation tasks.\n"
        "Antigravity: use for larger app prototypes and product workflow building.\n\n"
        "The router chooses one, optimizes the prompt, redacts obvious secrets, logs the decision, "
        "and recommends a verifier only when useful."
    )


def handle_tool_call(message_id: Any, params: dict[str, Any]) -> None:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name == "route_task":
        request = RouteRequest(
            task=arguments["task"],
            mode=arguments.get("mode", "balanced"),
            budget=arguments.get("budget", "medium"),
            project=arguments.get("project"),
            context=arguments.get("context"),
            preferred_agent=arguments.get("preferred_agent"),
            allow_multi_agent=arguments.get("allow_multi_agent", True),
        )
        decision = route_task(request)
        log_route(request.task, request.mode, request.budget, decision)
        respond(message_id, {"content": [{"type": "text", "text": json.dumps(decision, indent=2)}]})
        return
    if name == "explain_agents":
        respond(message_id, {"content": [{"type": "text", "text": explain_agents()}]})
        return
    fail(message_id, -32601, f"Unknown tool: {name}")


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
            method = msg.get("method")
            message_id = msg.get("id")
            if method == "initialize":
                respond(message_id, {"protocolVersion": "2024-11-05", "serverInfo": SERVER_INFO, "capabilities": {"tools": {}}})
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                respond(message_id, {"tools": TOOLS})
            elif method == "tools/call":
                handle_tool_call(message_id, msg.get("params", {}))
            else:
                fail(message_id, -32601, f"Unknown method: {method}")
        except Exception as exc:
            fail(None, -32603, str(exc))


if __name__ == "__main__":
    main()

