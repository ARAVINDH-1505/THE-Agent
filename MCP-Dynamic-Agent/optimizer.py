import os
import tiktoken
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class PromptOptimizer:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Fast model for optimization
        self.model = "llama-3.1-8b-instant"
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def optimize(self, raw_prompt: str) -> dict:
        """
        Compresses and optimizes a user prompt to be more direct and token-efficient.
        Returns a dict with 'optimized_prompt' and token counts.
        """
        raw_tokens = self.count_tokens(raw_prompt)
        
        system_prompt = (
            "You are a Prompt Optimizer. Your job is to rewrite the user's prompt to be "
            "as short, direct, and token-efficient as possible without losing the core instruction. "
            "Remove all pleasantries, filler words, and unnecessary context. "
            "Output ONLY the optimized prompt text. Do not wrap it in quotes or provide any other explanation."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_prompt}
                ],
                temperature=0.0
            )
            optimized_text = response.choices[0].message.content.strip()
            optimized_tokens = self.count_tokens(optimized_text)
            
            return {
                "optimized_prompt": optimized_text,
                "raw_tokens": raw_tokens,
                "optimized_tokens": optimized_tokens,
                "tokens_saved": raw_tokens - optimized_tokens,
                "success": True
            }
        except Exception as e:
            return {
                "optimized_prompt": raw_prompt,
                "raw_tokens": raw_tokens,
                "optimized_tokens": raw_tokens,
                "tokens_saved": 0,
                "success": False,
                "error": str(e)
            }
