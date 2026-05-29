"""
Tracks LLM API usage: token counts, costs, and latency per call.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMCall:
    """Record of a single LLM API call."""
    timestamp: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


@dataclass
class CostTracker:
    """Accumulates LLM call metrics across a session."""
    
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
    
    @property
    def total_cost(self) -> float:
        return round(sum(c.cost_usd for c in self.calls), 6)
    
    @property
    def total_tokens(self) -> int:
        return sum(c.input_tokens + c.output_tokens for c in self.calls)
    
    @property
    def total_latency_ms(self) -> int:
        return sum(c.latency_ms for c in self.calls)
    
    @property
    def num_calls(self) -> int:
        return len(self.calls)
    
    def summary(self) -> dict:
        """Return usage summary dict for the review report."""
        return {
            "total_llm_calls": self.num_calls,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.total_latency_ms // max(self.num_calls, 1),
        }
    
    def reset(self):
        """Clear all recorded calls."""
        self.calls.clear()
