import time
import nextcord
from nextcord.ext import commands
from sqlalchemy import select
from shared.db import AsyncSession
from shared.models.social import TrustLog, ThankLog
from shared.models.user import User
from shared.models.quest import UserQuest
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements

class SocialCog(commands.Cog):
    """🤝 Trust, Thank, Karma, Shoutout"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.command(name="trust")
    @with_achievements("trust")
    async def cmd_trust(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """🤝 !trust <user> — tặng 1 trust point."""
        uid = ctx.author.id
        if member.id == uid:
            return await ctx.send(embed=make_embed(
                desc="❌ Không thể tự trust.", color=nextcord.Color.red()
            ))

        now = int(time.time())
        async with bot.sessionmaker() as session:
            giver = await session.get(User, uid)
            if not giver:
                giver = User(id=uid, created_at=int(time.time()))
                session.add(giver)
                await session.commit()
            exists = await session.get(TrustLog, (uid, member.id))
            if exists:
                return await ctx.send(embed=make_embed(
                    desc="⚠️ Bạn đã trust người này rồi.", color=nextcord.Color.orange()
                ))
            session.add(TrustLog(giver_id=uid, receiver_id=member.id, timestamp=now))
            tgt = await session.get(User, member.id)
            if not tgt:
                tgt = User(id=member.id, created_at=int(time.time()))
                session.add(tgt)
            tgt.trust_points = (tgt.trust_points or 0) + 1
            session.add(tgt)

            # Update daily_trust quest progress
            row = await session.execute(
                select(UserQuest).where(
                    UserQuest.user_id == uid,
                    UserQuest.quest_key == "daily_trust",
                    UserQuest.period == "daily",
                    UserQuest.completed == False
                )
            )
            uq: UserQuest | None = row.scalar_one_or_none()
            if uq:
                uq.progress += 1
                if uq.progress >= uq.req:
                    uq.completed = True
                    uq.completed_at = now
                session.add(uq)

            await session.commit()

        await ctx.send(embed=make_embed(
            desc=f"✅ Bạn đã trust {member.mention}", color=nextcord.Color.green()
        ))

    @commands.command(name="shoutout")
    @with_achievements("shoutout")
    async def cmd_shoutout(self, ctx: commands.Context, channel: nextcord.TextChannel, *, msg: str):
        """📣 !shoutout <#channel> <message> — quảng bá (yêu cầu level 50)."""
        bot = self.bot
        uid = ctx.author.id

        # Kiểm tra level
        async with bot.sessionmaker() as session:
            user = await session.get(User, uid) or User(id=uid)
            if (user.level or 1) < 50:
                return await ctx.send(embed=make_embed(
                    desc="🚫 Bạn cần đạt **level 50** mới được sử dụng lệnh này.",
                    color=nextcord.Color.red()
                ))

        await channel.send(embed=make_embed(
            title="📣 Shoutout!", desc=f"{ctx.author.mention} nói:\n> {msg}", color=nextcord.Color.orange()
        ))
        await ctx.send(embed=make_embed(
            desc=f"✅ Shoutout tới {channel.mention}", color=nextcord.Color.green()
        ))

def setup(bot: commands.Bot):
    bot.add_cog(SocialCog(bot))
