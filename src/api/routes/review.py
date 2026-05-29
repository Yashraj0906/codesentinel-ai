# ============================================================
# review.py -- Code Review API routes
# ============================================================
# ENDPOINTS:
#   POST /review/analyze   -- Submit code for review
#   GET  /review/{id}      -- Get a specific review result
#
# HOW FASTAPI ROUTES WORK:
# 1. You define a function with a decorator (@router.post)
# 2. FastAPI automatically:
#    - Validates the request body (using Pydantic models)
#    - Converts Python dict to JSON response
#    - Generates API documentation at /docs
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel
from src.review import CodeReviewPipeline
from src.review.report_generator import ReportGenerator
import asyncio

router = APIRouter()

# Pydantic models for request/response validation
# These define WHAT the API accepts and returns


class ReviewRequest(BaseModel):
    """What the frontend sends to start a review."""
    code: str                               # The code to review
    file_path: str = "submitted_code.py"    # Optional file name


class ReviewResponse(BaseModel):
    """What the API returns after a review."""
    review_id: str
    summary: str
    risk_level: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues_auto_fixed: int
    total_time_ms: int
    total_cost_usd: float
    issues: list[dict]
    markdown_report: str


@router.post("/analyze", response_model=ReviewResponse)
async def analyze_code(request: ReviewRequest):
    """
    Submit code for review.
    
    This is the main endpoint. The frontend sends code here,
    and gets back a full review report with bugs, fixes, and costs.
    """
    # Run the pipeline in a thread so it doesn't block the async event loop.
    # Without this, the server freezes for ~80 seconds and the request times out.
    def _run_pipeline():
        pipeline = CodeReviewPipeline()
        return pipeline.review_code(request.code, request.file_path)
    
    report = await asyncio.to_thread(_run_pipeline)
    
    # Generate markdown version
    markdown = ReportGenerator().to_markdown(report)
    
    return ReviewResponse(
        review_id=report.review_id,
        summary=report.summary,
        risk_level=report.risk_level,
        total_issues=report.total_issues,
        critical_count=report.critical_count,
        high_count=report.high_count,
        medium_count=report.medium_count,
        low_count=report.low_count,
        issues_auto_fixed=report.issues_auto_fixed,
        total_time_ms=report.total_time_ms,
        total_cost_usd=report.total_cost_usd,
        issues=report.issues,
        markdown_report=markdown,
    )
