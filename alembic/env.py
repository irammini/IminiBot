import asyncio
from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

load_dotenv("IminiBot (main)/.env")

import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
from shared.db import Base
from shared.models import user, achievement, inventory, social, quest, minigame, shop, event, item, job, chaosstat, audit, secretunlock, trivia, giftcode
config = context.config

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL not found in environment variables.")
config.set_main_option("sqlalchemy.url", db_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode."""
    print(">>> Alembic is seeing these tables:", target_metadata.tables.keys())
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url")
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    print("Running migrations in offline mode...")
    run_migrations_offline()
else:
    print("Running migrations in online mode...")
    # Xóa dòng print(...) bạn đã thêm vào hàm này để tránh in 2 lần
    # print(">>> Alembic is seeing these tables:", target_metadata.tables.keys()) 
    asyncio.run(run_migrations_online())