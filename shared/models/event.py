# models/event.py

from sqlalchemy import Column, String, BigInteger, Integer, Boolean
from shared.db import Base

class Event(Base):
    __tablename__ = "events"

    key = Column(String, primary_key=True)
    name = Column(String)
    type = Column(String)  # voice, reaction, trivia...
    goal = Column(Integer) # mốc cần đạt (time, count)
    reward_coin = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    reward_role = Column(String)
    reward_badge = Column(String)
    ends_at = Column(BigInteger)
    enabled = Column(Boolean, default=True)

class UserEvent(Base):
    __tablename__ = "user_events"

    user_id = Column(BigInteger, primary_key=True)
    event_key = Column(String, primary_key=True)
    claimed_at = Column(BigInteger)