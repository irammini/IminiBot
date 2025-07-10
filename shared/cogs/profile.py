# cogs/profile.py

import re
import nextcord
from nextcord.ext import commands
from sqlalchemy import select, update, func
from shared.db import AsyncSession
from shared.models.user import User
from shared.models.inventory import Inventory
from shared.models.achievement import Achievement as AchModel
from shared.data.fish import FISH_ITEMS
from shared.utils.embed import make_embed
from shared.utils.achievement import award

# cấu hình frame tự động theo level
FRAMES = {
    "bronze":   {"emoji": "🟦", "name": "Bronze Frame",   "min_level": 25},
    "silver":   {"emoji": "🟨", "name": "Silver Frame",   "min_level": 50},
    "gold":     {"emoji": "🟥", "name": "Gold Frame",     "min_level": 75},
    "platinum": {"emoji": "🟪", "name": "Platinum Frame", "min_level": 100},
    "mythic":   {"emoji": "🌈", "name": "Mythic Frame",   "min_level": 150},
}

HEX_COLOR_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}){1,2}$")

# item keys
ITEM_PROFILE_EMOJI   = "profile_emoji"
ITEM_FRAME_OVERRIDE  = "frame_override"
ITEM_TITLE_CUSTOMIZE = "title_customizer"
ITEM_COLOR_ACCENT    = "color_accent"
ITEM_PROFILE_THEME   = "profile_theme"

class ProfileCog(commands.Cog):
    """📋 Quản lý hồ sơ: text embed + kết nối profilecard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    async def _get_user(self, uid: int) -> User | None:
        async with self.bot.sessionmaker() as s:
            return await s.get(User, uid)

    async def _sum_fish(self, uid: int) -> int:
        fish_ids = [fid for fid, *_ in FISH_ITEMS]  # Lấy toàn bộ fish_id

        async with self.bot.sessionmaker() as s:
            q = await s.execute(
                select(func.sum(Inventory.quantity)).where(
                    Inventory.user_id == uid,
                    Inventory.item_id.in_(fish_ids)
                )
            )
            return q.scalar() or 0

    async def _has_item(self, uid: int, item_key: str) -> bool:
        async with self.bot.sessionmaker() as s:
            q = await s.execute(
                select(Inventory.quantity)
                .where(Inventory.user_id == uid,
                       Inventory.item_id == item_key)
            )
            return (q.scalar() or 0) > 0

    async def _update_user(self, uid: int, **fields):
        async with self.bot.sessionmaker() as s:
            await s.execute(update(User).where(User.id == uid).values(**fields))
            await s.commit()

    def get_effective_frame(self, user: User) -> str:
        """Nếu user.profile_frame chưa set hoặc invalid, chọn frame theo level."""
        if user.profile_frame in FRAMES:
            return user.profile_frame
        for key, cfg in sorted(FRAMES.items(), key=lambda x: x[1]["min_level"], reverse=True):
            if user.level >= cfg["min_level"]:
                return key
        return "bronze"

    @commands.command(name="profile")
    async def cmd_profile(self, ctx: commands.Context, member: nextcord.Member = None):
        """📋 Hiển thị hồ sơ text + auto-award badges."""
        target = member or ctx.author
        user = await self._get_user(target.id)
        if not user:
            return await ctx.send(embed=make_embed(desc="❌ Không tìm thấy hồ sơ.", color=nextcord.Color.red()))

        total_fish = await self._sum_fish(target.id)

        flex_text = "—"
        if user.flex_key:
            async with self.bot.sessionmaker() as s:
                badge = await s.get(AchModel, user.flex_key)
            flex_text = badge.name if badge else "—"

        frame_key = self.get_effective_frame(user)
        frame_cfg = FRAMES[frame_key]
        frame_text = f"{frame_cfg['emoji']} {frame_cfg['name']}"

        # ⭐ Auto award badge
        for key, lvl in [("lv5",5),("lv10",10),("lv25",25),("lv50",50)]:
            if user.level >= lvl: await award(self.bot, user.id, key)
        for key, days in [("daily",1),("daily3",3),("daily7",7),("daily14",14),("daily365",365),("daily1000",1000)]:
            if user.streak >= days: await award(self.bot, user.id, key)
        if (user.voice_time or 0) >= 60: await award(self.bot, user.id, "voice1h")
        await award(self.bot, user.id, "profile_viewer")

        # 🌈 Màu sắc embed
        ec = nextcord.Color.teal()
        if user.accent_color and HEX_COLOR_RE.match(user.accent_color):
            try: ec = nextcord.Color.from_str(user.accent_color)
            except: pass

        # 🎨 Tiêu đề
        emoji = user.profile_emoji or ""
        title_suffix = f" • {user.custom_title}" if user.custom_title else ""
        eb = make_embed(
            title=f"📋 Hồ sơ: {target.display_name} {emoji}{title_suffix}",
            color=ec
        )

        # 🔢 XP nâng cấp
        def target_xp(lv): return 50 + lv * 25
        xp_goal = target_xp(user.level)
        progress_pct = min(user.xp / xp_goal * 100, 100)
        xp_display = f"{user.xp:,} / {xp_goal:,} XP ({progress_pct:.0f}%)"

        # 🧩 Các field thông tin
        eb.add_field(name="💰 Ví",            value=f"{user.wallet:,} xu",                inline=True)
        eb.add_field(
        name="🏦 Ngân hàng",
        value=f"{user.bank_balance:,} / {user.bank_limit:,} xu",
        inline=True
        )
        eb.add_field(name="💳 Nợ",            value=f"{(user.debt or 0):,} xu",           inline=True)
        eb.add_field(name="🏷️ Level",         value=str(user.level),                      inline=True)
        eb.add_field(name="⭐ XP",             value=xp_display,                           inline=True)
        eb.add_field(name="🔥 Streak",        value=f"{user.streak:,} ngày",              inline=True)
        if user.voice_time and user.voice_time >= 1:
            eb.add_field(name="🎤 Voice time", value=f"{user.voice_time:.2f} phút",        inline=True)
        eb.add_field(name="🐟 Tổng cá",       value=f"{total_fish:,}",                    inline=True)
        eb.add_field(name="🕯️ Pray Points",   value=f"{user.prayer_progress or 0}",       inline=True)
        eb.add_field(name="🤝 Trust Points",  value=f"{user.trust_points or 0}",          inline=True)

        eb.add_field(name="🎖️ Flex Badge",   value=flex_text,                             inline=False)
        eb.add_field(name="🎨 Frame (BETA)",  value=frame_text,                            inline=True)
        eb.add_field(name="🖼️ Ảnh hồ sơ (BETA)", value="Gõ `!previewcard` để xem bản banner PNG", inline=False)

        if target.avatar:
            eb.set_thumbnail(url=target.avatar.url)
        eb.set_footer(text="IminiBot • Profile")

        await ctx.send(embed=eb)

    # --- Các lệnh set... đều kèm preview ảnh ---
    @commands.command(name="setemoji")
    async def cmd_setemoji(self, ctx, emoji: str):
        uid = ctx.author.id
        if not await self._has_item(uid, ITEM_PROFILE_EMOJI):
            return await ctx.send(embed=make_embed(desc="❌ Bạn không có item Profile Emoji.", color=nextcord.Color.red()))
        await self._update_user(uid, profile_emoji=emoji)
        await ctx.send(embed=make_embed(desc=f"✅ Đã đặt emoji `{emoji}`.", color=nextcord.Color.green()))
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

    @commands.command(name="setframe")
    async def cmd_setframe(self, ctx, key: str):
        uid = ctx.author.id
        key = key.lower()
        if key not in FRAMES:
            return await ctx.send(embed=make_embed(desc="❌ Key frame không hợp lệ.", color=nextcord.Color.red()))
        user = await self._get_user(uid)
        has_item = await self._has_item(uid, ITEM_FRAME_OVERRIDE)
        if user.level < FRAMES[key]["min_level"] and not has_item:
            return await ctx.send(embed=make_embed(
                desc=f"❌ Cần level ≥{FRAMES[key]['min_level']} hoặc item Frame Override.",
                color=nextcord.Color.red()))
        await self._update_user(uid, profile_frame=key)
        await ctx.send(embed=make_embed(desc=f"✅ Đã chọn frame `{key}`.", color=nextcord.Color.green()))
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

    @commands.command(name="settitle")
    async def cmd_settitle(self, ctx, *, title: str):
        uid = ctx.author.id
        if not await self._has_item(uid, ITEM_TITLE_CUSTOMIZE):
            return await ctx.send(embed=make_embed(desc="❌ Bạn không có item Custom Title.", color=nextcord.Color.red()))
        await self._update_user(uid, custom_title=title)
        await ctx.send(embed=make_embed(desc=f"✅ Đã đặt title `{title}`.", color=nextcord.Color.green()))
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

    @commands.command(name="setcolor")
    async def cmd_setcolor(self, ctx, hex_color: str):
        uid = ctx.author.id
        if not await self._has_item(uid, ITEM_COLOR_ACCENT):
            return await ctx.send(embed=make_embed(desc="❌ Bạn không có item Color Accent.", color=nextcord.Color.red()))
        if not HEX_COLOR_RE.match(hex_color):
            return await ctx.send(embed=make_embed(desc="❌ Mã màu không hợp lệ. Ví dụ: #ffcc00", color=nextcord.Color.red()))
        await self._update_user(uid, accent_color=hex_color)
        await ctx.send(embed=make_embed(desc=f"✅ Đã đặt accent color `{hex_color}`.", color=nextcord.Color.green()))
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

    @commands.command(name="settheme")
    async def cmd_settheme(self, ctx, theme: str):
        uid = ctx.author.id
        if not await self._has_item(uid, ITEM_PROFILE_THEME):
            return await ctx.send(embed=make_embed(desc="❌ Bạn không có item Profile Theme.", color=nextcord.Color.red()))
        await self._update_user(uid, profile_theme=theme)
        await ctx.send(embed=make_embed(desc=f"✅ Đã đặt theme `{theme}`.", color=nextcord.Color.green()))
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

    @commands.command(name="resetprofile")
    async def cmd_resetprofile(self, ctx):
        uid = ctx.author.id
        await self._update_user(uid,
            profile_emoji=None, profile_frame=None,
            custom_title=None, accent_color=None,
            profile_theme=None
        )
        await ctx.send(embed=make_embed(desc="✅ Đã reset profile về mặc định.", color=nextcord.Color.green()))
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

    @commands.command(name="previewcombo")
    async def cmd_previewcombo(self, ctx):
        """🔄 Gửi cả embed Profile và ảnh profilecard."""
        # gọi text-profile
        await self.cmd_profile(ctx)
        # gọi ảnh-profilecard
        await self.bot.get_cog("ProfileCardCog").cmd_previewcard(ctx)

def setup(bot: commands.Bot):
    bot.add_cog(ProfileCog(bot))