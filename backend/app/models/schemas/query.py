# backend/app/models/schemas/query.py
from pydantic import BaseModel, Field
from typing import Optional

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    language: str = Field(default="ar", pattern="^(ar|en)$")
    specialty: Optional[str] = None