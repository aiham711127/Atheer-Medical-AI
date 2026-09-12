# # scripts/check_db.py
# import asyncio
# from qdrant_client import AsyncQdrantClient
# from app.core.config import settings

# async def main():
#     qdrant_url = settings.QDRANT_HOST if settings.QDRANT_HOST.startswith("http") else f"https://{settings.QDRANT_HOST}"
#     if f":{settings.QDRANT_PORT}" not in qdrant_url:
#         qdrant_url = f"{qdrant_url}:{settings.QDRANT_PORT}"
        
#     client = AsyncQdrantClient(url=qdrant_url, api_key=settings.QDRANT_API_KEY)
#     count = await client.count(collection_name=settings.COLLECTION_NAME)
    
#     print("\n======================================")
#     print(f"📊 حجم قاعدة البيانات: {count.count} بحث طبي")
#     print("======================================\n")

# asyncio.run(main())


import asyncio
from qdrant_client import QdrantClient
from app.core.config import settings

def check_qdrant_vectors():
    print("🔍 جاري فحص Qdrant Cloud Vector DB...")
    try:
        # الاتصال بـ Qdrant Cloud
        client = QdrantClient(
            url=settings.QDRANT_HOST,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        )
        
        # جلب قائمة المجموعات المتاحة
        collections = client.get_collections().collections
        print(f"📁 المجموعات الموجودة: {[c.name for c in collections]}")
        
        # فحص المجموعة الحالية
        target_collection = settings.COLLECTION_NAME
        info = client.get_collection(collection_name=target_collection)
        
        print("\n======================================")
        print(f"📊 عدد المتجهات في Qdrant ({target_collection}): {info.points_count}")
        print("======================================\n")
        
    except Exception as e:
        print(f"❌ خطأ أثناء الاتصال بـ Qdrant: {e}")

if __name__ == "__main__":
    check_qdrant_vectors()
