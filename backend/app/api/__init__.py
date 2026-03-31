from fastapi import APIRouter
from app.api.endpoints import audit, rules, reports, settings, alerts, defense

api_router = APIRouter()

api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(defense.router, prefix="/defense", tags=["defense"])
