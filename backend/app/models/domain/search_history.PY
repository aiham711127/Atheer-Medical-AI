# backend/app/models/domain/search_history.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True)  # قائمة المراجع بتنسيق JSON
    confidence_score = Column(Float, nullable=True)
    user_feedback = Column(String(10), nullable=True)  # "up" أو "down"
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SearchHistory {self.id}>"