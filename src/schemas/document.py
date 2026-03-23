from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.enums import DocumentStatusEnum


class DocumentResponseSchema(BaseModel):
    """Schema for document response."""
    document_id: UUID
    status: DocumentStatusEnum


class DocumentItemSchema(BaseModel):
    """Schema for document item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: DocumentStatusEnum
    chunk_count: int
    created_at: datetime


class DocumentListResponseSchema(BaseModel):
    """Schema for document list response."""
    documents: list[DocumentItemSchema]