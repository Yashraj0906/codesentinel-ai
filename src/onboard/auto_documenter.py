from src.shared.llm_client import LLMClient
from src.onboard.code_chunker import CodeChunk


class AutoDocumenter:
    """Generates LLM-powered documentation summaries for code chunks."""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def summarize(self, chunk: CodeChunk) -> str:
        """
        Generate a 1-2 sentence summary of a code chunk.
        Uses LLM to understand what the code does.
        """
        prompt = f"""Summarize this Python code in 1-2 sentences. 
Be specific about WHAT it does and HOW, not just the name.

File: {chunk.file_path}
Type: {chunk.chunk_type}
Name: {chunk.name}

```python
{chunk.code[:2000]}
```

Return ONLY the summary text, nothing else."""
        
        result = self.llm.chat([
            {"role": "system", "content": "You summarize code concisely. Return only the summary."},
            {"role": "user", "content": prompt},
        ], max_tokens=200)
        
        return result["content"].strip()
    
    def summarize_batch(self, chunks: list[CodeChunk], max_chunks: int = 50) -> dict[str, str]:
        """
        Summarize multiple chunks. Returns dict mapping chunk_id to summary.
        Limits to max_chunks to control LLM cost during indexing.
        """
        summaries = {}
        
        # Only summarize functions and classes, skip module-level
        important_chunks = [c for c in chunks if c.chunk_type in ("function", "class")]
        
        # Limit to avoid excessive LLM costs
        to_summarize = important_chunks[:max_chunks]
        
        print(f"[*] Generating summaries for {len(to_summarize)} chunks...")
        
        for i, chunk in enumerate(to_summarize):
            try:
                summary = self.summarize(chunk)
                summaries[chunk.chunk_id] = summary
                if (i + 1) % 10 == 0:
                    print(f"   Summarized {i+1}/{len(to_summarize)}")
            except Exception as e:
                print(f"   [WARN] Failed to summarize {chunk.name}: {e}")
                summaries[chunk.chunk_id] = chunk.docstring or f"{chunk.chunk_type}: {chunk.name}"
        
        print(f"[OK] Generated {len(summaries)} summaries")
        return summaries
