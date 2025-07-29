import asyncio
from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Tải các biến môi trường từ file .env của bạn
load_dotenv("IminiBot (main)/.env")

# Import Base từ project của bạn để Alembic biết về các model
# Cần thêm đường dẫn của project vào sys.path để có thể import
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
from shared.db import Base
# Import tất cả các model để Base biết về chúng
from shared.models import user, achievement, inventory, social, quest, minigame, shop, event, item, job, chaosstat, audit, secretunlock, trivia, giftcode
# Cấu hình Alembic từ file .ini
config = context.config

# Lấy URL database từ biến môi trường đã load
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL not found in environment variables.")
config.set_main_option("sqlalchemy.url", db_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Đặt target_metadata là Base.metadata của bạn
target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Các tùy chọn khác nếu cần
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url")
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    # Chạy offline không được hỗ trợ trong setup async này
    raise NotImplementedError("Offline mode is not supported for this async setup.")
else:
    asyncio.run(run_migrations_online())