import time
import nextcord
from nextcord.ext import commands
from sqlalchemy import select
from shared.db import AsyncSession
from shared.models.social import TrustLog, ThankLog
from shared.models.user import User
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
            giver = await session.get(User, uid) or User(id=uid)
            if now - (giver.created_at or 0) < 30*24*3600:
                return await ctx.send(embed=make_embed(
                    desc="🚫 Acc phải ≥30 ngày mới trust.", color=nextcord.Color.orange()
                ))
            exists = await session.get(TrustLog, (uid, member.id))
            if exists:
                return await ctx.send(embed=make_embed(
                    desc="⚠️ Bạn đã trust người này rồi.", color=nextcord.Color.orange()
                ))
            session.add(TrustLog(giver_id=uid, receiver_id=member.id, timestamp=now))
            tgt = await session.get(User, member.id) or User(id=member.id)
            tgt.trust_points = (tgt.trust_points or 0) + 1
            session.add(tgt)
            await session.commit()

        await ctx.send(embed=make_embed(
            desc=f"✅ Bạn đã trust {member.mention}", color=nextcord.Color.green()
        ))

    @commands.command(name="thank")
    @with_achievements("thank")
    async def cmd_thank(self, ctx: commands.Context, member: nextcord.Member):
        bot = self.bot
        """🙏 !thank <user> — gửi lời cảm ơn, +1 karma."""
        uid = ctx.author.id
        if member.id == uid:
            return await ctx.send(embed=make_embed(
                desc="❌ Không thể tự thank.", color=nextcord.Color.red()
            ))

        now = int(time.time())
        async with bot.sessionmaker() as session:
            exists = await session.get(ThankLog, (uid, member.id))
            if exists:
                return await ctx.send(embed=make_embed(
                    desc="⚠️ Bạn đã thank rồi.", color=nextcord.Color.orange()
                ))
            session.add(ThankLog(sender_id=uid, receiver_id=member.id, timestamp=now))
            tgt = await session.get(User, member.id) or User(id=member.id)
            tgt.karma = (tgt.karma or 0) + 1
            session.add(tgt)
            await session.commit()

        await ctx.send(embed=make_embed(
            desc=f"🙏 Bạn đã thank {member.mention}", color=nextcord.Color.green()
        ))

    @commands.command(name="shoutout")
    @with_achievements("shoutout")
    async def cmd_shoutout(self, ctx: commands.Context, channel: nextcord.TextChannel, *, msg: str):
        """📣 !shoutout <#channel> <message> — quảng bá."""
        await channel.send(embed=make_embed(
            title="📣 Shoutout!", desc=f"{ctx.author.mention} nói:\n> {msg}", color=nextcord.Color.orange()
        ))
        await ctx.send(embed=make_embed(
            desc=f"✅ Shoutout tới {channel.mention}", color=nextcord.Color.green()
        ))

def setup(bot: commands.Bot):
    bot.add_cog(SocialCog(bot))