# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.domain.user import User

# تحديد المسار الذي سيتوجه إليه المستخدم للحصول على الـ Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    هذه الدالة تعترض أي طلب، تفحص الـ Token، وترجع بيانات المستخدم بالكامل.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="تعذر التحقق من بيانات الاعتماد (Token غير صالح أو منتهي).",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. فك تشفير التوكن
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    # 2. استخراج المعرف (User ID)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    # 3. جلب المستخدم من قاعدة البيانات بشكل غير متزامن
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user