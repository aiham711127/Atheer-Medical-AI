#backend/alembic/env.py
import asyncio
import ssl
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.database import Base
# استيراد النماذج (سيتم إضافة Document هنا لاحقاً)
from app.models.domain import User, Article

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🔴 التعديل المعماري الحاسم: قراءة الرابط ديناميكياً من الإعدادات وليس كنص ثابت
target_url = settings.async_database_url
config.set_main_option("sqlalchemy.url", target_url)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    # 🔴 إعداد التشفير بذكاء: نفعله فقط إذا لم نكن في بيئة الدوكر المحلية
    connect_args = {}
    if not any(local_host in target_url for local_host in ["@localhost", "@127.0.0.1", "@db"]):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args  # تمرير إعدادات الاتصال الآمنة
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()