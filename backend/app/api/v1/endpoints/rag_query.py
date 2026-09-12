# backend/app/api/v1/endpoints/rag_query.py
from typing import List, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.rag.llm_engine import generate_rag_response_stream
from app.api.deps import get_current_user
from app.models.domain.user import User

router = APIRouter()

# 1. التقييد الصارم للأدوار (Role Validation via Literal)
class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[ChatMessage]] = []

@router.post("/chat")
async def chat_with_atheer(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    مسار الدردشة الطبي المعزز بذاكرة سياقية وحماية من البيانات المشوهة.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="لا يمكن أن يكون السؤال فارغاً.")

    # 2. جسر التحويل (Role Mapping): تحويل assistant إلى model ليتوافق مع Gemini Native API
    formatted_history = [
        {
            "role": "model" if msg.role == "assistant" else "user",
            "parts": [msg.content]
        }
        for msg in request.history
    ] if request.history else []

    return StreamingResponse(
        generate_rag_response_stream(
            user_message=request.query, 
            chat_history=formatted_history,
            user_role=current_user.role.value
        ),
        media_type="text/event-stream"
    )
