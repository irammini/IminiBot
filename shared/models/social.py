# models/social.py

from sqlalchemy import Column, BigInteger, String, Integer
from shared.db import Base

class TrustLog(Base):
    __tablename__ = "trust_logs"

    giver_id = Column(BigInteger, primary_key=True)
    receiver_id = Column(BigInteger, primary_key=True)
    timestamp = Column(BigInteger)

class ThankLog(Base):
    __tablename__ = "thank_logs"

    sender_id = Column(BigInteger, primary_key=True)
    receiver_id = Column(BigInteger, primary_key=True)
    timestamp = Column(BigInteger)