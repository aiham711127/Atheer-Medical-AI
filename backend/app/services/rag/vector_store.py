# backend/app/services/rag/vector_store.py
import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        # 1. تنظيف اسم المضيف من أي مسافات مخفية قد تدمر الشروط
        host = settings.QDRANT_HOST.strip()

        # 2. تحديد البروتوكول بذكاء ومرونة أعلى
        if host.startswith("http://") or host.startswith("https://"):
            qdrant_url = host
        elif host in ["qdrant", "localhost", "127.0.0.1", "host.docker.internal", "atheer_qdrant"]:
            qdrant_url = f"http://{host}" # محلي
        else:
            qdrant_url = f"https://{host}" # سحابي
            
        # 3. إضافة المنفذ إذا لم يكن موجوداً
        if f":{settings.QDRANT_PORT}" not in qdrant_url:
            qdrant_url = f"{qdrant_url}:{settings.QDRANT_PORT}"
            
        # 4. استنتاج حالة التشفير برمجياً وبشكل قاطع (هذا هو الحل الجذري)
        is_secure = qdrant_url.startswith("https://")
            
        # إعداد مفتاح API
        api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        
        # 5. بناء الاتصال وتمرير حالة التشفير كأمر صارم للمكتبة
        self.client = AsyncQdrantClient(
            url=qdrant_url,
            api_key=api_key,
            https=is_secure,  # 🔴 الآن أصبح النظام ديناميكياً 100% بناءً على البيئة
            timeout=60.0
        )
        self.collection_name = settings.COLLECTION_NAME
        self.vector_dim = settings.VECTOR_DIM
        
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
                
                # التحقق من الأبعاد الفعلية في السحابة/المحلي
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