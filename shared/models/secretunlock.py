# models/secretunlock.py
import time
from sqlalchemy import Column, BigInteger, String
from shared.db import Base

class SecretUnlock(Base):
    __tablename__ = "secret_unlocks"

    user_id = Column(BigInteger, primary_key=True)
    unlock_key = Column(String, primary_key=True)       # key lệnh/dungeon ẩn
    unlocked_at = Column(BigInteger, default=lambda: int(time.time()))