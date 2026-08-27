# backend/app/core/arabic_utils.py
import re

def normalize_arabic_text(text: str) -> str:
    """
    توحيد النص العربي لتسهيل البحث والتضمين (Hybrid Retrieval).
    مُحسنة للأداء باستخدام str.translate بدلاً من تكرار re.sub.
    """
    if not text:
        return text

    # 1. إزالة التشكيل (الحركات) والتطويل (كشيدة)
    # \u064B-\u065F: الحركات العادية والشدة
    # \u0670: الألف الخنجرية
    # \u0640: التطويل (ـ)
    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)

    # 2. إعداد خريطة الاستبدال السريعة (Translation Table)
    # هذه الطريقة أسرع بكثير من استخدام re.sub لكل حرف
    normalization_map = str.maketrans({
        'أ': 'ا',
        'إ': 'ا',
        'آ': 'ا',
        'ٱ': 'ا', # ألف الوصل
        'ة': 'ه',
        'ى': 'ي',
        'ؤ': 'ء', # توحيد الهمزات (اختياري، يفضل في البحث الطبي)
        'ئ': 'ء', # توحيد الهمزات (اختياري)
    })
    
    # 3. تطبيق الاستبدال
    text = text.translate(normalization_map)

    # 4. تنظيف المسافات (إزالة المسافات المزدوجة ومسافات البداية والنهاية)
    # خطوة هامة جداً لتوحيد النصوص قبل تحويلها إلى Vectors
    text = " ".join(text.split())

    return text