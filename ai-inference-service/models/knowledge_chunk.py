import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from config.database import Base

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    chunk_id: Mapped[str] = mapped_column(String(255), nullable=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=True)
    section_type: Mapped[str] = mapped_column(String(50), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_name: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(768))