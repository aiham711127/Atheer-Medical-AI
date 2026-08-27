# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

app = FastAPI(title="Atheer Med API")

# إعدادات الأمان للسماح لتطبيق Flutter بالاتصال بالسيرفر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# دمج جميع المسارات لتبدأ بـ /api/v1
app.include_router(api_router, prefix="/api/v1")