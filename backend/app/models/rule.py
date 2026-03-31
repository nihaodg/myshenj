from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from app.core.database import Base


class CustomRule(Base):
    __tablename__ = "custom_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    language = Column(String(50), nullable=True)
    pattern = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CustomRule(id={self.id}, rule_id='{self.rule_id}', name='{self.name}')>"
