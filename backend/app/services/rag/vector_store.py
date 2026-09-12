# backend/app/services/rag/vector_store.py
import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        # بناء الرابط السحابي الصحيح لـ Qdrant
        qdrant_url = settings.QDRANT_HOST if settings.QDRANT_HOST.startswith("http") else f"https://{settings.QDRANT_HOST}"
        if f":{settings.QDRANT_PORT}" not in qdrant_url:
            qdrant_url = f"{qdrant_url}:{settings.QDRANT_PORT}"
        
        self.client = AsyncQdrantClient(
            url=qdrant_url,
            api_key=settings.QDRANT_API_KEY,
            timeout=60.0
        )
        self.collection_name = settings.COLLECTION_NAME
        self.vector_dim = settings.VECTOR_DIM  # سيسحب القيمة 384 من ملف الإعدادات

    async def ensure_collection_exists(self):
        """
        يتحقق من وجود المجموعة، ويقوم بإنشائها إذا لم تكن موجودة.
        الأهم: يتحقق من توافق الأبعاد (Dimension Mismatch Guardrail).
        """
        try:
            exists = await self.client.collection_exists(self.collection_name)
            
            if not exists:
                logger.info(f"Creating new collection '{self.collection_name}' with dimension {self.vector_dim}")
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
                )
            else:
                # نظام الحماية (Guardrail): استرداد إعدادات المجموعة الحالية
                collection_info = await self.client.get_collection(self.collection_name)
                
                # التحقق من الأبعاد الفعلية في السحابة
                actual_dim = collection_info.config.params.vectors.size
                
                if actual_dim != self.vector_dim:
                    error_msg = (
                        f"CRITICAL: Vector Dimension Mismatch! "
                        f"Database has {actual_dim} dimensions, but the code expects {self.vector_dim}. "
                        f"Please delete the existing collection in Qdrant and re-ingest the data."
                    )
                    logger.error(error_msg)
                    # إيقاف التنفيذ فوراً لتجنب الأخطاء أثناء استعلامات المرضى
                    raise ValueError(error_msg)
                
                logger.info(f"Collection '{self.collection_name}' verified successfully with {actual_dim} dimensions.")
                
        except Exception as e:
            logger.error(f"Error checking/creating collection: {e}")
            raise