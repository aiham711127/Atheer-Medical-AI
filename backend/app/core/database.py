# backend/app/core/database.py
import ssl
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 1. إعداد الـ SSL بناءً على البيئة (محلي أو سحابي)
connect_args = {}

# نتحقق إذا كان الرابط السحابي لا يحتوي على أسماء مضيفين محليين، حينها فقط نفعل التشفير
if not any(local_host in settings.async_database_url for local_host in ["@localhost", "@127.0.0.1", "@db"]):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

# 2. إنشاء المحرك وتمرير connect_args ديناميكياً
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args=connect_args  # <--- الآن يتم التمرير بذكاء حسب البيئة
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db(): 
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()