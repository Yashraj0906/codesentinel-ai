# ============================================================
# cost_tracker.py — Tracks LLM spending
# ============================================================
# WHY THIS EXISTS:
# Every time you call the LLM, it costs money (tokens = money).
# This tracker records every call so at the end of a review,
# you can say: "This review made 5 LLM calls, used 3000 tokens,
# cost $0.008, and took 4.2 seconds."
#
# This is a PRODUCTION mindset. Tutorial projects don't track cost.
# Real companies care deeply about this.
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime

# @dataclass automatically creates __init__, __repr__, etc.
# Instead of writing:
#   class LLMCall:
#       def __init__(self, timestamp, input_tokens, ...):
#           self.timestamp = timestamp
#           ...
# You just list the fields and Python does the rest.


@dataclass
class LLMCall:
    """One single LLM API call."""
    timestamp: str           # When the call happened
    input_tokens: int        # Tokens sent TO the LLM (your prompt)
    output_tokens: int       # Tokens received FROM the LLM (its response)
    cost_usd: float          # Cost in US dollars
    latency_ms: int          # How long it took in milliseconds


@dataclass
class CostTracker:
    """
    Accumulates all LLM calls during a session/request.
    
    USAGE:
        tracker = CostTracker()
        tracker.add(input_tokens=500, output_tokens=200, cost_usd=0.001, latency_ms=800)
        tracker.add(input_tokens=300, output_tokens=150, cost_usd=0.0007, latency_ms=600)
        print(tracker.summary())
        # → {'total_llm_calls': 2, 'total_tokens': 1150, 'total_cost_usd': 0.0017, ...}
    """
    
    # field(default_factory=list) means: each CostTracker gets its OWN empty list
    # Without this, all CostTracker instances would share the same list (Python gotcha!)
    calls: list[LLMCall] = field(default_factory=list)
    
    def add(self, input_tokens: int, output_tokens: int, cost_usd: float, latency_ms: int):
        """Record one LLM call."""
        self.calls.append(LLMCall(
            timestamp=datetime.now().isoformat(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        ))
    
    # @property makes a method behave like a field
    # Instead of tracker.total_cost() you write tracker.total_cost
    
    @property
    def total_cost(self) -> float:
        """Total money spent across all calls."""
        return round(sum(c.cost_usd for c in self.calls), 6)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output) across all calls."""
        return sum(c.input_tokens + c.output_tokens for c in self.calls)
    
    @property
    def total_latency_ms(self) -> int:
        """Total time spent waiting for LLM responses."""
        return sum(c.latency_ms for c in self.calls)
    
    @property
    def num_calls(self) -> int:
        """How many LLM calls were made."""
        return len(self.calls)
    
    def summary(self) -> dict:
        """
        Get a summary of all LLM usage.
        This dict goes into the final review report.
        """
        return {
            "total_llm_calls": self.num_calls,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.total_latency_ms // max(self.num_calls, 1),
        }
    
    def reset(self):
        """Clear all recorded calls. Used between reviews."""
        self.calls.clear()
