import os
import asyncio
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
from groq import AsyncGroq
from sentence_transformers import SentenceTransformer

# ==========================================
# 1. إعدادات البيئة (Environment Config)
# ==========================================
load_dotenv()

raw_host = os.getenv("QDRANT_HOST", "").strip()
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

COLLECTION_NAME = "medical_knowledge_base"

# هندسة الرابط لتجنب أخطاء الاتصال
if not raw_host.startswith("http"):
    raw_host = f"https://{raw_host}"

qdrant_url = f"{raw_host}:{QDRANT_PORT}" if f":{QDRANT_PORT}" not in raw_host else raw_host

# ==========================================
# 2. تهيئة المحركات غير المتزامنة (Async Clients)
# ==========================================
qdrant_client = AsyncQdrantClient(url=qdrant_url, api_key=QDRANT_API_KEY, timeout=60.0)
llm_client = AsyncGroq(api_key=GROQ_API_KEY)

# تحميل نفس النموذج المحلي الخفيف المستخدم في رفع البيانات
embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# 3. الاسترجاع الذكي (Smart Retrieval)
# ==========================================
async def retrieve_context(user_message: str):
    try:
        # تحويل النص لمتجهات بنفس الأبعاد (384)
        query_vector = embedding_model.encode(user_message, normalize_embeddings=True).tolist()
        
        response = await qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=2,
            score_threshold=0.3 
        )
        
        points = response.points or []
        if not points:
            return "", []

        context_parts = []
        sources = []
        
        for index, hit in enumerate(points, start=1):
            payload = hit.payload or {}
            text = payload.get("text", "").strip()
            source_name = payload.get("source", "مستند غير معروف").strip()
            
            if not text:
                continue
                
            source_label = f"S{index}"
            sources.append({"id": source_label, "name": source_name})
            context_parts.append(f"[{source_label}]\nالمصدر: {source_name}\nالنص: {text}\n")
            
        context_text = "\n---\n".join(context_parts)
        return context_text, sources
    
    except Exception as e:
        print(f"[خطأ في الاسترجاع] {e}")
        return "", []


# 4. التوليد المعزز بالذاكرة (Memory-Enhanced RAG)
# ==========================================
async def generate_rag_response_stream(user_message: str, user_role: str = "student", history: list = None):
    if history is None:
        history = []

    try:
        # 1. هندسة الاسترجاع الذكي (Smart Contextual Search)
        # إذا كان هناك ذاكرة، ندمج السؤال الحالي مع آخر سؤال للمستخدم لزيادة دقة البحث في Qdrant
        search_query = user_message
        if history:
            last_user_msg = next((msg['content'] for msg in reversed(history) if msg['role'] == 'user'), "")
            if last_user_msg:
                search_query = f"{last_user_msg} {user_message}" # دمج الكلمات المفتاحية

        # البحث في Qdrant باستخدام السؤال المدمج
        context_text, sources = await retrieve_context(search_query)
        
        # نظام الرفض الآمن (Safe Refusal)
        if not context_text:
            yield "عذراً، قاعدة المعرفة الطبية المتاحة لدي لا تحتوي على معلومات موثوقة حول هذا الموضوع."
            return

        # تحديد نبرة الذكاء الاصطناعي بناءً على دور المستخدم
        role_instruction = ""
        if user_role == "doctor":
            role_instruction = "أنت تتحدث مع طبيب ممارس. قدم خلاصة سريرية دقيقة، واستخدم المصطلحات الطبية المتقدمة."
        else:
            role_instruction = "أنت تتحدث مع طالب طب. اشرح الفسيولوجيا المرضية والمفاهيم بطريقة تعليمية مبسطة."

        # قالب هندسة الأوامر المتقدم (بدون تغيير)
        system_prompt = f"""
        أنت "أثير"، مساعد طبي ذكي يعمل بنظام Retrieval-Augmented Generation (RAG).

{role_instruction}

============================================================
[1] قاعدة المعرفة المسموح بها
============================================================
<MEDICAL_CONTEXT>
{context_text}
</MEDICAL_CONTEXT>

- اعتمد حصرياً على المعلومات الصريحة في السياق.
- إذا كانت المعلومات المسترجعة غير كافية للإجابة، صرّح بذلك بوضوح ولا تحاول اختلاق إجابة.

============================================================
[2] التنسيق الإلزامي للإجابة
============================================================
### [عنوان دقيق ومختصر باللغة العربية]

[الإجابة المباشرة والشرح المنظم]

---
**المراجع المستند إليها:**
[أدرج فقط المراجع التي استُخدمت فعليًا]

⚠️ **تنبيه:** هذه المعلومات لأغراض تثقيفية ولا تُعد بديلاً عن تقييم الطبيب أو المختص.
"""

        # 2. بناء رسائل المحادثة (Message Builder)
        messages_to_send = [{"role": "system", "content": system_prompt}]

# 🔴 التعديل هنا: أخذ آخر رسالتين فقط (السؤال السابق وإجابته) لضمان عدم اختناق النموذج
        recent_history = history[-2:] if history else []

        # إضافة التاريخ السابق للرسائل (لكي يتذكر النموذج ما قلته له)
        for msg in history:
            messages_to_send.append({"role": msg["role"], "content": msg["content"]})
            
        # إضافة السؤال الحالي في النهاية
        messages_to_send.append({"role": "user", "content": user_message})

        # طلب الإجابة من Groq باستخدام نموذج علاّم
        chat_completion = await llm_client.chat.completions.create(
            messages=messages_to_send,
            model="allam-2-7b",
            temperature=0.3,
            top_p=0.9,
            max_tokens=1024,
            stream=True
        )

        # بث الاستجابة المباشرة
        async for chunk in chat_completion:
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                yield content

    except Exception as e:
        yield f"\n[خطأ داخلي في الخادم: {str(e)}]"