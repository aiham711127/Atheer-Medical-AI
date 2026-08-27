import os
import uuid
import fitz  # مكتبة PyMuPDF
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

# ==========================================
# 1. إعدادات البيئة والمحركات
# ==========================================
load_dotenv()
raw_host = os.getenv("QDRANT_HOST", "").strip()
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
COLLECTION_NAME = "medical_knowledge_base"

if not raw_host.startswith("http"):
    raw_host = f"https://{raw_host}"
qdrant_url = f"{raw_host}:{QDRANT_PORT}" if f":{QDRANT_PORT}" not in raw_host else raw_host

# تهيئة الاتصال السحابي ونموذج التضمين
qdrant_client = AsyncQdrantClient(url=qdrant_url, api_key=QDRANT_API_KEY, timeout=60.0)
embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# 2. هندسة تقطيع النصوص (Text Chunking)
# ==========================================
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """تقسيم النص الطويل إلى أجزاء صغيرة مع تداخل للحفاظ على السياق الطبي"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# ==========================================
# 3. المعالجة والرفع (Process & Upsert)
# ==========================================
async def process_and_upload_pdf(file_bytes: bytes, filename: str) -> str:
    try:
        # قراءة محتوى الـ PDF من الذاكرة مباشرة
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
            
        if not full_text.strip():
            return "الملف فارغ أو يحتوي على صور فقط (لا يمكن قراءة النصوص)."

        # تقطيع النص
        chunks = chunk_text(full_text)
        points_to_upsert = []

        # تحويل النصوص إلى متجهات ورفعها
        for i, chunk in enumerate(chunks):
            vector = embedding_model.encode(chunk, normalize_embeddings=True).tolist()
            payload = {
                "text": chunk,
                "source": filename,
                "chunk_id": i
            }
            point_id = str(uuid.uuid4())
            points_to_upsert.append(PointStruct(id=point_id, vector=vector, payload=payload))

        # رفع المتجهات إلى قاعدة البيانات
        if points_to_upsert:
            await qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points_to_upsert)

        return f"تم تحليل {len(chunks)} مقطع طبي من ملف '{filename}' ودمجها في ذاكرة أثير بنجاح."

    except Exception as e:
        return f"حدث خطأ أثناء معالجة الملف: {str(e)}"