# backend/app/core/config.py

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# إجبار النظام على قراءة ملف .env قبل أي شيء آخر
load_dotenv()
   
class Settings(BaseSettings):
    PROJECT_NAME: str = "Atheer Med API"
    DEBUG: bool = True
    
    # ----------------------------------------------------
    # Security & Database
    # ----------------------------------------------------
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_secret_key_for_dev")
    ALGORITHM: str = "HS256"  # <--- هذا السطر كان مفقوداً
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # <--- وهذا السطر كان مفقوداً
    async_database_url: str = os.getenv("DATABASE_URL", "")

    GOOGLE_API_KEY: str  = os.getenv("GOOGLE_API_KEY", "") # مفتاح قوقل 


    # ----------------------------------------------------
    # Vector Database (Qdrant Cloud)
    # ----------------------------------------------------
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: str = os.getenv("QDRANT_PORT", "6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "medical_knowledge_base")
    
    # ----------------------------------------------------
    # Unified Embedding Strategy (Pure Local)
    # ----------------------------------------------------
    # تم توحيد النموذج والأبعاد هنا لتكون المرجع الوحيد لجميع الملفات
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    VECTOR_DIM: int = 384  # بُعد قاطع لا يتغير لحماية قاعدة البيانات
    
    # ----------------------------------------------------
    # LLM & Retrieval Config
# ----------------------------------------------------
    # Third-Party APIs
    # ----------------------------------------------------
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # تم سحب القيمة الثابتة هنا مع تعيين النموذج الجديد كافتراضي
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "")
    RETRIEVAL_MIN_SCORE: float = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.15"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()