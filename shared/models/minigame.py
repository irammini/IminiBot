# models/minigame.py

from sqlalchemy import Column, BigInteger, Integer, String
from shared.db import Base

class Minigame(Base):
    __tablename__ = "minigames"

    user_id = Column(BigInteger, primary_key=True)
    total_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    last_game = Column(String, nullable=True)  # lưu tên trò chơi cuối cùng chơi

    def __repr__(self):
        return (
            f"<Minigame(user_id={self.user_id}, wins={self.total_wins}, "
            f"streak={self.current_streak}/{self.longest_streak})>"
        )