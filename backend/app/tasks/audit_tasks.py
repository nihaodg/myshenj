from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "deepaudit",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1
)


@celery_app.task(bind=True)
def run_audit_task(self, task_id: int):
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.models.task import AuditTask, Issue
    from app.services.audit_services import CodeAuditService, LogAuditService, TrafficAuditService
    from app.utils.file_utils import extract_zip, get_all_files
    from datetime import datetime
    import zipfile

    async def _run():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(select(AuditTask).where(AuditTask.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                return {"error": "Task not found"}

            task.status = "running"
            await db.commit()

            try:
                use_ai = task.mode == "ai"

                if task.file_path and zipfile.is_zipfile(task.file_path):
                    extract_dir, files = extract_zip(task.file_path, task_id)
                else:
                    extract_dir = None
                    files = []

                if task.type == "code":
                    service = CodeAuditService()
                    if extract_dir:
                        result_data = await service.audit_directory(extract_dir, use_ai)
                    elif task.file_path:
                        result_data = await service.audit_file(task.file_path, use_ai)
                        result_data['total_files'] = 1
                        result_data['issues'] = result_data.get('issues', [])
                    else:
                        result_data = {"total_files": 0, "total_issues": 0, "issues": [], "severity_summary": {}}

                elif task.type == "log":
                    service = LogAuditService()
                    if task.file_path:
                        result_data = await service.audit_log_file(task.file_path, use_ai)
                    else:
                        result_data = {"total_lines": 0, "issues": [], "attack_chain": [], "severity_summary": {}}

                elif task.type == "traffic":
                    service = TrafficAuditService()
                    if task.file_path:
                        result_data = await service.audit_pcap(task.file_path, use_ai)
                    else:
                        result_data = {"total_packets": 0, "issues": [], "attack_graph": {}, "severity_summary": {}}
                else:
                    result_data = {"error": "Unknown audit type"}

                issues_data = result_data.get('issues', [])
                task.file_count = result_data.get('total_files', result_data.get('total_packets', result_data.get('total_lines', 0)))
                task.issue_count = len(issues_data)
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.result_summary = {
                    "severity_summary": result_data.get('severity_summary', {}),
                    "ai_used": use_ai
                }

                for issue_data in issues_data:
                    issue = Issue(
                        task_id=task_id,
                        file_name=issue_data.get('file_name'),
                        line_number=issue_data.get('line_number'),
                        rule_id=issue_data.get('rule_id'),
                        severity=issue_data.get('severity', 'medium'),
                        title=issue_data.get('rule_name', issue_data.get('title', 'Unknown Issue')),
                        description=issue_data.get('message', issue_data.get('description', '')),
                        recommendation=issue_data.get('recommendation', '')
                    )
                    db.add(issue)

                await db.commit()
                return result_data

            except Exception as e:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                await db.commit()
                return {"error": str(e)}

    return asyncio.run(_run())
