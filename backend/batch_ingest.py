import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import uuid

# ==========================================
# 0. تحميل المفاتيح بأمان
# ==========================================
load_dotenv()

# التأكد من إضافة https:// للرابط إذا نسيها المستخدم
raw_url = os.getenv("QDRANT_HOST", "").strip()
QDRANT_URL = raw_url if raw_url.startswith("http") else f"https://{raw_url}"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    print("❌ خطأ: لم يتم العثور على المفاتيح في ملف .env")
    exit()

# ==========================================
# 1. إعدادات النظام
# ==========================================
PDF_DIRECTORY = "medical_papers"
COLLECTION_NAME = "medical_knowledge_base"

print("🚀 بدء تشغيل محرك التغذية السحابية...")

# ==========================================
# 2. إعداد الاتصال السحابي (مع زيادة وقت الانتظار)
# ==========================================
print(f"🔌 جاري الاتصال بقاعدة Qdrant السحابية...")
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=300.0  # إجبار الخادم على الانتظار لمدة 5 دقائق كاملة للرد (يمنع الـ Timeout)
)

print("📥 جاري تجهيز نموذج الذكاء الاصطناعي...")
embedding_model = SentenceTransformer("BAAI/bge-m3")
VECTOR_SIZE = embedding_model.get_embedding_dimension() # تم تحديث الدالة لتجنب التحذير

if not client.collection_exists(COLLECTION_NAME):
    print(f"✨ إنشاء مساحة جديدة في قاعدة البيانات باسم: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

# ==========================================
# 3. محرك المعالجة والرفع على دفعات (Batching)
# ==========================================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=150, 
    separators=["\n\n", "\n", ".", " "]
)

pdf_files = glob.glob(os.path.join(PDF_DIRECTORY, "*.pdf"))

if not pdf_files:
    print(f"⚠️ لم يتم العثور على أبحاث في '{PDF_DIRECTORY}'. يرجى إضافتها.")
    exit()

print(f"📚 جاري معالجة {len(pdf_files)} أبحاث ورفعها للسحابة بطريقة الدفعات...")

for pdf_path in tqdm(pdf_files, desc="تغذية البيانات الكلية"):
    try:
        loader = PyMuPDFLoader(pdf_path)
        documents = loader.load()
        file_name = os.path.basename(pdf_path)
        
        chunks = text_splitter.split_documents(documents)
        points_to_upsert = []
        
        for i, chunk in enumerate(chunks):
            vector = embedding_model.encode(chunk.page_content).tolist()
            payload = {
                "text": chunk.page_content,
                "source": file_name,
                "page": chunk.metadata.get("page", 0) + 1,
                "chunk_id": i
            }
            point_id = str(uuid.uuid4())
            points_to_upsert.append(PointStruct(id=point_id, vector=vector, payload=payload))
            
        # تقسيم النقاط إلى دفعات صغيرة (50 فقرة لكل دفعة) لتسريع الرفع ومنع الانقطاع
        batch_size = 50
        for j in range(0, len(points_to_upsert), batch_size):
            batch = points_to_upsert[j:j + batch_size]
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch
            )
            
    except Exception as e:
        print(f"\n❌ خطأ في معالجة '{file_name}': {e}")

print("\n✅ اكتملت العملية بنجاح! قاعدة البيانات السحابية جاهزة 100%.")