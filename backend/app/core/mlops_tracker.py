# backend/app/core/mlops_tracker.py
import os
import yaml
import mlflow
import dagshub
import logging
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

class MLOpsTracker:
    def __init__(self):
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        self.is_active = bool(self.tracking_uri)
        self._cached_params = None  # ذاكرة التخزين المؤقت للمعاملات (Cache)
        
# ابحث عن دالة __init__ واستبدل جزء التهيئة بهذا:
        if self.is_active:
            try:
                # إعداد التوكن برمجياً لمنع فتح المتصفح في الحاوية
                os.environ["DAGSHUB_USER_TOKEN"] = os.getenv("MLFLOW_TRACKING_PASSWORD", "")
                
                dagshub.init(repo_owner=os.getenv("MLFLOW_TRACKING_USERNAME"), 
                             repo_name="atheer_platform", 
                             mlflow=True)
                mlflow.set_tracking_uri(self.tracking_uri)
                logger.info("[MLOps] Successfully connected to DagsHub & MLflow.")
            except Exception as e:
                logger.error(f"[MLOps] Failed to connect to DagsHub: {e}")
                self.is_active = False

    def load_params(self, yaml_path: str = "params.yaml", force_reload: bool = False):
        """قراءة المعلمات الفائقة وإرجاعها من الذاكرة (Cache) لتجنب حظر الـ Async"""
        if self._cached_params is not None and not force_reload:
            return self._cached_params

        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            full_path = base_dir / yaml_path
            
            with open(full_path, "r", encoding="utf-8") as file:
                self._cached_params = yaml.safe_load(file)
                return self._cached_params
        except Exception as e:
            logger.warning(f"[MLOps] params.yaml error: {e}")
            return {}

    def start_rag_experiment(self, experiment_name: str = "RAG_Medical_Baseline"):
        """بدء تجربة جديدة وتسجيل المعلمات"""
        if not self.is_active:
            return None

        mlflow.set_experiment(experiment_name)
        params = self.load_params()
        
        # استخراج المعلمات الجاهزة للتسجيل
        llm_params = params.get("llm", {})
        retrieval_params = params.get("retrieval", {})
        ingestion_params = params.get("ingestion", {})

        # بدء جلسة التسجيل
        active_run = mlflow.start_run(run_name="Gemini_RAG_Test")
        
        # تسجيل المعلمات (Hyperparameters)
        mlflow.log_params({
            "model_name": llm_params.get("model_name"),
            "temperature": llm_params.get("temperature"),
            "top_k": retrieval_params.get("top_k"),
            "score_threshold": retrieval_params.get("score_threshold"),
            "chunk_size": ingestion_params.get("chunk_size")
        })
        
        logger.info(f"[MLOps] Experiment '{experiment_name}' started. Params logged to MLflow.")
        return active_run

    def end_experiment(self):
        """إنهاء التجربة"""
        if self.is_active:
            mlflow.end_run()

# إنشاء كائن جاهز للاستخدام في أي مكان في التطبيق (Singleton)
mlops_tracker = MLOpsTracker()