from __future__ import annotations

import argparse
import json

from .models import RouteRequest
from .router import route_task
from .storage import log_route


def main() -> None:
    parser = argparse.ArgumentParser(description="Route a task to Claude, Cursor, Codex, or Antigravity.")
    parser.add_argument("task", help="Task to route")
    parser.add_argument("--mode", default="balanced", choices=["fast", "balanced", "careful", "research", "coding", "build", "learning"])
    parser.add_argument("--budget", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--context", default=None)
    parser.add_argument("--preferred-agent", default=None, choices=["claude", "cursor", "codex", "antigravity"])
    parser.add_argument("--single-agent", action="store_true")
    args = parser.parse_args()

    request = RouteRequest(
        task=args.task,
        mode=args.mode,
        budget=args.budget,
        context=args.context,
        preferred_agent=args.preferred_agent,
        allow_multi_agent=not args.single_agent,
    )
    decision = route_task(request)
    log_route(args.task, args.mode, args.budget, decision)
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
