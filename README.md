# Agent Router MCP Python

A local MCP-style router that helps you choose the right assistant for each task across the tools you already use:

- Claude
- Codex
- Cursor
- Antigravity

This project is built for personal and small-team productivity. It reduces wasted tokens by choosing the right agent, trimming noisy context, redacting obvious secrets, and logging decisions in a local dashboard.

## Current Status

This is the initial Python MVP.

It can:

1. Accept a task from CLI, MCP, or dashboard.
2. Classify the task as `coding`, `research`, `writing`, `build`, `review`, or `general`.
3. Estimate risk as `low`, `medium`, or `high`.
4. Choose one primary agent from Claude, Codex, Cursor, or Antigravity.
5. Generate an optimized handoff prompt.
6. Redact obvious secrets before prompt generation.
7. Log route decisions into local SQLite.
8. Show a local dashboard at `http://127.0.0.1:8765`.

It does not yet directly control all four GUI applications. For now, it creates the optimized instruction that you paste into the recommended app. Direct adapters can be added later where an app exposes a stable API, CLI, or MCP interface.

## How The Four Apps Are Used

| App | Best For | Router Behavior |
| --- | --- | --- |
| Codex | Repo edits, terminal work, tests, debugging, refactoring, GitHub changes | Usually selected for coding tasks |
| Claude | Research, papers, planning, long reasoning, careful review | Usually selected for research or high-risk review |
| Cursor | Focused IDE edits, code navigation, small local fixes | Useful when you are already working inside the IDE |
| Antigravity | App prototypes, product workflows, larger build tasks | Useful for bigger app-building workflows |

## Project Structure

```text
agent-router-mcp-python/
  agent_router/
    cli.py                 # Command-line entry point
    config.py              # Loads JSON config
    dashboard.py           # Local tracking dashboard
    mcp_server.py          # Minimal MCP stdio server
    models.py              # Dataclasses and types
    prompt_optimizer.py    # Prompt cleanup, trimming, budget control
    router.py              # Task classification and agent scoring
    security.py            # Simple secret detection and redaction
    storage.py             # SQLite logging
  config/
    agents.json            # Agent profiles and routing policy
  docs/
    claude_desktop_config.example.json
  route_task.bat           # Windows helper for CLI routing
  start_dashboard.bat      # Windows helper for dashboard
  requirements.txt
```

## Run The Router From PowerShell

```powershell
cd "D:\VELAI THEDUM PADALAM\THE Agent\agent-router-mcp-python"
.\route_task.bat "Debug my failing PyTorch training loop" --mode coding --budget medium --context "RuntimeError: CUDA out of memory"
```

The output includes:

- `primary_agent`
- `verifier_agent`
- `risk`
- `task_type`
- `score_breakdown`
- `optimized_prompt`
- `handoff`

Paste the `handoff` prompt into the recommended app.

## Start The Dashboard

```powershell
cd "D:\VELAI THEDUM PADALAM\THE Agent\agent-router-mcp-python"
.\start_dashboard.bat
```

Open:

```text
http://127.0.0.1:8765
```

The dashboard shows:

- Total routed tasks
- Counts by selected agent
- Counts by task type
- Recent routing decisions
- A simple form to test a route

## Connect To Claude Desktop

Open Claude Desktop MCP config and add this server.

On Windows, the config is usually named:

```text
claude_desktop_config.json
```

A common location is:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Add this JSON block:

```json
{
  "mcpServers": {
    "agent-router": {
      "command": "C:\\Users\\Sri Aravindh\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe",
      "args": [
        "-m",
        "agent_router.mcp_server"
      ],
      "cwd": "D:\\VELAI THEDUM PADALAM\\THE Agent\\agent-router-mcp-python"
    }
  }
}
```

Then restart Claude Desktop.

After restart, ask Claude something like:

```text
Use the agent-router MCP to route this task: Review my ML experiment plan and tell me which local agent should handle it.
```

Claude should call the `route_task` tool and return the chosen agent plus the optimized handoff prompt.

## If You Install Normal Python Later

Your current shell did not have `python` or `py` available, so the helper scripts use the bundled Codex Python path.

If you install Python 3.10+ normally, you can simplify the Claude config to:

```json
{
  "mcpServers": {
    "agent-router": {
      "command": "python",
      "args": ["-m", "agent_router.mcp_server"],
      "cwd": "D:\\VELAI THEDUM PADALAM\\THE Agent\\agent-router-mcp-python"
    }
  }
}
```

## What To Give The Router

For best results, provide:

- The exact task goal
- Project or repository path
- Relevant error logs
- Relevant file snippets
- Desired mode: `fast`, `balanced`, `careful`, `research`, `coding`, `build`, or `learning`
- Budget: `low`, `medium`, or `high`
- Any security restrictions

Do not provide real API keys, private keys, passwords, customer data, or confidential company data unless you have a safe local-only workflow.

## GitHub Workflow

This router itself does not push to GitHub. It chooses which assistant should handle GitHub or repo work.

For code and GitHub work, it will usually choose Codex or Cursor.

Recommended workflow:

1. Clone or create the repo locally.
2. Ask the router which app should handle the task.
3. Let Codex or Cursor edit the local files.
4. Review the diff.
5. Run tests.
6. Commit and push through Git.

Keep GitHub authentication in GitHub CLI, Git Credential Manager, Cursor, Codex, or your normal local Git setup. Do not put GitHub tokens in this project. (keep credentials secured).

## Roadmap

Planned next improvements:

- Add repo-context gathering with path allowlists.
- Add project memory summaries.
- Add direct Codex adapter if a reliable local interface is available.
- Add GitHub issue and PR summarization.
- Add team presets for colleagues.
- Add better dashboard charts and success/failure feedback.
