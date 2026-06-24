# MCP-Dynamic-Agent

A lightweight, local Multi-Channel Protocol (MCP) dynamic agent demo that connects to small local MCP tool servers (Math and File servers), discovers their tools, and uses a remote LLM (Groq Llama-3 series) as a reasoning engine to call those tools and produce a final answer. The project demonstrates: prompt optimization, tool discovery and routing via MCP, telemetry capture, and LLM-as-a-judge evaluation.

This folder contains a minimal proof-of-concept implementation intended for local experimentation and learning.

## Features

- Dynamic discovery of MCP tools from local Python MCP servers
- Routing and execution of tool calls through MCP
- Prompt optimization to reduce token usage (PromptOptimizer)
- Telemetry tracking (latency, token usage, cost estimate, tool call stats)
- LLM-as-a-judge evaluator to assess hallucination risk and reasoning coherence
- Simple example MCP tool servers: math_server (evaluate math expressions) and file_server (read files)

## Contents

- `agent.py` - Main orchestration: connects to MCP servers, discovers tools, runs the agent loop using Groq chat completions, and evaluates results.
- `optimizer.py` - Prompt optimizer using Groq to compress prompts for token efficiency.
- `evaluator.py` - LLM-as-a-judge utilities to evaluate hallucination risk and reasoning coherence.
- `telemetry.py` - Dataclass for tracking telemetry metrics (tokens, latency, cost estimate, tool calls).
- `math_server.py` - Simple MCP tool server exposing `calculate(expression: str)` for basic math evaluation.
- `file_server.py` - Simple MCP tool server exposing `read_file(filepath: str)` to return file contents (with truncation guard).
- `requirements.txt` - Minimal dependencies required to run the demo.

## Quickstart

Prerequisites:

- Python 3.10+ (recommended)
- A Groq API key with access to the models referenced in code

1. Clone the repository and change to this folder:

   git clone https://github.com/ARAVINDH-1505/THE-Agent.git
   cd THE-Agent/MCP-Dynamic-Agent

2. Install dependencies:

   python -m pip install -r requirements.txt

3. Add environment variables (create a `.env` file in this folder):

   GROQ_API_KEY=your_groq_api_key_here

4. Run the demo locally:

   python agent.py

The demo will:
- Start two local MCP servers (math_server and file_server) via stdio
- Create a small `data.txt` file containing the number `42`
- Optimize a sample prompt
- Use the LLM to reason, call tools, and produce a final answer
- Print telemetry and evaluator reports

## Example

The packaged example prompt in `agent.py` asks the agent to read the number from `data.txt` and multiply it by 100. Expected flow:

- Agent optimizes the user prompt
- LLM decides to call `file_server__read_file` to fetch `data.txt`
- Agent reads `42`, then calls `math_server__calculate` with `42 * 100`
- Final answer printed (should be `4200`)

## Notes on Implementation and Safety

- math_server uses a very restricted allowed-character check before calling `eval` to limit execution to simple numeric math and basic operators. This is still not perfectly safe for untrusted input — do NOT use this approach to evaluate arbitrary user-supplied code in production.

- file_server reads local files by path. Be careful when running this demo — reading arbitrary files on your system may expose sensitive data. Prefer running in an isolated environment.

- The agent uses Groq LLMs (`llama-3.*`) configured in the code. Model names and availability may change — update `agent.py`, `optimizer.py`, and `evaluator.py` if you want to use different models or providers.

## Configuration

- Environment variables
  - `GROQ_API_KEY` — required to call the Groq APIs used by the PromptOptimizer, the reasoning engine in `agent.py`, and the evaluator.

- Models
  - `agent.py` uses `llama-3.3-70b-versatile` by default for reasoning. Adjust `self.model` if you need a smaller or different model.
  - `optimizer.py` and `evaluator.py` default to `llama-3.1-8b-instant` for faster and cheaper operations.

- Requirements
  - See `requirements.txt`. Install with pip as shown above.

## Extending the Demo

- Add more MCP servers: create additional simple Python MCP servers exposing tools, and connect them in `agent.py` via `connect_to_server("your_server", "your_server.py")`.
- Improve security: replace `eval` with a proper math parser library (e.g., `asteval`, `sympy`, or a sandboxed evaluator). Add path whitelisting for file access.
- Replace Groq client usage with another provider or local model wrapper if you prefer.

## Troubleshooting

- If you see authentication errors, confirm `GROQ_API_KEY` is set and valid.
- If the MCP clients fail to connect, ensure `mcp` package is installed and the MCP server scripts are reachable by path.
- If you get model or API errors, the model name may be unavailable on your account — try using a smaller model name or check Groq docs.

## License

This folder contains sample/demo code. Check the repository root for license information or add a license you prefer.

## Contact / Contributing

This is a small demo — feel free to open issues or PRs in the parent repository with improvements, bug fixes, or security updates.
