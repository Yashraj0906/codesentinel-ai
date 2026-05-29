from dataclasses import dataclass, field
from src.config import get_settings
from src.shared.llm_client import LLMClient
from src.shared.vector_store import VectorStore
from src.shared.cache import CacheService


@dataclass
class QAResponse:
    """Response from the QA agent."""
    answer: str                     # The answer text
    code_references: list[dict]     # [{file_path, name, start_line, end_line, code}]
    confidence: float               # How confident the answer is
    cached: bool                    # Was this served from cache?


class QAAgent:
    """Answers natural language questions about an indexed codebase using RAG."""
    
    def __init__(self):
        settings = get_settings()
        self.llm = LLMClient()
        self.vector_store = VectorStore()
        self.collection = settings.qdrant_collection_code
        self.top_k = settings.top_k_code_results
        
        # Cache is optional -- if Redis is not available, skip caching
        try:
            self.cache = CacheService()
            # Test connection
            self.cache.client.ping()
        except Exception:
            self.cache = None
    
    def ask(self, question: str) -> QAResponse:
        """Answer a question about the indexed codebase using RAG."""
        if self.cache:
            cached = self.cache.get("onboard_qa", question)
            if cached:
                return QAResponse(
                    answer=cached["answer"],
                    code_references=cached.get("code_references", []),
                    confidence=cached.get("confidence", 0.9),
                    cached=True,
                )
        
        try:
            results = self.vector_store.search(
                collection=self.collection,
                query=question,
                top_k=self.top_k,
            )
        except Exception as e:
            return QAResponse(
                answer=f"Search failed: {e}. Is the codebase indexed?",
                code_references=[],
                confidence=0.0,
                cached=False,
            )
        
        if not results:
            return QAResponse(
                answer="No relevant code found. Make sure the repository is indexed first.",
                code_references=[],
                confidence=0.0,
                cached=False,
            )
        
        context = self._build_context(results)
        code_refs = self._extract_references(results)
        
        prompt = f"""You are a codebase expert helping a new team member understand the code.

QUESTION: {question}

RELEVANT CODE CHUNKS (from the codebase):
{context}

INSTRUCTIONS:
1. Answer the question based ONLY on the code provided above
2. Reference specific files and line numbers
3. Explain the flow: which function calls which
4. If the code doesn't answer the question, say so
5. Use simple language - the reader is new to this codebase

Provide a clear, detailed answer."""
        
        result = self.llm.chat([
            {"role": "system", "content": "You are a helpful codebase guide. Answer based only on the provided code. Reference file paths and line numbers."},
            {"role": "user", "content": prompt},
        ])
        
        answer = result["content"]
        
        # Cache the answer
        if self.cache:
            self.cache.set("onboard_qa", question, {
                "answer": answer,
                "code_references": code_refs,
                "confidence": 0.85,
            })
        
        return QAResponse(
            answer=answer,
            code_references=code_refs,
            confidence=0.85,
            cached=False,
        )
    
    def _build_context(self, results: list[dict]) -> str:
        """
        Build a context string from search results.
        Each result includes the code, file path, summary, and call graph info.
        """
        parts = []
        for i, r in enumerate(results):
            meta = r["metadata"]
            part = f"""--- Chunk {i+1} ---
File: {meta.get('file_path', 'unknown')}
Name: {meta.get('name', 'unknown')} ({meta.get('chunk_type', 'unknown')})
Lines: {meta.get('start_line', '?')}-{meta.get('end_line', '?')}
Summary: {meta.get('summary', 'No summary')}
Calls: {meta.get('calls', 'none')}
Called by: {meta.get('called_by', 'none')}

Code:
{r['text'][:1500]}
"""
            parts.append(part)
        
        return "\n".join(parts)
    
    def _extract_references(self, results: list[dict]) -> list[dict]:
        """Extract clean code references from search results."""
        refs = []
        for r in results:
            meta = r["metadata"]
            refs.append({
                "file_path": meta.get("file_path", ""),
                "name": meta.get("name", ""),
                "chunk_type": meta.get("chunk_type", ""),
                "start_line": meta.get("start_line", 0),
                "end_line": meta.get("end_line", 0),
                "summary": meta.get("summary", ""),
                "score": r["score"],
            })
        return refs
