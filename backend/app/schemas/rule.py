from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RuleBase(BaseModel):
    rule_id: str
    name: str
    severity: str = "medium"
    language: Optional[str] = None
    pattern: str
    message: str
    enabled: bool = True


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    severity: Optional[str] = None
    language: Optional[str] = None
    pattern: Optional[str] = None
    message: Optional[str] = None
    enabled: Optional[bool] = None


class RuleResponse(RuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
