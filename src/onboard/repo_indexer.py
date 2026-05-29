# ============================================================
# repo_indexer.py -- Clones and indexes a GitHub repository
# ============================================================
# WHY THIS EXISTS:
# This is the ENTRY POINT for onboarding. When someone pastes
# a GitHub repo URL, this file:
#   1. Clones the repo
#   2. Chunks all Python files
#   3. Builds the call graph
#   4. Generates summaries (auto-documenter)
#   5. Stores everything in Qdrant
#
# After indexing, the QA agent can answer questions about it.
# ============================================================

import os
import shutil
import tempfile
from git import Repo
from src.config import get_settings
from src.onboard.code_chunker import CodeChunker
from src.onboard.graph_builder import GraphBuilder
from src.onboard.auto_documenter import AutoDocumenter
from src.shared.vector_store import VectorStore


class RepoIndexer:
    """
    Clones a GitHub repo and indexes it into Qdrant.
    
    USAGE:
        indexer = RepoIndexer()
        stats = indexer.index_repo("https://github.com/user/repo")
        print(stats)
        # {'files': 25, 'chunks': 80, 'graph_nodes': 45}
    """
    
    def __init__(self):
        settings = get_settings()
        self.chunker = CodeChunker()
        self.graph_builder = GraphBuilder()
        self.documenter = AutoDocumenter()
        self.vector_store = VectorStore()
        self.collection = settings.qdrant_collection_code
    
    def index_repo(self, repo_url: str, branch: str = "main") -> dict:
        """
        Clone and index a GitHub repository.
        
        Steps:
        1. Clone the repo to a temp directory
        2. Chunk all Python files into functions/classes
        3. Build the function call graph
        4. Auto-generate summaries for each chunk
        5. Embed and store in Qdrant
        6. Clean up the temp directory
        """
        print(f"[*] Indexing repository: {repo_url}")
        
        # Step 1: Clone
        tmp_dir = tempfile.mkdtemp(prefix="codesentinel_repo_")
        try:
            print("[1/5] Cloning repository...")
            Repo.clone_from(repo_url, tmp_dir, branch=branch, depth=1)
            
            # Step 2: Chunk
            print("[2/5] Chunking code files...")
            chunks = self.chunker.chunk_directory(tmp_dir)
            
            if not chunks:
                print("[WARN] No Python files found in repository")
                return {"files": 0, "chunks": 0, "graph_nodes": 0}
            
            # Step 3: Build call graph
            print("[3/5] Building call graph...")
            graph = self.graph_builder.build(chunks)
            
            # Step 4: Auto-document (summaries)
            print("[4/5] Generating documentation...")
            summaries = self.documenter.summarize_batch(chunks)
            
            # Step 5: Store in Qdrant
            print("[5/5] Storing in vector database...")
            self._store_chunks(chunks, summaries, graph)
            
            stats = {
                "files": len(set(c.file_path for c in chunks)),
                "chunks": len(chunks),
                "graph_nodes": len(graph),
                "summaries": len(summaries),
            }
            
            print(f"[OK] Indexing complete: {stats}")
            return stats
            
        finally:
            # Always clean up temp directory
            shutil.rmtree(tmp_dir, ignore_errors=True)
    
    def index_local(self, directory: str) -> dict:
        """
        Index a local directory (no cloning needed).
        Useful for testing with your own code.
        """
        print(f"[*] Indexing local directory: {directory}")
        
        chunks = self.chunker.chunk_directory(directory)
        
        if not chunks:
            print("[WARN] No Python files found")
            return {"files": 0, "chunks": 0, "graph_nodes": 0}
        
        graph = self.graph_builder.build(chunks)
        summaries = self.documenter.summarize_batch(chunks)
        self._store_chunks(chunks, summaries, graph)
        
        stats = {
            "files": len(set(c.file_path for c in chunks)),
            "chunks": len(chunks),
            "graph_nodes": len(graph),
            "summaries": len(summaries),
        }
        
        print(f"[OK] Indexing complete: {stats}")
        return stats
    
    def _store_chunks(self, chunks, summaries, graph):
        """
        Store chunks in Qdrant with their summaries and graph info.
        
        Each document has:
        - text: the code itself (what gets embedded and searched)
        - metadata: file_path, name, type, summary, calls, called_by
        """
        settings = get_settings()
        
        # Create collection if not exists
        self.vector_store.create_collection(
            self.collection,
            dimension=settings.embedding_dimension,
        )
        
        # Build documents for Qdrant
        documents = []
        for chunk in chunks:
            # Combine code + summary for richer embeddings
            summary = summaries.get(chunk.chunk_id, chunk.docstring or "")
            search_text = f"{chunk.name}: {summary}\n\n{chunk.code}"
            
            # Get graph info
            graph_node = graph.get(chunk.name)
            calls = graph_node.calls if graph_node else chunk.calls
            called_by = graph_node.called_by if graph_node else []
            
            documents.append({
                "id": chunk.chunk_id,
                "text": search_text,
                "metadata": {
                    "file_path": chunk.file_path,
                    "name": chunk.name,
                    "chunk_type": chunk.chunk_type,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "summary": summary,
                    "calls": ",".join(calls[:20]),       # Store as comma-separated string
                    "called_by": ",".join(called_by[:20]),
                    "parent_class": chunk.parent_class,
                },
            })
        
        # Upsert in batches of 50
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            self.vector_store.upsert(self.collection, batch)
