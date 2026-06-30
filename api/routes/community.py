"""
Community endpoints — Vote and Comment (FR6, BR8).

Both endpoints require authentication (registered user only).
Guest users cannot vote or comment.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.models.schemas import VoteRequest, CommentRequest
from api.services.supabase_client import get_supabase_client
from api.utils.rate_limiter import check_rate_limit
from api.utils.auth import require_auth

router = APIRouter()

@router.post("/analyses/{analysis_id}/vote")
async def vote_analysis(analysis_id: str, vote: VoteRequest, request: Request):
    """
    Vote on an analysis (agree/disagree). Requires authentication (BR8).
    One user can only vote once per analysis.
    """
    check_rate_limit(request)

    user_id = await require_auth(request)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk memberikan vote.",
                "code": "AUTH_REQUIRED",
            },
        )

    try:
        supabase = get_supabase_client()

        # Check if analysis exists
        analysis = (
            supabase.table("analyses").select("id").eq("id", analysis_id).execute()
        )
        if not analysis.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Analisis tidak ditemukan.",
                    "code": "NOT_FOUND",
                },
            )

        # Upsert vote (update if exists, insert if not)
        supabase.table("votes").upsert(
            {
                "analysis_id": analysis_id,
                "user_id": user_id,
                "is_agree": vote.is_agree,
            },
            on_conflict="analysis_id,user_id",
        ).execute()

        # Return updated vote counts
        all_votes = (
            supabase.table("votes")
            .select("is_agree")
            .eq("analysis_id", analysis_id)
            .execute()
        )
        votes_data = all_votes.data or []
        vote_agree = sum(1 for v in votes_data if v["is_agree"])
        vote_disagree = sum(1 for v in votes_data if not v["is_agree"])

        return {
            "success": True,
            "data": {
                "vote_agree": vote_agree,
                "vote_disagree": vote_disagree,
                "user_vote": vote.is_agree,
            },
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal menyimpan vote.",
                "code": "VOTE_ERROR",
            },
        )


@router.post("/analyses/{analysis_id}/comment")
async def add_comment(analysis_id: str, comment: CommentRequest, request: Request):
    """
    Add a comment to an analysis. Requires authentication (BR8).
    No moderation — comments are published immediately (BR9).
    """
    check_rate_limit(request)

    user_id = await require_auth(request)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk berkomentar.",
                "code": "AUTH_REQUIRED",
            },
        )

    try:
        supabase = get_supabase_client()

        # Check if analysis exists
        analysis = (
            supabase.table("analyses").select("id").eq("id", analysis_id).execute()
        )
        if not analysis.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Analisis tidak ditemukan.",
                    "code": "NOT_FOUND",
                },
            )

        # Insert comment
        result = (
            supabase.table("comments")
            .insert({
                "analysis_id": analysis_id,
                "user_id": user_id,
                "content": comment.content,
            })
            .execute()
        )

        # Get user name for response
        user_result = (
            supabase.table("users").select("name").eq("id", user_id).execute()
        )
        user_name = user_result.data[0]["name"] if user_result.data else "Anonim"

        return {
            "success": True,
            "data": {
                "id": result.data[0]["id"],
                "user_name": user_name,
                "content": comment.content,
                "created_at": result.data[0]["created_at"],
            },
            "message": "Komentar berhasil ditambahkan.",
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal menyimpan komentar.",
                "code": "COMMENT_ERROR",
            },
        )
