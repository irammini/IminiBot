# cogs/admin.py

import logging
import nextcord
from nextcord.ext import commands
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError

# --- Local Imports ---
from shared.models.user import User
from shared.models.inventory import Inventory
from shared.models.item import Item
from shared.models.achievement import UserAchievement, Achievement as AchModel
from shared.data.items import ITEMS
from shared.data.achievements import ACH_LIST
from shared.data.fish import FISH_ITEMS, TRASH_ITEMS
from shared.utils.embed import make_embed
from shared.utils.audit import admin_audit
from shared.utils.decorators import with_achievements
from shared.utils.achievement import award

logger = logging.getLogger(__name__)

# Danh sách ID Dev / Owner bot
DEV_IDS = [] # Thêm danh sách ID vào đây, VD: 123456789, 987654321

class AdminCog(commands.Cog, name="Admin"):
    """🔧 Các lệnh quản trị (Dev only): clear, reset, add coin,…"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Áp dụng cho mọi lệnh trong Cog này
    def cog_check(self, ctx: commands.Context):
        """Kiểm tra xem người dùng có phải là dev không."""
        if ctx.author.id not in DEV_IDS:
            raise commands.CheckFailure("⛔ Lệnh này chỉ dành cho dev.")
        return True

    async def handle_db_error(self, ctx: commands.Context, command_name: str, error: Exception):
        """Hàm trợ giúp xử lý lỗi database và ghi log."""
        logger.exception(f"Lỗi trong lệnh '{command_name}': {error}")
        await ctx.send(embed=make_embed(
            desc=f"❌ Đã xảy ra lỗi database khi thực thi lệnh `{command_name}`.",
            color=nextcord.Color.red()
        ), delete_after=10)

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
    async def set_level(self, ctx: commands.Context, level: int, member: nextcord.Member = None):
        """📈 Chỉnh cấp độ user. Mặc định là bạn nếu không chỉ định."""
        target = member or ctx.author
        if level < 1:
            return await ctx.send(embed=make_embed(desc="❌ Level phải lớn hơn hoặc bằng 1.", color=nextcord.Color.red()))
        try:
            async with self.bot.sessionmaker() as session:
                user = await session.get(User, target.id) or User(id=target.id)
                user.level = level
                session.add(user)
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"📈 Đã đặt level **{level}** cho {target.mention}.", color=nextcord.Color.green()))
            return
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "setlevel", e)

    @commands.command(name="resetlevelall")
    @admin_audit
    async def reset_level_all(self, ctx: commands.Context):
        """🔄 Reset XP, Level, Voice & Streak cho tất cả user."""
        try:
            async with self.bot.sessionmaker() as session:
                await session.execute(update(User).values(xp=0, level=1, voice_time=0, streak=0))
                await session.commit()
            await ctx.send(embed=make_embed(desc="🔄 Đã reset hệ thống Level cho tất cả.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "resetlevelall", e)

    @commands.command(name="resetlevel")
    @admin_audit
    async def reset_level(self, ctx: commands.Context, member: nextcord.Member = None):
        """🔄 Reset XP, Level, Voice & Streak. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                await session.execute(update(User).where(User.id == target.id).values(xp=0, level=1, voice_time=0, streak=0))
                await session.commit()
            await award(self.bot, target.id, "adminreset")
            await ctx.send(embed=make_embed(desc=f"� Đã reset Level cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "resetlevel", e)

    @commands.command(name="additem")
    @admin_audit
    async def cmd_additem(self, ctx: commands.Context, item_id: str, quantity: int = 1, member: nextcord.Member = None):
        """🎁 Cấp item cho người chơi. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                item_exists = await session.get(Item, item_id)
                if not item_exists:
                    return await ctx.send(embed=make_embed(desc=f"❌ Item ID `{item_id}` không tồn tại trong database.", color=nextcord.Color.red()))
                inv_item = await session.scalar(select(Inventory).where(Inventory.user_id == target.id, Inventory.item_id == item_id))
                if inv_item:
                    inv_item.quantity += quantity
                else:
                    session.add(Inventory(user_id=target.id, item_id=item_id, quantity=quantity))
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"✅ Đã cấp `{item_id}` ×{quantity} cho `{target.display_name}`.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "additem", e)

    @commands.command(name="addstreak")
    @admin_audit
    async def add_streak(self, ctx: commands.Context, days: int, member: nextcord.Member = None):
        """➕ Cộng ngày streak cho user. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                user = await session.get(User, target.id) or User(id=target.id)
                user.streak += days
                session.add(user)
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"✅ Đã cộng **{days}** ngày streak cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "addstreak", e)

    @commands.command(name="resetstreak")
    @admin_audit
    async def reset_streak(self, ctx: commands.Context, member: nextcord.Member = None):
        """🔄 Reset streak về 0. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                await session.execute(update(User).where(User.id == target.id).values(streak=0))
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"🔄 Đã reset streak cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "resetstreak", e)

    @commands.command(name="addvoicetime")
    @admin_audit
    async def add_voice_time(self, ctx: commands.Context, hours: float, member: nextcord.Member = None):
        """➕ Cộng voice_time (giờ). Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                user = await session.get(User, target.id) or User(id=target.id)
                user.voice_time += hours
                session.add(user)
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"✅ Đã cộng **{hours:.2f}h** voice cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "addvoicetime", e)

    @commands.command(name="resetvoicetime")
    @admin_audit
    async def reset_voice_time(self, ctx: commands.Context, member: nextcord.Member = None):
        """🔄 Reset voice_time về 0. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                await session.execute(update(User).where(User.id == target.id).values(voice_time=0))
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"🔄 Đã reset voice time cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "resetvoicetime", e)

    @commands.command(name="giveach")
    @admin_audit
    async def give_achievement(self, ctx: commands.Context, key: str, member: nextcord.Member = None):
        """🎖️ Award badge thủ công. Mặc định là bạn."""
        target = member or ctx.author
        try:
            success = await award(self.bot, target.id, key)
            if not success:
                return await ctx.send(embed=make_embed(desc=f"❌ Không thể award badge `{key}` (có thể đã có hoặc ID sai).", color=nextcord.Color.red()))
            await ctx.send(embed=make_embed(desc=f"🎖️ Đã award `{key}` cho {target.mention}.", color=nextcord.Color.gold()))
        except Exception as e:
            await self.handle_db_error(ctx, "giveach", e)

    @commands.command(name="showach")
    @admin_audit
    async def show_achievements(self, ctx: commands.Context, member: nextcord.Member = None):
        """📜 Xem danh sách badge. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                rows = await session.execute(
                    select(AchModel.name, UserAchievement.unlocked_at)
                    .join(UserAchievement, AchModel.key == UserAchievement.ach_key)
                    .where(UserAchievement.user_id == target.id).order_by(UserAchievement.unlocked_at)
                )
                data = rows.all()
            if not data:
                return await ctx.send(embed=make_embed(desc=f"📭 {target.mention} chưa có badge nào.", color=nextcord.Color.dark_gray()))
            eb = make_embed(title=f"🏅 Badges đã mở của {target.display_name}", color=nextcord.Color.gold())
            for name, ts in data:
                eb.add_field(name=name, value=f"<t:{int(ts)}:R>", inline=False)
            await ctx.send(embed=eb)
        except Exception as e:
            await self.handle_db_error(ctx, "showach", e)

    @commands.command(name="addcoin")
    @with_achievements("adminboost")
    @admin_audit
    async def add_coin(self, ctx: commands.Context, amount: int, member: nextcord.Member = None):
        """➕ Cộng coin vào ví. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                user = await session.get(User, target.id) or User(id=target.id)
                user.wallet += amount
                session.add(user)
                await session.commit()
            await award(self.bot, target.id, "adminboost")
            await ctx.send(embed=make_embed(desc=f"✅ Đã cộng **{amount:,} 🪙** cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "addcoin", e)

    @commands.command(name="resetcoin")
    @with_achievements("adminreset")
    @admin_audit
    async def reset_coin(self, ctx: commands.Context, member: nextcord.Member = None):
        """🔄 Reset ví về 0. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as session:
                await session.execute(update(User).where(User.id == target.id).values(wallet=0))
                await session.commit()
            await award(self.bot, target.id, "adminreset")
            await ctx.send(embed=make_embed(desc=f"🔄 Đã reset coin cho {target.mention}.", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "resetcoin", e)

    @commands.command(name="seeditems")
    async def cmd_seeditems(self, ctx: commands.Context):
        """
        🧰 Seed toàn bộ item thường, cá, và rác vào bảng items.
        In log chi tiết theo từng nhóm.
        """
        if ctx.author.id not in DEV_IDS:
            return await ctx.send("⛔ Bạn không có quyền dùng lệnh này.")

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
        """🛠️ Mở khóa toàn bộ badge cho chính bạn."""
        unlocked = []
        for key, *_ in ACH_LIST:
            if await award(self.bot, ctx.author.id, key, announce=False):
                unlocked.append(key)
        await ctx.send(embed=make_embed(desc=f"✅ Đã mở {len(unlocked)} badge mới.", color=nextcord.Color.green()))

    @commands.command(name="addpraypoint")
    async def add_pray_point(self, ctx: commands.Context, amount: int = 1, member: nextcord.Member = None):
        """🙏 +N prayer_progress. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as s:
                user = await s.get(User, target.id) or User(id=target.id)
                user.prayer_progress = (user.prayer_progress or 0) + amount
                s.add(user)
                await s.commit()
            await ctx.send(embed=make_embed(desc=f"🌟 +{amount} prayer_progress cho **{target.display_name}** → Tổng: `{user.prayer_progress}`", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "addpraypoint", e)

    @commands.command(name="addtrustpoint")
    async def add_trust_point(self, ctx: commands.Context, amount: int = 1, member: nextcord.Member = None):
        """🤝 +N trust_points. Mặc định là bạn."""
        target = member or ctx.author
        try:
            async with self.bot.sessionmaker() as s:
                user = await s.get(User, target.id) or User(id=target.id)
                user.trust_points = (user.trust_points or 0) + amount
                s.add(user)
                await s.commit()
            await ctx.send(embed=make_embed(desc=f"🤝 +{amount} trust_points cho **{target.display_name}** → Tổng: `{user.trust_points}`", color=nextcord.Color.green()))
        except SQLAlchemyError as e:
            await self.handle_db_error(ctx, "addtrustpoint", e)

def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))
    