#backend/app/api/v1/endpoints/upload.py

import hashlib
import os
import shutil
import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, get_db
from app.models.domain.user import User
from app.models.domain.document import Document
from app.services.rag.ingestion_engine import process_document_task

router = APIRouter()

# إنشاء مجلد الرفع المؤقت إذا لم يكن موجوداً
UPLOAD_DIR = "/tmp/atheer_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def upload_medical_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    نقطة رفع المراجع الطبية: تحمي الرام، تمنع التكرار، ولا تجمد السيرفر.
    """
    # 1. التحقق من صيغة الملف مبدئياً
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="يُسمح فقط برفع ملفات PDF الطبية.")

    # 2. حساب البصمة الرقمية (Hash) بشكل تدفقي لحماية الـ RAM 
    sha256_hash = hashlib.sha256()
    while chunk := await file.read(8192):
        sha256_hash.update(chunk)
    
    file_hash = sha256_hash.hexdigest()
    await file.seek(0) # إعادة مؤشر القراءة للبداية لنتمكن من حفظه لاحقاً

    # 3. إعداد السجل في قاعدة البيانات
    new_doc = Document(
        filename=file.filename,
        file_hash=file_hash,
        uploaded_by=current_user.id
    )
    db.add(new_doc)

    try:
        await db.commit()
        await db.refresh(new_doc)
    except IntegrityError:
        # 🔴 حماية الدبل كليك والتكرار: الملف موجود مسبقاً!
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="هذا البحث الطبي موجود مسبقاً في قاعدة المعرفة المركزية. لا داعي لرفعه مجدداً."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"حدث خطأ داخلي: {str(e)}")

    # 4. حفظ الملف مؤقتاً على القرص ليقرأه المحرك المعزول
    file_path = os.path.join(UPLOAD_DIR, f"{new_doc.id}.pdf")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        await db.delete(new_doc)
        await db.commit()
        raise HTTPException(status_code=500, detail="فشل في حفظ الملف على الخادم.")

    # 5. التفويض: إرسال المهمة الثقيلة لتعمل في الخلفية (Fire and Forget)
    asyncio.create_task(process_document_task(doc_id=new_doc.id, file_path=file_path))

    # 6. إرجاع استجابة سريعة جداً للمستخدم (202 Accepted)
    return {
        "message": "تم استلام الملف بنجاح. جاري المعالجة واستخراج البيانات الطبية في الخلفية.",
        "document_id": str(new_doc.id),
        "status": new_doc.status
    }