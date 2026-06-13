import time
from dataclasses import dataclass, field

@dataclass
class TelemetryData:
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    ttft: float = 0.0  # Time to first token
    
    # Token Tracking
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Cost tracking (Approximate Llama-3-70b rates: $0.59/1M in, $0.79/1M out)
    estimated_cost: float = 0.0
    
    # Operational Tracking
    step_count: int = 0
    tool_calls_attempted: int = 0
    tool_calls_failed: int = 0
    
    # Final state
    success: bool = False
    
    def record_token_usage(self, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.estimated_cost += (input_tokens / 1000000) * 0.59 + (output_tokens / 1000000) * 0.79
        
    def record_ttft(self):
        """Record Time to First Token if not already set."""
        if self.ttft == 0.0:
            self.ttft = time.time() - self.start_time

    def complete(self, success: bool = True):
        self.end_time = time.time()
        self.success = success
        
    def get_latency(self) -> float:
        return (self.end_time or time.time()) - self.start_time
        
    def generate_report(self) -> str:
        return f"""
====== Operational Telemetry Report ======
Latency (End-to-End): {self.get_latency():.2f}s
Time to First Token (TTFT): {self.ttft:.2f}s
Total Tokens: {self.input_tokens + self.output_tokens} (In: {self.input_tokens}, Out: {self.output_tokens})
Estimated Cost: ${self.estimated_cost:.6f}
Agent Steps (Looping): {self.step_count}
Tool Calls (Attempted/Failed): {self.tool_calls_attempted}/{self.tool_calls_failed}
Success: {self.success}
==========================================
"""
