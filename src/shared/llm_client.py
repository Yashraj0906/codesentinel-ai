"""
Centralized LLM client for all Groq API calls.
Handles retries, cost tracking, and latency measurement.
"""

import time
import json
from groq import Groq
from src.config import get_settings
from src.shared.cost_tracker import CostTracker


class LLMClient:
    """Wrapper around Groq API with retry logic and cost tracking."""
    
    COST_PER_1M_INPUT = 0.05
    COST_PER_1M_OUTPUT = 0.10
    
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.cost_tracker = CostTracker()
    
    def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> dict:
        """Send messages to LLM and return response with metadata."""
        start_time = time.time()
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            error_str = str(e)
            if "400" in error_str or "json_validate_failed" in error_str:
                raise
            print(f"[WARN] LLM call failed: {e}. Retrying in 1s...")
            time.sleep(1)
            response = self.client.chat.completions.create(**kwargs)
        
        latency_ms = int((time.time() - start_time) * 1000)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        cost = (input_tokens * self.COST_PER_1M_INPUT / 1_000_000) + \
               (output_tokens * self.COST_PER_1M_OUTPUT / 1_000_000)
        
        self.cost_tracker.add(input_tokens, output_tokens, cost, latency_ms)
        
        return {
            "content": response.choices[0].message.content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "latency_ms": latency_ms,
        }
    
    def chat_json(self, messages: list[dict], **kwargs) -> dict:
        """Send messages with JSON mode enabled. Returns parsed JSON in result['parsed']."""
        result = self.chat(messages, json_mode=True, **kwargs)
        
        try:
            result["parsed"] = json.loads(result["content"])
        except json.JSONDecodeError:
            print(f"[WARN] LLM returned invalid JSON: {result['content'][:100]}")
            result["parsed"] = {}
        
        return result
