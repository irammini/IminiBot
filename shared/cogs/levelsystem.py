# cogs/levelsystem.py

import time
import math
import logging
import datetime

import nextcord
from nextcord.ext import commands
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from shared.models.achievement import UserAchievement

from shared.db import AsyncSession
from shared.models.user import User
from shared.utils.embed import make_embed

logger = logging.getLogger(__name__)
LEVEL_UP_CHANNEL_ID = 0  # ▶️ Thay ID channel thông báo level up

class LevelSystemCog(commands.Cog):
    """📈 Hệ thống Level, XP, Voice, Streak & Flex Badge"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_msg_ts: dict[int, float] = {}
        self.voice_start: dict[int, float] = {}

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot or not message.guild:
            return

        uid = message.author.id
        now = time.time()

        # 60s cooldown kiếm XP
        if now - self.last_msg_ts.get(uid, 0) < 60:
            return
        self.last_msg_ts[uid] = now

        try:
            async with self.bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.level = user.level or 1  # đảm bảo không None
                base = self.bot.config.get("xp_base", 100)
                power = self.bot.config.get("xp_power", 1.6)
                gain = math.floor(base * (user.level ** power))
                gain = min(gain, 150)  # không cho quá mạnh
                user.xp = (user.xp or 0) + gain

                # streak daily
                last_day = datetime.date.fromtimestamp(user.last_daily or 0)
                today = datetime.date.today()
                if today != last_day:
                    user.streak = (user.streak or 0) + 1
                    user.last_daily = int(now)

                # level up
                req = round(base * (user.level ** power))
                if user.xp >= req and user.level < 100:
                    user.xp -= req
                    user.level += 1
                    await session.commit()
                    await self._announce_level_up(message.author, user.level)
                else:
                    await session.commit()
        except SQLAlchemyError:
            logger.exception("LevelSystem on_message DB error")

        # check achievement auto
        ach = self.bot.get_cog("Achievement")
        if ach:
            await ach.check_unlock(uid)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or not member.guild:
            return

        uid = member.id
        now = time.time()

        # join
        if after.channel and not before.channel:
            self.voice_start[uid] = now
            return

        # leave
        if before.channel and not after.channel and uid in self.voice_start:
            start = self.voice_start.pop(uid)
            hours = (now - start) / 3600

            try:
                async with self.bot.sessionmaker() as session:
                    user = await session.get(User, uid) or User(id=uid)
                    user.voice_time = (user.voice_time or 0) + hours
                    session.add(user)
                    await session.commit()
            except SQLAlchemyError:
                logger.exception("LevelSystem on_voice DB error")

            # milestone voice
            await self._handle_voice_milestone(member, (user.voice_time or 0))
            # check achievement auto
            ach = self.bot.get_cog("Achievement")
            if ach:
                await ach.check_unlock(uid)

    async def _announce_level_up(self, member: nextcord.Member, new_level: int):
        ch = self.bot.get_channel(self.bot.config.get("levelup_channel", LEVEL_UP_CHANNEL_ID))
        embed = make_embed(
            title="🎉 Level Up!",
            desc=f"{member.mention} đã lên **Level {new_level}**",
            color=nextcord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        if ch:
            await ch.send(embed=embed)

        # tự động gán role nếu cần (bạn cấu hình roles_map)
        roles_map = {
            5: "Chatter I", 10: "Chatter II", 20: "Chatter III",
            30: "Chatter IV", 50: "Chatter V", 75: "Chatter VI", 100: "Chatter VII"
        }
        if new_level in roles_map:
            role = nextcord.utils.get(member.guild.roles, name=roles_map[new_level])
            if role:
                await member.add_roles(role)

    async def _handle_voice_milestone(self, member: nextcord.Member, voice_time: float):
        """Xử lý milestone voice time, thông báo và gán role nếu cần"""
        milestones = {
            10: "Voice Chatter I",
            50: "Voice Chatter II",
            100: "Voice Chatter III",
            200: "Voice Chatter IV",
            500: "Voice Chatter V"
        }
        ch = self.bot.get_channel(self.bot.config.get("levelup_channel", LEVEL_UP_CHANNEL_ID))
        for milestone, role_name in milestones.items():
            # Kiểm tra nếu voice_time vừa đạt milestone (ví dụ: từ dưới milestone lên >= milestone)
            # Để tránh spam, ta cần kiểm tra user đã có role chưa
            if voice_time >= milestone:
                role = nextcord.utils.get(member.guild.roles, name=role_name)
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                        if ch:
                            embed = make_embed(
                                title="🎤 Voice Milestone!",
                                desc=f"{member.mention} đã đạt mốc **{milestone} giờ** trong voice và được nhận role **{role_name}**!",
                                color=nextcord.Color.blue(),
                                timestamp=datetime.datetime.utcnow()
                            )
                            await ch.send(embed=embed)
                    except Exception as e:
                        logger.error(f"Lỗi khi gán role milestone voice: {e}")
                    break

    @commands.command(name="setflex")
    async def set_flex(self, ctx: commands.Context, ach_key: str):
        bot = self.bot
        """🎖️ !setflex <achievement_key> — chọn Flex Badge hiển thị."""
        uid = ctx.author.id
        try:
            # Kiểm tra user đã mở badge chưa
            async with bot.sessionmaker() as session:
                result = await session.execute(
                    select(UserAchievement)
                    .where(UserAchievement.user_id == uid,
                           UserAchievement.ach_key == ach_key)
                )
                exists = result.scalar_one_or_none() is not None

            if not exists:
                return await ctx.send(embed=make_embed(
                    desc="❌ Bạn chưa mở badge này hoặc nhập sai key.",
                    color=nextcord.Color.red()
                ), delete_after=6)

            # Lưu badge flex
            async with bot.sessionmaker() as session:
                await session.execute(
                    update(User).where(User.id == uid).values(flex_key=ach_key)
                )
                await session.commit()

            await ctx.send(embed=make_embed(
                desc=f"🎉 Đã đặt Flex Badge `{ach_key}`.",
                color=nextcord.Color.green()
            ))

        except Exception:
            logger.exception("❌ setflex exception")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi đặt Flex Badge.",
                color=nextcord.Color.red()
            ), delete_after=6)

    @commands.command(name="unsetflex")
    async def unset_flex(self, ctx: commands.Context):
        bot = self.bot
        """❌ !unsetflex — gỡ Flex Badge."""
        uid = ctx.author.id
        try:
            async with bot.sessionmaker() as session:
                await session.execute(
                    update(User).where(User.id == uid).values(flex_key=None)
                )
                await session.commit()
            await ctx.send(embed=make_embed(
                desc="✅ Đã gỡ Flex Badge.", color=nextcord.Color.green()
            ))
        except SQLAlchemyError:
            logger.exception("unsetflex DB error")
            await ctx.send(embed=make_embed(
                desc="❌ Lỗi khi gỡ flex badge.", color=nextcord.Color.red()
            ), delete_after=5)

def setup(bot: commands.Bot):
    bot.add_cog(LevelSystemCog(bot))