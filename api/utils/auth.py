from fastapi import Request
from api.services.supabase_client import get_supabase_client

async def require_auth(request: Request) -> str | None:
    """
    Extract and validate user_id from Bearer token.
    Syncs the user profile from auth.users to public.users on first login.
    Returns user_id (UUID string from public.users) or None if not authenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")

    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)
        
        if user_response and user_response.user:
            auth_user = user_response.user
            
            # Sync user to public.users table using select then insert (safer than upsert)
            upsert_data = {
                "auth_id": auth_user.id,
                "email": auth_user.email,
                "name": auth_user.user_metadata.get("name") if auth_user.user_metadata else None
            }
            
            result = supabase.table("users").select("id").eq("auth_id", auth_user.id).execute()
            
            if not result.data:
                # User doesn't exist, insert them
                insert_result = supabase.table("users").insert(upsert_data).execute()
                if insert_result.data:
                    return insert_result.data[0]["id"]
            else:
                return result.data[0]["id"]
    except Exception as e:
        print(f"Auth error: {e}")
        pass

    return None
