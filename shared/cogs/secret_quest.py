# cogs/secret_quest.py

import random
import time

import nextcord
from nextcord.ext import commands
from sqlalchemy.exc import SQLAlchemyError

from shared.db import AsyncSession
from shared.models.user import User
from shared.models.quest import UserQuest
from shared.data.quests import SECRET_POOL
from shared.utils.embed import make_embed

class SecretQuestCog(commands.Cog):
    """
    🗝️ Quest ẩn:
     - !secretquest          : Xem quest ẩn (nếu unlocked)
     - React 🔄 trên embed   : Đổi quest khác
     - !complete_secret <k>  : Hoàn thành quest ẩn
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._messages: dict[int, dict] = {}  # message_id -> quest_key

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @commands.command(name="secretquest")
    async def secretquest(self, ctx: commands.Context):
        bot = self.bot
        """🗝️ !secretquest — show quest ẩn (nếu bạn đã mở khóa)."""
        async with bot.sessionmaker() as session:
            user = await session.get(User, ctx.author.id)

        if not getattr(user, "has_secret_access", False):
            return await ctx.send(embed=make_embed(
                desc="🚫 Bạn chưa mở khóa quest ẩn.", color=nextcord.Color.red()
            ), delete_after=5)

        # chọn random quest
        q = random.choice(SECRET_POOL)
        desc = f"{q['text']} — Yêu cầu: **{q['req']}**"
        embed = make_embed(title="🗝️ Quest Bí Ẩn", desc=desc, color=nextcord.Color.purple())
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🔄")
        # lưu mapping để xử lý reaction
        self._messages[msg.id] = {"key": q["key"], "req": q["req"], "text": q["text"]}

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: nextcord.Reaction, user: nextcord.Member):
        """🔄 Nếu reaction trên embed quest ẩn, đổi quest khác."""
        if user.bot:
            return
        msg_id = reaction.message.id
        if reaction.emoji != "🔄" or msg_id not in self._messages:
            return

        # chọn quest mới
        q = random.choice(SECRET_POOL)
        desc = f"{q['text']} — Yêu cầu: **{q['req']}**"
        embed = make_embed(title="🗝️ Quest Bí Ẩn", desc=desc, color=nextcord.Color.purple())
        await reaction.message.edit(embed=embed)
        # cập nhật mapping
        self._messages[msg_id] = {"key": q["key"], "req": q["req"], "text": q["text"]}

    @commands.command(name="complete_secret")
    async def complete_secret(self, ctx: commands.Context, key: str):
        bot = self.bot
        """
        ✅ !complete_secret <key> — hoàn thành quest ẩn.
        Nếu đạt yêu cầu, mở achievement bí mật.
        """
        # tìm quest trong pool
        q = next((q for q in SECRET_POOL if q["key"] == key), None)
        if not q:
            return await ctx.send(embed=make_embed(
                desc="❌ Key không tồn tại trong quest ẩn.", color=nextcord.Color.red()
            ), delete_after=5)

        uid = ctx.author.id
        now_ts = int(time.time())
        async with bot.sessionmaker() as session:
            user = await session.get(User, uid)
            # tăng progress
            prog = getattr(user, f"{key}_progress", 0) + 1
            setattr(user, f"{key}_progress", prog)

            # nếu đủ req → unlock achievement và mark completed
            if prog >= q["req"]:
                # lưu vào user_quests để tránh lặp
                uq = UserQuest(
                    user_id=uid,
                    quest_key=key,
                    period="secret",
                    progress=q["req"],
                    req=q["req"],
                    reward_coin=0,
                    reward_xp=0,
                    completed=True,
                    created_at=now_ts,
                    expires_at=now_ts + 86400*365  # không hết hạn
                )
                session.add(uq)

                # unlock achievement bí mật
                ach = self.bot.get_cog("Achievement")
                if ach:
                    await ach.unlock(uid, f"secret_{key}")

                await ctx.send(embed=make_embed(
                    desc=f"🎉 Bạn hoàn thành quest ẩn **{q['text']}**! Achievement bí mật đã mở.",
                    color=nextcord.Color.green()
                ))
            else:
                await ctx.send(embed=make_embed(
                    desc=f"• Tiến độ: {prog}/{q['req']}", color=nextcord.Color.orange()
                ), delete_after=5)

            session.add(user)
            await session.commit()

def setup(bot: commands.Bot):
    bot.add_cog(SecretQuestCog(bot))