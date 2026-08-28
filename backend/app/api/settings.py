from fastapi import APIRouter, Body
from app.core.settings_manager import load_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/")
def get_settings():
    return load_settings()

@router.patch("/")
def update_settings(settings: dict = Body(...)):
    current = load_settings()
    current.update(settings)
    save_settings(current)
    return current
