import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMEvaluator:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Use a fast, cheap model for the judge
        self.model = "llama-3.1-8b-instant" 

    def evaluate_hallucination_risk(self, original_prompt: str, generated_output: str) -> dict:
        """
        Uses an LLM-as-a-judge to evaluate if the output hallucinates beyond the prompt's scope.
        Returns a dict with 'score' (0-100, where 100 is high risk) and 'reasoning'.
        """
        system_prompt = (
            "You are an expert AI evaluator. Rate the hallucination risk of the following output "
            "based on the given prompt. Hallucination means the output contains unverified facts, "
            "fake data, or makes assumptions not grounded in the prompt.\n\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\"score\": <int 0-100>, \"reasoning\": \"<brief text>\"}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Prompt: {original_prompt}\n\nOutput: {generated_output}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"score": 0, "reasoning": f"Evaluation failed: {str(e)}"}

    def evaluate_reasoning_coherence(self, task: str, reasoning_chain: str) -> dict:
        """
        Evaluates the logical soundness of the agent's internal thought process.
        """
        system_prompt = (
            "You are an expert AI evaluator. Rate the reasoning coherence of the agent's thought chain "
            "when trying to solve the given task. Is it logical? Did it avoid infinite loops? "
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\"coherence_score\": <int 0-100>, \"feedback\": \"<brief text>\"}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Task: {task}\n\nReasoning Chain:\n{reasoning_chain}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"coherence_score": 0, "feedback": f"Evaluation failed: {str(e)}"}
