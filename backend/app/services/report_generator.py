import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Template
from app.core.config import settings
from app.models.task import AuditTask, Issue


_report_template_md = """# 安全审计报告

## 审计概览

- **任务ID**: {{ task_id }}
- **任务名称**: {{ task_name }}
- **审计类型**: {{ audit_type }}
- **分析模式**: {{ audit_mode }}
- **审计时间**: {{ start_time }}
- **完成时间**: {{ end_time }}
{% if file_count %}
- **文件数**: {{ file_count }}
{% endif %}
- **发现问题数**: {{ issue_count }}

## 风险分布

| 等级 | 数量 |
|------|------|
{% for severity, count in severity_summary.items() %}
| {{ severity | upper }} | {{ count }} |
{% endfor %}

{% if result_summary and result_summary.total_packets is defined %}
## 流量分析概览

- **总数据包**: {{ result_summary.total_packets }}
- **唯一IP数**: {{ result_summary.unique_ips | length }}
- **会话数**: {{ result_summary.session_count }}
{% endif %}

{% if result_summary and result_summary.total_lines is defined %}
## 日志分析概览

- **日志行数**: {{ result_summary.total_lines }}
{% endif %}

## 问题详情

{% for issue in issues %}
### {{ loop.index }}. [{{ issue.severity | upper }}] {{ issue.title }}

{% if issue.file_name %}
- **文件**: {{ issue.file_name }}
{% endif %}
{% if issue.line_number %}
- **行号**: {{ issue.line_number }}
{% endif %}
{% if issue.rule_id %}
- **规则ID**: {{ issue.rule_id }}
{% endif %}
- **描述**: {{ issue.description or issue.message or 'N/A' }}
{% if issue.recommendation %}
- **修复建议**: {{ issue.recommendation }}
{% endif %}

---
{% endfor %}

{% if attack_chain and attack_chain | length > 0 %}
## 攻击链条

{% for step in attack_chain %}
### 步骤 {{ loop.index }}

- **时间**: {{ step.timestamp or 'N/A' }}
- **IP**: {{ step.ip or 'N/A' }}
- **动作**: {{ step.action or 'N/A' }}
- **描述**: {{ step.description or 'N/A' }}
- **严重程度**: {{ step.severity or 'N/A' }}

{% endfor %}
{% endif %}

{% if attack_graph and attack_graph.nodes %}
## 攻击路径图

节点: {{ attack_graph.nodes | length }}
边: {{ attack_graph.edges | length }}

{% endif %}

---
*报告生成时间: {{ report_time }}*
*DeepAudit Lite 安全审计系统*
"""


async def generate_markdown_report(
    task: AuditTask,
    issues: list,
    result_summary: Optional[Dict[str, Any]] = None,
    attack_chain: Optional[list] = None,
    attack_graph: Optional[Dict] = None
) -> str:
    template = Template(_report_template_md)

    severity_summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for issue in issues:
        sev = issue.severity.lower() if hasattr(issue, 'severity') else issue.get('severity', 'medium')
        if sev in severity_summary:
            severity_summary[sev] += 1

    report_content = template.render(
        task_id=task.id,
        task_name=task.name,
        audit_type=task.type.upper(),
        audit_mode=task.mode.upper(),
        start_time=task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else 'N/A',
        end_time=task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else 'N/A',
        file_count=task.file_count or 0,
        issue_count=len(issues),
        severity_summary=severity_summary,
        issues=issues,
        result_summary=result_summary,
        attack_chain=attack_chain,
        attack_graph=attack_graph,
        report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    return report_content


async def generate_pdf_report(
    task: AuditTask,
    issues: list,
    result_summary: Optional[Dict[str, Any]] = None,
    attack_chain: Optional[list] = None
) -> bytes:
    markdown_content = await generate_markdown_report(
        task, issues, result_summary, attack_chain
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; margin: 40px; }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 30px; }}
            h3 {{ color: #666; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f8f9fa; }}
            .critical {{ color: #dc3545; font-weight: bold; }}
            .high {{ color: #fd7e14; font-weight: bold; }}
            .medium {{ color: #ffc107; font-weight: bold; }}
            .low {{ color: #28a745; }}
            code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            .issue {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }}
            .attack-chain {{ background-color: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <pre>{markdown_content}</pre>
    </body>
    </html>
    """

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        return markdown_content.encode('utf-8')


def save_report(content: str, format: str, task_id: int) -> str:
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    filename = f"report_{task_id}.{format}"
    filepath = os.path.join(settings.REPORT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath
