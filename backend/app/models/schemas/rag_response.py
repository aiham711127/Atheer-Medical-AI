# backend/app/models/schemas/rag_response.py
from pydantic import BaseModel
from typing import List, Optional

class Citation(BaseModel):
    pubmed_id: str
    title: str
    url: Optional[str] = None
    relevance_score: float

class RAGQueryResponse(BaseModel):
    answer: Optional[str] = None
    citations: List[Citation] = []
    confidence: Optional[float] = None
    processing_time_ms: float
    fallback: bool = False
    message: Optional[str] = None