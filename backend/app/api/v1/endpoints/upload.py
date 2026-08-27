#backend/app/api/v1/endpoints/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
# استدعاء محرك معالجة الملفات الذي أنشأناه سابقاً
from app.services.rag.ingestion_engine import process_and_upload_pdf

router = APIRouter()

@router.post("/upload")
async def upload_medical_document(file: UploadFile = File(...)):
    """نقطة نهاية لاستقبال ملفات PDF وتغذية قاعدة المعرفة"""
    
    # حماية النظام: التأكد من أن الملف هو PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="يُسمح فقط برفع ملفات PDF.")
    
    try:
        # قراءة الملف كـ Bytes
        file_bytes = await file.read()
        
        # إرسال الملف لمحرك المعالجة ليتم تحويله لمتجهات
        result_message = await process_and_upload_pdf(file_bytes, file.filename)
        
        return {"status": "success", "message": result_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))