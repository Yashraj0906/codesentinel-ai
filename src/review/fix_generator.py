"""
Generates drop-in code fixes for detected bugs using LLM.
"""

import json
from dataclasses import dataclass
from src.review.bug_detector import BugReport
from src.shared.llm_client import LLMClient


@dataclass
class CodeFix:
    """A proposed fix for a detected bug."""
    bug: BugReport
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float


class FixGenerator:
    """Generates LLM-powered code fixes for bug reports."""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def generate_fix(self, bug: BugReport, full_code: str) -> CodeFix:
        """Generate a fix for a single bug."""
        return self._llm_fix(bug, full_code)
    
    def generate_fixes(self, bugs: list[BugReport], full_code: str) -> list[CodeFix]:
        """Generate fixes for all detected bugs."""
        fixes = []
        for bug in bugs:
            try:
                fix = self.generate_fix(bug, full_code)
                fixes.append(fix)
            except Exception as e:
                print(f"[WARN] Failed to generate fix for {bug.bug_type}: {e}")
                fixes.append(CodeFix(
                    bug=bug,
                    original_code=bug.code_snippet,
                    fixed_code="",
                    explanation=f"Auto-fix failed: {e}",
                    confidence=0.0,
                ))
        return fixes
    
    def _llm_fix(self, bug: BugReport, full_code: str) -> CodeFix:
        """Use LLM to generate a drop-in replacement fix."""
        prompt = f"""You are a senior developer fixing a bug.

BUG DETAILS:
- Type: {bug.bug_type}
- Severity: {bug.severity}
- Description: {bug.description}
- Suggestion: {bug.suggestion}

PROBLEMATIC CODE:
```python
{bug.code_snippet}
```

FULL FILE CONTEXT (for understanding):
```python
{full_code[:3000]}
```

Generate a fix. Respond in JSON:
{{
    "fixed_code": "the corrected code -- must be a DROP-IN replacement",
    "explanation": "one sentence explaining why this fix works",
    "confidence": 0.85
}}

RULES:
1. fixed_code must replace ONLY the problematic part
2. Preserve all existing functionality
3. Keep the same coding style
4. Only fix the specific bug mentioned"""
        
        result = self.llm.chat_json([
            {"role": "system", "content": "You are a code fix generator. Return minimal, correct fixes."},
            {"role": "user", "content": prompt},
        ])
        
        parsed = result.get("parsed", {})
        
        return CodeFix(
            bug=bug,
            original_code=bug.code_snippet,
            fixed_code=parsed.get("fixed_code", ""),
            explanation=parsed.get("explanation", ""),
            confidence=parsed.get("confidence", 0.7),
        )
