from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    top = "top"
    bottom = "bottom"
    shoes = "shoes"
    accessories = "accessories"
    outerwear = "outerwear"


class Season(str, Enum):
    spring = "spring"
    summer = "summer"
    autumn = "autumn"
    winter = "winter"
    all_season = "all_season"


class CatalogItemCreate(BaseModel):
    name: str
    category: Category
    colors: list[str] = []
    brand: Optional[str] = None
    size: Optional[str] = None
    seasons: list[Season] = []
    style_tags: list[str] = []
    fit_type: Optional[str] = None
    notes: Optional[str] = None


class CatalogItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[Category] = None
    colors: Optional[list[str]] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    seasons: Optional[list[Season]] = None
    style_tags: Optional[list[str]] = None
    fit_type: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None


class CatalogItemResponse(BaseModel):
    id: str
    user_id: str
    name: str
    category: str
    colors: list[str]
    brand: Optional[str]
    size: Optional[str]
    seasons: list[str]
    style_tags: list[str]
    fit_type: Optional[str]
    image_url: Optional[str]
    image_url_original: Optional[str]
    is_favorite: bool
    notes: Optional[str]
    created_at: datetime


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: str
