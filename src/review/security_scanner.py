"""
RAG-based security vulnerability scanner.
Searches Qdrant for similar CWE patterns, then uses LLM to confirm matches.
"""

from src.review.diff_analyzer import DiffAnalysis, FunctionChange
from src.review.bug_detector import BugReport
from src.shared.vector_store import VectorStore
from src.shared.llm_client import LLMClient
from src.config import get_settings


class SecurityScanner:
    """Scans code for security vulnerabilities using vector search + LLM confirmation."""
    
    def __init__(self):
        settings = get_settings()
        self.vector_store = VectorStore()
        self.llm = LLMClient()
        self.collection = settings.qdrant_collection_cve
        self.top_k = settings.top_k_security_results
    
    def scan(self, analysis: DiffAnalysis) -> list[BugReport]:
        """Scan all changed functions for security vulnerabilities."""
        all_issues = []
        for func in analysis.functions_changed:
            issues = self._check_function(func)
            all_issues.extend(issues)
        return all_issues
    
    def _check_function(self, func: FunctionChange) -> list[BugReport]:
        """Check one function against the CWE database via RAG."""
        if len(func.code.strip()) < 20:
            return []
        
        try:
            similar_cwes = self.vector_store.search(
                collection=self.collection,
                query=func.code,
                top_k=self.top_k,
            )
        except Exception as e:
            print(f"[WARN] Qdrant search failed: {e}")
            return []
        
        if not similar_cwes:
            return []
        
        issues = []
        for cwe in similar_cwes:
            if cwe["score"] < 0.3:
                continue
            confirmed = self._confirm_vulnerability(func, cwe)
            if confirmed:
                issues.append(confirmed)
        
        return issues
    
    def _confirm_vulnerability(self, func: FunctionChange, cwe: dict) -> BugReport | None:
        """Use LLM to confirm whether the code actually exhibits the vulnerability."""
        cwe_id = cwe["metadata"].get("cwe_id", "Unknown")
        cwe_text = cwe["text"]
        similarity_score = cwe["score"]
        
        prompt = f"""Analyze this code for the specific vulnerability described below.

CODE TO ANALYZE:
```python
{func.code}
```

POTENTIAL VULNERABILITY (similarity score: {similarity_score:.2f}):
{cwe_text}

QUESTION: Does this code ACTUALLY exhibit {cwe_id}?

Respond in JSON:
{{
    "is_vulnerable": true or false,
    "confidence": 0.0 to 1.0,
    "evidence": "the specific line or pattern that confirms the vulnerability",
    "description": "explanation of the vulnerability in this specific code",
    "suggestion": "how to fix it in this specific case"
}}

RULES:
- Only confirm if you are genuinely confident (>0.7)
- Look for the SPECIFIC patterns described in the vulnerability
- If the code uses parameterized queries, it's NOT sql injection
- If the code properly escapes input, it's NOT xss
- Don't flag theoretical risks -- only actual vulnerable code"""
        
        try:
            result = self.llm.chat_json([
                {"role": "system", "content": "You are a security auditor. Be precise, minimize false positives."},
                {"role": "user", "content": prompt},
            ])
            
            parsed = result.get("parsed", {})
            
            if parsed.get("is_vulnerable") and parsed.get("confidence", 0) > 0.7:
                return BugReport(
                    bug_type=cwe_id.lower().replace("-", "_"),
                    severity=cwe["metadata"].get("severity", "high"),
                    file_path=func.file_path,
                    line_number=func.start_line,
                    code_snippet=parsed.get("evidence", func.code[:200]),
                    description=f"[{cwe_id}] {parsed.get('description', '')}",
                    suggestion=parsed.get("suggestion", ""),
                    confidence=parsed.get("confidence", 0.8),
                    detection_method="security_rag",
                )
            
            return None
            
        except Exception as e:
            print(f"[WARN] Security confirmation failed for {cwe_id}: {e}")
            return None
