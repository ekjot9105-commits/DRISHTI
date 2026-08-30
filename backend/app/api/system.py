from fastapi import APIRouter
from app.core.system_monitor import sys_monitor

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/status")
def get_system_status():
    return sys_monitor.get_stats()
