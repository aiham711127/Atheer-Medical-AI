import os
import sys
import requests
from dotenv import load_dotenv

# تحميل ملف البيئة .env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def find_groq_models():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[-] مفتاح GROQ_API_KEY مفقود من ملف .env")
        return

    print("[*] جاري الاتصال بخوادم Groq لجلب النماذج المتاحة لمفتاحك...")
    url = "https://api.groq.com/openai/v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[!] خطأ في الاتصال: {response.text}")
        return

    models = response.json().get("data", [])
    print("\n✅ النماذج المتاحة لك حالياً على Groq هي:")
    
    # فلترة وطباعة النماذج
    for model in models:
        model_id = model.get("id")
        # سنستبعد نماذج الصوت (whisper) لنركز على نماذج النصوص
        if "whisper" not in model_id:
            print(f" - {model_id}")

if __name__ == "__main__":
    find_groq_models()