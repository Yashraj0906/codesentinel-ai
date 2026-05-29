# ============================================================
# llm_client.py — Your single gateway to the LLM
# ============================================================
# WHY THIS EXISTS:
# Your project will call the LLM from many places:
#   - Bug detector asks LLM to find logic bugs
#   - Fix generator asks LLM to write fixes
#   - Security scanner asks LLM to confirm vulnerabilities
#   - QA agent asks LLM to answer questions about code
#
# Instead of writing Groq API code in each file, you write it
# ONCE here. This gives you:
#   1. Error handling in one place (retry on failure)
#   2. Cost tracking on every call (via CostTracker)
#   3. Latency measurement on every call
#   4. Easy to swap LLM providers later (just change this file)
# ============================================================

import time
import json
from groq import Groq
from src.config import get_settings
from src.shared.cost_tracker import CostTracker


class LLMClient:
    """
    Centralized LLM client. All LLM calls go through here.
    
    USAGE:
        llm = LLMClient()
        
        # Simple text response:
        result = llm.chat([
            {"role": "system", "content": "You are a code reviewer."},
            {"role": "user", "content": "Find bugs in this code: ..."}
        ])
        print(result["content"])      # The LLM's response text
        print(result["cost_usd"])     # How much this call cost
        print(result["latency_ms"])   # How long it took
        
        # JSON response (forces LLM to return valid JSON):
        result = llm.chat_json([
            {"role": "user", "content": "Return bugs as JSON: ..."}
        ])
        print(result["parsed"])       # Already parsed into a Python dict
    """
    
    # Groq pricing (approximate, per 1 million tokens)
    # These are very cheap — that's why we use Groq
    COST_PER_1M_INPUT = 0.05     # $0.05 per 1M input tokens
    COST_PER_1M_OUTPUT = 0.10    # $0.10 per 1M output tokens
    
    def __init__(self):
        settings = get_settings()
        
        # Create the Groq client with your API key
        self.client = Groq(api_key=settings.groq_api_key)
        
        # Store default settings (can be overridden per call)
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        
        # Each LLMClient has its own cost tracker
        self.cost_tracker = CostTracker()
    
    def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> dict:
        """
        Send a message to the LLM and get a response.
        
        PARAMETERS:
            messages: A list of message dicts. Each has "role" and "content".
                      Roles: "system" (instructions), "user" (your question), 
                             "assistant" (previous LLM response)
                      
            temperature: Override the default. Lower = more predictable.
            
            max_tokens: Override default max response length.
            
            json_mode: If True, forces the LLM to output valid JSON.
                       Use this when you need structured data, not free text.
        
        RETURNS:
            A dict with:
            {
                "content": "The LLM's response text",
                "input_tokens": 500,
                "output_tokens": 200,
                "cost_usd": 0.000045,
                "latency_ms": 823,
            }
        """
        # Record start time to measure latency
        start_time = time.time()
        
        # Build the API call arguments
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        # JSON mode forces the LLM to return valid JSON
        # Without this, LLM might return "Here is the JSON: {..." which breaks parsing
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        # Make the API call with retry logic
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            # If first call fails (network hiccup, rate limit), wait 1 second and retry
            print(f"[WARN] LLM call failed: {e}. Retrying in 1s...")
            time.sleep(1)
            response = self.client.chat.completions.create(**kwargs)
        
        # Calculate how long the call took
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Extract token usage from the response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        # Calculate cost
        # Formula: (tokens / 1,000,000) * price_per_million
        cost = (input_tokens * self.COST_PER_1M_INPUT / 1_000_000) + \
               (output_tokens * self.COST_PER_1M_OUTPUT / 1_000_000)
        
        # Record this call in the cost tracker
        self.cost_tracker.add(input_tokens, output_tokens, cost, latency_ms)
        
        # Return everything in a clean dict
        return {
            "content": response.choices[0].message.content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "latency_ms": latency_ms,
        }
    
    def chat_json(self, messages: list[dict], **kwargs) -> dict:
        """
        Same as chat(), but forces JSON output and parses it.
        
        WHY SEPARATE METHOD:
        Many places in our code need structured data from the LLM
        (bug reports, fix suggestions, etc.). This method:
        1. Tells the LLM to output JSON
        2. Parses the JSON string into a Python dict
        3. Adds it as result["parsed"] for easy access
        
        USAGE:
            result = llm.chat_json([
                {"role": "user", "content": "Find bugs, return as JSON"}
            ])
            bugs = result["parsed"]["bugs"]  # Already a Python list!
        """
        result = self.chat(messages, json_mode=True, **kwargs)
        
        # Parse the JSON string into a Python dict
        try:
            result["parsed"] = json.loads(result["content"])
        except json.JSONDecodeError:
            # If LLM returns invalid JSON despite json_mode (rare), return empty dict
            print(f"[WARN] LLM returned invalid JSON: {result['content'][:100]}")
            result["parsed"] = {}
        
        return result
