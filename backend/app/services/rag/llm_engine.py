import logging
import json
import time # ضروري لحساب سرعة الاستجابة (TTFB)
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStoreManager # 🔴 [التعديل المعماري]: استيراد مدير الاتصال الموحد
from app.core.mlops_tracker import mlops_tracker

# تثبيت إصدار الـ Prompt (يجب تغييره عند أي تعديل على النص)
CURRENT_PROMPT_VERSION = "v1.0-strict-medical"

# العتبة الصارمة لمنع الهلوسة 
# MIN_RETRIEVAL_SCORE = 0.65
MIN_RETRIEVAL_SCORE = 0.30

logger = logging.getLogger("uvicorn.error")

# تهيئة عميل جوجل
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
# 🔴 [التعديل هنا]: تهيئة الاتصال مرة واحدة فقط على مستوى السيرفر لجميع المستخدمين
vector_store = VectorStoreManager()
embedding_service = EmbeddingService()

async def retrieve_context(user_message: str):
    try:
        params = mlops_tracker.load_params()
        score_threshold = params.get("retrieval", {}).get("score_threshold", 0.6)
        top_k = params.get("retrieval", {}).get("top_k", 5)

        # استخدام الخدمات المُهيأة مسبقاً (سريع جداً ولن يستهلك الذاكرة)
        vector_dict = await embedding_service.encode(user_message)
        
        response = await vector_store.client.query_points(
            collection_name=vector_store.collection_name,
            query=vector_dict["dense"],
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True 
        )
        
        points = response.points or []
        if not points:
            return "", 0.0
            
        max_score = max([hit.score for hit in points]) if points else 0.0

        context_parts = [f"[S{i}]\nالمصدر: {hit.payload.get('source', '')}\nالنص: {hit.payload.get('text', '')}\n" 
                         for i, hit in enumerate(points, start=1) if hit.payload.get("text")]
                         
        return "\n---\n".join(context_parts), max_score
        
    except Exception as e:
        logger.error(f"[Vector DB Error]: {str(e)}", exc_info=True)
        return "", 0.0
    
async def generate_rag_response_stream(user_message: str, chat_history: list = None, user_role: str = "student"):
    start_time = time.time()
    max_score = 0.0
    
    try:
        status_payload = json.dumps({"type": "status", "text": "جاري تحليل الأبحاث الطبية..."}, ensure_ascii=False)
        yield f"event: status\ndata: {status_payload}\n\n"

        # استلام النص مع نسبة التطابق
        context_text, max_score = await retrieve_context(user_message)
        
        # صمام الأمان - منع الهلوسة وتسجيل الرفض في DagsHub
        if not context_text or max_score < MIN_RETRIEVAL_SCORE:
            ttfb = time.time() - start_time
            mlops_tracker.log_llm_metrics(
                prompt_version=CURRENT_PROMPT_VERSION,
                ttfb=ttfb,
                retrieval_score=max_score,
                status="MED_ERR_INSUFFICIENT_DATA"
            )
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
        formatted_history = []
        for msg in (chat_history[-window_size:] if chat_history else []):
            role = "model" if msg.get("role") == "assistant" else "user"
            formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(msg.get("content", ""))]))
            
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=params.get("llm", {}).get("temperature", 0.0)
        )

        chat = gemini_client.chats.create(model=model_name, config=config, history=formatted_history)
        response_stream = chat.send_message_stream(user_message)
        
        # حساب الـ TTFB
        first_token_received = False
        ttfb = 0.0
        
        for chunk in response_stream:
            if not first_token_received:
                ttfb = time.time() - start_time
                first_token_received = True
                
            if chunk.text:
                payload = json.dumps({"type": "message", "text": chunk.text}, ensure_ascii=False)
                yield f"event: message\ndata: {payload}\n\n"

        # تسجيل النجاح التام
        mlops_tracker.log_llm_metrics(
            prompt_version=CURRENT_PROMPT_VERSION,
            ttfb=ttfb,
            retrieval_score=max_score,
            status="SUCCESS"
        )

    except Exception as e:
        mlops_tracker.log_llm_metrics(
            prompt_version=CURRENT_PROMPT_VERSION,
            ttfb=time.time() - start_time,
            retrieval_score=max_score,
            status="MED_ERR_UPSTREAM_FAILED"
        )
        logger.error(f"[Generation Error]: {str(e)}", exc_info=True)
        err_payload = json.dumps({"type": "error", "status_code": 500, "message": "حدث خطأ في الخوادم، يرجى المحاولة لاحقاً."}, ensure_ascii=False)
        yield f"event: error\ndata: {err_payload}\n\n"