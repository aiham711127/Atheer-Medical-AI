import os
import uuid
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ==========================================
# 1. Environment Config
# ==========================================
load_dotenv()

raw_host = os.getenv("QDRANT_HOST", "").strip()
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()

COLLECTION_NAME = "medical_knowledge_base"
VECTOR_DIM = 384  

if not raw_host.startswith("http"):
    raw_host = f"https://{raw_host}"

if f":{QDRANT_PORT}" not in raw_host:
    qdrant_url = f"{raw_host}:{QDRANT_PORT}"
else:
    qdrant_url = raw_host

# ==========================================
# 2. Resilient Database Connection
# ==========================================
print(f"🔌 Connecting to Cloud: {qdrant_url}")
# Increased timeout to 300 seconds (5 minutes) for unstable networks
qdrant_client = QdrantClient(url=qdrant_url, api_key=QDRANT_API_KEY, timeout=300.0)

print("🧠 Loading Lightweight Local Model...")
embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# 3. Recreate Database with Retry Logic
# ==========================================
print("🗑️ Resetting Database...")
max_retries = 3
for attempt in range(max_retries):
    try:
        if qdrant_client.collection_exists(collection_name=COLLECTION_NAME):
            qdrant_client.delete_collection(collection_name=COLLECTION_NAME)

        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        break # Success, exit retry loop
    except Exception as e:
        print(f"⚠️ Network error during DB setup: {e}. Retrying {attempt+1}/{max_retries} in 5 seconds...")
        time.sleep(5)
        if attempt == max_retries - 1:
            raise e # Fail if all retries exhausted

# ==========================================
# 4. Fetch Dataset
# ==========================================
print("🚀 Downloading Cardiology Dataset from HuggingFace...")
dataset = load_dataset("medalpaca/medical_meadow_medical_flashcards", split="train")

keywords = ["heart", "cardiac", "cardiology", "myocardial", "arrhythmia", "blood pressure"]
filtered_data = []

print("🔍 Filtering Data...")
for row in dataset:
    text_content = (row['input'] + " " + row['output']).lower()
    if any(k in text_content for k in keywords):
        filtered_data.append(row)
        if len(filtered_data) >= 500:
            break

print(f"✅ Found {len(filtered_data)} cases.")

# ==========================================
# 5. Fault-Tolerant Ingestion (Embedding & Upsert)
# ==========================================
print("⚙️ Embedding and Uploading...")
# Extremely small batch size to prevent timeouts on slow connections
batch_size = 5 
points_to_upsert = []

def safe_upsert(points):
    """Upsert with a built-in retry mechanism"""
    for attempt in range(max_retries):
        try:
            qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
            return
        except Exception as e:
            print(f"\n⚠️ Upload timeout/error. Retrying in 5s... ({attempt+1}/{max_retries})")
            time.sleep(5)
            if attempt == max_retries - 1:
                raise e

for i, row in enumerate(tqdm(filtered_data, desc="Processing Data")):
    combined_text = f"سؤال سريري: {row['input']}\nإجابة طبية: {row['output']}"
    
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

print("\n🎉 Success! Data uploaded safely despite network instability.")