from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 💠 Base dùng chung để định nghĩa các model
Base = declarative_base()

def init_engine(database_url: str):
    """
    Khởi tạo SQLAlchemy engine & session maker dùng async.

    Parameters:
        database_url (str): URL kết nối database PostgreSQL qua asyncpg

    Returns:
        Tuple: (engine, sessionmaker instance)
    """
    engine = create_async_engine(
        database_url,
        echo=False,              # Đặt True nếu cần log SQL cho debug
        pool_size=5,             # Số kết nối khởi tạo
        max_overflow=10,         # Số kết nối dư nếu cần
        pool_pre_ping=True       # Ping trước khi dùng để tránh timeout
    )

    SessionLocal = sessionmaker(
        bind=engine,
        class_= AsyncSession,
        expire_on_commit=False
    )

    return engine, SessionLocal