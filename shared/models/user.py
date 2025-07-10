# models/user.py
import time
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import Column, Text, BigInteger, Integer, Float, String, Boolean, ARRAY, VARCHAR, JSON
from shared.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    xp = Column(BigInteger, default=0)
    level = Column(BigInteger, nullable=False, default=1)
    voice_time = Column(Float, default=0)
    wallet = Column(BigInteger, default=0)
    bank_balance = Column(BigInteger, default=0)
    bank_limit = Column(BigInteger, default=1_000_000_000)
    debt = Column(BigInteger, default=0)
    streak = Column(BigInteger, default=0)
    pending_streak_charge = Column(Boolean, default=False)
    flex_key = Column(Text, nullable=True)
    last_daily = Column(Integer, default=0)
    last_deposit = Column(Integer, default=0)
    job = Column(String, default=None)
    mastery = Column(BigInteger, default=0)
    job_tokens = Column(BigInteger, default=0)
    skills = Column(MutableDict.as_mutable(JSON), default=dict)
    trust_points = Column(BigInteger, default=0)
    items = Column(ARRAY(String), default=[])
    ribbon = Column(Text)
    created_at = Column(BigInteger, default=int(time.time()))
    has_secret_access = Column(Boolean, default=False)
    prayer_progress = Column(BigInteger, default=0)
    templog = Column(MutableDict.as_mutable(JSON), default=dict)

        # 🎨 Tùy chỉnh hồ sơ
    profile_emoji = Column(String)       # ví dụ: "🔥", "🐉"
    profile_frame = Column(String)       # ví dụ: "silver", "mythic"
    custom_title = Column(String)      # Danh hiệu cá nhân
    accent_color = Column(VARCHAR)     # Màu nền (HEX)
    profile_theme = Column(String)    # Giao diện

