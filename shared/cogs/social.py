# cogs/social.py

import time
import nextcord
from nextcord.ext import commands
from sqlalchemy import select
from shared.db import AsyncSession
from shared.models.social import TrustLog
from shared.models.user import User
from shared.models.quest import UserQuest
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements

class SocialCog(commands.Cog):
    """🤝 Trust, Thank, Karma, Shoutout"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="trust")
    @with_achievements("trust")
    async def cmd_trust(self, ctx: commands.Context, member: nextcord.Member):
        """🤝 Tặng 1 trust point (cả 2 phải có Imini ID)."""
        uid = ctx.author.id
        if member.id == uid:
            return await ctx.send(embed=make_embed(desc="❌ Không thể tự trust.", color=nextcord.Color.red()))
        if member.bot:
            return await ctx.send(embed=make_embed(desc="❌ Không thể trust bot.", color=nextcord.Color.red()))

        now = int(time.time())
        async with self.bot.sessionmaker() as session:
            giver = await session.get(User, uid)
            receiver = await session.get(User, member.id)

            # --- Nâng cấp: Kiểm tra Imini ID ---
            if not giver or not giver.imini_id:
                return await ctx.send(embed=make_embed(desc="❌ Bạn cần có Imini ID để trust người khác. Dùng `!requestid`.", color=nextcord.Color.red()))
            if not receiver or not receiver.imini_id:
                return await ctx.send(embed=make_embed(desc=f"❌ {member.mention} chưa có Imini ID.", color=nextcord.Color.red()))
            # ------------------------------------

            exists = await session.get(TrustLog, (uid, member.id))
            if exists:
                return await ctx.send(embed=make_embed(desc="⚠️ Bạn đã trust người này rồi.", color=nextcord.Color.orange()))
            
            session.add(TrustLog(giver_id=uid, receiver_id=member.id, timestamp=now))
            receiver.trust_points = (receiver.trust_points or 0) + 1
            
            # Update quest
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

        await ctx.send(embed=make_embed(desc=f"✅ Bạn đã trust {member.mention}", color=nextcord.Color.green()))

    @commands.command(name="shoutout")
    @with_achievements("shoutout")
    async def cmd_shoutout(self, ctx: commands.Context, channel: nextcord.TextChannel, *, msg: str):
        """📣 Quảng bá (yêu cầu level 50)."""
        async with self.bot.sessionmaker() as session:
            user = await session.get(User, ctx.author.id) or User(id=ctx.author.id)
            if (user.level or 1) < 50:
                return await ctx.send(embed=make_embed(desc="🚫 Bạn cần đạt **level 50** mới được sử dụng lệnh này.", color=nextcord.Color.red()))

        await channel.send(embed=make_embed(title="📣 Shoutout!", desc=f"{ctx.author.mention} nói:\n> {msg}", color=nextcord.Color.orange()))
        await ctx.send(embed=make_embed(desc=f"✅ Shoutout tới {channel.mention}", color=nextcord.Color.green()))

def setup(bot: commands.Bot):
    bot.add_cog(SocialCog(bot))
