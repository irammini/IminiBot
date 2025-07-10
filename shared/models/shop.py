# models/shop.py

from sqlalchemy import Column, Text, Integer, Boolean, VARCHAR
from shared.db import Base


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Text, primary_key=True)       # ID định danh item
    name = Column(Text, nullable=False)       # Tên hiển thị
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=True)    # None = không giới hạn
    available = Column(Boolean, default=True)
    rarity = Column(Text, nullable=True) 
    featured = Column(Boolean, default=False)
    category    = Column(VARCHAR)  # ví dụ: "fish", "trash", "consumable"
    emoji   = Column(VARCHAR)


    def __repr__(self):
        return f"<ShopItem(id='{self.id}', price={self.price}, available={self.available})>"


class ShopMeta(Base):
    __tablename__ = "shop_meta"

    key = Column(Text, primary_key=True)
    value = Column(Text)