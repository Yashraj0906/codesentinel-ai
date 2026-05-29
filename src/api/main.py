# ============================================================
# api/main.py -- FastAPI application entry point
# ============================================================
# HOW TO RUN:
#   uvicorn src.api.main:app --reload
#
# WHAT IS FastAPI:
# FastAPI is a Python web framework for building APIs.
# An API is how your frontend (Streamlit) talks to your backend.
#   Frontend: "POST /review/analyze with this code"
#   Backend: "Here are the bugs I found"
#
# YOU NEED TO WATCH: "FastAPI in 1 hour - Tech With Tim"
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import review, onboard, health


# Create the FastAPI app
app = FastAPI(
    title="CodeSentinel AI",
    description="AI-powered code review and codebase onboarding platform",
    version="1.0.0",
)

# CORS middleware -- allows the Streamlit frontend to talk to this API
# Without this, browser blocks requests from localhost:8501 to localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(health.router, tags=["Health"])
app.include_router(review.router, prefix="/review", tags=["Code Review"])
app.include_router(onboard.router, prefix="/onboard", tags=["Onboarding"])


@app.get("/")
async def root():
    return {
        "name": "CodeSentinel AI",
        "version": "1.0.0",
        "docs": "/docs",       # FastAPI auto-generates API docs here
    }
