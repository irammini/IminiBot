# models/inventory.py

from sqlalchemy import Column, Integer, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from shared.db import Base
from shared.models.item import Item

class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = {"extend_existing": True}

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    item_id = Column(Text, ForeignKey("items.id"), primary_key=True)
    quantity = Column(Integer, default=0)

    item = relationship("Item", back_populates="holders")

    def __repr__(self):
        return f"<Inventory(user_id={self.user_id}, item_id='{self.item_id}', qty={self.quantity})>"