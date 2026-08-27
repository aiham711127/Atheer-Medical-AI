# backend/app/services/rag/embeddings.py
import requests
import time
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is missing! تأكد من ملف .env")

    def encode(self, text: str) -> dict:
        # استخدام النموذج الأساسي والمستقر دائماً من جوجل
        model_name = "gemini-embedding-001"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent?key={self.api_key}"
        
        payload = {
            "model": f"models/{model_name}",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        # آلية إعادة المحاولة القوية
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    embedding_vector = data["embedding"]["values"]
                    return {"dense": embedding_vector}
                else:
                    print(f"[-] محاولة {attempt+1} فشلت. الخطأ: {response.text}")
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"[!] انقطاع في الشبكة (المحاولة {attempt+1})...")
            
            time.sleep(2)
            
        raise Exception("فشل الاتصال بخوادم Google Embeddings بعد 3 محاولات.")