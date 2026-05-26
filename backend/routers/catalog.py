import uuid
import io
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional
from models.schemas import CatalogItemCreate, CatalogItemUpdate, CatalogItemResponse, Category
from db.supabase_client import get_supabase
from services.image_service import remove_background_png, validate_and_resize
from routers.auth import get_current_user

router = APIRouter(prefix="/catalog", tags=["catalog"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_item(
    name: str = Form(...),
    category: Category = Form(...),
    colors: str = Form(""),           # comma-separated
    brand: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    seasons: str = Form(""),          # comma-separated
    style_tags: str = Form(""),       # comma-separated
    fit_type: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    authorization: str = Header(...),
):
    user = await get_current_user(authorization)
    sb = get_supabase()

    # Validate file
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images are accepted")

    raw_bytes = await photo.read()
    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image must be under 10 MB")

    item_id = str(uuid.uuid4())

    # Upload original
    original_path = f"{user.id}/{item_id}/original.jpg"
    original_bytes = validate_and_resize(raw_bytes)
    sb.storage.from_("catalog").upload(original_path, original_bytes, {"content-type": "image/jpeg"})
    original_url = sb.storage.from_("catalog").get_public_url(original_path)

    # Remove background → upload as PNG
    bg_removed = remove_background_png(raw_bytes)
    processed_path = f"{user.id}/{item_id}/processed.png"
    sb.storage.from_("catalog").upload(processed_path, bg_removed, {"content-type": "image/png"})
    processed_url = sb.storage.from_("catalog").get_public_url(processed_path)

    # Parse list fields
    def parse_list(s: str) -> list[str]:
        return [x.strip() for x in s.split(",") if x.strip()] if s else []

    row = {
        "id": item_id,
        "user_id": user.id,
        "name": name,
        "category": category.value,
        "colors": parse_list(colors),
        "brand": brand,
        "size": size,
        "seasons": parse_list(seasons),
        "style_tags": parse_list(style_tags),
        "fit_type": fit_type,
        "image_url": processed_url,
        "image_url_original": original_url,
        "is_favorite": False,
        "notes": notes,
    }

    result = sb.table("catalog_items").insert(row).execute()
    return result.data[0]


@router.get("/", response_model=list[CatalogItemResponse])
async def list_items(
    category: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    authorization: str = Header(...),
):
    user = await get_current_user(authorization)
    sb = get_supabase()

    query = sb.table("catalog_items").select("*").eq("user_id", user.id).order("created_at", desc=True)

    if category:
        query = query.eq("category", category)
    if season:
        query = query.contains("seasons", [season])
    if color:
        query = query.contains("colors", [color])
    if search:
        query = query.ilike("name", f"%{search}%")

    result = query.execute()
    return result.data


@router.get("/{item_id}", response_model=CatalogItemResponse)
async def get_item(item_id: str, authorization: str = Header(...)):
    user = await get_current_user(authorization)
    sb = get_supabase()

    result = sb.table("catalog_items").select("*").eq("id", item_id).eq("user_id", user.id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return result.data


@router.patch("/{item_id}", response_model=CatalogItemResponse)
async def update_item(item_id: str, payload: CatalogItemUpdate, authorization: str = Header(...)):
    user = await get_current_user(authorization)
    sb = get_supabase()

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        sb.table("catalog_items")
        .update(updates)
        .eq("id", item_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return result.data[0]


@router.delete("/{item_id}")
async def delete_item(item_id: str, authorization: str = Header(...)):
    user = await get_current_user(authorization)
    sb = get_supabase()

    # Remove storage files
    for suffix in ["original.jpg", "processed.png"]:
        try:
            sb.storage.from_("catalog").remove([f"{user.id}/{item_id}/{suffix}"])
        except Exception:
            pass

    result = (
        sb.table("catalog_items")
        .delete()
        .eq("id", item_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"deleted": True}


@router.patch("/{item_id}/favorite")
async def toggle_favorite(item_id: str, authorization: str = Header(...)):
    user = await get_current_user(authorization)
    sb = get_supabase()

    current = (
        sb.table("catalog_items").select("is_favorite").eq("id", item_id).eq("user_id", user.id).single().execute()
    )
    if not current.data:
        raise HTTPException(status_code=404, detail="Item not found")

    new_val = not current.data["is_favorite"]
    result = (
        sb.table("catalog_items")
        .update({"is_favorite": new_val})
        .eq("id", item_id)
        .eq("user_id", user.id)
        .execute()
    )
    return {"is_favorite": new_val}
