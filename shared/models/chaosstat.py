# models/chaosstat.py
import time
from sqlalchemy import Column, BigInteger, Integer
from shared.db import Base

class ChaosStat(Base):
    __tablename__ = "chaos_stats"

    user_id = Column(BigInteger, primary_key=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    high_score = Column(Integer, default=0)
    updated_at = Column(BigInteger, default=lambda: int(time.time()))