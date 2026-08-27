# backend/app/services/rag/orchestrator.py
import time
from app.services.rag.hybrid_retriever import HybridRetriever
from app.services.rag.llm_engine import LLMEngine
from app.core.config import settings

class RAGOrchestrator:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.llm = LLMEngine()

    def answer(self, question: str) -> dict:
        start = time.perf_counter()

        # استرجاع
        docs = self.retriever.retrieve(question)

        if not docs or docs[0]["score"] < 0.3:
       # if not docs or docs[0]["score"] < settings.RETRIEVAL_MIN_SCORE:
            return {
                "answer": None,
                "citations": [],
                "confidence": docs[0]["score"] if docs else 0.0,
                "fallback": True,
                "message": "لا توجد أبحاث موثقة كافية للإجابة على هذا السؤال.",
                "processing_time_ms": (time.perf_counter() - start) * 1000
            }

        # تحضير السياق
        context = "\n\n".join([f"[PMID: {d['pubmed_id']}] {d['text']}" for d in docs])

        # توليد
        answer_text = self.llm.generate(context, question)

        # تجهيز المراجع
        citations = []
        for d in docs:
            citations.append({
                "pubmed_id": d["pubmed_id"],
                "title": d["title"],
                "relevance_score": d["score"]
            })

        return {
            "answer": answer_text,
            "citations": citations,
            "confidence": docs[0]["score"],
            "fallback": False,
            "message": None,
            "processing_time_ms": (time.perf_counter() - start) * 1000
        }
    # أضف هذه الدالة داخل كلاس RAGOrchestrator في ملف orchestrator.py

    # def answer_stream(self, question: str):
    #     """البحث عن المستندات وبث الإجابة مباشرة لتقليل زمن الانتظار"""
    #     from app.core.config import settings
        
    #     # 1. استرجاع الأبحاث
    #     docs = self.retriever.retrieve(question)
        
    #     # 2. حماية من الهلوسة (Fallback)
    #     if not docs or docs[0]["score"] < settings.RETRIEVAL_MIN_SCORE:
    #         yield "لا توجد أبحاث موثقة كافية للإجابة على هذا السؤال."
    #         return
            
    #     # 3. تجميع النصوص
    #     context = "\n".join([f"- {d['title']}" for d in docs])
        
    #     # 4. بث الإجابة (وهنا دمجنا شرط اللغة العربية)
    #     prompt = f"أجب باللغة العربية بأسلوب طبي دقيق بناءً على الأبحاث التالية فقط:\n{context}\n\nالسؤال: {question}"
        
    #     for chunk in self.llm.generate_stream(context, prompt):
    #         yield chunk
    def answer_stream(self, question: str):
        """البحث عن المستندات وبث الإجابة مباشرة"""
        
        # 1. استرجاع الأبحاث
        docs = self.retriever.retrieve(question)
        
        # 2. حماية بسيطة: إذا لم يجد أي بحث إطلاقاً
        if not docs:
            yield "عذراً، لم أجد أي أبحاث قريبة من سؤالك في قاعدة البيانات."
            return
            
        # 3. تجميع النصوص (تخطينا شرط الحد الأدنى للثقة لنجبره على الإجابة)
        context = "\n".join([f"- {d['title']}" for d in docs])
        
        # 4. بث الإجابة
        prompt = f"أنت طبيب ذكي. أجب باللغة العربية بناءً على الأبحاث التالية:\n{context}\n\nالسؤال: {question}"
        
        for chunk in self.llm.generate_stream(context, prompt):
            yield chunk