# cogs/chaos_game.py

import random
import time
import asyncio

import nextcord
from nextcord.ext import commands
from shared.utils.embed import make_embed
from shared.models.user import User
from shared.db import AsyncSession

# Định nghĩa các thử thách Chaos
TASKS = [
    {"text": "Gõ `!meow` 5 lần", "command": "meow", "count": 5, "duration": 60},
    {"text": "Spam emoji 🐱 10 lần", "emoji": "🐱", "count": 10, "duration": 45},
    {"text": "React 🔄 vào embed này 5 lần", "react": "🔄", "count": 5, "duration": 30},
]

class ChaosGameCog(commands.Cog):
    """🎲 Chaos Game"""

    def __init__(self, bot):
        self.bot = bot
        self.active_challenges = {}  # {user_id: {"type": str, "progress": int, "goal": int}}

    @commands.command(name="chaos")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def cmd_chaos(self, ctx):
        """Bắt đầu thử thách Chaos (random)"""
        if ctx.author.id in self.active_challenges:
            return await ctx.send(embed=make_embed(desc="Bạn đang có thử thách Chaos chưa hoàn thành!", color=nextcord.Color.orange()))
        import random
        challenge_type = random.choice(["message", "emoji", "reaction"])
        goal = random.randint(3, 7)
        self.active_challenges[ctx.author.id] = {"type": challenge_type, "progress": 0, "goal": goal}
        await ctx.send(embed=make_embed(desc=f"Thử thách: gửi {goal} {challenge_type} liên tiếp!", color=nextcord.Color.blue()))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        challenge = self.active_challenges.get(message.author.id)
        if challenge and challenge["type"] == "message":
            challenge["progress"] += 1
            if challenge["progress"] >= challenge["goal"]:
                await self._complete_challenge(message.author, message.channel)

    async def _complete_challenge(self, user, channel):
        async with self.bot.sessionmaker() as sess:
            db_user = await sess.get(User, user.id)
            if not db_user:
                db_user = User(id=user.id)
                sess.add(db_user)
            db_user.wallet += 500
            await sess.commit()
        self.active_challenges.pop(user.id, None)
        await channel.send(embed=make_embed(desc=f"🎉 {user.mention} đã hoàn thành thử thách Chaos và nhận 500 xu!", color=nextcord.Color.green()))

def setup(bot: commands.Bot):
    bot.add_cog(ChaosGameCog(bot))