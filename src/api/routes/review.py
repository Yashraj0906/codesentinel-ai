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
