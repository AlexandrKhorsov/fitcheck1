from fastapi import APIRouter, HTTPException, Header
from db.supabase_client import get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(authorization: str = Header(...)):
    """Validate Supabase JWT and return user dict."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.removeprefix("Bearer ")
    sb = get_supabase()

    try:
        response = sb.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/me")
async def me(authorization: str = Header(...)):
    user = await get_current_user(authorization)
    sb = get_supabase()

    profile = sb.table("users").select("*").eq("id", user.id).single().execute()
    return profile.data
