from __future__ import annotations

from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    status: str


class SourceSnippet(BaseModel):
    chunk_index: int
    snippet: str | None = None
    score: float | None = None
    filename: str | None = None


class AskResponse(BaseModel):
    answer: str
    question: str
    document_id: str
    sources: list[SourceSnippet]
