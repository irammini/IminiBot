# models/trivia.py

from sqlalchemy import Column, Text, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from shared.db import Base

class TriviaQuestion(Base):
    __tablename__ = "trivia_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    options = Column(ARRAY(String), nullable=False)
    answer = Column(Text, nullable=False)  # phải khớp với 1 option
    level = Column(String, nullable=False)  # easy, normal, hard, extreme, nightmare
    category = Column(String)  # optional