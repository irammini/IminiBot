# cogs/shop.py

import random
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
from sqlalchemy import select, update

from shared.db import AsyncSession
from shared.models.shop import ShopItem
from shared.models.inventory import Inventory
from shared.models.user import User
from shared.data.fish import FISH_ITEMS, TRASH_ITEMS
from shared.data.items import ITEMS, TREASURE_ITEMS
from shared.models.item import Item
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_shop_refresh = datetime.utcnow()

    def get_item_name(self, item_id):
        for it in ITEMS + [dict(key=k, name=n) for k,n,_,_ in TREASURE_ITEMS]:
            if it["key"] == item_id:
                return it["name"]
        return item_id

    async def rotate_shop_items(self):
        async with self.bot.sessionmaker() as sess:
            await sess.execute(
            update(ShopItem).where(ShopItem.featured == True).values(featured=False)
)

            rows = await sess.execute(select(ShopItem))
            all_items = rows.scalars().all()

            new_featured = random.sample(all_items, k=min(3, len(all_items)))
            for item in new_featured:
                item.featured = True
                item.stock = random.randint(3, 8)
            sess.add_all(new_featured)
            await sess.commit()
            self.last_shop_refresh = datetime.utcnow() 

    async def get_or_create_user(self, session, user_id: int) -> User:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                wallet=0,
                bank_balance=0,
                xp=0,
                level=1,
                items=[],
                skills={},
                templog={}
            )
            session.add(user)
            await session.commit()
        return user

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.command(name="shop")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cmd_shop(self, ctx: commands.Context):
        """🛍️ !shop — xem danh sách item đang bán hôm nay."""
        now = datetime.utcnow()

        # ⏳ Nếu đủ thời gian thì tự động xoay shop
        if now - self.last_shop_refresh >= timedelta(hours=6):
            await self.rotate_shop_items()

        async with self.bot.sessionmaker() as sess:
            rows = await sess.execute(select(ShopItem).where(ShopItem.featured))
            shop_items = rows.scalars().all()

        if not shop_items:
            return await ctx.send(embed=make_embed(desc="🛒 Shop hôm nay trống.", color=nextcord.Color.orange()))

        eb = make_embed(title="🛍️ Shop Hôm Nay", color=nextcord.Color.green())
        for it in shop_items:
            emoji = it.emoji or ""
            name_display = f"{emoji} {it.name}" if emoji else it.name
            stock = f" (còn {it.stock})" if it.stock is not None else ""
            eb.add_field(
                name=f"{name_display} — {it.price:,} 🪙{stock}",
                value=f"ID: `{it.id}`",
                inline=False
            )

        # 🕒 Hiển thị countdown tới lần xoay tiếp theo
        cooldown_remaining = max(0, 21600 - int((datetime.utcnow() - self.last_shop_refresh).total_seconds()))
        hr, rem = divmod(cooldown_remaining, 3600)
        mn, _ = divmod(rem, 60)
        eb.set_footer(text=f"🕒 Làm mới sau: {hr}h{mn}m" if cooldown_remaining > 0 else "🕒 Vừa xoay shop!")

        await ctx.send(embed=eb)

    @commands.command()
    async def shopdebug(self, ctx):
        self.last_shop_refresh = datetime.utcnow() - timedelta(hours=7)
        await self.rotate_shop_items()
        await ctx.send("✅ Shop đã xoay thử.")

    @commands.command(name="buy")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @with_achievements("buy")
    async def cmd_buy(self, ctx: commands.Context, item_id: str, qty: int = 1):
        """💸 !buy <item_id> [qty] — mua item từ shop."""
        if qty <= 0:
            return await ctx.send(embed=make_embed(
                desc="❌ Số lượng phải ≥ 1.",
                color=nextcord.Color.red()
            ))

        uid = ctx.author.id
        async with self.bot.sessionmaker() as sess:
            shop_item = await sess.get(ShopItem, item_id)
            user = await sess.get(User, uid)

            if not shop_item or not shop_item.featured:
                return await ctx.send(embed=make_embed(
                    desc="❌ Item không tồn tại hoặc không bán trong shop.",
                    color=nextcord.Color.red()
                ))

            total = shop_item.price * qty
            if (user.wallet or 0) < total:
                return await ctx.send(embed=make_embed(
                    desc="❌ Bạn không đủ xu.",
                    color=nextcord.Color.red()
                ))

            user.wallet -= total
            if shop_item.stock is not None:
                shop_item.stock = max(shop_item.stock - qty, 0)
                sess.add(shop_item)

            inv = await sess.get(Inventory, (uid, item_id))
            if not inv:
                inv = Inventory(user_id=uid, item_id=item_id, quantity=0)
            inv.quantity += qty
            sess.add_all([user, inv])
            await sess.commit()

        await ctx.send(embed=make_embed(
            desc=f"✅ Mua thành công **{qty}× {shop_item.name}**!",
            color=nextcord.Color.green()
        ))

    @commands.command(name="inventory", aliases=["inv"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cmd_inventory(self, ctx: commands.Context):
        """🎒 !inventory — xem đồ trong túi."""
        uid = ctx.author.id
        async with self.bot.sessionmaker() as sess:
            rows = await sess.execute(
                select(Inventory, Item)
                .join(Item, Inventory.item_id == Item.id)
                .where(Inventory.user_id == uid, Inventory.quantity > 0)
            )
            data = rows.all()

        if not data:
            return await ctx.send(embed=make_embed(
                desc="📭 Túi đồ trống.",
                color=nextcord.Color.greyple()
            ))

        eb = make_embed(title="🎒 Túi đồ của bạn", color=nextcord.Color.blue())
        for inv, it in data:
            emoji = it.emoji or ""
            name_display = f"{emoji} {it.name}" if emoji else it.name
            eb.add_field(name=name_display, value=f"x{inv.quantity}", inline=True)

        await ctx.send(embed=eb)

    @commands.command(name="use", aliases=["useitem"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @with_achievements("useitem")
    async def cmd_use(self, ctx: commands.Context, item_id: str):
        """🔧 !use <item_id> — dùng item từ túi."""
        uid = ctx.author.id
        async with self.bot.sessionmaker() as sess:
            inv = await sess.get(Inventory, (uid, item_id))
            if not inv or inv.quantity < 1:
                return await ctx.send(embed=make_embed(
                    desc="❌ Bạn không có item này.",
                    color=nextcord.Color.red()
                ))
            item = await sess.get(ShopItem, item_id)

            if item_id == "xp_juice":
                user = await sess.get(User, uid)
                user.xp = (user.xp or 0) + 2000
                inv.quantity -= 1
                sess.add_all([user, inv])
                await sess.commit()
                return await ctx.send(embed=make_embed(
                    desc="🧪 Dùng XP Juice! +2000 XP",
                    color=nextcord.Color.purple()
                ))
            if item_id == "streak_charge":
                user = await sess.get(User, uid)
                user.pending_streak_charge = True
                inv.quantity -= 1
                sess.add_all([user, inv])
                await sess.commit()
                return await ctx.send(embed=make_embed(
                    desc="⚡ Dùng Streak Charge! Lần `!daily` tiếp theo sẽ +2 streak.",
                    color=nextcord.Color.orange()
                ))
            if item_id != "treasure_chest":
                return await ctx.send("❌ Bạn chỉ có thể dùng hòm kho báu với lệnh này.")

            async with self.bot.sessionmaker() as sess:
                inv = await sess.get(Inventory, (uid, item_id))
                if not inv or inv.quantity < 1:
                    return await ctx.send("📦 Bạn không có hòm kho báu để mở.")

                inv.quantity -= 1
                sess.add(inv)

                # 🎁 Loot cố định: Dog Shield
                loot_ids = ["dog_shield"]

                # 🎲 Loot thêm: lấy 2 item theo tỷ lệ
                pool = []
                pool += ["shark_head", "whale_tail"] * 30
                pool += ["dino_bone"] * 2
                pool += ["deep_key"] * 1
                pool += ["iminicash_bag", "crate", "luck_crate"] * 67

                pool += ["deep_key"] * 1  # 1 xuất
                pool += ["retry_token"] * 199  # để hệ pool có 200 slot ⇒ 0.5% là đúng

                chosen = random.sample(pool, 2)
                loot_ids += chosen

                # Cộng vào inventory & gửi phản hồi
                for item_id in loot_ids:
                    it = await sess.get(Item, item_id)
                    if not it:
                        continue
                    user_item = await sess.get(Inventory, (uid, item_id))
                    if not user_item:
                        user_item = Inventory(user_id=uid, item_id=item_id, quantity=0)
                    user_item.quantity += 1
                    sess.add(user_item)

                await sess.commit()

            loot_names = [self.get_item_name(i) for i in loot_ids]
            await ctx.send(embed=make_embed(
                title="📦 Bạn mở hòm kho báu!",
                desc="Bạn nhận được: " + ", ".join(f"**{name}**" for name in loot_names),
                color=nextcord.Color.gold()
            ))

        await ctx.send(embed=make_embed(
            desc=f"🎉 Bạn đã dùng **{item.name}**!",
            color=nextcord.Color.green()
        ))

    @commands.command(name="sell")
    async def cmd_sell(self, ctx, item_id: str, amount: int = 1):
        uid = ctx.author.id

        # Tìm giá item
        item_data = next(
        (it for it in ITEMS + [dict(key=k, name=n, price=p) for k, n, _, p in TREASURE_ITEMS]
        if it["key"] == item_id),
        None
    )
        if not item_data:
            return await ctx.send("❌ Không tìm thấy vật phẩm đó trong hệ thống.")

        price = item_data.get("price")
        if price is None or price == 0:
            return await ctx.send("📦 Vật phẩm này không thể bán.")

        async with self.bot.sessionmaker() as session:
            inv = await session.get(Inventory, (uid, item_id))
            if not inv or inv.quantity < amount:
                return await ctx.send("❌ Bạn không đủ vật phẩm để bán.")

            inv.quantity -= amount
            session.add(inv)

            coins = price * amount
            user = await self.get_or_create_user(session, uid)
            user.wallet += coins
            session.add(user)

            await session.commit()

        await ctx.send(embed=make_embed(
            desc=f"💰 Bạn đã bán **{amount}× {item_data['name']}** và nhận được **{coins} xu**!",
            color=nextcord.Color.green()
        ))

    @commands.command(name="fish")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @with_achievements("fish")
    async def cmd_fish(self, ctx: commands.Context):
        uid = ctx.author.id

        roll = random.randint(1, 100)
        if roll <= 5:
            item_id = "treasure_chest"
            async with self.bot.sessionmaker() as sess:
                inv = await sess.get(Inventory, (uid, item_id))
                if not inv:
                    inv = Inventory(user_id=uid, item_id=item_id, quantity=0)
                inv.quantity += 1
                sess.add(inv)
                await sess.commit()
            return await ctx.send(embed=make_embed(
                desc="📦 Bạn bất ngờ bắt được **Hòm kho báu**! (5%)",
                color=nextcord.Color.gold()
            ))

        # 🎣 Câu cá bình thường
        pool = FISH_ITEMS + TRASH_ITEMS
        catch = random.choice(pool)
        item_id, name = catch[0], catch[1]
        rarity = catch[2] if len(catch) > 2 else "?"

        is_fish = any(f[0] == item_id for f in FISH_ITEMS)

        async with self.bot.sessionmaker() as sess:
            inv = await sess.get(Inventory, (uid, item_id))
            if not inv:
                inv = Inventory(user_id=uid, item_id=item_id, quantity=0)
            inv.quantity += 1
            sess.add(inv)
            await sess.commit()

        emoji = {
            "Common": "🐟", "Uncommon": "🐠", "Rare": "🦈",
            "Epic": "🐉", "Legendary": "🌟"
        }.get(rarity, "🐡")

        desc = f"{emoji} Bạn câu được **{name}**! (Độ hiếm: {rarity})" if is_fish else f"🗑️ Bạn vớ phải rác **{name}**..."
        color = nextcord.Color.blurple() if is_fish else nextcord.Color.dark_grey()

        await ctx.send(embed=make_embed(desc=desc, color=color))

    @commands.command(name="trash")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cmd_trash(self, ctx: commands.Context):
        """🗑️ !trash — xem rác đã câu được."""
        uid = ctx.author.id
        trash_ids = [tid for tid, _ in TRASH_ITEMS]
        async with self.bot.sessionmaker() as sess:
            rows = await sess.execute(
                select(Inventory).where(
                    Inventory.user_id == uid,
                    Inventory.item_id.in_(trash_ids),
                    Inventory.quantity > 0
                )
            )
            trash_list = rows.scalars().all()

        if not trash_list:
            return await ctx.send(embed=make_embed(
                desc="📭 Bạn chưa có rác nào trong túi.",
                color=nextcord.Color.greyple()
            ))

        eb = make_embed(title="🗑️ Túi rác của bạn", color=nextcord.Color.dark_grey())
        for inv in trash_list:
            name = next(name for id_, name in TRASH_ITEMS if id_ == inv.item_id)
            eb.add_field(name=name, value=f"x{inv.quantity}", inline=True)
        await ctx.send(embed=eb)

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        """Bắt và báo thời gian cooldown chung cho ShopCog."""
        if isinstance(error, commands.CommandOnCooldown):
            retry = int(error.retry_after)
            m, s = divmod(retry, 60)
            time_str = f"{m} phút {s} giây" if m else f"{s} giây"
            return await ctx.send(embed=make_embed(
                desc=f"⏳ Vui lòng chờ **{time_str}** trước khi dùng lại lệnh.",
                color=nextcord.Color.orange()
            ))
        raise error

def setup(bot: commands.Bot):
    bot.add_cog(ShopCog(bot))