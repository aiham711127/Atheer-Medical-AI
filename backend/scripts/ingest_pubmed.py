# backend/scripts/ingest_pubmed.py
import os
import sys
import asyncio
import ssl

# أمر لتجاهل فحص شهادة الأمان (مفيد عند استخدام VPN)
ssl._create_default_https_context = ssl._create_unverified_context

# إضافة مسار المشروع الجذري ليتعرف على ملفات app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Bio import Entrez
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStore
import time 

# أدخل بريدك الإلكتروني لكي تسمح لك PubMed باستخدام الـ API الخاص بهم
Entrez.email = "aiham711127@gmail.com" 

def fetch_medical_abstracts(query: str, max_results: int = 10, retries: int = 3):
    """جلب الأبحاث من PubMed مع آلية إعادة المحاولة عند انقطاع الإنترنت"""
    print(f"\n[*] جاري البحث في PubMed عن: {query}...")
    
    for attempt in range(retries):
        try:
            # 1. البحث عن أرقام الأبحاث (IDs)
            search_handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            id_list = search_results.get("IdList", [])
            if not id_list:
                return []

            # 2. جلب التفاصيل والملخصات باستخدام الأرقام
            fetch_handle = Entrez.efetch(db="pubmed", id=id_list, retmode="xml")
            articles = Entrez.read(fetch_handle)
            fetch_handle.close()

            documents = []
            for article in articles.get("PubmedArticle", []):
                try:
                    medline = article["MedlineCitation"]
                    pmid = int(medline["PMID"])
                    title = medline["Article"]["ArticleTitle"]
                    
                    abstract = ""
                    if "Abstract" in medline["Article"] and "AbstractText" in medline["Article"]["Abstract"]:
                        abstract_texts = medline["Article"]["Abstract"]["AbstractText"]
                        abstract = " ".join([str(text) for text in abstract_texts])
                    
                    if not abstract:
                        continue

                    documents.append({
                        "id": pmid,
                        "title": title,
                        "abstract": abstract,
                        "full_text": f"Title: {title}\nAbstract: {abstract}" 
                    })
                except Exception as e:
                    continue
                    
            return documents # نجاح العملية، نخرج من حلقة الإعادة

        except Exception as e:
            print(f"[!] انقطع الاتصال في المحاولة {attempt + 1}: {str(e)[:50]}")
            if attempt < retries - 1:
                print("[-] جاري الانتظار 3 ثوانٍ قبل المحاولة مرة أخرى...")
                time.sleep(3)
            else:
                print("[X] فشل جلب البيانات بعد 3 محاولات. يرجى التأكد من استقرار الـ VPN أو الإنترنت.")
                return []
async def main():
    embedder = EmbeddingService()
    store = VectorStore()
    
    # تأكد من بناء الجدول في Qdrant
    store.ensure_collection()

    # وسعنا قائمة الأمراض لنجعل "أثير" أكثر ذكاءً
    topics = [
        "Hypertension symptoms and treatment", # ضغط الدم
        "Migraine headache symptoms",          # الشقيقة (الصداع النصفي)
        "Type 2 Diabetes management"           # السكري
    ]

    total_inserted = 0
    
    for topic in topics:
        # نجلب 15 بحثاً كامل الملخص لكل مرض (بإجمالي 45 بحث دسم)
        docs = fetch_medical_abstracts(topic, max_results=15)
        
        for doc in docs:
            print(f"[-] جاري معالجة بحث: {doc['title'][:50]}...")
            
            # تحويل النص الكامل (عنوان + ملخص) إلى متجهات
            embeddings = embedder.encode(doc["full_text"])
            
            # تخزين البيانات في Qdrant
            payload = {
                "title": doc["title"],
                "text": doc["full_text"], # خزنّا النص الكامل لكي يقرأه جيميناي
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{doc['id']}/"
            }
            
            store.upsert(doc_id=doc["id"], dense_vector=embeddings["dense"], payload=payload)
            total_inserted += 1
            time.sleep(0.5) # استراحة قصيرة بين كل بحث لتجنب الـ Rate Limit

    print(f"\n[+] اكتملت العملية بنجاح! تم ضخ {total_inserted} بحث طبي مع الملخصات الكاملة إلى قاعدة بيانات Qdrant.")


if __name__ == "__main__":
    asyncio.run(main())