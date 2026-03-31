from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class IssueBase(BaseModel):
    file_name: Optional[str] = None
    line_number: Optional[int] = None
    rule_id: Optional[str] = None
    severity: str
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None


class IssueCreate(IssueBase):
    task_id: int


class IssueResponse(IssueBase):
    id: int
    task_id: int

    class Config:
        from_attributes = True


class AuditTaskBase(BaseModel):
    name: str
    type: str
    mode: str


class AuditTaskCreate(AuditTaskBase):
    pass


class AuditTaskUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    result_summary: Optional[dict] = None
    error_message: Optional[str] = None


class AuditTaskResponse(AuditTaskBase):
    id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_count: int = 0
    issue_count: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AuditTaskDetailResponse(AuditTaskResponse):
    issues: List[IssueResponse] = []

    class Config:
        from_attributes = True
