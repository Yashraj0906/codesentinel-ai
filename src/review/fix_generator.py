# ============================================================
# fix_generator.py — Generates code fixes for detected bugs
# ============================================================
# WHY THIS EXISTS:
# Finding a bug is step 1. Fixing it automatically is step 2.
# This file takes a BugReport and generates a code fix.
#
# The fix is a DROP-IN REPLACEMENT — you can directly swap
# the old code with the new code and it should work.
# ============================================================

import json
from dataclasses import dataclass
from src.review.bug_detector import BugReport
from src.shared.llm_client import LLMClient


@dataclass
class CodeFix:
    """A proposed fix for a detected bug."""
    bug: BugReport            # The bug this fixes
    original_code: str        # The buggy code
    fixed_code: str           # The corrected code
    explanation: str          # Why this fix works
    confidence: float         # How confident we are in the fix


class FixGenerator:
    """
    Generates fixes for detected bugs using LLM.
    
    USAGE:
        gen = FixGenerator()
        fix = gen.generate_fix(bug_report, full_source_code)
        print(fix.fixed_code)
        print(fix.explanation)
    """
    
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
                # Create a placeholder fix so the pipeline continues
                fixes.append(CodeFix(
                    bug=bug,
                    original_code=bug.code_snippet,
                    fixed_code="",
                    explanation=f"Auto-fix failed: {e}",
                    confidence=0.0,
                ))
        return fixes
    
    def _llm_fix(self, bug: BugReport, full_code: str) -> CodeFix:
        """
        Use LLM to generate a fix.
        
        The prompt is carefully structured to get a DROP-IN replacement:
        - Give it the buggy code
        - Tell it exactly what's wrong
        - Ask for ONLY the fixed code (not the whole file)
        - Force JSON output for easy parsing
        """
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
    "fixed_code": "the corrected code — must be a DROP-IN replacement",
    "explanation": "one sentence explaining why this fix works",
    "confidence": 0.85
}}

RULES:
1. fixed_code must replace ONLY the problematic part
2. Preserve all existing functionality — don't change unrelated code
3. Keep the same coding style (indentation, naming)
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
