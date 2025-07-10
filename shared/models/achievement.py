# models/achievement.py

from sqlalchemy import Column, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from shared.db import Base
from sqlalchemy import BigInteger

class Achievement(Base):
    __tablename__ = "achievements"

    key = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    hidden = Column(Boolean, default=True)

    # Relationship to users who unlocked this achievement
    users = relationship("UserAchievement", back_populates="achievement")
    
class UserAchievement(Base):
    __tablename__ = "user_achievements"  # 👈 sửa lại tên bảng
    __table_args__ = {"extend_existing": True}

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    ach_key = Column(Text, ForeignKey("achievements.key"), primary_key=True)
    unlocked_at = Column(BigInteger)

    # Đây là ManyToOne (nhiều record UserAchievement → 1 Achievement)
    achievement = relationship("Achievement", back_populates="users")