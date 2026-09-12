# backend/app/services/rag/embeddings.py
import asyncio
import logging
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        # Singleton Pattern: نضمن تحميل النموذج مرة واحدة فقط في الذاكرة
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # تهيئة النموذج فقط إذا لم يكن قد تم تحميله مسبقاً
        if self._model is None:
            logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL_NAME}...")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("Local Embedding Model loaded successfully.")

    async def encode(self, text: str) -> dict:
        """
        توليد التضمين بشكل غير متزامن لتجنب تجميد خادم FastAPI
        """
        if not text or not text.strip():
            raise ValueError("النص فارغ، لا يمكن توليد التضمين.")

        # الحصول على الـ Event Loop الحالي الخاص بـ FastAPI
        loop = asyncio.get_running_loop()
        
        # تغليف عملية الـ CPU الثقيلة للعمل في الخلفية (Background Thread)
        def _encode_sync():
            # normalize_embeddings=True يُحسن دقة حساب مسافة جيب التمام (Cosine Similarity)
            vector = self._model.encode(text, normalize_embeddings=True).tolist()
            return vector
        
        # تنفيذ التضمين دون حجب الخادم
        vector_result = await loop.run_in_executor(None, _encode_sync)
        
        # الإرجاع بنفس الهيكلية التي يتوقعها محرك الـ RAG
        return {"dense": vector_result}