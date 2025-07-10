# models/audit.py

from sqlalchemy import Column, BigInteger, Text, Integer
from shared.db import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # thêm id PK
    user_id   = Column(BigInteger, nullable=False)
    action    = Column(Text,      nullable=False)
    details   = Column(Text)
    timestamp = Column(Integer)