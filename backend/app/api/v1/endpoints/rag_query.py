# backend/app/api/v1/endpoints/rag_query.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
# استدعاء محرك الذكاء الاصطناعي
from app.services.rag.llm_engine import generate_rag_response_stream
from fastapi.responses import StreamingResponse

router = APIRouter()

# 1. تصميم هيكل رسالة الذاكرة
class Message(BaseModel):
    role: str
    content: str

# 2. تحديث هيكل الطلب ليقبل الذاكرة (history)
class ChatRequest(BaseModel):
    query: str
    role: str = "student"
    history: Optional[List[Message]] = []  # قائمة اختيارية للرسائل السابقة

@router.post("/chat")
async def chat_with_atheer(request: ChatRequest):
    try:
        # تحويل الذاكرة من Pydantic إلى قائمة قواميس (Dictionaries) ليفهمها المحرك
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        # إرسال السؤال والدور والذاكرة إلى المحرك
        return StreamingResponse(
            generate_rag_response_stream(
                user_message=request.query, 
                user_role=request.role,
                history=history_dicts
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))