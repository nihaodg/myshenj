from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
from app.core.database import get_db
from app.services.alerter import alert_system
from pydantic import BaseModel

router = APIRouter()


class AlertConfigUpdate(BaseModel):
    web_notification: bool = True
    email_notification: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_recipients: List[str] = []
    min_severity: str = "medium"
    alert_throttling: bool = True
    throttle_period: int = 300
    webhook_url: str = ""
    webhook_enabled: bool = False


@router.get("/alerts")
async def get_alerts(limit: int = 100):
    return alert_system.get_recent_alerts(limit)


@router.get("/alerts/stats")
async def get_alert_stats():
    return alert_system.get_alert_stats()


@router.post("/alerts/config")
async def update_alert_config(config: AlertConfigUpdate):
    alert_system.update_config(config.model_dump())
    return {"message": "告警配置已更新"}


@router.post("/alerts/test")
async def test_alert():
    alert = alert_system.create_alert(
        alert_type="测试告警",
        severity="medium",
        message="这是一条测试告警，用于验证告警配置是否正确",
        src_ip="127.0.0.1",
        action="已发送"
    )
    return {"message": "测试告警已发送", "alert": alert}
