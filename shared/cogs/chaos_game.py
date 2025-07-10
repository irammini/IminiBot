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
    """
    🎲 Chaos Game:  
      - !chaos : Bot chọn 1 thử thách ngẫu nhiên, hoàn thành trong thời gian giới hạn.
      - on_message/on_reaction_add : Đếm tiến độ, kết thúc kiểm tra.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # active[user_id] = {"task": TASK, "count": int, "end": timestamp, "msg": Message}
        self.active: dict[int, dict] = {}

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.command(name="chaos")
    async def chaos(self, ctx: commands.Context):
        bot = self.bot
        """🎲 !chaos — Nhận Challenge ngẫu nhiên."""
        user_id = ctx.author.id
        if user_id in self.active:
            return await ctx.send(embed=make_embed(
                "⚠️ Bạn đang có thử thách đang chạy.", nextcord.Color.orange()
            ))

        task = random.choice(TASKS)
        desc = f"{task['text']}\nHoàn thành trước khi hết **{task['duration']}s**!"
        embed = make_embed(title="🎲 Chaos Challenge", desc=desc, color=nextcord.Color.dark_red())
        m = await ctx.send(embed=embed)

        # Khởi tạo tiến độ
        self.active[user_id] = {
            "task": task,
            "count": 0,
            "end": time.time() + task["duration"],
            "msg": m
        }

        # Chờ hết thời gian
        await asyncio.sleep(task["duration"])
        info = self.active.pop(user_id, None)
        if not info:
            return

        # Kết quả
        if info["count"] >= task["count"]:
            reward = 50
            async with bot.sessionmaker() as session:
                u = await session.get(User, user_id)
                u.wallet = (u.wallet or 0) + reward
                session.add(u)
                await session.commit()
            await ctx.send(embed=make_embed(
                f"🎉 Thử thách hoàn thành! Bạn nhận +{reward} 🪙",
                color=0x57F287
            ))
        else:
            await ctx.send(embed=make_embed(
                f"😢 Thất bại! Bạn chỉ hoàn thành {info['count']}/{task['count']}.",
                color=0xE74C3C
            ))

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        """Đếm task command hoặc emoji."""
        if message.author.bot:
            return
        user_id = message.author.id
        info = self.active.get(user_id)
        if not info:
            return

        now = time.time()
        if now > info["end"]:
            return

        task = info["task"]
        # Nếu task yêu cầu command
        if "command" in task:
            if message.content.strip().lower().startswith(f"!{task['command']}"):
                info["count"] += 1

        # Nếu task yêu cầu emoji trong nội dung tin nhắn
        if "emoji" in task:
            info["count"] += message.content.count(task["emoji"])

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: nextcord.Reaction, user: nextcord.User):
        """Đếm task reaction."""
        if user.bot:
            return
        info = self.active.get(user.id)
        if not info:
            return

        now = time.time()
        if now > info["end"]:
            return

        task = info["task"]
        if "react" in task and str(reaction.emoji) == task["react"]:
            info["count"] += 1

def setup(bot: commands.Bot):
    bot.add_cog(ChaosGameCog(bot))