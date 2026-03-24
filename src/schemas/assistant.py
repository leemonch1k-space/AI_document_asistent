from pydantic import BaseModel
from uuid import UUID


class AskRequestSchema(BaseModel):
    question: str
    document_ids: list[UUID]


class SourceSchema(BaseModel):
    document: str
    chunk_id: str | None = None


class AskResponseSchema(BaseModel):
    answer: str
    sources: list[SourceSchema]


class AskSummaryRequestSchema(BaseModel):
    document_id: UUID


class AskSummaryResponseSchema(AskSummaryRequestSchema):
    summary: str
