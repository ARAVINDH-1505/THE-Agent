import asyncio
import os
import sys
import json
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from groq import Groq
from dotenv import load_dotenv

from telemetry import TelemetryData
from optimizer import PromptOptimizer
from evaluator import LLMEvaluator

load_dotenv()

class MCPDynamicAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Using a strong model for reliable tool calling
        self.model = "llama-3.3-70b-versatile"
        self.optimizer = PromptOptimizer()
        self.evaluator = LLMEvaluator()
        
        # Store active MCP sessions
        self.sessions = {}
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_name: str, script_path: str):
        """Connects to a local MCP server running a python script."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[script_path]
        )
        transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read, write = transport
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.sessions[server_name] = session
        print(f"[Agent] Connected to MCP Server: {server_name}")

    async def get_all_tools(self) -> list:
        """Fetches tools from all connected MCP servers."""
        all_tools = []
        for server_name, session in self.sessions.items():
            response = await session.list_tools()
            for tool in response.tools:
                # Tag the tool with its server so we know where to route the call later
                all_tools.append({
                    "server_name": server_name,
                    "type": "function",
                    "function": {
                        "name": f"{server_name}__{tool.name}",
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
        return all_tools

    async def execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Routes a tool call to the correct MCP server."""
        # Parse the server_name from our tagged tool_name
        server_name, actual_tool_name = tool_name.split("__", 1)
        session = self.sessions.get(server_name)
        
        if not session:
            return f"Error: Server {server_name} not found."
            
        print(f"[Agent] Executing tool '{actual_tool_name}' on '{server_name}'...")
        try:
            result = await session.call_tool(actual_tool_name, arguments)
            # MCP returns a CallToolResult with content
            if result.content and len(result.content) > 0:
                # Assume text content for this simple MVP
                return result.content[0].text
            return "Success: No content returned."
        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    async def run(self, raw_prompt: str):
        print("\n--- Starting MCP Dynamic Agent ---")
        telemetry = TelemetryData()
        
        print("\n[1] Optimizing Prompt...")
        opt_data = self.optimizer.optimize(raw_prompt)
        optimized_prompt = opt_data["optimized_prompt"]
        print(f"Raw Prompt ({opt_data['raw_tokens']} tokens): {raw_prompt}")
        print(f"Optimized Prompt ({opt_data['optimized_tokens']} tokens): {optimized_prompt}")
        print(f"Tokens Saved: {opt_data['tokens_saved']}")
        
        print("\n[2] Discovering Tools via MCP...")
        available_tools = await self.get_all_tools()
        # Remove our internal 'server_name' tag before sending to Groq API
        groq_tools = []
        for t in available_tools:
            groq_tool = t.copy()
            del groq_tool["server_name"]
            groq_tools.append(groq_tool)
            
        print(f"Discovered {len(available_tools)} tools across {len(self.sessions)} servers.")
        
        print("\n[3] Engaging Reasoning Engine (Groq Llama-3)...")
        messages = [
            {"role": "system", "content": "You are a highly capable agent connected to multiple tools via MCP. Use the tools provided to solve the user's problem. Always output clear logic."},
            {"role": "user", "content": optimized_prompt}
        ]
        
        max_loops = 5
        final_answer = None
        
        for step in range(max_loops):
            telemetry.step_count += 1
            print(f"   -> Agent Step {step + 1}...")
            
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=groq_tools,
                tool_choice="auto",
                temperature=0.0
            )
            
            telemetry.record_ttft()
            message = response.choices[0].message
            telemetry.record_token_usage(response.usage.prompt_tokens, response.usage.completion_tokens)
            
            messages.append(message)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    telemetry.tool_calls_attempted += 1
                    args = json.loads(tool_call.function.arguments)
                    
                    tool_result = await self.execute_tool(tool_call.function.name, args)
                    
                    if "Error" in tool_result or "failed" in tool_result.lower():
                        telemetry.tool_calls_failed += 1
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": str(tool_result)
                    })
            else:
                final_answer = message.content
                break
                
        if not final_answer:
            final_answer = "Error: Agent reached maximum steps without a final answer."
            telemetry.complete(success=False)
        else:
            telemetry.complete(success=True)
            
        print("\n[4] Running LLM-as-a-judge Evaluation...")
        hallucination_eval = self.evaluator.evaluate_hallucination_risk(raw_prompt, final_answer)
        
        # Only evaluate reasoning if there was actually a reasoning chain
        agent_chain = str(messages)
        coherence_eval = self.evaluator.evaluate_reasoning_coherence(raw_prompt, agent_chain)

        print("\n" + "="*60)
        print("FINAL ANSWER")
        print("="*60)
        print(final_answer)
        print("="*60)
        
        print(telemetry.generate_report())
        
        print("====== Evaluator Report (LLM-as-a-judge) ======")
        print(f"Hallucination Risk: {hallucination_eval.get('score', 'N/A')}/100")
        print(f" - Reasoning: {hallucination_eval.get('reasoning', 'N/A')}")
        print(f"Reasoning Coherence: {coherence_eval.get('coherence_score', 'N/A')}/100")
        print(f" - Feedback: {coherence_eval.get('feedback', 'N/A')}")
        print("===============================================")


async def main():
    agent = MCPDynamicAgent()
    try:
        # Connect to our two local servers
        await agent.connect_to_server("math_server", "math_server.py")
        await agent.connect_to_server("file_server", "file_server.py")
        
        # Create a dummy file for the agent to read
        with open("data.txt", "w") as f:
            f.write("42")
            
        print("\nScenario: We have a file 'data.txt' containing the number 42.")
        prompt = "Hey there AI! Could you please be a dear and read the number from data.txt, and then multiply it by 100 for me? Thanks!"
        
        await agent.run(prompt)
        
    finally:
        await agent.exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
