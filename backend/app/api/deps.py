
import uuid
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.domain.user import User

# إعداد الـ Logger الاحترافي
logger = logging.getLogger("uvicorn")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="تعذر التحقق من بيانات الاعتماد (Token غير صالح أو منتهي).",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. فك تشفير التوكن
    payload = decode_access_token(token)
    if payload is None:
        logger.error("AUTH FAIL: التوكن غير صالح أو المفتاح السري مختلف.")
        raise credentials_exception
        
    # 2. استخراج المعرف
    user_id: str = payload.get("sub")
    if not user_id:
        logger.error("AUTH FAIL: التوكن لا يحتوي على معرف المستخدم 'sub'.")
        raise credentials_exception
        
    # 3. جلب المستخدم من قاعدة البيانات غير المتزامنة (مع ضمان تحويل UUID)
    try:
        user_uuid = uuid.UUID(user_id) # تحويل إجباري ليتوافق مع PostgreSQL
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"AUTH FAIL: خطأ أثناء استعلام قاعدة البيانات: {str(e)}")
        raise credentials_exception
        
    if user is None:
        logger.error(f"AUTH FAIL: لم يتم العثور على المستخدم '{user_id}' في الداتابيز.")
        raise credentials_exception
        
    return user