import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# ضع رابط NeonDB الخاص بك بين علامات التنصيص هنا
DB_URL = "postgresql+asyncpg://neondb_owner:npg_LSzQY86XGurh@ep-ancient-hill-aywswge8-pooler.c-5.us-east-2.aws.neon.tech/neondb"

engine = create_async_engine(DB_URL)

async def run():
    async with engine.begin() as conn:
        await conn.execute(text('DROP TABLE IF EXISTS users CASCADE;'))
        print("✅ تم حذف الجدول القديم بنجاح!")

asyncio.run(run())