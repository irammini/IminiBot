# models/giftcode.py

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text
from sqlalchemy.dialects.postgresql import ARRAY
from shared.db import Base

class GiftCode(Base):
    __tablename__ = "giftcodes"
    code = Column(String, primary_key=True)
    coin = Column(Integer, default=0)
    items = Column(ARRAY(String), default=[])
    expires_at = Column(BigInteger, nullable=True)
    max_usage = Column(Integer, default=100)
    per_user_cooldown = Column(Integer, default=60)
    creator_id = Column(BigInteger)
    enabled = Column(Boolean, default=True)
    allowed_user_ids = Column(ARRAY(BigInteger), nullable=True)

class UserGiftCode(Base):
    __tablename__ = "user_giftcodes"
    user_id = Column(BigInteger, primary_key=True)
    code = Column(String, primary_key=True)
    used_at = Column(BigInteger)