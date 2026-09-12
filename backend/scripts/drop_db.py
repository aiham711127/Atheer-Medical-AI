# backend/scripts/drop_db.py
from app.core.config import settings
from qdrant_client import QdrantClient

print("🔌 جاري الاتصال بالسحابة باستخدام إعدادات التطبيق المعتمدة...")

# استخدام نفس عميل الاتصال والإعدادات الموجودة في السيرفر
client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=int(settings.QDRANT_PORT),
    api_key=settings.QDRANT_API_KEY,
    timeout=30.0
)

COLLECTION_NAME = settings.COLLECTION_NAME

try:
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✅ تم تدمير القاعدة القديمة '{COLLECTION_NAME}' من السحابة بنجاح تام!")
    else:
        print(f"⚠️ القاعدة '{COLLECTION_NAME}' غير موجودة أصلاً في هذا الاتصال.")
except Exception as e:
    print(f"❌ حدث خطأ أثناء الاتصال أو الحذف: {e}")