"""
AST-based code parser that extracts individual functions from submitted code.
Supports both raw code input and unified git diff format.
"""

import ast
import re
from dataclasses import dataclass, field
from unidiff import PatchSet


@dataclass
class FunctionChange:
    """Represents one extracted function/method."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    code: str
    change_type: str
    docstring: str | None = None


@dataclass
class DiffAnalysis:
    """Complete parsing result with extracted functions and metadata."""
    files_changed: list[str]
    lines_added: int
    lines_removed: int
    functions_changed: list[FunctionChange]
    change_type: str
    risk_level: str
    raw_diff: str


class DiffAnalyzer:
    """Parses code or diffs to extract functions for analysis."""
    
    HIGH_RISK_PATTERNS = [
        r"auth", r"login", r"password", r"payment", r"billing",
        r"migration", r"security", r"crypto", r"token",
    ]
    
    def parse_diff(self, diff_text: str) -> DiffAnalysis:
        """Parse a unified git diff and extract changed functions."""
        try:
            patch = PatchSet(diff_text)
        except Exception:
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
            
            added_code = ""
            for hunk in patched_file:
                for line in hunk:
                    if line.is_added:
                        added_code += line.value
            
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
        """Parse raw code string and extract functions using AST."""
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
        """Use AST to extract all function/method definitions from code."""
        functions = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
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
        """Classify change type based on file paths."""
        file_str = " ".join(files).lower()
        
        if any(f.startswith("test") or "/test" in f for f in files):
            return "test"
        if any(p in file_str for p in ["config", ".env", ".yml", ".yaml", ".toml"]):
            return "config"
        if any(p in file_str for p in ["readme", "doc", ".md"]):
            return "docs"
        return "feature"
    
    def _assess_risk(self, files: list[str], total_changes: int) -> str:
        """Assess risk level based on file sensitivity and change size."""
        file_str = " ".join(files).lower()
        
        if any(re.search(p, file_str) for p in self.HIGH_RISK_PATTERNS):
            return "high"
        if total_changes > 200:
            return "high"
        
        if any(p in file_str for p in ["service", "handler", "api", "route"]):
            return "medium"
        if total_changes > 50:
            return "medium"
        
        return "low"
