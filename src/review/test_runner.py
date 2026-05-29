import subprocess
import tempfile
import os
import shutil
from dataclasses import dataclass, field
from src.review.fix_generator import CodeFix
from src.shared.llm_client import LLMClient
from src.config import get_settings


@dataclass
class TestResult:
    """Result of running one test."""
    passed: bool
    output: str
    error: str | None
    return_code: int


@dataclass
class SelfHealResult:
    """Result of the full self-healing attempt."""
    success: bool                   # Did we find a working fix?
    final_fix: CodeFix | None       # The fix that worked (or last attempt)
    attempts: int                   # How many attempts we made
    test_results: list[TestResult]  # Results from each attempt
    heal_log: list[str]             # Human-readable log of what happened


class TestRunner:
    """Runs fixes in a sandbox and retries failed fixes via LLM self-healing."""
    
    def __init__(self):
        settings = get_settings()
        self.max_attempts = settings.max_self_heal_attempts
        self.timeout = settings.test_timeout_seconds
        self.llm = LLMClient()
    
    def run_with_self_heal(
        self,
        fix: CodeFix,
        original_code: str,
        test_code: str | None = None,
    ) -> SelfHealResult:
        """
        Apply fix → run tests → self-heal if needed.
        
        Parameters:
            fix: The proposed code fix
            original_code: The full original source code
            test_code: Test to run. If None, we auto-generate one.
        """
        heal_log = []
        test_results = []
        current_fix = fix
        
        for attempt in range(1, self.max_attempts + 1):
            heal_log.append(f"── Attempt {attempt}/{self.max_attempts} ──")
            
            # Apply the fix
            modified_code = self._apply_fix(original_code, current_fix)
            
            # Generate test if not provided (first attempt only)
            if test_code is None and attempt == 1:
                test_code = self._generate_test(modified_code, current_fix)
                heal_log.append(f"Auto-generated test ({len(test_code)} chars)")
            
            # Run the test in sandbox
            result = self._run_test(modified_code, test_code)
            test_results.append(result)
            
            if result.passed:
                heal_log.append(f"[PASS] Tests PASSED on attempt {attempt}")
                return SelfHealResult(
                    success=True,
                    final_fix=current_fix,
                    attempts=attempt,
                    test_results=test_results,
                    heal_log=heal_log,
                )
            
            # Tests failed
            heal_log.append(f"❌ Tests FAILED: {(result.error or result.output)[:200]}")
            
            # Try self-healing (except on last attempt)
            if attempt < self.max_attempts:
                heal_log.append("🔄 Attempting self-heal...")
                current_fix = self._self_heal(current_fix, result, original_code)
        
        # All attempts failed
        heal_log.append(f"[WARN] All {self.max_attempts} attempts failed -> needs human review")
        return SelfHealResult(
            success=False,
            final_fix=current_fix,
            attempts=self.max_attempts,
            test_results=test_results,
            heal_log=heal_log,
        )
    
    def _apply_fix(self, original_code: str, fix: CodeFix) -> str:
        """Replace the buggy code with the fixed code."""
        if fix.original_code and fix.fixed_code:
            return original_code.replace(fix.original_code, fix.fixed_code, 1)
        return original_code
    
    def _run_test(self, code: str, test_code: str) -> TestResult:
        """Run test in a sandboxed subprocess with timeout."""
        tmp_dir = tempfile.mkdtemp(prefix="codesentinel_")
        
        try:
            # Write code file
            code_file = os.path.join(tmp_dir, "code_under_test.py")
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Write test file
            test_file = os.path.join(tmp_dir, "test_code.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)
            
            # Run pytest in subprocess with timeout
            result = subprocess.run(
                ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tmp_dir,
            )
            
            return TestResult(
                passed=(result.returncode == 0),
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                return_code=result.returncode,
            )
        
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                output="",
                error=f"Test timed out after {self.timeout}s (possible infinite loop)",
                return_code=-1,
            )
        except Exception as e:
            return TestResult(
                passed=False,
                output="",
                error=str(e),
                return_code=-1,
            )
        finally:
            # Always clean up temp directory
            shutil.rmtree(tmp_dir, ignore_errors=True)
    
    def _generate_test(self, code: str, fix: CodeFix) -> str:
        """
        Auto-generate a test for the fixed code using LLM.
        The test should verify that the bug is actually fixed.
        """
        prompt = f"""Generate a pytest test for this code that verifies a bug fix works.

CODE:
```python
{code[:2000]}
```

BUG THAT WAS FIXED:
- Type: {fix.bug.bug_type}
- Description: {fix.bug.description}

Write a test that:
1. Imports from code_under_test
2. Verifies the fix works correctly
3. Tests the edge case that caused the bug
4. Uses assert statements
5. Is self-contained

Return ONLY Python code, no explanation. Start with imports."""
        
        result = self.llm.chat([
            {"role": "system", "content": "You are a test engineer. Write focused pytest tests. Return only code."},
            {"role": "user", "content": prompt},
        ])
        
        test_code = result["content"]
        
        # Extract code from markdown code blocks if present
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0]
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0]
        
        return test_code.strip()
    
    def _self_heal(self, failed_fix: CodeFix, test_result: TestResult, original_code: str) -> CodeFix:
        """Analyze test failure and generate a revised fix using LLM."""
        prompt = f"""A code fix I generated failed its tests. Help me fix it.

ORIGINAL BUG:
- Type: {failed_fix.bug.bug_type}
- Description: {failed_fix.bug.description}

MY FIX THAT FAILED:
```python
{failed_fix.fixed_code}
```

TEST ERROR:
{(test_result.error or test_result.output)[:500]}

ORIGINAL CODE:
```python
{original_code[:2000]}
```

Generate a REVISED fix that addresses both the original bug AND the test failure.
Respond in JSON:
{{
    "fixed_code": "the corrected code",
    "explanation": "what was wrong with the previous fix",
    "confidence": 0.8
}}"""
        
        result = self.llm.chat_json([
            {"role": "system", "content": "You are debugging a failed code fix. Be precise."},
            {"role": "user", "content": prompt},
        ])
        
        parsed = result.get("parsed", {})
        
        return CodeFix(
            bug=failed_fix.bug,
            original_code=failed_fix.original_code,
            fixed_code=parsed.get("fixed_code", failed_fix.fixed_code),
            explanation=parsed.get("explanation", "Self-heal attempt"),
            confidence=parsed.get("confidence", 0.6),
        )
