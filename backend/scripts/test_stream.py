import requests
import sys

# هذا السكريبت يحاكي تطبيق الهاتف (Flutter) 
url = "http://127.0.0.1:8000/api/v1/rag/query"

payload = {
    "question": "ما هي الأعراض والمحفزات المرتبطة بصداع الشقيقة؟",
    "language": "ar",
    "specialty": "general"
}

print("🤖 أثير يقرأ الأبحاث الطبية ويكتب الإجابة...\n")
print("-" * 50)

try:
    with requests.post(url, json=payload, stream=True) as response:
        if response.status_code != 200:
            print(f"خطأ من السيرفر: {response.status_code}")
            sys.exit(1)
            
        in_think_block = False
        buffer = ""
        
        # طباعة الكلمات فور وصولها (حرفاً بحرف)
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                buffer += chunk
                
                # تتبع ما إذا كنا داخل قسم التفكير
                if "<think>" in buffer:
                    in_think_block = True
                    buffer = buffer.replace("<think>", "")
                    
                if "</think>" in buffer:
                    in_think_block = False
                    # التخلص من علامة نهاية التفكير وأي مسافات بعدها
                    buffer = buffer.split("</think>")[-1].lstrip()
                
                # طباعة النص فقط إذا لم نكن داخل قسم التفكير
                if not in_think_block:
                    print(buffer, end='', flush=True)
                    buffer = "" # تفريغ البفر بعد الطباعة
                
    print("\n\n" + "-" * 50)
    print("✅ اكتملت الإجابة بنجاح!")
    
except Exception as e:
    print(f"\n[!] خطأ في الاتصال: {e}")