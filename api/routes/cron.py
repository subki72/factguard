"""
POST /api/cron/crawl — Crawler endpoint triggered by Vercel Cron.

Scheduled to run daily at 08:00 WIB (01:00 UTC) via vercel.json.
Protected by CRON_SECRET_KEY to prevent unauthorized access.

Crawls political articles from Indonesian news portals, analyzes them
via Groq, and saves results to crawled_articles table (FR8, BR11, BR12).
"""

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.services.crawler import crawl_and_analyze

router = APIRouter()


@router.post("/crawl")
async def trigger_crawl(request: Request):
    """
    Trigger the daily news crawler.

    Security: Only accessible with valid CRON_SECRET_KEY.
    On Vercel, this is sent automatically via the Authorization header
    by the Vercel Cron system.
    """
    # Verify cron secret
    expected_secret = os.getenv("CRON_SECRET_KEY", "")
    auth_header = request.headers.get("Authorization", "")

    if not expected_secret or auth_header != f"Bearer {expected_secret}":
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Unauthorized.",
                "code": "UNAUTHORIZED",
            },
        )

    try:
        result = await crawl_and_analyze()
        return {
            "success": True,
            "data": result,
            "message": "Crawling selesai.",
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Crawling gagal: {str(e)}",
                "code": "CRAWL_ERROR",
            },
        )
