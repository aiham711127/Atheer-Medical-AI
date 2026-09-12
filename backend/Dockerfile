# # syntax=docker/dockerfile:1

# # ==========================================
# # Stage 1: Builder (مرحلة التجميع وتثبيت المكتبات)
# FROM python:3.11-slim AS builder

# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# WORKDIR /app

# # تثبيت أدوات البناء الأساسية
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc build-essential && rm -rf /var/lib/apt/lists/*

# # إنشاء البيئة الوهمية وتفعيلها
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# # تحديث pip
# RUN pip install --upgrade pip

# # 1. نسخ وتثبيت مكتبات الذكاء الاصطناعي الثقيلة أولاً (مع ميزة حفظ التحميل)
# COPY requirements-ai.txt .
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install --default-timeout=1000 --retries=10 -r requirements-ai.txt

# # 2. نسخ وتثبيت باقي مكتبات المشروع الخفيفة (مع ميزة حفظ التحميل)
# COPY requirements.txt .
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install --default-timeout=1000 --retries=10 -r requirements.txt

# # ==========================================
# # Stage 2: Micro-Runner (مرحلة التشغيل الخفيفة والآمنة)
# FROM python:3.11-slim AS runner

# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
# WORKDIR /app

# # نسخ البيئة الوهمية الجاهزة من المرحلة الأولى (بدون أدوات البناء الثقيلة)
# COPY --from=builder /opt/venv /opt/venv

# # إعداد مستخدم بصلاحيات محدودة لمزيد من الأمان
# RUN useradd -m -s /bin/bash atheeruser && chown -R atheeruser:atheeruser /app
# USER atheeruser

# # نسخ ملفات المشروع الخاصة بك
# COPY --chown=atheeruser:atheeruser . .

# # فحص صحة التطبيق
# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#   CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# EXPOSE 8000

# # تشغيل التطبيق
# CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# 1. تثبيت أدوات النظام المطلوبة
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements-ai.txt .
COPY requirements.txt .

# 2. الاستراتيجية الجذرية: التثبيت والتنظيف في طبقة واحدة لمنع انهيار الـ RAM
# هذا السطر سيحمل المكتبات، يثبتها، ثم يمسح الكاش والمترجمات فوراً لتقليل حجم الحاوية.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements-ai.txt && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt && \
    apt-get purge -y gcc build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /root/.cache/pip

# 🎯 الخدعة الذكية: تثبيت المكتبة الناقصة هنا كطبقة جديدة للحفاظ على كاش PyTorch
RUN pip install --no-cache-dir email-validator==2.3.0 python-multipart

# 3. الأمان ونقل الملفات
RUN useradd -m -s /bin/bash atheeruser && chown -R atheeruser:atheeruser /app
USER atheeruser

COPY --chown=atheeruser:atheeruser . .

# 4. فحص الصحة والتشغيل
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]