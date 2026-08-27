# backend/app/models/schemas/article.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ArticleCreate(BaseModel):
    pubmed_id: str
    title: str
    abstract: Optional[str] = None
    source_url: Optional[str] = None
    publication_date: Optional[datetime] = None

class ArticleResponse(ArticleCreate):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True