import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from config.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), index=True)
    role = Column(String(50)) # 'user' hoặc 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)