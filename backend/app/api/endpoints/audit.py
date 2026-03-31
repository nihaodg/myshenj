from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.core.database import get_db
from app.models.task import AuditTask, Issue
from app.schemas.task import AuditTaskCreate, AuditTaskResponse, AuditTaskDetailResponse, IssueResponse
from app.utils.file_utils import save_upload_file
from app.tasks.audit_tasks import run_audit_task

router = APIRouter()


@router.post("/upload", response_model=AuditTaskResponse)
async def create_audit_task(
    name: str = Form(...),
    type: str = Form(...),
    mode: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    task = AuditTask(
        name=name,
        type=type,
        mode=mode,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    if file:
        file_path = await save_upload_file(file, task.id)
        task.file_path = file_path
        await db.commit()

    try:
        run_audit_task.delay(task.id)
    except Exception:
        pass

    return task


@router.get("/tasks")
async def get_audit_tasks(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    audit_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditTask).order_by(AuditTask.created_at.desc())

    if status:
        query = query.where(AuditTask.status == status)
    if audit_type:
        query = query.where(AuditTask.type == audit_type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    count_query = select(func.count(AuditTask.id))
    if status:
        count_query = count_query.where(AuditTask.status == status)
    if audit_type:
        count_query = count_query.where(AuditTask.type == audit_type)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {"items": tasks, "total": total}


@router.get("/tasks/{task_id}")
async def get_audit_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditTask).where(AuditTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/{task_id}/detail")
async def get_audit_task_detail(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditTask).where(AuditTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    issues_result = await db.execute(
        select(Issue).where(Issue.task_id == task_id).order_by(Issue.id)
    )
    issues = issues_result.scalars().all()

    return {"task": task, "issues": issues}


@router.delete("/tasks/{task_id}")
async def delete_audit_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditTask).where(AuditTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}


@router.get("/statistics")
async def get_task_statistics(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(select(func.count(AuditTask.id)))
    total_tasks = total_result.scalar()

    completed_result = await db.execute(
        select(func.count(AuditTask.id)).where(AuditTask.status == "completed")
    )
    completed_tasks = completed_result.scalar()

    issues_result = await db.execute(select(func.count(Issue.id)))
    total_issues = issues_result.scalar()

    high_issues_result = await db.execute(
        select(func.count(Issue.id)).where(Issue.severity.in_(["high", "critical"]))
    )
    high_issues = high_issues_result.scalar()

    return {
        "total_tasks": total_tasks or 0,
        "completed_tasks": completed_tasks or 0,
        "total_issues": total_issues or 0,
        "high_issues": high_issues or 0
    }
