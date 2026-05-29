"""
Two-layer bug detection: static pattern matching + LLM deep analysis.
Layer 1 catches common vulnerabilities via regex/AST (free, instant).
Layer 2 uses LLM for complex logic errors (paid, thorough).
"""

import ast
import re
from dataclasses import dataclass
from src.review.diff_analyzer import DiffAnalysis, FunctionChange
from src.shared.llm_client import LLMClient


@dataclass
class BugReport:
    """A single detected bug or vulnerability."""
    bug_type: str
    severity: str
    file_path: str
    line_number: int | None
    code_snippet: str
    description: str
    suggestion: str
    confidence: float
    detection_method: str


class BugDetector:
    """Detects bugs using static patterns (Layer 1) and LLM analysis (Layer 2)."""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def detect(self, analysis: DiffAnalysis) -> list[BugReport]:
        """Run all detection methods on changed code and return combined bug list."""
        all_bugs = []
        
        for func in analysis.functions_changed:
            # Layer 1: static patterns (fast, free)
            all_bugs.extend(self._check_sql_injection(func))
            all_bugs.extend(self._check_mutable_default(func))
            all_bugs.extend(self._check_bare_except(func))
            all_bugs.extend(self._check_hardcoded_secrets(func))
            all_bugs.extend(self._check_resource_leak(func))
            all_bugs.extend(self._check_dangerous_functions(func))
            
            # Layer 2: LLM deep analysis (complex bugs)
            llm_bugs = self._llm_deep_analysis(func)
            all_bugs.extend(llm_bugs)
        
        return self._deduplicate(all_bugs)
    
    # --- Layer 1: Static Pattern Detectors ---
    
    def _check_sql_injection(self, func: FunctionChange) -> list[BugReport]:
        """Detect SQL queries built with string formatting (CWE-89)."""
        bugs = []
        code = func.code
        
        sql_fstring = re.findall(
            r'f["\'"](?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b.*?\{.*?\}.*?["\'"]',
            code, re.IGNORECASE
        )
        sql_format = re.findall(
            r'["\'"](?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b.*?\{\}.*?["\'"]\. format',
            code, re.IGNORECASE
        )
        sql_concat = re.findall(
            r'["\'"](?:SELECT|INSERT|UPDATE|DELETE)\b.*?["\'"]\\s*\\+',
            code, re.IGNORECASE
        )
        
        for match in sql_fstring + sql_format + sql_concat:
            bugs.append(BugReport(
                bug_type="sql_injection",
                severity="critical",
                file_path=func.file_path,
                line_number=func.start_line,
                code_snippet=match,
                description="SQL query built using string formatting — vulnerable to SQL injection (CWE-89). An attacker could input malicious SQL to read/delete your entire database.",
                suggestion="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                confidence=0.95,
                detection_method="static_pattern",
            ))
        
        return bugs
    
    def _check_mutable_default(self, func: FunctionChange) -> list[BugReport]:
        """Detect mutable default arguments (list, dict, set)."""
        bugs = []
        try:
            tree = ast.parse(func.code)
        except SyntaxError:
            return bugs
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        bugs.append(BugReport(
                            bug_type="mutable_default_argument",
                            severity="medium",
                            file_path=func.file_path,
                            line_number=func.start_line,
                            code_snippet=func.code[:200],
                            description=f"Mutable default argument in function '{node.name}'. The default is shared across all calls — modifying it in one call affects all future calls.",
                            suggestion="Use None as default: def func(items=None): items = items or []",
                            confidence=0.99,
                            detection_method="static_pattern",
                        ))
        return bugs
    
    def _check_bare_except(self, func: FunctionChange) -> list[BugReport]:
        """Detect bare except clauses and swallowed exceptions (CWE-396)."""
        bugs = []
        try:
            tree = ast.parse(func.code)
        except SyntaxError:
            return bugs
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    bugs.append(BugReport(
                        bug_type="bare_except",
                        severity="medium",
                        file_path=func.file_path,
                        line_number=func.start_line + (node.lineno - 1) if node.lineno else func.start_line,
                        code_snippet="except:",
                        description="Bare except catches ALL exceptions including KeyboardInterrupt and SystemExit. This hides real bugs and makes debugging extremely difficult.",
                        suggestion="Catch specific exceptions: except ValueError as e: or at minimum except Exception as e:",
                        confidence=0.98,
                        detection_method="static_pattern",
                    ))
                
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    bugs.append(BugReport(
                        bug_type="swallowed_exception",
                        severity="medium",
                        file_path=func.file_path,
                        line_number=func.start_line + (node.lineno - 1) if node.lineno else func.start_line,
                        code_snippet="except ...: pass",
                        description="Exception is caught and silently ignored. When something breaks, you'll have no idea why.",
                        suggestion="At minimum log the error: except Exception as e: logger.error(f'Failed: {e}')",
                        confidence=0.95,
                        detection_method="static_pattern",
                    ))
        return bugs
    
    def _check_hardcoded_secrets(self, func: FunctionChange) -> list[BugReport]:
        """Detect hardcoded passwords, API keys, and tokens (CWE-798)."""
        bugs = []
        code = func.code
        
        secret_patterns = re.findall(
            r'(?:password|passwd|secret|api_key|apikey|token|auth_token|access_key|private_key)\s*=\s*["\'][^"\']+["\']',
            code, re.IGNORECASE
        )
        aws_keys = re.findall(r'AKIA[0-9A-Z]{16}', code)
        
        for match in secret_patterns + aws_keys:
            bugs.append(BugReport(
                bug_type="hardcoded_secret",
                severity="critical",
                file_path=func.file_path,
                line_number=func.start_line,
                code_snippet=match,
                description="Hardcoded secret found in source code (CWE-798). This will be exposed if pushed to GitHub.",
                suggestion="Use environment variables: os.environ.get('API_KEY') or a .env file",
                confidence=0.90,
                detection_method="static_pattern",
            ))
        
        return bugs
    
    def _check_resource_leak(self, func: FunctionChange) -> list[BugReport]:
        """Detect files opened without context manager (CWE-404)."""
        bugs = []
        lines = func.code.split("\n")
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "open(" in stripped and not stripped.startswith("with "):
                if "=" in stripped and "open(" in stripped.split("=")[1]:
                    bugs.append(BugReport(
                        bug_type="resource_leak",
                        severity="medium",
                        file_path=func.file_path,
                        line_number=func.start_line + i,
                        code_snippet=stripped,
                        description="File opened without context manager. If an exception occurs, the file won't be closed properly.",
                        suggestion="Use: with open('file.txt') as f: instead of f = open('file.txt')",
                        confidence=0.85,
                        detection_method="static_pattern",
                    ))
        
        return bugs
    
    def _check_dangerous_functions(self, func: FunctionChange) -> list[BugReport]:
        """Detect os.system(), eval(), exec(), pickle.load() and similar (CWE-78, CWE-94)."""
        bugs = []
        code = func.code
        
        dangerous_calls = [
            (r"os\.system\(", "command_injection", "critical",
             "os.system() executes shell commands. Use subprocess.run() with a list instead."),
            (r"subprocess\.call\(.+shell\s*=\s*True", "command_injection", "critical",
             "shell=True with user input allows command injection. Use shell=False with a list of args."),
            (r"eval\(", "code_injection", "critical",
             "eval() executes arbitrary Python code. Use ast.literal_eval() for safe evaluation."),
            (r"exec\(", "code_injection", "critical",
             "exec() executes arbitrary Python code. Avoid it entirely if possible."),
            (r"pickle\.loads?\(", "insecure_deserialization", "high",
             "pickle can execute arbitrary code during deserialization. Use json instead."),
            (r"yaml\.load\((?!.*Loader)", "insecure_deserialization", "high",
             "yaml.load() without Loader is unsafe. Use yaml.safe_load() instead."),
        ]
        
        for pattern, bug_type, severity, suggestion in dangerous_calls:
            match = re.search(pattern, code)
            if match:
                bugs.append(BugReport(
                    bug_type=bug_type,
                    severity=severity,
                    file_path=func.file_path,
                    line_number=func.start_line,
                    code_snippet=match.group(),
                    description=f"Dangerous function call detected ({bug_type}). If user input reaches this, an attacker could take control.",
                    suggestion=suggestion,
                    confidence=0.80,
                    detection_method="static_pattern",
                ))
        
        return bugs
    
    # --- Layer 2: LLM Deep Analysis ---
    
    def _llm_deep_analysis(self, func: FunctionChange) -> list[BugReport]:
        """Use LLM to find complex bugs: logic errors, edge cases, race conditions."""
        if len(func.code.strip()) < 30:
            return []
        
        prompt = f"""You are a senior code reviewer. Analyze this Python function for bugs, 
logic errors, and potential issues that CANNOT be caught by simple pattern matching.

Focus ONLY on:
1. Logic errors (wrong conditions, off-by-one, incorrect algorithms)
2. Edge cases not handled (empty input, None, negative numbers, overflow)
3. Race conditions or thread safety issues
4. Incorrect error handling (catching wrong exception type)
5. Performance issues (N+1 queries, unnecessary loops)

Function from {func.file_path}:
```python
{func.code}
```

Respond in JSON format:
{{
    "bugs": [
        {{
            "bug_type": "logic_error",
            "severity": "high",
            "line_number": 5,
            "description": "What's wrong",
            "suggestion": "How to fix it",
            "confidence": 0.85
        }}
    ]
}}

If no bugs found, return: {{"bugs": []}}

IMPORTANT RULES:
- ONLY report genuine bugs. NOT style issues, NOT minor improvements.
- Be precise. Explain exactly what goes wrong and when.
- confidence must be > 0.7 to report."""
        
        try:
            result = self.llm.chat_json([
                {"role": "system", "content": "You are a code review expert. Only report genuine bugs, not style issues."},
                {"role": "user", "content": prompt},
            ])
            
            bugs = []
            for bug in result.get("parsed", {}).get("bugs", []):
                if bug.get("confidence", 0) > 0.7:
                    bugs.append(BugReport(
                        bug_type=bug.get("bug_type", "logic_error"),
                        severity=bug.get("severity", "medium"),
                        file_path=func.file_path,
                        line_number=bug.get("line_number"),
                        code_snippet=func.code[:200],
                        description=bug.get("description", ""),
                        suggestion=bug.get("suggestion", ""),
                        confidence=bug.get("confidence", 0.7),
                        detection_method="llm_analysis",
                    ))
            
            return bugs
            
        except Exception as e:
            print(f"[WARN] LLM analysis failed for {func.name}: {e}")
            return []
    
    def _deduplicate(self, bugs: list[BugReport]) -> list[BugReport]:
        """Remove duplicate bugs (same type + same file + same line)."""
        seen = set()
        unique = []
        for bug in bugs:
            key = (bug.bug_type, bug.file_path, bug.line_number)
            if key not in seen:
                seen.add(key)
                unique.append(bug)
        return unique
