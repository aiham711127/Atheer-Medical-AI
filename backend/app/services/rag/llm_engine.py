import logging
import json
# [التحديث]: استخدام المكتبة الجديدة
from google import genai
from google.genai import types
from qdrant_client import AsyncQdrantClient

from app.core.config import settings
from app.services.rag.embeddings import EmbeddingService
from app.core.mlops_tracker import mlops_tracker

logger = logging.getLogger("uvicorn.error")

# إعداد قاعدة البيانات
qdrant_url = settings.QDRANT_HOST if settings.QDRANT_HOST.startswith("http") else f"https://{settings.QDRANT_HOST}"
if f":{settings.QDRANT_PORT}" not in qdrant_url:
    qdrant_url = f"{qdrant_url}:{settings.QDRANT_PORT}"

qdrant_client = AsyncQdrantClient(url=qdrant_url, api_key=settings.QDRANT_API_KEY, timeout=60.0)

# [التحديث]: تهيئة عميل جوجل الجديد
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def retrieve_context(user_message: str):
    try:
        # القراءة الآن لحظية من الذاكرة (Cached)
        params = mlops_tracker.load_params()
        score_threshold = params.get("retrieval", {}).get("score_threshold", 0.6)
        top_k = params.get("retrieval", {}).get("top_k", 5)

        embedding_service = EmbeddingService()
        vector_dict = await embedding_service.encode(user_message)
        
        response = await qdrant_client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=vector_dict["dense"],
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True 
        )
        
        points = response.points or []
        if not points:
            return ""

        context_parts = [f"[S{i}]\nالمصدر: {hit.payload.get('source', '')}\nالنص: {hit.payload.get('text', '')}\n" 
                         for i, hit in enumerate(points, start=1) if hit.payload.get("text")]
        return "\n---\n".join(context_parts)
    except Exception as e:
        logger.error(f"[Vector DB Error]: {str(e)}", exc_info=True)
        return ""

    
async def generate_rag_response_stream(user_message: str, chat_history: list = None, user_role: str = "student"):
    try:
        status_payload = json.dumps({"type": "status", "text": "جاري تحليل الأبحاث الطبية..."}, ensure_ascii=False)
        yield f"event: status\ndata: {status_payload}\n\n"

        context_text = await retrieve_context(user_message)
        
        if not context_text:
            payload = json.dumps({"type": "refusal", "text": "عذراً، الأبحاث الطبية المتاحة لدي لا تحتوي على معلومات موثوقة حول هذا الموضوع."}, ensure_ascii=False)
            yield f"event: message\ndata: {payload}\n\n"
            return

        params = mlops_tracker.load_params()
        model_name = params.get("llm", {}).get("model_name", settings.GEMINI_MODEL_NAME)
        window_size = params.get("llm", {}).get("sliding_window", 4)

        role_instruction = (
            "أنت طبيب ممارس. قدم خلاصة سريرية دقيقة." if user_role == "doctor" 
            else "أنت مساعد تعليمي لطلاب الطب. اشرح المفاهيم الطبية خطوة بخطوة."
        )

        system_instruction = f"""أنت "أثير"، مساعد طبي يعمل بنظام RAG.
{role_instruction}
[السياق الطبي المسترجع]:
{context_text}
[القواعد]:
1. الإجابة بالعربية العلمية حصراً، والمصطلحات بالإنجليزية بين قوسين.
2. ادعم الجمل بـ [S1]. يمنع التخمين الخارجي.
"""
        # [التحديث]: تجهيز الذاكرة والمحادثة للمكتبة الجديدة
        formatted_history = []
        for msg in (chat_history[-window_size:] if chat_history else []):
            role = "model" if msg.get("role") == "assistant" else "user"
            formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(msg.get("content", ""))]))
            
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=params.get("llm", {}).get("temperature", 0.0)
        )

        # [التحديث]: بدء الدردشة وإرسال الرسالة باستخدام المكتبة الجديدة
        chat = gemini_client.chats.create(model=model_name, config=config, history=formatted_history)
        response_stream = chat.send_message_stream(user_message)
        
        for chunk in response_stream:
            if chunk.text:
                payload = json.dumps({"type": "message", "text": chunk.text}, ensure_ascii=False)
                yield f"event: message\ndata: {payload}\n\n"

    except Exception as e:
        logger.error(f"[Generation Error]: {str(e)}", exc_info=True)
        err_payload = json.dumps({"type": "error", "status_code": 500, "message": "حدث خطأ في الخوادم، يرجى المحاولة لاحقاً."}, ensure_ascii=False)
        yield f"event: error\ndata: {err_payload}\n\n"