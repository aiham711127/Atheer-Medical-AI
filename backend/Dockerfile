# استخدام نسخة بايثون رسمية، حديثة، وخفيفة جداً (Slim)
FROM python:3.10-slim

# منع بايثون من كتابة ملفات .pyc المؤقتة وتفعيل طباعة السجلات فوراً
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مسار العمل داخل الحاوية
WORKDIR /app

# تثبيت متطلبات النظام الأساسية (C++ Compilers) التي تحتاجها مكتبات مثل pgvector و sentence-transformers
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المكتبات أولاً (للاستفادة من ميزة Docker Cache وتسريع البناء)
COPY requirements.txt .

# تثبيت المكتبات وتجاهل الذاكرة المؤقتة لتقليل حجم الحاوية
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع إلى الحاوية
COPY . .

# فتح المنفذ الذي سيعمل عليه FastAPI
EXPOSE 8000

# أمر التشغيل النهائي للخادم
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]