from pydantic import BaseModel
from typing import Optional


class SettingsBase(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False


class SettingsUpdate(BaseModel):
    value: str
    is_encrypted: bool = False


class SettingsResponse(SettingsBase):
    class Config:
        from_attributes = True
