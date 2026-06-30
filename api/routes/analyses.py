"""
GET /api/analyses/:id — Get detailed analysis result.

Returns the full analysis data including community votes and comments.
Public endpoint — no auth required.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.services.supabase_client import get_supabase_client
from api.utils.auth import require_auth
from fastapi import Request

router = APIRouter()


@router.get("/analyses/history")
async def get_analysis_history(request: Request):
    """Get history of analyses for the currently authenticated user."""
    user_id = await require_auth(request)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk melihat riwayat.",
                "code": "AUTH_REQUIRED",
            },
        )
        
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("analyses")
            .select("id, input_type, extracted_text, detected_language, score, label, reasoning, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        
        history = []
        for row in result.data or []:
            history.append({
                "analysis_id": row["id"],
                "input_type": row["input_type"],
                "extracted_text": row["extracted_text"],
                "detected_language": row["detected_language"],
                "score": row["score"],
                "label": row["label"],
                "reasoning": row["reasoning"],
                "timestamp": row["created_at"]
            })
            
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        print(f"Error fetching history: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal mengambil riwayat analisis.",
                "code": "FETCH_ERROR",
            },
        )


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get detailed analysis result by ID, including community data."""
    try:
        supabase = get_supabase_client()

        # Fetch analysis
        result = (
            supabase.table("analyses")
            .select("*")
            .eq("id", analysis_id)
            .execute()
        )

        if not result.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Analisis tidak ditemukan.",
                    "code": "NOT_FOUND",
                },
            )

        analysis = result.data[0]

        # Fetch vote counts
        votes_result = (
            supabase.table("votes")
            .select("is_agree")
            .eq("analysis_id", analysis_id)
            .execute()
        )
        votes = votes_result.data or []
        vote_agree = sum(1 for v in votes if v["is_agree"])
        vote_disagree = sum(1 for v in votes if not v["is_agree"])

        # Fetch comments with user names
        comments_result = (
            supabase.table("comments")
            .select("id, content, created_at, user_id")
            .eq("analysis_id", analysis_id)
            .order("created_at", desc=False)
            .execute()
        )
        comments = []
        for comment in comments_result.data or []:
            # Fetch user name for each comment
            user_result = (
                supabase.table("users")
                .select("name")
                .eq("id", comment["user_id"])
                .execute()
            )
            user_name = user_result.data[0]["name"] if user_result.data else "Anonim"
            comments.append({
                "id": comment["id"],
                "user_name": user_name,
                "content": comment["content"],
                "created_at": comment["created_at"],
            })

        return {
            "success": True,
            "data": {
                **analysis,
                "vote_agree": vote_agree,
                "vote_disagree": vote_disagree,
                "comments": comments,
            },
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal mengambil data analisis.",
                "code": "FETCH_ERROR",
            },
        )


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str, request: Request):
    """SR3.1: Delete an analysis and log the action."""
    user_id = await require_auth(request)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk menghapus analisis.",
                "code": "AUTH_REQUIRED",
            },
        )
        
    try:
        supabase = get_supabase_client()
        
        # Verify ownership
        result = supabase.table("analyses").select("user_id").eq("id", analysis_id).execute()
        
        if not result.data:
            return JSONResponse(status_code=404, content={"success": False, "error": "Analisis tidak ditemukan."})
            
        if result.data[0]["user_id"] != user_id:
            return JSONResponse(status_code=403, content={"success": False, "error": "Akses ditolak."})
            
        # Delete analysis
        supabase.table("analyses").delete().eq("id", analysis_id).execute()
        
        # Log to audit_logs
        try:
            from api.utils.rate_limiter import get_client_ip_hash
            ip_hash = get_client_ip_hash(request)
            supabase.table("audit_logs").insert({
                "user_id": user_id,
                "ip_hash": ip_hash,
                "action_type": "ANALYSIS_DELETED",
                "details": {"analysis_id": analysis_id}
            }).execute()
        except Exception:
            pass # ignore audit log errors to not fail the main request
            
        return {"success": True, "message": "Analisis berhasil dihapus."}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal menghapus analisis.",
                "code": "DELETE_ERROR",
            },
        )
