from sqlalchemy import Column, Integer, String, Text, Boolean
from app.core.database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    is_encrypted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<SystemSettings(key='{self.key}')>"
