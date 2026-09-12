# scripts/ingest_cardiology.py
import os
import sys
import uuid
import time
from tqdm import tqdm
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# ==========================================
# 1. Architectural Alignment (توحيد المعمارية)
# ==========================================
# إجبار السكربت على قراءة إعدادات الخادم المركزية لمنع الانفصال
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

# بناء الرابط بنفس الطريقة التي يستخدمها الخادم تماماً
qdrant_url = settings.QDRANT_HOST if settings.QDRANT_HOST.startswith("http") else f"https://{settings.QDRANT_HOST}"
if f":{settings.QDRANT_PORT}" not in qdrant_url:
    qdrant_url = f"{qdrant_url}:{settings.QDRANT_PORT}"

print(f"🔌 Connecting to Cloud: {qdrant_url}")
print(f"📁 Target Collection: {settings.COLLECTION_NAME}")

# ==========================================
# 2. Resilient Database Connection
# ==========================================
qdrant_client = QdrantClient(url=qdrant_url, api_key=settings.QDRANT_API_KEY, timeout=300.0)

print("🧠 Loading Project Embedding Model...")
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

# ==========================================
# 3. Recreate Database
# ==========================================
print(f"🗑️ Resetting Database '{settings.COLLECTION_NAME}'...")
if qdrant_client.collection_exists(collection_name=settings.COLLECTION_NAME):
    qdrant_client.delete_collection(collection_name=settings.COLLECTION_NAME)

qdrant_client.create_collection(
    collection_name=settings.COLLECTION_NAME,
    vectors_config=VectorParams(size=settings.VECTOR_DIM, distance=Distance.COSINE),
)

# ==========================================
# 4. Fetch Dataset
# ==========================================
print("🚀 Downloading Cardiology Dataset from HuggingFace...")
dataset = load_dataset("medalpaca/medical_meadow_medical_flashcards", split="train")

keywords = ["heart", "cardiac", "cardiology", "myocardial", "arrhythmia", "blood pressure"]
filtered_data = []

print("🔍 Filtering Data...")
for row in dataset:
    # استخدام .get لتجنب أخطاء المفاتيح المفقودة
    text_content = str(row.get('input', '') + " " + row.get('output', '')).lower()
    if any(k in text_content for k in keywords):
        filtered_data.append(row)
        if len(filtered_data) >= 500:
            break

print(f"✅ Found {len(filtered_data)} cases.")

# ==========================================
# 5. Fault-Tolerant Ingestion
# ==========================================
print("⚙️ Embedding and Uploading...")
batch_size = 10 
points_to_upsert = []

def safe_upsert(points):
    for attempt in range(3):
        try:
            # إجبار السحابة على تأكيد الحفظ قبل الانتقال للدفعة التالية (wait=True)
            qdrant_client.upsert(collection_name=settings.COLLECTION_NAME, points=points, wait=True)
            return
        except Exception as e:
            print(f"\n⚠️ Upload error. Retrying in 5s... ({attempt+1}/3)")
            time.sleep(5)
            if attempt == 2:
                raise e

for i, row in enumerate(tqdm(filtered_data, desc="Processing Data")):
    combined_text = f"سؤال سريري: {row.get('input', '')}\nإجابة طبية: {row.get('output', '')}"
    vector = embedding_model.encode(combined_text, normalize_embeddings=True).tolist()
    
    payload = {
        "text": combined_text,
        "source": "HuggingFace: Medical Meadow (Cardiology)",
        "chunk_id": i
    }
    
    point_id = str(uuid.uuid4())
    points_to_upsert.append(PointStruct(id=point_id, vector=vector, payload=payload))
    
    if len(points_to_upsert) >= batch_size:
        safe_upsert(points_to_upsert)
        points_to_upsert = []

if points_to_upsert:
    safe_upsert(points_to_upsert)

# ==========================================
# 6. Final Validation (فحص العدد الحقيقي في السحابة)
# ==========================================
count = qdrant_client.count(collection_name=settings.COLLECTION_NAME)
print("\n======================================")
print(f"🎉 Success! Final Count in DB: {count.count} cases.")
print("======================================\n")