# backend/app/services/rag/vector_store.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings, BASE_DIR
import os

class VectorStore:
    def __init__(self):
        db_path = os.path.join(BASE_DIR, "qdrant_local_data")
        self.client = QdrantClient(path=str(db_path))
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    def ensure_collection(self):
        """تأكد من وجود الجدول، وإنشاؤه فقط إذا لم يكن موجوداً (لحماية البيانات من الحذف)"""
        ACTUAL_DIMENSION = 3072
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        # إذا لم يكن الجدول موجوداً، قم بإنشائه. (لن نقوم بحذفه أبداً بعد اليوم)
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=ACTUAL_DIMENSION,
                    distance=Distance.COSINE
                )
            )

    def upsert(self, doc_id: str, dense_vector: list, payload: dict):
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=doc_id, vector=dense_vector, payload=payload)]
        )

    def search(self, dense_vector: list, limit: int = 10):
        """البحث الذكي: يدعم إصدارات مكتبة Qdrant القديمة والحديثة"""
        if hasattr(self.client, "search"):
            # للإصدارات القديمة
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=dense_vector,
                limit=limit,
                with_payload=True
            )
        else:
            # للإصدارات الحديثة جداً التي استبدلت search بـ query_points
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=dense_vector,
                limit=limit,
                with_payload=True
            )
            return response.points