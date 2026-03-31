from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.task import AuditTask, Issue
from app.services.report_generator import generate_markdown_report, generate_pdf_report, save_report

router = APIRouter()


@router.get("/{task_id}")
async def get_report(
    task_id: int,
    format: str = Query("md", enum=["md", "pdf"]),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AuditTask).where(AuditTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    issues_result = await db.execute(
        select(Issue).where(Issue.task_id == task_id)
    )
    issues = issues_result.scalars().all()

    attack_chain = None
    attack_graph = None
    if task.result_summary:
        if isinstance(task.result_summary, dict):
            attack_chain = task.result_summary.get('attack_chain')
            attack_graph = task.result_summary.get('attack_graph')

    if format == "md":
        content = await generate_markdown_report(task, issues, task.result_summary, attack_chain, attack_graph)
        filepath = save_report(content, "md", task_id)

        return FileResponse(
            filepath,
            media_type="text/markdown",
            filename=f"report_{task_id}.md"
        )
    else:
        try:
            content = await generate_pdf_report(task, issues, task.result_summary, attack_chain)
            filepath = save_report(content if isinstance(content, str) else content.decode(), "pdf", task_id)

            if not filepath.endswith('.pdf'):
                filepath = save_report(content.decode(), "md", task_id)
                return FileResponse(
                    filepath,
                    media_type="text/markdown",
                    filename=f"report_{task_id}.md"
                )

            return FileResponse(
                filepath,
                media_type="application/pdf",
                filename=f"report_{task_id}.pdf"
            )
        except Exception as e:
            content = await generate_markdown_report(task, issues, task.result_summary, attack_chain, attack_graph)
            return content
