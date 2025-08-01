# models/user.py
import time
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import Column, Text, BigInteger, Integer, Float, String, Boolean, ARRAY, VARCHAR, JSON, DECIMAL

from shared.db import Base


class User(Base):
    """
    User model for IminiBot, updated for v3.9 "The Custom Profile Update".
    """
    __tablename__ = "users"

    # --- Core Identity ---
    id = Column(BigInteger, primary_key=True, index=True)
    imini_id = Column(String(10), nullable=True, unique=True, index=True) # ID người dùng duy nhất của IminiBot
    created_at = Column(BigInteger, default=int(time.time()))

    # --- Leveling & Stats ---
    xp = Column(BigInteger, default=0, index=True)
    level = Column(BigInteger, nullable=False, default=1, index=True)
    voice_time = Column(Float, default=0)
    streak = Column(BigInteger, default=0, index=True)
    last_daily = Column(Integer, default=0)

    # --- Economy ---
    wallet = Column(DECIMAL(38, 0), default=0, index=True)
    bank_balance = Column(BigInteger, default=0, index=True)
    bank_limit = Column(BigInteger, default=1_000_000_000)
    debt = Column(BigInteger, default=0)

    # --- Job System ---
    job = Column(String, nullable=True, index=True)
    mastery = Column(BigInteger, default=0)
    job_tokens = Column(BigInteger, default=0)
    skills = Column(MutableDict.as_mutable(JSON), default=dict)

    # --- Social & Misc ---
    trust_points = Column(BigInteger, default=0)
    prayer_progress = Column(BigInteger, default=0)
    items = Column(ARRAY(String), default=[])
    has_secret_access = Column(Boolean, default=False)
    templog = Column(MutableDict.as_mutable(JSON), default=dict)

    # --- Profile Customization (v3.9) ---
    # Page 1 - Visuals
    profile_emoji = Column(String, nullable=True)
    profile_frame = Column(String, nullable=True)
    custom_title = Column(String, nullable=True)
    accent_color = Column(VARCHAR, nullable=True)
    flex_key = Column(Text, nullable=True)
    custom_avatar_url = Column(String, nullable=True)
    profile_banner_url = Column(String, nullable=True) # Nâng cấp: Ảnh lớn

    # Page 2 - Personal Info
    about_me = Column(String(250), nullable=True)
    custom_status = Column(String(100), nullable=True)
    vibe_text = Column(String(100), nullable=True)
    custom_field_title = Column(String(50), nullable=True) # Nâng cấp: Tiêu đề field
    custom_field_value = Column(String(250), nullable=True) # Nâng cấp: Nội dung field

    # Settings
    profile_is_private = Column(Boolean, nullable=False, server_default='false')

    # Nâng cấp: Hệ thống Moods/Templates
    profile_moods = Column(MutableDict.as_mutable(JSON), default=dict, nullable=False, server_default='{}')

    # --- Future Features (v4.0) ---
    ingame_role = Column(String, nullable=True)

