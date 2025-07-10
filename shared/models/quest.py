# models/quest.py

from sqlalchemy import Column, BigInteger, Text, Integer, Boolean, String
from shared.db import Base


class DailyQuest(Base):
    __tablename__ = "daily_quests"

    id = Column(Text, primary_key=True)     # ví dụ: "earn", "message"
    quest = Column(Text, nullable=False)
    special = Column(Boolean, default=False)   
    date = Column(Integer, nullable=False) 
    name = Column(Text, nullable=False)         # tên nhiệm vụ
    description = Column(Text, nullable=True)   # mô tả
    required = Column(Integer, nullable=False)  # mục tiêu (ví dụ: 5 tin nhắn)
    reward_coin = Column(Integer, default=0)    # phần thưởng
    reward_xp = Column(Integer, default=0)


class UserQuest(Base):
    __tablename__ = "user_quests"
    user_id = Column(BigInteger, primary_key=True)
    quest_key = Column(String, primary_key=True)
    period = Column(String)  # daily or weekly
    progress = Column(Integer, default=0)
    req = Column(Integer)
    reward_coin = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(BigInteger)
    expires_at = Column(BigInteger)
    completed_at = Column(BigInteger, nullable=True)