from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import review, onboard, health


app = FastAPI(
    title="CodeSentinel AI",
    description="AI-powered code review and codebase onboarding platform",
    version="1.0.0",
)

# CORS middleware -- allows the Streamlit frontend to talk to this API
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
