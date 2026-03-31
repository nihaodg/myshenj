from fastapi import APIRouter
from app.api.endpoints import audit, rules, reports, settings

api_router = APIRouter()

api_router.include_router(audit.router, prefix="", tags=["audit"])
api_router.include_router(rules.router, prefix="", tags=["rules"])
api_router.include_router(reports.router, prefix="", tags=["reports"])
api_router.include_router(settings.router, prefix="", tags=["settings"])
