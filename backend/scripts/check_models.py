#سؤال خوادم جوجل مباشرة: "ما هي نماذج التضمين (Embeddings) المتاحة لديكم الآن؟"
import os
import sys
import requests

# إضافة مسار المشروع للوصول إلى مفتاح الـ API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def find_llm_models():
    print("[*] جاري الاتصال بخوادم جوجل لجلب النماذج المتاحة...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.GOOGLE_API_KEY}"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[!] خطأ في الاتصال: {response.text}")
        return

    models = response.json().get("models", [])
    print("\n✅ نماذج الذكاء الاصطناعي (توليد النصوص) المتاحة لك حالياً هي:")
    
    for model in models:
        # نبحث هذه المرة عن النماذج التي تدعم المحادثة وتوليد النصوص
        if "generateContent" in model.get("supportedGenerationMethods", []):
            print(f" - {model['name'].replace('models/', '')}")

if __name__ == "__main__":
    find_llm_models()