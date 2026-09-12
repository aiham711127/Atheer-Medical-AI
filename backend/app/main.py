# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.v1.router import api_router
from app.core.database import engine, Base
import app.models.domain.user  # استيراد النماذج لإنشاء الجداول
from app.services.rag.vector_store import VectorStoreManager
from app.services.rag.embeddings import EmbeddingService
from app.core.mlops_tracker import mlops_tracker
import os
os.environ["HF_HUB_OFFLINE"] = "1"
logger = logging.getLogger("uvicorn")

# ==========================================
# دورة حياة الخادم (Lifespan Hook)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # عند التشغيل: التحقق من قاعدة البيانات وبدء تجربة MLOps
    logger.info("Starting Atheer Med Engine...")
    vector_store = VectorStoreManager()
    await vector_store.ensure_collection_exists()
    
    # ربط التسجيل بدورة حياة الخادم
    mlops_tracker.start_rag_experiment(experiment_name="Atheer_Production_Run")
    
    yield
    
    # عند الإغلاق: إنهاء التجربة بأمان
    mlops_tracker.end_experiment()
    logger.info("Shutting down Atheer Med Engine safely.")

    app = FastAPI(title="Atheer Med API", lifespan=lifespan)
    # 1. إنشاء جداول PostgreSQL إذا لم تكن موجودة (مثل جدول المستخدمين)
    logger.info("Checking PostgreSQL Database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. التحقق من سلامة أبعاد قاعدة Qdrant
    logger.info("Verifying Qdrant Vector Store Dimensions...")
    vector_store = VectorStoreManager()
    await vector_store.ensure_collection_exists()
    
    # 3. التحميل المسبق لنموذج MiniLM في الذاكرة لتسريع أول استجابة
    logger.info("Pre-loading local MiniLM embedding model...")
    EmbeddingService()
    
    logger.info("✅ Atheer Med Server is ready to accept requests.")
    yield
    # (هنا يمكن وضع أكواد تنظيف الذاكرة عند إغلاق السيرفر)

# ==========================================
# إعداد الخادم
# ==========================================
app = FastAPI(title="Atheer Med API", lifespan=lifespan) # إضافة الـ lifespan هنا

# إعدادات الأمان CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------
# أضف نقطة فحص الصحة هنا (في الجذر الرئيسي)
# ------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# دمج جميع المسارات
app.include_router(api_router, prefix="/api/v1")
