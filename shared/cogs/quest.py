# cogs/quest.py

import time
import datetime
import random
import logging

import nextcord
from nextcord.ext import commands
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from shared.db import AsyncSession
from shared.models.user import User
from shared.models.quest import UserQuest
from shared.data.quests import DAILY_POOL, WEEKLY_POOL
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements

# module-level logger
logger = logging.getLogger(__name__)

class QuestCog(commands.Cog):
    """📜 Quests: xem và hoàn thành quest daily/weekly."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        uid = message.author.id
        async with self.bot.sessionmaker() as session:
            # Lấy quest daily_chat chưa hoàn thành
            row = await session.execute(
                select(UserQuest).where(
                    UserQuest.user_id == uid,
                    UserQuest.quest_key == "daily_chat",
                    UserQuest.period == "daily",
                    UserQuest.completed == False
                )
            )
            uq: UserQuest | None = row.scalar_one_or_none()
            if uq:
                uq.progress += 1
                if uq.progress >= uq.req:
                    uq.completed = True
                    uq.completed_at = int(time.time())
                session.add(uq)
                await session.commit()

    def _today_midnight(self) -> datetime.datetime:
        now = datetime.datetime.utcnow()
        return datetime.datetime(now.year, now.month, now.day)

    def _next_midnight(self) -> datetime.datetime:
        return self._today_midnight() + datetime.timedelta(days=1)

    async def _ensure_quests(self, uid: int, period: str) -> list[UserQuest]:
        now_ts = int(time.time())

        # Xác định pool và expires
        if period == "daily":
            expires_ts = int(self._next_midnight().timestamp())
            pool = DAILY_POOL
        else:
            expires_ts = int((self._today_midnight() + datetime.timedelta(days=7)).timestamp())
            pool = WEEKLY_POOL

        # Debug thông tin đầu vào
        logger.debug(f"[quest] ensure_quests start uid={uid}, period={period}, pool_size={len(pool)}")

        if len(pool) < 3:
            # quá ít quest để chọn
            raise ValueError(f"Quest pool '{period}' chỉ có {len(pool)} mục, cần ≥3.")

        async with self.bot.sessionmaker() as session:
            try:
                # Xóa quest expired
                await session.execute(
                    delete(UserQuest).where(
                        UserQuest.user_id == uid,
                        UserQuest.period == period,
                        UserQuest.expires_at < now_ts
                    )
                )
                # Lấy existing
                rows = await session.execute(
                    select(UserQuest).where(
                        UserQuest.user_id == uid,
                        UserQuest.period == period,
                        UserQuest.expires_at > now_ts
                    )
                )
                existing = rows.scalars().all()
                logger.debug(f"[quest] found existing quests: {len(existing)}")

                if len(existing) >= 3:
                    return existing

                # Xóa toàn bộ và commit để tránh unique constraint
                await session.execute(
                    delete(UserQuest).where(
                        UserQuest.user_id == uid,
                        UserQuest.period == period
                    )
                )
                await session.commit()

                # Seed 3 quest mới
                picks = random.sample(pool, k=3)
                logger.debug(f"[quest] seeding quests: {[q['key'] for q in picks]}")
                for q in picks:
                    uq = UserQuest(
                        user_id     = uid,
                        quest_key   = q["key"],
                        period      = period,
                        progress    = 0,
                        req         = q["req"],
                        reward_coin = q.get("reward_coin", 0),
                        reward_xp   = q.get("reward_xp", 0),
                        completed   = False,
                        created_at  = now_ts,
                        expires_at  = expires_ts
                    )
                    session.add(uq)

                await session.commit()

                # Lấy lại sau seed
                rows = await session.execute(
                    select(UserQuest).where(
                        UserQuest.user_id == uid,
                        UserQuest.period == period,
                        UserQuest.expires_at > now_ts
                    )
                )
                new_list = rows.scalars().all()
                logger.debug(f"[quest] total quests after seed: {len(new_list)}")
                return new_list

            except SQLAlchemyError as db_err:
                logger.exception("[quest] database error in _ensure_quests")
                raise

    @commands.command(name="quest")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_quest(self, ctx: commands.Context, period: str = None):
        """
        📜 !quest [daily|weekly] — xem danh sách quest.
        Cooldown 60s.
        """
        uid = ctx.author.id
        periods = ["daily", "weekly"] if not period else [period.lower()]
        embed = make_embed(title="📜 Your Quests", color=nextcord.Color.teal())

        for p in periods:
            if p not in ("daily", "weekly"):
                embed_err = make_embed(
                    desc=f"⚠️ Unknown period '{p}'. Use 'daily' or 'weekly'.",
                    color=nextcord.Color.orange()
                )
                await ctx.send(embed=embed_err)
                continue

            try:
                qs = await self._ensure_quests(uid, p)
            except ValueError as ve:
                # lỗi pool quá ít
                logger.warning(f"[quest] value error: {ve}")
                await ctx.send(embed=make_embed(desc=str(ve), color=nextcord.Color.red()))
                return
            except Exception:
                logger.exception("[quest] Failed to create or fetch quests")
                await ctx.send(embed=make_embed(
                    desc="❌ Lỗi khi tạo quest. Hãy thử lại sau.",
                    color=nextcord.Color.red()
                ))
                return

            # Hiển thị quest
            title = "🗓️ Daily Quests" if p == "daily" else "📅 Weekly Quests"
            pool  = DAILY_POOL if p == "daily" else WEEKLY_POOL
            lines = []
            for uq in qs:
                status = "✅" if uq.completed else f"{uq.progress}/{uq.req}"
                # tìm text dựa trên quest_key
                text = next((q["text"] for q in pool if q["key"] == uq.quest_key), uq.quest_key)
                lines.append(f"`{uq.quest_key}` {text} — **{status}**")

            expires_str = datetime.datetime.utcfromtimestamp(qs[0].expires_at)\
                               .strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(
                name=f"{title} (expires: {expires_str})",
                value="\n".join(lines) if lines else "Không có quest.",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="complete")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @with_achievements("complete")
    async def cmd_complete(self, ctx: commands.Context, key: str):
        bot = self.bot
        """
        ✅ !complete <key> — hoàn thành quest.
        Cooldown 30s. Thực thi khi progress ≥ req.
        """
        uid = ctx.author.id
        now = int(time.time())

        async with bot.sessionmaker() as session:
            # Lấy quest tồn tại
            row = await session.execute(
                select(UserQuest).where(
                    UserQuest.user_id == uid,
                    UserQuest.quest_key == key,
                    UserQuest.expires_at > now
                )
            )
            uq: UserQuest | None = row.scalar_one_or_none()

            if not uq:
                return await ctx.send(embed=make_embed(
                    desc="❌ Quest không tồn tại hoặc đã hết hạn.",
                    color=nextcord.Color.red()
                ))
            if uq.completed:
                return await ctx.send(embed=make_embed(
                    desc="⚠️ Quest đã hoàn thành.",
                    color=nextcord.Color.orange()
                ))
            if uq.progress < uq.req:
                return await ctx.send(embed=make_embed(
                    desc=f"❌ Bạn chưa hoàn thành đủ yêu cầu ({uq.progress}/{uq.req}).",
                    color=nextcord.Color.orange()
                ))

            # Hoàn thành quest và cấp thưởng
            try:
                uq.completed    = True
                uq.completed_at = now

                user: User = await session.get(User, uid)
                user.wallet = (user.wallet or 0) + (uq.reward_coin or 0)
                user.xp     = (user.xp or 0)     + (uq.reward_xp or 0)

                session.add_all([uq, user])
                await session.commit()

            except SQLAlchemyError:
                logger.exception("[quest] Error committing quest completion")
                return await ctx.send(embed=make_embed(
                    desc="❌ Lỗi hệ thống, vui lòng thử lại sau.",
                    color=nextcord.Color.red()
                ))

        parts = [f"🎉 Hoàn thành **{key}**!"]
        if uq.reward_coin:
            parts.append(f"+{uq.reward_coin} 🪙")
        if uq.reward_xp:
            parts.append(f"+{uq.reward_xp} XP")

        await ctx.send(embed=make_embed(
            desc=" ".join(parts),
            color=nextcord.Color.green()
        ))

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        """Bắt cooldown & relay các lỗi khác."""
        if isinstance(error, commands.CommandOnCooldown):
            retry = int(error.retry_after)
            m, s = divmod(retry, 60)
            time_str = f"{m} phút {s} giây" if m else f"{s} giây"
            return await ctx.send(embed=make_embed(
                desc=f"⏳ Vui lòng chờ **{time_str}** trước khi dùng lại lệnh này.",
                color=nextcord.Color.orange()
            ))
        # các lỗi khác pass lên global handler
        raise error

def setup(bot: commands.Bot):
    bot.add_cog(QuestCog(bot))