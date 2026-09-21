# # syntax=docker/dockerfile:1

# FROM python:3.11-slim

# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# WORKDIR /app

# # 1. تثبيت أدوات النظام المطلوبة
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc build-essential && rm -rf /var/lib/apt/lists/*

# COPY requirements-ai.txt .
# COPY requirements.txt .

# # 2. الاستراتيجية الجذرية: التثبيت والتنظيف في طبقة واحدة لمنع انهيار الـ RAM
# # هذا السطر سيحمل المكتبات، يثبتها، ثم يمسح الكاش والمترجمات فوراً لتقليل حجم الحاوية.
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir --default-timeout=1000 -r requirements-ai.txt && \
#     pip install --no-cache-dir --default-timeout=1000 -r requirements.txt && \
#     apt-get purge -y gcc build-essential && \
#     apt-get autoremove -y && \
#     apt-get clean && \
#     rm -rf /root/.cache/pip

# # 🎯 الخدعة الذكية: تثبيت المكتبات الناقصة هنا كطبقة جديدة للحفاظ على كاش PyTorch
# # قمنا بدمج langchain-text-splitters هنا لكي تُثبت بصلاحيات الـ Root
# RUN pip install --no-cache-dir email-validator==2.3.0 python-multipart langchain-text-splitters

# # 3. الأمان ونقل الملفات
# RUN useradd -m -s /bin/bash atheeruser && \
#     mkdir -p /home/atheeruser/.cache/huggingface && \
#     chown -R atheeruser:atheeruser /app /home/atheeruser
# USER atheeruser
# # 🔴 أضف هذا السطر الجديد تحته مباشرة
# RUN pip install langchain-text-splitters
# COPY --chown=atheeruser:atheeruser . .

# # 4. فحص الصحة والتشغيل
# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#   CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# EXPOSE 8000
# CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential && rm -rf /var/lib/apt/lists/*

# 1. الطبقة الثقيلة (PyTorch وأخواتها): تُبنى مرة واحدة فقط وتُقفل في الكاش
COPY requirements-ai.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements-ai.txt

# 2. الطبقة الخفيفة (المكتبات اليومية): أي تعديل هنا سيُبنى في ثوانٍ ولن يمس الطبقة العلوية
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt && \
    apt-get purge -y gcc build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /root/.cache/pip

# 3. الأمان ونقل الملفات
RUN useradd -m -s /bin/bash atheeruser && \
    mkdir -p /home/atheeruser/.cache/huggingface && \
    chown -R atheeruser:atheeruser /app /home/atheeruser

USER atheeruser
COPY --chown=atheeruser:atheeruser . .

# 4. فحص الصحة والتشغيل
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]