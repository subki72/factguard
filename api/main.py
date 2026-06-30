"""
AI Fake News Detection — FastAPI Backend Entry Point

This is the main entry point for the FastAPI application.
On Vercel, this file is served as a serverless function via vercel.json rewrites.
Locally, run with: uvicorn api.main:app --reload --port 8000
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import analyze, analyses, community, trending, cron, feedback
from api.utils.rate_limiter import RateLimitExceeded

load_dotenv()

app = FastAPI(
    title="AI Fake News Detection API",
    description="API untuk mendeteksi objektivitas narasi politik Indonesia",
    version="0.1.0",
)

# CORS — izinkan frontend Next.js mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        os.getenv("FRONTEND_URL", ""),  # Production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(analyze.router, prefix="/api", tags=["Analyze"])
app.include_router(analyses.router, prefix="/api", tags=["Analyses"])
app.include_router(trending.router, prefix="/api", tags=["Trending"])
app.include_router(community.router, prefix="/api", tags=["Community"])
app.include_router(cron.router, prefix="/api/cron", tags=["Cron"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Global handler for rate limit errors (BR13: 3 req/min/IP)."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Terlalu banyak permintaan. Silakan tunggu sebentar sebelum mencoba lagi.",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler to prevent server crashes (Convention #4)."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Terjadi kesalahan internal. Silakan coba lagi nanti.",
            "code": "INTERNAL_ERROR",
        },
    )


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"success": True, "data": {"status": "ok"}}
