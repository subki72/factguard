import os
import smtplib
from email.message import EmailMessage
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.utils.auth import require_auth
from api.services.supabase_client import get_supabase_client

router = APIRouter()

class FeedbackRequest(BaseModel):
    subject: str
    message: str

@router.post("/submit")
async def submit_feedback(payload: FeedbackRequest, request: Request):
    user_id = await require_auth(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required to submit feedback.")

    if not payload.subject.strip() or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Subject and message cannot be empty.")

    # Get user info from database
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("name, email").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found.")
        
        user_name = result.data[0].get("name") or "User"
        user_email = result.data[0].get("email") or "Unknown Email"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Prepare email
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_username or not smtp_password:
        print("Warning: SMTP credentials are not configured in .env. Simulating email sending.")
        # If not configured, just return success so UI doesn't break in local dev without .env
        return {"success": True, "sent": True, "note": "Simulated (No SMTP Config)"}

    msg = EmailMessage()
    msg.set_content(f"Dari: {user_name} ({user_email})\n\nPesan:\n{payload.message}")
    msg["Subject"] = f"[Kritik & Saran FG] {payload.subject}"
    msg["From"] = smtp_username
    msg["To"] = "subkisyafii@gmail.com"

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
    except Exception as e:
        print(f"SMTP Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Gagal mengirim email. Pastikan konfigurasi SMTP benar.")

    return {"success": True, "sent": True}
