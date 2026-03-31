from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.config import settings
from app.core.security import encrypt_value, decrypt_value
from app.models.settings import SystemSettings

router = APIRouter()


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()

    settings_dict = {}
    for s in settings_list:
        if s.is_encrypted:
            try:
                settings_dict[s.key] = decrypt_value(s.value)
            except:
                settings_dict[s.key] = s.value
        else:
            settings_dict[s.key] = s.value

    if 'AI_API_KEY' not in settings_dict or not settings_dict['AI_API_KEY']:
        settings_dict['AI_API_KEY'] = settings.AI_API_KEY or ""
    if 'AI_PROVIDER' not in settings_dict:
        settings_dict['AI_PROVIDER'] = settings.AI_PROVIDER
    if 'AI_MODEL' not in settings_dict:
        settings_dict['AI_MODEL'] = settings.AI_MODEL
    if 'AI_BASE_URL' not in settings_dict:
        settings_dict['AI_BASE_URL'] = settings.AI_BASE_URL

    return settings_dict


@router.put("")
async def update_settings(
    settings_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    for key, value in settings_data.items():
        result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
        existing = result.scalar_one_or_none()

        is_encrypted = key in ['AI_API_KEY', 'SECRET_KEY']

        if existing:
            if is_encrypted and value:
                value = encrypt_value(value)
            existing.value = value
            existing.is_encrypted = is_encrypted
        else:
            if is_encrypted and value:
                value = encrypt_value(value)
            new_setting = SystemSettings(key=key, value=value, is_encrypted=is_encrypted)
            db.add(new_setting)

    await db.commit()
    return {"message": "Settings updated"}


@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
    setting = result.scalar_one_or_none()

    if not setting:
        return None

    if setting.is_encrypted:
        try:
            return decrypt_value(setting.value)
        except:
            return setting.value
    return setting.value
