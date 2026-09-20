#المسار: backend/app/services/rag/ingestion_engine.py
import logging
import asyncio
import os
import fitz  # PyMuPDF
from uuid import UUID, uuid4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from app.core.database import AsyncSessionLocal
from app.models.domain.document import Document, DocumentStatus
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

def _extract_and_embed_sync(file_path: str, doc_id: UUID) -> list:
    """
    [المحرك المتزامن المعزول - CPU-Bound Worker]
    يقوم باستخراج النص، تقطيعه، وتحويله لأرقام عبر SentenceTransformer.
    """
    logger.info(f"[THREAD] Starting PDF extraction for {doc_id}")
    
    # 1. قراءة الـ PDF واستخراج النص
    full_text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                full_text += page.get_text()
    except Exception as e:
        raise ValueError(f"فشل في قراءة ملف PDF. قد يكون الملف تالفاً أو مشفراً. التفاصيل: {str(e)}")

    if not full_text.strip():
        raise ValueError("الملف فارغ أو يحتوي على صور ممسوحة ضوئياً فقط. يرجى رفع مرجع طبي نصي.")

    # 2. التقطيع الذكي (Chunking) مع الحفاظ على السياق الطبي
    # نستخدم Overlap لضمان عدم قطع الجمل الطبية في منتصفها
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_text(full_text)
    
    logger.info(f"[THREAD] Document split into {len(chunks)} chunks. Generating embeddings...")

    # 3. توليد المتجهات (Embeddings) بشكل جماعي (Batching) لحماية الـ RAM
    embedder = EmbeddingService()
    # نصل للنموذج مباشرة من الـ Singleton لإجراء عملية تشفير جماعية سريعة
    vectors = embedder._model.encode(chunks, batch_size=32, normalize_embeddings=True).tolist()

    # 4. تجهيز النقاط (Points) لقاعدة Qdrant
    points_data = []
    for chunk, vector in zip(chunks, vectors):
        points_data.append({
            "id": str(uuid4()),  # معرف فريد لكل مقطع
            "vector": vector,
            "payload": {
                "document_id": str(doc_id),
                "text": chunk
            }
        })
        
    return points_data


async def process_document_task(doc_id: UUID, file_path: str):
    """
    [المنسق غير المتزامن - Async Coordinator]
    """
    async with AsyncSessionLocal() as session:
        # 1. تحديث الحالة
        doc = await session.get(Document, doc_id)
        if not doc:
            return
        doc.status = DocumentStatus.PROCESSING
        await session.commit()

        try:
            # 2. إرسال المهمة الثقيلة للـ Thread المعزول (الاستخراج والتقطيع والتضمين)
            points_data = await asyncio.to_thread(_extract_and_embed_sync, file_path, doc_id)
            
            # 3. حفظ المتجهات في Qdrant (عبر دفعات Batches لحماية الشبكة والذاكرة)
            vector_store = VectorStoreManager()
            await vector_store.ensure_collection_exists()
            
            batch_size = 100
            for i in range(0, len(points_data), batch_size):
                batch = points_data[i:i + batch_size]
                
                # تحويل البيانات إلى هيكل Qdrant PointStruct
                qdrant_points = [
                    PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                    for p in batch
                ]
                
                # الإدراج في قاعدة البيانات المتجهية
                await vector_store.client.upsert(
                    collection_name=vector_store.collection_name,
                    points=qdrant_points
                )
                logger.info(f"Upserted batch {i//batch_size + 1} for document {doc_id}")

            # 4. التحديث النهائي للنجاح
            doc.status = DocumentStatus.COMPLETED
            doc.error_message = None
            logger.info(f"Successfully fully processed and ingested document {doc_id}")

        except Exception as e:
            # 5. تسجيل الانهيار إن حدث
            logger.error(f"Ingestion failed for document {doc_id}. Error: {str(e)}")
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            
        finally:
            await session.commit()
            # مسح الملف من مجلد الخادم لتوفير مساحة التخزين (Cleanup)
            if os.path.exists(file_path):
                os.remove(file_path)