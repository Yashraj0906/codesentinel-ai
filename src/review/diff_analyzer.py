# ============================================================
# diff_analyzer.py — Parses code and extracts functions
# ============================================================
# WHY THIS EXISTS:
# When someone submits code for review, you don't want to dump
# the entire file into the LLM. Instead:
#   1. Parse the code using Python's AST (Abstract Syntax Tree)
#   2. Extract each function/class separately
#   3. Feed each function to the bug detector individually
#
# WHAT IS AST:
# AST converts your code from text into a tree structure.
#   def add(a, b):
#       return a + b
# Becomes:
#   FunctionDef(name='add', args=['a','b'], body=[Return(a+b)])
#
# This lets you UNDERSTAND code structure, not just read text.
# ============================================================

import ast
import re
from dataclasses import dataclass, field
from unidiff import PatchSet


@dataclass
class FunctionChange:
    """
    Represents one function/method found in the code.
    Each of these gets sent to the bug detector separately.
    """
    name: str               # Function name (e.g., "get_user")
    file_path: str           # Which file it's in
    start_line: int          # Where it starts
    end_line: int            # Where it ends
    code: str                # The actual code of this function
    change_type: str         # "added" | "modified" | "deleted"
    docstring: str | None = None  # Function's docstring if it has one


@dataclass
class DiffAnalysis:
    """
    Complete analysis result. Contains everything the bug detector needs.
    """
    files_changed: list[str]              # List of file paths
    lines_added: int                       # Total lines added
    lines_removed: int                     # Total lines removed
    functions_changed: list[FunctionChange]  # Individual functions found
    change_type: str                       # "feature" | "bugfix" | "test" | "config"
    risk_level: str                        # "low" | "medium" | "high"
    raw_diff: str                          # The original input


class DiffAnalyzer:
    """
    Analyzes code to extract functions and assess risk.
    
    TWO WAYS TO USE:
    1. parse_diff(diff_text)   → for git diff input
    2. parse_code(code_string) → for raw code input (simpler, used more often)
    """
    
    # Files that touch these areas = HIGH RISK
    # Why? A bug in auth/payment can cause real damage
    HIGH_RISK_PATTERNS = [
        r"auth", r"login", r"password", r"payment", r"billing",
        r"migration", r"security", r"crypto", r"token",
    ]
    
    def parse_diff(self, diff_text: str) -> DiffAnalysis:
        """
        Parse a unified git diff string.
        
        WHAT IS A UNIFIED DIFF:
        When you run `git diff`, you get something like:
            --- a/app.py
            +++ b/app.py
            @@ -10,5 +10,7 @@
            +def new_function():
            +    return "hello"
        
        The `unidiff` library turns this into structured data.
        """
        try:
            patch = PatchSet(diff_text)
        except Exception:
            # If it's not a valid diff, treat as raw code
            return self.parse_code(diff_text)
        
        files_changed = []
        total_added = 0
        total_removed = 0
        all_functions = []
        
        for patched_file in patch:
            file_path = patched_file.path
            files_changed.append(file_path)
            total_added += patched_file.added
            total_removed += patched_file.removed
            
            # Extract the added code from the diff
            added_code = ""
            for hunk in patched_file:
                for line in hunk:
                    if line.is_added:
                        added_code += line.value
            
            # If it's a Python file, extract functions using AST
            if file_path.endswith(".py") and added_code.strip():
                functions = self._extract_functions(added_code, file_path)
                all_functions.extend(functions)
        
        return DiffAnalysis(
            files_changed=files_changed,
            lines_added=total_added,
            lines_removed=total_removed,
            functions_changed=all_functions,
            change_type=self._classify_change(files_changed),
            risk_level=self._assess_risk(files_changed, total_added + total_removed),
            raw_diff=diff_text,
        )
    
    def parse_code(self, code: str, file_path: str = "submitted_code.py") -> DiffAnalysis:
        """
        Parse a raw code string (not a diff).
        This is the simpler, more commonly used method.
        
        Use this when someone pastes code directly into the UI.
        """
        functions = self._extract_functions(code, file_path)
        
        return DiffAnalysis(
            files_changed=[file_path],
            lines_added=len(code.split("\n")),
            lines_removed=0,
            functions_changed=functions,
            change_type=self._classify_change([file_path]),
            risk_level=self._assess_risk([file_path], len(code.split("\n"))),
            raw_diff=code,
        )
    
    def _extract_functions(self, code: str, file_path: str) -> list[FunctionChange]:
        """
        Use Python's AST to find all functions in the code.
        
        THIS IS THE KEY DIFFERENTIATOR:
        - Tutorial approach: regex to find "def " → breaks on edge cases
        - Production approach: AST parsing → understands nested functions,
          decorators, async functions, classes, everything
        
        HOW IT WORKS:
        1. ast.parse(code) → converts code string to a tree
        2. ast.walk(tree) → visits every node in the tree
        3. Find FunctionDef and AsyncFunctionDef nodes
        4. Extract name, code, docstring from each
        """
        functions = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Code might be invalid Python (partial diff, other language)
            # In that case, treat the whole code as one "function"
            if code.strip():
                functions.append(FunctionChange(
                    name="<unparseable>",
                    file_path=file_path,
                    start_line=1,
                    end_line=len(code.split("\n")),
                    code=code,
                    change_type="modified",
                ))
            return functions
        
        lines = code.split("\n")
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Extract the function's source code from line numbers
                func_code = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                
                functions.append(FunctionChange(
                    name=node.name,
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    code=func_code,
                    change_type="modified",
                    docstring=ast.get_docstring(node),
                ))
        
        # If no functions found but code exists, treat whole code as one chunk
        if not functions and code.strip():
            functions.append(FunctionChange(
                name="<module_level>",
                file_path=file_path,
                start_line=1,
                end_line=len(lines),
                code=code,
                change_type="modified",
            ))
        
        return functions
    
    def _classify_change(self, files: list[str]) -> str:
        """
        Guess what type of change this is based on file paths.
        Used for reporting — "This looks like a test change"
        """
        file_str = " ".join(files).lower()
        
        if any(f.startswith("test") or "/test" in f for f in files):
            return "test"
        if any(p in file_str for p in ["config", ".env", ".yml", ".yaml", ".toml"]):
            return "config"
        if any(p in file_str for p in ["readme", "doc", ".md"]):
            return "docs"
        return "feature"
    
    def _assess_risk(self, files: list[str], total_changes: int) -> str:
        """
        Assess how risky this change is.
        
        WHY:
        - Changes to auth.py → high risk (security implications)
        - Changes to tests/ → low risk (can't break production)
        - 500 lines changed → high risk (too much to review carefully)
        """
        file_str = " ".join(files).lower()
        
        # High risk: security-sensitive files or very large changes
        if any(re.search(p, file_str) for p in self.HIGH_RISK_PATTERNS):
            return "high"
        if total_changes > 200:
            return "high"
        
        # Medium risk: business logic
        if any(p in file_str for p in ["service", "handler", "api", "route"]):
            return "medium"
        if total_changes > 50:
            return "medium"
        
        return "low"
