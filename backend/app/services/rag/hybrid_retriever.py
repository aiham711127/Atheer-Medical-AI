# backend/app/services/rag/hybrid_retriever.py
import re
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStore
from app.core.config import settings

def normalize_arabic_text(text: str) -> str:
    """
    توحيد النص العربي لتسهيل البحث الطبي.
    مُحسنة للأداء باستخدام str.translate بدلاً من تكرار re.sub.
    """
    if not text:
        return text

    # إزالة التشكيل (الحركات) والتطويل
    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)

    # توحيد الحروف (الألف، التاء المربوطة، الياء، والهمزات)
    normalization_map = str.maketrans({
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
        'ة': 'ه', 'ى': 'ي', 'ؤ': 'ء', 'ئ': 'ء',
    })
    
    text = text.translate(normalization_map)
    text = " ".join(text.split())
    return text

class HybridRetriever:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.store = VectorStore()
        # نتأكد من أن الجدول موجود في قاعدة البيانات
        self.store.ensure_collection()

    def retrieve(self, query: str, top_k: int = None):
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K

        # 1. تنظيف السؤال الذي كتبه المريض
        cleaned_query = normalize_arabic_text(query)
        
        # 2. تحويل السؤال إلى أرقام (عبر سيرفرات جوجل)
        embeddings = self.embedder.encode(cleaned_query)

        # 3. البحث عن أقرب المقالات في قاعدة البيانات
        results = self.store.search(dense_vector=embeddings["dense"], limit=top_k)

        # 4. تجميع وترتيب النتائج
        docs = []
        for point in results:
            score = point.score
            payload = point.payload or {}
            docs.append({
                "text": payload.get("text", ""),
                "pubmed_id": payload.get("pubmed_id"),
                "title": payload.get("title", "بدون عنوان"),
                "score": score
            })
        return docs