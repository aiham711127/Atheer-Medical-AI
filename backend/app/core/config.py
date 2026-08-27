# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# تحديد المسار الجذر للمشروع (أعلى مجلد backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Server
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Atheer Med"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # PostgreSQL (قاعدة البيانات التي أصلحناها سابقاً)
    async_database_url: str = "postgresql+asyncpg://neondb_owner:npg_LSzQY86XGurh@ep-ancient-hill-aywswge8-pooler.c-5.us-east-2.aws.neon.tech/neondb"
    # (ملاحظة: تأكد أن تضع رابط Neon الحقيقي الخاص بك في السطر الأعلى بدلاً من الـ XXXXXX)


    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Qdrant (قاعدة بيانات المتجهات)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "medical_articles"

    # --- إعدادات جوجل الجديدة (الخفيفة والسريعة) ---
# --- إعدادات جوجل الجديدة (الخفيفة والسريعة) ---
    GOOGLE_API_KEY: Optional[str] = None
    EMBEDDING_PROVIDER: str = "google"
    EMBEDDING_MODEL_NAME: str = "embedding-001"
    #RETRIEVAL_MIN_SCORE: float = 0.6
    RETRIEVAL_MIN_SCORE: float = 0.1 # للاختبار فقط
    RETRIEVAL_TOP_K: int = 3
    VECTOR_DIM: int = 3072  # <-- تم التعديل هنا ليتطابق مع مقاس جوجل
    
    LLM_PROVIDER: str = "google"
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()