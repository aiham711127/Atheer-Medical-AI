from app.core.config import settings
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(settings.async_database_url)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Database connection OK:", result.scalar())
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())