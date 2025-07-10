# cogs/admin.py

import logging
import nextcord
from nextcord.ext import commands
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError

from shared.db import AsyncSession
from shared.models.user import User
from shared.models.inventory import Inventory
from shared.models.item import Item
from shared.models.shop import ShopItem
from shared.data.items import ITEMS
from shared.data.achievements import ACH_LIST
from shared.utils.embed import make_embed
from shared.utils.audit import admin_audit
from shared.utils.decorators import with_achievements

logger = logging.getLogger(__name__)

# Danh sách ID Dev / Owner bot
DEV_IDS = [1064509322228412416, 1327287076122787940]

class AdminCog(commands.Cog, name="Admin"):
    """🔧 Các lệnh quản trị (Dev only): clear, reset, add coin,…"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    # Áp dụng cho mọi lệnh trong Cog này
    def cog_check(self, ctx: commands.Context):
        return ctx.author.id in DEV_IDS

    @commands.command(name="adminclear")
    @admin_audit
    async def admin_clear(self, ctx: commands.Context, amount: int = 5):
        """🧹 Xóa nhanh <amount> tin nhắn (mặc định 5)."""
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(embed=make_embed(
            desc=f"🧹 Đã xóa {len(deleted)-1} tin nhắn.",
            color=nextcord.Color.green()
        ), delete_after=5)

    @commands.command(name="setlevel")
    @admin_audit
    async def set_level(self, ctx: commands.Context, member: nextcord.Member, level: int):
        bot = self.bot
        """📈 Chỉnh cấp độ user"""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.level = level
                session.add(user)
                await session.commit()
            await ctx.send(embed=make_embed(
                desc=f"📈 Set level **{level}** cho {member.mention}",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("setlevel failed")
        await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi set level", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="resetlevelall")
    @admin_audit
    async def reset_level_all(self, ctx: commands.Context):
        bot = self.bot
        """🔄 Reset XP, Level, Voice & Streak cho tất cả user."""
        try:
            async with bot.sessionmaker() as session:
                await session.execute(
                    update(User)
                    .values(xp=0, level=1, voice_time=0, streak=0)
                )
                await session.commit()
            await ctx.send(embed=make_embed(
                desc="🔄 Đã reset hệ thống Level cho tất cả.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("resetlevelall failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi reset all.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="resetlevel")
    @admin_audit
    async def reset_level(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """🔄 Reset XP, Level, Voice & Streak cho cá nhân."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.xp = 0
                user.level = 1
                user.voice_time = 0
                user.streak = 0
                session.add(user)
                await session.commit()

            # Unlock achievement adminreset
            ach = self.bot.get_cog("Achievement")
            if ach:
                await ach.unlock(uid, "adminreset")

            await ctx.send(embed=make_embed(
                desc=f"🔄 Đã reset Level cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)

        except SQLAlchemyError:
            logger.exception("resetlevel failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi reset user.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="additem")
    async def cmd_additem(self, ctx: commands.Context, member: nextcord.Member, item_id: str, quantity: int = 1):
        bot = self.bot
        """🎁 Cấp item cho người chơi (chỉ dành cho dev)."""

        if ctx.author.id not in DEV_IDS:
            return await ctx.send(embed=make_embed(
                desc="❌ Bạn không có quyền sử dụng lệnh này.",
                color=nextcord.Color.red()
            ))

        uid = member.id
        async with bot.sessionmaker() as session:
            q = await session.execute(
                select(Inventory).where(Inventory.user_id == uid, Inventory.item_id == item_id)
            )
            inv = q.scalar()

            if inv:
                inv.quantity += quantity
            else:
                session.add(Inventory(user_id=uid, item_id=item_id, quantity=quantity))

            await session.commit()

        await ctx.send(embed=make_embed(
            desc=f"✅ Đã cấp `{item_id}` ×{quantity} cho `{member.display_name}`.",
            color=nextcord.Color.green()
        ))


    @commands.command(name="addstreak")
    @admin_audit
    async def add_streak(self, ctx: commands.Context, member: nextcord.Member, days: int):
        bot = self.bot
        """➕ Cộng ngày streak cho user."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.streak += days
                session.add(user)
                await session.commit()
            await ctx.send(embed=make_embed(
                desc=f"✅ Đã cộng **{days}** ngày streak cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("addstreak failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi cộng streak.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="resetstreak")
    @admin_audit
    async def reset_streak(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """🔄 Reset streak về 0."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid)
                if user:
                    user.streak = 0
                    await session.commit()
            await ctx.send(embed=make_embed(
                desc=f"🔄 Đã reset streak cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("resetstreak failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi reset streak.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="addvoicetime")
    @admin_audit
    async def add_voice_time(self, ctx: commands.Context, member: nextcord.Member, hours: float):
        bot = self.bot
        """➕ Cộng voice_time (giờ)."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.voice_time += hours
                session.add(user)
                await session.commit()
            await ctx.send(embed=make_embed(
                desc=f"✅ Đã cộng **{hours:.2f}h** voice cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("addvoicetime failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi cộng voice time.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="resetvoicetime")
    @admin_audit
    async def reset_voice_time(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """🔄 Reset voice_time về 0."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid)
                if user:
                    user.voice_time = 0
                    await session.commit()
            await ctx.send(embed=make_embed(
                desc=f"🔄 Đã reset voice time cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("resetvoicetime failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi reset voice time.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="giveach")
    @admin_audit
    async def give_achievement(self, ctx: commands.Context, member: nextcord.Member, key: str):
        """🎖️ Award badge thủ công cho user."""
        try:
            from shared.utils.achievement import award
            success = await award(self.bot, member.id, key)
            if not success:
                return await ctx.send(embed=make_embed(
                    desc=f"❌ Không thể award badge `{key}`",
                    color=nextcord.Color.red()
                ), delete_after=5)
            await ctx.send(embed=make_embed(
                desc=f"🎖️ Đã award `{key}` cho {member.mention}",
                color=nextcord.Color.gold()
            ), delete_after=5)
        except Exception:
            logger.exception("giveach failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi award badge", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="showach")
    @admin_audit
    async def show_achievements(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """📜 Xem danh sách badge của người chơi."""
        uid = member.id
        try:
            from shared.models.achievement import UserAchievement
            from shared.models.achievement import Achievement as AchModel
            from sqlalchemy import select

            async with bot.sessionmaker() as session:
                rows = await session.execute(
                    select(AchModel.name, UserAchievement.unlocked_at)
                    .join(UserAchievement, AchModel.key == UserAchievement.ach_key)
                    .where(UserAchievement.user_id == uid)
                    .order_by(UserAchievement.unlocked_at)
                )
                data = rows.all()

            if not data:
                return await ctx.send(embed=make_embed(
                    desc=f"📭 {member.mention} chưa có badge nào.",
                    color=nextcord.Color.dark_gray()
                ), delete_after=7)

            eb = make_embed(
                title=f"🏅 Badges đã mở của {member.display_name}",
                color=nextcord.Color.gold()
            )
            for name, ts in data:
                eb.add_field(name=name, value=f"<t:{ts}:R>", inline=False)

            await ctx.send(embed=eb)

        except Exception:
            logger.exception("showach failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi xem badge.", color=nextcord.Color.red()
            ), delete_after=6)

    @commands.command(name="addcoin")
    @with_achievements("adminboost")
    @admin_audit
    async def add_coin(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        bot = self.bot
        """➕ Cộng coin vào ví."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.wallet += amount
                session.add(user)
                await session.commit()
            # Unlock adminboost achievement
            ach = self.bot.get_cog("Achievement")
            if ach:
                await ach.unlock(uid, "adminboost")

            await ctx.send(embed=make_embed(
                desc=f"✅ Đã cộng **{amount} 🪙** cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("addcoin failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi cộng coin.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="resetcoin")
    @with_achievements("adminreset")
    @admin_audit
    async def reset_coin(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """🔄 Reset ví về 0."""
        uid = member.id
        try:
            async with bot.sessionmaker() as session:
                user = await session.get(User, uid)
                if user:
                    user.wallet = 0
                    await session.commit()
            # Unlock adminreset achievement
            ach = self.bot.get_cog("Achievement")
            if ach:
                await ach.unlock(uid, "adminreset")

            await ctx.send(embed=make_embed(
                desc=f"🔄 Đã reset coin cho {member.mention}.",
                color=nextcord.Color.green()
            ), delete_after=5)
        except SQLAlchemyError:
            logger.exception("resetcoin failed")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi reset coin.", color=nextcord.Color.red()
            ), delete_after=5)

    @commands.command(name="seeditems")
    async def cmd_seeditems(self, ctx: commands.Context):
        """
        🧰 Seed toàn bộ item thường, cá, và rác vào bảng items.
        In log chi tiết theo từng nhóm.
        """
        if ctx.author.id not in DEV_IDS:
            return await ctx.send("⛔ Bạn không có quyền dùng lệnh này.")

        from shared.data.fish import FISH_ITEMS, TRASH_ITEMS
        from shared.data.items import ITEMS  # hoặc file đang chứa ITEMS của bạn

        def price_by_rarity(r: str) -> int:
            return {
                "Common": 1, "Uncommon": 3, "Rare": 7,
                "Epic": 15, "Legendary": 50
            }.get(r, 1)

        async with self.bot.sessionmaker() as sess:
            rows = await sess.execute(select(Item.id))
            existing_ids = set(row[0] for row in rows)

            added_common = []
            added_fish = []
            added_trash = []

            # 🎁 ITEMS thường
            for item in ITEMS:
                item_id = item["key"]
                if item_id in existing_ids:
                    print(f"[skip] {item_id} đã có.")
                    continue
                sess.add(Item(
                    id=item_id,
                    name=item.get("name", ""),
                    price=item.get("price", 0),
                    emoji=item.get("emoji", ""),
                    limit=item.get("limit", 1),
                    rarity=item.get("rarity", "Common"),
                    category=item.get("category", "misc"),
                    description=item.get("description", "")
                ))
                added_common.append(item_id)
                print(f"[+] Added item: {item_id} — {item['name']}")

            # 🐟 FISH_ITEMS
            for fid, name, rarity in FISH_ITEMS:
                if fid in existing_ids:
                    print(f"[skip] {fid} đã có.")
                    continue
                sess.add(Item(
                    id=fid,
                    name=name,
                    price=price_by_rarity(rarity),
                    emoji="🐟",
                    limit=None,
                    rarity=rarity,
                    category="fish",
                    description=f"Một con cá ({rarity}) câu được."
                ))
                added_fish.append(fid)
                print(f"[+] Added fish: {fid} — {name}")

            # 🗑️ TRASH_ITEMS
            for tid, name in TRASH_ITEMS:
                if tid in existing_ids:
                    print(f"[skip] {tid} đã có.")
                    continue
                sess.add(Item(
                    id=tid,
                    name=name,
                    price=0,
                    emoji="🗑️",
                    limit=None,
                    rarity="Trash",
                    category="trash",
                    description="Một món rác từ hồ câu."
                ))
                added_trash.append(tid)
                print(f"[+] Added trash: {tid} — {name}")

            await sess.commit()

        total = len(added_common) + len(added_fish) + len(added_trash)
        await ctx.send(embed=make_embed(
            desc=(
                f"✅ Seed thành công `{total}` item mới!\n"
                f"- 🎁 Item thường: `{len(added_common)}`\n"
                f"- 🐟 Cá: `{len(added_fish)}`\n"
                f"- 🗑️ Rác: `{len(added_trash)}`"
            ),
            color=nextcord.Color.green()
        ))

    @commands.command(name="unlockallach")
    async def unlock_all_achievements(self, ctx: commands.Context):
        """🛠️ Dev-only: Unlock toàn bộ badge cho người dùng."""
        if ctx.author.id not in DEV_IDS:
            return await ctx.send("⛔ Lệnh này chỉ dành cho dev.")

        from shared.utils.achievement import award
        unlocked = []
        for key, *_ in ACH_LIST:
            if await award(self.bot, ctx.author.id, key, announce=False):
                unlocked.append(key)

        await ctx.send(embed=make_embed(
            desc=f"✅ Đã mở {len(unlocked)} badge mới.",
            color=nextcord.Color.green()
        ))

    @commands.command(name="addpraypoint")
    async def add_pray_point(self, ctx: commands.Context, member: nextcord.Member = None, amount: int = 1):
        """🙏 Dev-only: +N prayer_progress cho user chỉ định (mặc định là bạn)."""
        if ctx.author.id not in DEV_IDS:
            return await ctx.send("⛔ Lệnh này chỉ dành cho dev.")
        
        target = member or ctx.author

        async with self.bot.sessionmaker() as s:
            user = await s.get(User, target.id)
            user.prayer_progress = (user.prayer_progress or 0) + amount
            await s.commit()

        await ctx.send(embed=make_embed(
            desc=f"🌟 +{amount} prayer_progress cho **{target.display_name}** → Tổng: `{user.prayer_progress}`",
            color=nextcord.Color.green()
        ))

    @commands.command(name="addtrustpoint")
    async def add_trust_point(self, ctx: commands.Context, member: nextcord.Member = None, amount: int = 1):
        """🤝 Dev-only: +N trust_points cho user chỉ định (mặc định là bạn)."""
        if ctx.author.id not in DEV_IDS:
            return await ctx.send("⛔ Lệnh này chỉ dành cho dev.")
        
        target = member or ctx.author

        async with self.bot.sessionmaker() as s:
            user = await s.get(User, target.id)
            user.trust_points = (user.trust_points or 0) + amount
            await s.commit()

        await ctx.send(embed=make_embed(
            desc=f"🤝 +{amount} trust_points cho **{target.display_name}** → Tổng: `{user.trust_points}`",
            color=nextcord.Color.green()
        ))


def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))