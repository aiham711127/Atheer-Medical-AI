# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import rag_query, auth, upload # أضفنا auth هنا

api_router = APIRouter()

# تسجيل مسارات المصادقة (التسجيل والدخول)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# تسجيل مسار الدردشة
api_router.include_router(rag_query.router, tags=["Chat"])

# تسجيل مسار الرفع (إذا كان موجوداً لديك)
api_router.include_router(upload.router, tags=["Upload"])