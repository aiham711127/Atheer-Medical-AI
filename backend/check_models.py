import os
from groq import Groq
from dotenv import load_dotenv

# تحميل المفتاح من ملف .env الخاص بك
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

try:
    client = Groq(api_key=api_key)
    models = client.models.list()
    
    print("✅ النماذج المتاحة لمفتاحك السري حالياً هي:")
    for m in models.data:
        print(f"👉 {m.id}")
except Exception as e:
    print(f"❌ خطأ: {e}")


#      النماذج المتاحة لمفتاحك السري حالياً هي:
# 👉 openai/gpt-oss-120b
# 👉 allam-2-7b
# 👉 canopylabs/orpheus-arabic-saudi
# 👉 openai/gpt-oss-20b
# 👉 meta-llama/llama-prompt-guard-2-22m
# 👉 meta-llama/llama-prompt-guard-2-86m
# 👉 qwen/qwen3.6-27b
# 👉 openai/gpt-oss-safeguard-20b
# 👉 groq/compound-mini
# 👉 groq/compound
# 👉 whisper-large-v3
# 👉 canopylabs/orpheus-v1-english
# 👉 whisper-large-v3-turb