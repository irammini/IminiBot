# models/item.py

from sqlalchemy import Column, Text, Integer, BigInteger, String
from sqlalchemy.orm import relationship
from shared.db import Base

class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"extend_existing": True}

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Integer, default=0)
    emoji       = Column(String)
    limit       = Column(Integer)      
    rarity      = Column(String)
    category    = Column(String)


    holders = relationship("Inventory", back_populates="item")

    def __repr__(self):
        return f"<Item(id='{self.id}', name='{self.name}', price={self.price})>"
