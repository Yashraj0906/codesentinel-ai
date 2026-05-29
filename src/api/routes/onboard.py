# ============================================================
# onboard.py -- Codebase Onboarding API routes
# ============================================================
# ENDPOINTS:
#   POST /onboard/index   -- Index a GitHub repo
#   POST /onboard/ask     -- Ask a question about the indexed repo
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel
from src.onboard import RepoIndexer, QAAgent
import asyncio

router = APIRouter()


class IndexRequest(BaseModel):
    """Request to index a repository."""
    repo_url: str                    # GitHub repo URL
    branch: str = "main"             # Branch to index


class IndexResponse(BaseModel):
    """Response after indexing."""
    status: str
    files: int
    chunks: int
    graph_nodes: int
    summaries: int


class AskRequest(BaseModel):
    """Request to ask a question."""
    question: str


class AskResponse(BaseModel):
    """Response with the answer."""
    answer: str
    code_references: list[dict]
    confidence: float
    cached: bool


@router.post("/index", response_model=IndexResponse)
async def index_repo(request: IndexRequest):
    """Index a GitHub repository."""
    try:
        def _run():
            indexer = RepoIndexer()
            return indexer.index_repo(request.repo_url, request.branch)
        
        stats = await asyncio.to_thread(_run)
        
        return IndexResponse(
            status="completed",
            files=stats.get("files", 0),
            chunks=stats.get("chunks", 0),
            graph_nodes=stats.get("graph_nodes", 0),
            summaries=stats.get("summaries", 0),
        )
    except Exception as e:
        return IndexResponse(
            status=f"error: {str(e)[:200]}",
            files=0, chunks=0, graph_nodes=0, summaries=0,
        )


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a question about the indexed codebase."""
    try:
        def _run():
            qa = QAAgent()
            return qa.ask(request.question)
        
        response = await asyncio.to_thread(_run)
        
        return AskResponse(
            answer=response.answer,
            code_references=response.code_references,
            confidence=response.confidence,
            cached=response.cached,
        )
    except Exception as e:
        return AskResponse(
            answer=f"Error: {str(e)}. Make sure you have indexed a repository first.",
            code_references=[],
            confidence=0.0,
            cached=False,
        )

