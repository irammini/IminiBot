# cogs/economy.py

import time
import random

import nextcord
from nextcord.ext import commands

from shared.db import AsyncSession
from shared.models.user import User
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements

DAILY_CD = 86400
PRAY_CD = 3600

class EconomyCog(commands.Cog):
    """💰 Economy: beg, daily, pray, crime, steal, repay, give, deposit, withdraw."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    async def _get_user(self, uid: int) -> User:
        """Fetch or create a User record."""
        async with self.bot.sessionmaker() as session:
            user = await session.get(User, uid)
            if not user:
                user = User(id=uid)
                session.add(user)
                await session.commit()
            return user

    async def _save_user(self, user: User):
        """Persist changes to a User."""
        async with self.bot.sessionmaker() as session:
            session.add(user)
            await session.commit()

    @commands.command(name="beg")
    @commands.cooldown(1, 180, commands.BucketType.user)
    @with_achievements("beg")
    async def cmd_beg(self, ctx: commands.Context):
        """🙏 !beg — 50% chance nhận 25–150 xu."""
        user = await self._get_user(ctx.author.id)
        if random.random() < 0.5:
            amt = random.randint(25, 150)
            user.wallet = (user.wallet or 0) + amt
            await self._save_user(user)
            await ctx.send(embed=make_embed(
                desc=f"🪙 Bạn xin được **{amt:,}** xu!",
                color=nextcord.Color.green()
            ))
        else:
            await ctx.send(embed=make_embed(
                desc="😢 Xin không thành công.",
                color=nextcord.Color.red()
            ))

    @commands.command(name="daily")
    @commands.cooldown(1, DAILY_CD, commands.BucketType.user)
    @with_achievements("daily")
    async def cmd_daily(self, ctx: commands.Context):
        """🎁 !daily — nhận thưởng hàng ngày +1000 xu, +10000 XP, +1 streak."""
        user = await self._get_user(ctx.author.id)
        now = int(time.time())
        if now - (user.last_daily or 0) < DAILY_CD:
            return await ctx.send(embed=make_embed(
                desc="⏳ Bạn đã nhận hôm nay rồi.",
                color=nextcord.Color.red()
            ))

        user.wallet     = (user.wallet or 0) + 1000
        user.xp         = (user.xp or 0) + 10000
        user.streak     = (user.streak or 0) + 1
        user.last_daily = now
        await self._save_user(user)
        bonus_streak = 1
        if getattr(user, "pending_streak_charge", False):
            bonus_streak = 2
            user.pending_streak_charge = False
        user.streak += bonus_streak

        # Award badges for streak?
        # await award(self.bot, ctx.author.id, "streak_master")

        await ctx.send(embed=make_embed(
            desc=f"🎁 Bạn nhận +1000🪙 +10000XP\n🔥 Streak: {user.streak:,} ngày",
            color=nextcord.Color.green()
        ))

    @commands.command(name="pray")
    @commands.cooldown(1, PRAY_CD, commands.BucketType.user)
    @with_achievements("pray")
    async def cmd_pray(self, ctx: commands.Context):
        """🙏 !pray — tăng prayer_progress; có cơ hội nhận thưởng lớn."""
        user = await self._get_user(ctx.author.id)
        user.prayer_progress = (user.prayer_progress or 0) + 1

        chance = 0.00005 + (user.prayer_progress / 50000)
        roll   = random.random()
        desc, col = "🙏 Bạn đã cầu nguyện thành tâm.", nextcord.Color.teal()

        if roll < chance:
            reward = random.randint(1_000_000, 5_000_000)
            user.wallet = (user.wallet or 0) + reward
            desc, col = f"🌟 Phép màu! Bạn nhận **{reward:,}** xu!", nextcord.Color.gold()
            # await award(self.bot, ctx.author.id, "praybless")
        elif roll < chance + 0.05:
            user.xp = (user.xp or 0) + 100
            desc, col = "🌀 +100 XP từ phúc lành.", nextcord.Color.green()
        elif roll < chance + 0.10:
            user.wallet = (user.wallet or 0) + 20
            desc, col = "🪙 +20 xu nhặt quanh đền.", nextcord.Color.green()

        await self._save_user(user)
        await ctx.send(embed=make_embed(desc=desc, color=col))

    @commands.command(name="crime")
    @commands.cooldown(1, 300, commands.BucketType.user)
    @with_achievements("crime")
    async def cmd_crime(self, ctx: commands.Context):
        """🚓 !crime — 30% chance gain 2000–5000 xu; else bị phạt."""
        user = await self._get_user(ctx.author.id)

        if random.random() < 0.30:
            gain = random.randint(2000, 5000)
            user.wallet = (user.wallet or 0) + gain
            msg, col = f"😈 Phạm tội thành công! +{gain:,} xu", nextcord.Color.green()
        else:
            fine = random.randint(500, 1000)
            if (user.wallet or 0) >= fine:
                user.wallet -= fine
                msg = f"🚔 Bị bắt và mất {fine:,} xu"
            else:
                user.debt = (user.debt or 0) + fine
                msg = f"🚔 Bị bắt, nợ thêm {fine:,} xu"
            col = nextcord.Color.red()

        await self._save_user(user)
        await ctx.send(embed=make_embed(desc=msg, color=col))

    @commands.command(name="steal")
    @commands.cooldown(1, 600, commands.BucketType.user)
    @with_achievements("steal")
    async def cmd_steal(self, ctx: commands.Context, target: nextcord.Member):
        """🕵️ !steal <target> — trộm xu (cả hai Level ≥5)."""
        REQUIRED_LEVEL = 15

        uid, tid = ctx.author.id, target.id
        if uid == tid:
            return await ctx.send(embed=make_embed(
                desc="❌ Không thể trộm chính mình.",
                color=nextcord.Color.red()
            ))

        actor = await self._get_user(uid)
        victim = await self._get_user(tid)

        if actor.level < REQUIRED_LEVEL or victim.level < REQUIRED_LEVEL:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Cần cả hai Level ≥15.",
                color=nextcord.Color.orange()
            ))
        if (victim.wallet or 0) < 10:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Mục tiêu không đủ tiền.",
                color=nextcord.Color.orange()
            ))

        if random.random() < 0.6:
            amt = random.randint(10, min(50, victim.wallet))
            victim.wallet -= amt
            actor.wallet  = (actor.wallet or 0) + amt
            msg, col = f"🎉 Trộm thành công {amt:,} xu từ {target.mention}", nextcord.Color.green()
        else:
            msg, col = "💥 Trộm thất bại, bị phát hiện!", nextcord.Color.red()

        await self._save_user(victim)
        await self._save_user(actor)
        await ctx.send(embed=make_embed(desc=msg, color=col))

    @commands.command(name="repay")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @with_achievements("first_repay")
    async def cmd_repay(self, ctx: commands.Context, amount: int = None):
        """💳 !repay [amount] — trả bớt hoặc toàn bộ nợ."""
        user = await self._get_user(ctx.author.id)
        debt = user.debt or 0
        if debt <= 0:
            return await ctx.send(embed=make_embed(
                desc="✅ Bạn không còn nợ.",
                color=nextcord.Color.green()
            ))

        pay = min(amount or debt, user.wallet or 0)
        if pay <= 0:
            return await ctx.send(embed=make_embed(
                desc="❌ Không đủ tiền để trả nợ.",
                color=nextcord.Color.red()
            ))

        user.wallet -= pay
        user.debt   -= pay
        await self._save_user(user)

        await ctx.send(embed=make_embed(
            desc=f"💳 Trả {pay:,} xu. Nợ còn: {user.debt:,} xu",
            color=nextcord.Color.green()
        ))

    @commands.command(name="give")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @with_achievements("first_give")
    async def cmd_give(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """💸 !give <member> <amount> — gửi xu cho người khác."""
        uid, tid = ctx.author.id, member.id
        if uid == tid or amount <= 0:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Số tiền không hợp lệ.",
                color=nextcord.Color.red()
            ))

        sender = await self._get_user(uid)
        if (sender.wallet or 0) < amount:
            return await ctx.send(embed=make_embed(
                desc="❌ Bạn không đủ xu.",
                color=nextcord.Color.red()
            ))

        receiver = await self._get_user(tid)
        sender.wallet   -= amount
        receiver.wallet = (receiver.wallet or 0) + amount

        await self._save_user(sender)
        await self._save_user(receiver)
        await ctx.send(embed=make_embed(
            desc=f"💸 Đã gửi **{amount:,}** xu cho {member.mention}",
            color=nextcord.Color.green()
        ))

    @commands.command(name="deposit")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @with_achievements("deposit")
    async def cmd_deposit(self, ctx: commands.Context, amount: int):
        """🏦 !deposit <amount> — chuyển xu từ ví vào ngân hàng."""
        user = await self._get_user(ctx.author.id)

        # ❌ Kiểm tra số tiền hợp lệ
        if amount <= 0 or (user.wallet or 0) < amount:
            return await ctx.send(embed=make_embed(
                desc="❌ Số tiền không hợp lệ hoặc không đủ xu.",
                color=nextcord.Color.red()
            ))

        # 🚫 Kiểm tra giới hạn ngân hàng
        if (user.bank_balance or 0) + amount > (user.bank_limit or 1_000_000_000):
            max_deposit = max(0, (user.bank_limit or 1_000_000_000) - (user.bank_balance or 0))
            return await ctx.send(embed=make_embed(
                desc=f"🚫 Giới hạn bank của bạn là **{user.bank_limit:,}** xu.\n"
                    f"🏦 Bạn chỉ có thể gửi tối đa: **{max_deposit:,}** xu.",
                color=nextcord.Color.red()
            ))

        # ✅ Gửi tiền
        user.wallet       -= amount
        user.bank_balance += amount
        user.last_deposit = int(time.time())
        await self._save_user(user)

        await ctx.send(embed=make_embed(
            desc=f"✅ Bạn đã gửi **{amount:,}** xu vào ngân hàng.\n"
                f"🏦 Số dư hiện tại: **{user.bank_balance:,}** xu.",
            color=nextcord.Color.green()
        ))

    @commands.command(name="withdraw")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @with_achievements("withdraw")
    async def cmd_withdraw(self, ctx: commands.Context, amount: int):
        """🏧 !withdraw <amount> — rút xu từ ngân hàng về ví."""
        user = await self._get_user(ctx.author.id)
        if amount <= 0 or (user.bank_balance or 0) < amount:
            return await ctx.send(embed=make_embed(
                desc="❌ Số tiền không hợp lệ hoặc không đủ trong ngân hàng.",
                color=nextcord.Color.red()
            ))

        user.bank_balance -= amount
        user.wallet       = (user.wallet or 0) + amount
        await self._save_user(user)

        await ctx.send(embed=make_embed(
            desc=f"✅ Bạn đã rút **{amount:,}** xu về ví.\n💰 Ví hiện tại: {user.wallet:,} xu",
            color=nextcord.Color.green()
        ))

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        """Bắt và hiển thị thông báo khi command cooldown."""
        if isinstance(error, commands.CommandOnCooldown):
            retry = int(error.retry_after)
            m, s = divmod(retry, 60)
            time_str = f"{m} phút {s} giây" if m else f"{s} giây"
            return await ctx.send(embed=make_embed(
                desc=f"⏳ Vui lòng chờ **{time_str}** trước khi dùng lại lệnh này.",
                color=nextcord.Color.orange()
            ))
        # Để lỗi khác bubble lên global handler
        raise error

def setup(bot: commands.Bot):
    bot.add_cog(EconomyCog(bot))