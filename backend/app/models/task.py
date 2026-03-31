from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AuditTask(Base):
    __tablename__ = "audit_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    mode = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    file_path = Column(String(512), nullable=True)
    file_count = Column(Integer, default=0)
    issue_count = Column(Integer, default=0)
    result_summary = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    issues = relationship("Issue", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AuditTask(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("audit_tasks.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(512), nullable=True)
    line_number = Column(Integer, nullable=True)
    rule_id = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    task = relationship("AuditTask", back_populates="issues")

    def __repr__(self):
        return f"<Issue(id={self.id}, title='{self.title}', severity='{self.severity}')>"
