import logging
from sqlalchemy import select
from shared.data.items import ITEMS as SHOP_ITEMS
from shared.data.fish import FISH_ITEMS, TRASH_ITEMS
from shared.models.item import Item
from shared.models.shop import ShopItem

logger = logging.getLogger(__name__)

def format_item(data: dict) -> Item:
    return Item(
        id=data.get("key") or data.get("id"),
        name=data["name"],
        description=data.get("description", ""),
        price=data.get("price", 0),
        emoji=data.get("emoji", ""),
        limit=data.get("limit", 1),
        rarity=data.get("rarity", "Common"),
        category=data.get("category", "misc")
    )

async def seed_items(sessionmaker):
    async with sessionmaker() as sess:
        existing = await sess.execute(select(Item.id))
        existing_ids = {row[0] for row in existing}

        new_items = []

        # 🛍️ Seed shop + event items từ items.py
        for data in SHOP_ITEMS:
            item_id = data.get("key") or data.get("id")
            if item_id not in existing_ids:
                new_items.append(format_item(data))

        sess.add_all(new_items)
        await sess.commit()
        logger.info(f"✅ Seed xong {len(new_items)} item mới vào bảng `items`")

        # 🎣 Seed cá từ fish.py
        for fid, name, rarity in FISH_ITEMS:
            if fid not in existing_ids:
                new_items.append(Item(
                    id=fid,
                    name=name,
                    description=f"Cá hiếm ({rarity})",
                    emoji="🐟",
                    rarity=rarity,
                    category="fish",
                    limit=1,
                    price=0
                ))

        # 🗑️ Seed trash từ fish.py
        for tid, name in TRASH_ITEMS:
            if tid not in existing_ids:
                new_items.append(Item(
                    id=tid,
                    name=name,
                    description="Đồ rác câu được",
                    emoji="🗑️",
                    category="trash",
                    rarity="Common",
                    price=0,
                    limit=1
                ))

        sess.add_all(new_items)
        await sess.commit()

async def seed_shop_items(sessionmaker):
    async with sessionmaker() as sess:
        existing = await sess.execute(select(ShopItem.id))
        existing_ids = {row[0] for row in existing}

        new_items = []
        for data in SHOP_ITEMS:
            item_id = data.get("key") or data.get("id")
            if item_id not in existing_ids:
                new_items.append(ShopItem(
                    id=item_id,
                    name=data["name"],
                    description=data.get("description", ""),
                    price=data.get("price", 0),
                    emoji=data.get("emoji", ""),
                    stock=10,
                    available=True,
                    rarity=data.get("rarity", "Common"),
                    featured=False,
                    category=data.get("category", "misc")
                ))
        sess.add_all(new_items)
        await sess.commit()