from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from shared.db import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    base_pay = Column(Integer, nullable=False)
    mastery_req = Column(Integer, nullable=False)

    users = relationship("UserJob", back_populates="job")

class UserJob(Base):
    __tablename__ = "user_jobs"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    mastery = Column(Integer, default=0, nullable=False)
    job_skills = Column(ARRAY(String), default=[])

    job = relationship("Job", back_populates="users")