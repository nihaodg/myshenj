from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.services.ip_blocker import ip_blocker
from app.models.task import BlockedIP
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class BlockIPRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = None
    duration_hours: int = 24


class UnblockIPRequest(BaseModel):
    ip_address: str


@router.post("/block")
async def block_ip(request: BlockIPRequest):
    success = await ip_blocker.block_ip(
        request.ip_address,
        request.reason,
        request.duration_hours
    )
    if success:
        return {"message": f"IP {request.ip_address} 已封锁", "success": True}
    return {"message": "封锁失败", "success": False}


@router.post("/unblock")
async def unblock_ip(request: UnblockIPRequest):
    success = await ip_blocker.unblock_ip(request.ip_address)
    if success:
        return {"message": f"IP {request.ip_address} 已解除封锁", "success": True}
    return {"message": "解除封锁失败", "success": False}


@router.get("/blocked")
async def get_blocked_ips():
    blocked = await ip_blocker.get_blocked_ips()
    return {
        "blocked_ips": [
            {
                "ip_address": b.ip_address,
                "reason": b.reason,
                "blocked_at": b.blocked_at.isoformat() if b.blocked_at else None,
                "expires_at": b.expires_at.isoformat() if b.expires_at else None
            }
            for b in blocked
        ]
    }


@router.get("/check/{ip_address}")
async def check_ip(ip_address: str):
    is_blocked = await ip_blocker.is_blocked(ip_address)
    return {"ip_address": ip_address, "is_blocked": is_blocked}
