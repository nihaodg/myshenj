import re
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.models.task import BlockedIP


class IPBlocker:
    def __init__(self):
        self._blocked_ips_cache = set()

    async def block_ip(self, ip_address: str, reason: str = None,
                       duration_hours: int = 24) -> bool:
        if not self._is_valid_ip(ip_address):
            return False

        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                select(BlockedIP).where(BlockedIP.ip_address == ip_address)
            )
            blocked = existing.scalar_one_or_none()

            if blocked:
                blocked.is_active = True
                blocked.reason = reason
                blocked.blocked_at = datetime.utcnow()
                if duration_hours > 0:
                    blocked.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
            else:
                blocked = BlockedIP(
                    ip_address=ip_address,
                    reason=reason,
                    blocked_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=duration_hours) if duration_hours > 0 else None,
                    is_active=True
                )
                db.add(blocked)

            await db.commit()
            self._blocked_ips_cache.add(ip_address)
            return True

    async def unblock_ip(self, ip_address: str) -> bool:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(BlockedIP).where(BlockedIP.ip_address == ip_address)
            )
            blocked = result.scalar_one_or_none()

            if blocked:
                blocked.is_active = False
                await db.commit()
                self._blocked_ips_cache.discard(ip_address)
                return True
            return False

    async def is_blocked(self, ip_address: str) -> bool:
        if ip_address in self._blocked_ips_cache:
            return True

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(BlockedIP).where(
                    BlockedIP.ip_address == ip_address,
                    BlockedIP.is_active == True
                )
            )
            blocked = result.scalar_one_or_none()

            if blocked:
                if blocked.expires_at and blocked.expires_at < datetime.utcnow():
                    blocked.is_active = False
                    await db.commit()
                    return False
                self._blocked_ips_cache.add(ip_address)
                return True
            return False

    async def get_blocked_ips(self) -> list:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(BlockedIP).where(BlockedIP.is_active == True).order_by(BlockedIP.blocked_at.desc())
            )
            return result.scalars().all()

    def _is_valid_ip(self, ip: str) -> bool:
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'

        if re.match(ipv4_pattern, ip):
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        return bool(re.match(ipv6_pattern, ip))


ip_blocker = IPBlocker()
