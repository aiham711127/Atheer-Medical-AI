# backend/app/api/v1/router.py
# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import rag_query, upload  # إضافة مسار الرفع الجديد هنا

api_router = APIRouter()

# ربط ملف الدردشة بالمسار الرئيسي
api_router.include_router(rag_query.router, tags=["chat"])

# ربط ملف الرفع بالمسار الرئيسي
api_router.include_router(upload.router, tags=["upload"])