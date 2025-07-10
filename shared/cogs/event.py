import time
import nextcord
from nextcord import Color
from nextcord.ext import commands
from sqlalchemy import select
from shared.db import AsyncSession
from shared.models.event import Event, UserEvent
from shared.models.user import User
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements

class EventCog(commands.Cog):
    """🎊 Event: list, join, claim."""

    DEV_IDS = [1064509322228412416, 1327287076122787940]

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.command(name="createevent")
    async def create_event(self, ctx, key: str, name: str, coin: int = 0, ends: int = 0):
        if ctx.author.id not in self.DEV_IDS:
            return await ctx.send(embed=make_embed(desc="❌ Không quyền.", color=Color.red()))

        async with self.bot.sessionmaker() as session:
            e = await session.get(Event, key)
            if e:
                return await ctx.send(embed=make_embed(desc="⚠️ Event đã tồn tại.", color=Color.orange()))

            new = Event(key=key, name=name, reward_coin=coin, ends_at=ends or (int(time.time()) + 86400), enabled=True)
            session.add(new)
            await session.commit()

        await ctx.send(embed=make_embed(desc=f"✅ Tạo event **{name}** ({key}) thành công!", color=Color.green()))

    @commands.command(name="eventlist")
    async def eventlist(self, ctx):
        now = int(time.time())
        async with self.bot.sessionmaker() as s:
            events = (await s.execute(
                select(Event).where(Event.enabled == True, Event.ends_at > now)
            )).scalars().all()

        if not events:
            return await ctx.send(embed=make_embed(desc="📭 Không có event.", color=0x95A5A6))

        lines = "\n".join(f"`{e.key}` — {e.name}" for e in events)
        await ctx.send(embed=make_embed("🎊 Active Events", lines, 0xF1C40F))

    @commands.command(name="joinevent")
    @with_achievements("joinevent")
    async def joinevent(self, ctx, key: str):
        uid = ctx.author.id
        now = int(time.time())
        async with self.bot.sessionmaker() as s:
            e = await s.get(Event, key)
            if not e or not e.enabled or now > e.ends_at:
                return await ctx.send(embed=make_embed(desc="❌ Event không hợp lệ.", color=0xE74C3C))

            already = await s.get(UserEvent, (uid, key))
            if already:
                return await ctx.send(embed=make_embed(desc="⚠️ Bạn đã tham gia.", color=0xE67E22))

            s.add(UserEvent(user_id=uid, event_key=key, claimed_at=0))
            await s.commit()

        await ctx.send(embed=make_embed(desc=f"✋ Tham gia **{e.name}** thành công!", color=0x2ECC71))

    @commands.command(name="claim_event")
    @with_achievements("claim_event")
    async def claim_event(self, ctx, key: str):
        uid = ctx.author.id
        now = int(time.time())

        async with self.bot.sessionmaker() as s:
            ue = await s.get(UserEvent, (uid, key))
            e  = await s.get(Event, key)

            if not ue or not e or now > e.ends_at:
                return await ctx.send(embed=make_embed(desc="❌ Không thể claim.", color=0xE74C3C))
            if ue.claimed_at:
                return await ctx.send(embed=make_embed(desc="⚠️ Bạn đã claim.", color=0xE67E22))

            user = await s.get(User, uid)
            user.wallet = (user.wallet or 0) + (e.reward_coin or 0)
            ue.claimed_at = now

            s.add_all([ue, user])
            await s.commit()

        await ctx.send(embed=make_embed(desc=f"🎉 Claim thành công! +{e.reward_coin} 🪙", color=0x2ECC71))

def setup(bot):
    bot.add_cog(EventCog(bot))