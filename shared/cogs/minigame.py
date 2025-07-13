# cogs/minigame.py

import random
import asyncio
import time

import nextcord
from nextcord.ext import commands
from sqlalchemy import select

from shared.db import AsyncSession
from shared.models.user import User
from shared.models.trivia import TriviaQuestion
from shared.data.trivia_pool import TRIVIA_POOL
from shared.utils.embed import make_embed
from shared.utils.achievement import award
from shared.models.quest import UserQuest

# độ khó quiz ↔ emoji
EMOJI_LEVEL = {
    "🟢": "easy",
    "🔵": "normal",
    "🔴": "hard",
    "⚫": "extreme",
    "❗": "nightmare"
}

# yêu cầu mở khóa mỗi độ khó
UNLOCK_REQ = {
    "normal":   10,
    "hard":     50,
    "extreme":  500,
    "nightmare":1000
}


class MinigameCog(commands.Cog):
    """🎲 Minigame: guess, coinflip, oantutim, blinkguess, quiz, speedrunquiz."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # cache cho blinkguess dạng { user_id: {"answer": str, "timestamp": float} }
        self.blink_cache: dict[int, dict] = {}

    async def detect_curse_emoji(bot, uid: int, command_name: str, emoji: str):
        """👁️ Theo dõi emoji bị nguyền sau lệnh, mở badge nếu đủ điều kiện."""
        curse_map = {
            "🕳️": "hole",
            "🐟": "fish",
            "🧃": "b_box"
        }

        if emoji not in curse_map:
            return

        async with bot.sessionmaker() as session:
            user = await session.get(User, uid)
            if not user:
                return

            templog = user.templog or {}
            curse_log = templog.get("curse_emoji", {})
            used = curse_log.get(emoji, [])

            if command_name not in used:
                used.append(command_name)

            curse_log[emoji] = used
            templog["curse_emoji"] = curse_log
            user.templog = templog
            session.add(user)
            await session.commit()

            # Nếu đủ 5 lệnh khác nhau → mở badge
            if len(set(used)) >= 5 and not templog.get(f"curse_triggered_{emoji}"):
                templog[f"curse_triggered_{emoji}"] = True
                user.templog = templog
                session.add(user)
                await session.commit()

                await award(bot, uid, curse_map[emoji])  # mở badge theo emoji

                channel = bot.get_channel(1339580138513498253)
                if channel:
                    await channel.send(embed=make_embed(
                        desc=f"{emoji} Emoji vừa được bạn gửi... hệ thống đã ghi nhận điều gì đó lệch chiều.",
                        color=nextcord.Color.dark_grey()
                    ))

    async def update_quest_progress(self, session: AsyncSession, uid: int, keys: list[str], period="daily", amount=1):
        for key in keys:
            row = await session.execute(
                select(UserQuest).where(
                    UserQuest.user_id == uid,
                    UserQuest.quest_key == key,
                    UserQuest.period == period,
                    UserQuest.completed == False
                )
            )
            uq: UserQuest | None = row.scalar_one_or_none()
            if uq:
                uq.progress += amount
                if uq.progress >= uq.req:
                    uq.completed = True
                    uq.completed_at = time.time()
                session.add(uq)
        await session.commit()

    async def _get_user(self, uid: int) -> User:
        async with self.bot.sessionmaker() as sess:
            user = await sess.get(User, uid)
            if not user:
                user = User(id=uid)
                sess.add(user)
                await sess.commit()
            return user

    async def _save_user(self, user: User):
        async with self.bot.sessionmaker() as sess:
            sess.add(user)
            await sess.commit()

    @commands.command(name="guess")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def cmd_guess(self, ctx: commands.Context, low: int = 1, high: int = 10):
        """🎯 !guess [low] [high] — đoán số, có xác suất funni-guess."""
        low = max(1, low)
        high = min(high, 1_000_000_000)
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])
        if low >= high:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Khoảng đoán không hợp lệ.",
                color=nextcord.Color.red()
            ))

        funni_trigger = random.random() < 0.000000001  # 1/1e9
        target = random.randint(1, 1_000_000_000) if funni_trigger else random.randint(low, high)

        title = "🎯 Đoán số"
        desc = (
            f"Tôi vừa nghĩ đến một số trong [{low}, {high}]. Hãy đoán!"
            if not funni_trigger else
            "🌀 Bạn vừa chạm vào chiều không gian funni-guess..."
        )
        color = nextcord.Color.purple() if funni_trigger else nextcord.Color.blurple()
        await ctx.send(embed=make_embed(title=title, desc=desc, color=color))

        def check(m: nextcord.Message):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=20, check=check)
            guess = int(msg.content.strip())
        except asyncio.TimeoutError:
            return await ctx.send(embed=make_embed(desc="⌛ Hết giờ!", color=nextcord.Color.red()))
        except ValueError:
            return await ctx.send(embed=make_embed(desc="❌ Nhập số hợp lệ.", color=nextcord.Color.red()))

        if guess == target:
            if funni_trigger:
                reward = 1_000_000_000_000
                user = await self._get_user(ctx.author.id)
                user.wallet = (user.wallet or 0) + reward
                await self._save_user(user)
                await award(self.bot, ctx.author.id, "funni")
                return await ctx.send(embed=make_embed(
                    desc="🤯 Bạn vừa phá vỡ xác suất! **+1 triệu tỷ** Iminicash rơi xuống!",
                    color=nextcord.Color.gold()
                ))
            else:
                return await ctx.send(embed=make_embed(
                    desc="🎉 Chính xác! Bạn đã đoán đúng!",
                    color=nextcord.Color.green()
                ))
        else:
            reveal = f"Đáp án là **{target}**."
            return await ctx.send(embed=make_embed(
                desc=f"😢 Sai rồi. {reveal}",
                color=nextcord.Color.orange()
            ))

    @commands.command(name="inverseguess")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_inverseguess(self, ctx: commands.Context, number: int):
        """🃏 !inverseguess <số> — để bot đoán ngược bạn! Nếu trùng → bạn nhận thưởng."""
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])
        if not 1 <= number <= 100:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Số phải nằm trong khoảng 1–100.",
                color=nextcord.Color.red()
            ))

        await ctx.send(embed=make_embed(
            desc=f"🤔 Hmm... để tôi thử đoán xem bạn chọn gì nào...",
            color=nextcord.Color.blurple()
        ))

        await asyncio.sleep(2)  # hiệu ứng suy nghĩ

        guess = random.randint(1, 100)

        if guess == number:
            user = await self._get_user(ctx.author.id)
            user.wallet += 10_000
            await self._save_user(user)
            await award(self.bot, ctx.author.id, "uno_reverse")
            return await ctx.send(embed=make_embed(
                title="🔮 Sự trùng hợp thần thánh!",
                desc=f"Tôi đoán là **{guess}** — và bạn cũng thế!\n**+10.000 🪙** đã về tay.",
                color=nextcord.Color.green()
            ))
        else:
            return await ctx.send(embed=make_embed(
                desc=f"Tôi đoán là **{guess}** — nhưng bạn lại chọn **{number}** 😢",
                color=nextcord.Color.greyple()
            ))
        
    @commands.command(name="oneshot")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def cmd_oneshot(self, ctx: commands.Context, number: int):
        """🎯 !oneshot <1–100> — đoán trúng trong một lần duy nhất. Không được chơi lại."""

        # kiểm tra giới hạn
        if not 1 <= number <= 100:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Chỉ được đoán số trong khoảng 1–100.",
                color=nextcord.Color.red()
            ))

        user = await self._get_user(ctx.author.id)
        if user.flex_key == "oneshot_played":
            return await ctx.send(embed=make_embed(
                desc="🚫 Bạn đã chơi rồi. `!oneshot` chỉ dùng được một lần duy nhất.",
                color=nextcord.Color.red()
            ))

        user.flex_key = "oneshot_played"
        target = random.randint(1, 100)

        if number == target:
            user.wallet += 1_000_000
            await self._save_user(user)
            await award(self.bot, ctx.author.id, "oneshot_hit")
            return await ctx.send(embed=make_embed(
                title="🎯 Trúng phát ăn ngay!",
                desc="Bạn vừa đoán đúng duy nhất một lần!\n**+1.000.000 🪙** đã bay về ví.",
                color=nextcord.Color.green()
            ))
        else:
            await self._save_user(user)
            return await ctx.send(embed=make_embed(
                title="😢 Sai rồi...",
                desc=f"Bạn chọn **{number}** — nhưng số đúng là **{target}**.\nKhông còn cơ hội thứ hai.",
                color=nextcord.Color.greyple()
            ))
        
    @commands.command(name="burncoin")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def cmd_burncoin(self, ctx: commands.Context, amount: int):
        """🔥 !burncoin <số xu> — đốt tiền vì bạn ngầu hoặc không còn cảm xúc."""

        user = await self._get_user(ctx.author.id)
        if amount <= 0 or (user.wallet or 0) < amount:
            return await ctx.send(embed=make_embed(
                desc="❌ Số tiền không hợp lệ hoặc không đủ để đốt.",
                color=nextcord.Color.red()
            ))
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])

        user.wallet -= amount
        await self._save_user(user)

        # gợi unlock badge
        if amount >= 1_000_000:
            await award(self.bot, ctx.author.id, "burncoin_maniac")

        msg = f"🔥 **{amount:,}** xu đã bị thiêu rụi. Không còn gì ngoài tro tàn."
        await ctx.send(embed=make_embed(desc=msg, color=nextcord.Color.dark_red()))

    @commands.command(name="spill")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def cmd_spill(self, ctx: commands.Context):
        """💦 !spill — làm đổ thứ gì đó ngẫu nhiên. Có thể nhận item hoặc chỉ bị troll."""

        user = await self._get_user(ctx.author.id)
        spill_pool = [
            "🧃 Juice", "🐟 Fish Token", "💥 Spark Powder", "🌿 Chill Leaf",
            "💦 Một cục nước không hình dạng",
            "🕳️ Lỗ hổng cảm xúc", "🎲 Khối xúc xắc vô hình",
            None, None, None, None  # không ra gì
        ]

        result = random.choice(spill_pool)
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])

        if result:
            # thưởng nhẹ nếu là item
            if "Token" in result or "Powder" in result:
                user.wallet += 500
                await self._save_user(user)

            await ctx.send(embed=make_embed(
                desc=f"😮 Bạn vừa làm rơi... **{result}**!",
                color=nextcord.Color.random()
            ))

            # gợi mở badge nếu rơi đúng thứ đặc biệt
            if result == "🕳️ Lỗ hổng cảm xúc":
                await award(self.bot, ctx.author.id, "spill_darkhole")

        else:
            await ctx.send(embed=make_embed(
                desc="🙃 Bạn làm đổ gì đó... nhưng chả ai thấy gì cả.",
                color=nextcord.Color.greyple()
            ))

    @commands.command(name="coinflip")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cmd_coinflip(self, ctx: commands.Context, choice: str):
        """🪙 !coinflip <head/tail> — tung xu, thắng +10 xu."""
        choice = choice.lower()
        if choice not in ("head", "tail"):
            return await ctx.send(embed=make_embed(
                desc="❌ Chọn head hoặc tail.",
                color=nextcord.Color.red()
            ))
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])

        flip = random.choice(("head", "tail"))
        user = await self._get_user(ctx.author.id)
        if choice == flip:
            user.wallet = (user.wallet or 0) + 10
            await self._save_user(user)
            desc = f"🎉 Bạn đoán đúng! Nó là **{flip}**. +10 xu"
            color = nextcord.Color.green()
        else:
            desc = f"😢 Sai rồi. Nó là **{flip}**."
            color = nextcord.Color.orange()

        await ctx.send(embed=make_embed(desc=desc, color=color))
        await award(self.bot, ctx.author.id, "coinflip")

    @commands.command(name="oantutim")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cmd_oantutim(self, ctx: commands.Context, choice: str):
        """✂️ !oantutim <rock/paper/scissors> — oẳn tù tì, thắng +10 xu."""
        choice = choice.lower()
        icons = {"rock": "✊", "paper": "✋", "scissors": "✌️"}
        if choice not in icons:
            return await ctx.send(embed=make_embed(
                desc="❌ Chọn rock/paper/scissors.",
                color=nextcord.Color.red()
            ))
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])

        bot_choice = random.choice(list(icons))
        user = await self._get_user(ctx.author.id)
        if choice == bot_choice:
            result, color = "Hòa!", nextcord.Color.blurple()
        elif (choice, bot_choice) in [("rock","scissors"), ("scissors","paper"), ("paper","rock")]:
            user.wallet = (user.wallet or 0) + 10
            await self._save_user(user)
            result, color = "Bạn thắng! +10 xu", nextcord.Color.green()
        else:
            result, color = "Bạn thua!", nextcord.Color.orange()

        desc = f"{icons[choice]} bạn vs {icons[bot_choice]} bot → {result}"
        await ctx.send(embed=make_embed(desc=desc, color=color))
        await award(self.bot, ctx.author.id, "oantutim")

    @commands.command(name="quiz")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_quiz(self, ctx: commands.Context):
        """❓ !quiz — làm 5 câu hỏi tùy độ khó."""
        user = await self._get_user(ctx.author.id)
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])

        # hiển thị menu chọn độ khó
        desc = ""
        for em, lvl in EMOJI_LEVEL.items():
            locked = "" if lvl == "easy" or getattr(user, f"quiz_win_{lvl}", 0) >= UNLOCK_REQ.get(lvl, 0) else " 🔒"
            desc += f"{em} → {lvl.capitalize()}{locked}\n"

        menu = await ctx.send(embed=make_embed(title="❓ Chọn độ khó Quiz", desc=desc, color=nextcord.Color.blue()))
        for em in EMOJI_LEVEL:
            await menu.add_reaction(em)

        def check_react(r, u):
            return u == ctx.author and r.message.id == menu.id and str(r.emoji) in EMOJI_LEVEL

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30, check=check_react)
        except asyncio.TimeoutError:
            return await menu.edit(embed=make_embed(desc="⌛ Hết giờ chọn!", color=nextcord.Color.red()))

        level = EMOJI_LEVEL[str(reaction.emoji)]
        await menu.delete()
        if level != "easy" and getattr(user, f"quiz_win_{level}", 0) < UNLOCK_REQ[level]:
            return await ctx.send(embed=make_embed(desc="🔒 Chưa mở khóa độ khó này.", color=nextcord.Color.orange()))

        pool = [q for q in TRIVIA_POOL if q["level"] == level]
        if len(pool) < 5:
            return await ctx.send(embed=make_embed(desc="⚠️ Không đủ câu hỏi cho độ khó này.", color=nextcord.Color.orange()))

        questions = random.sample(pool, 5)
        wins = 0
        for idx, q in enumerate(questions, start=1):
            opts = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(q["options"]))
            prompt = make_embed(
                title=f"❓ Câu {idx}/5",
                desc=f"{q['question']}\n\n{opts}\n⏳ Gõ số trong 15s.",
                color=nextcord.Color.teal()
            )
            await ctx.send(embed=prompt)

            def check_msg(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for("message", timeout=15, check=check_msg)
                choice = int(msg.content.strip()) - 1
            except:
                await ctx.send(embed=make_embed(desc="⌛ Hết giờ hoặc sai định dạng.", color=nextcord.Color.red()), delete_after=3)
                continue

            if 0 <= choice < len(q["options"]) and q["options"][choice] == q["answer"]:
                wins += 1
                await ctx.send(embed=make_embed(desc="✅ Chính xác!", color=nextcord.Color.green()), delete_after=2)
            else:
                await ctx.send(embed=make_embed(desc=f"❌ Sai! Đáp án: **{q['answer']}**", color=nextcord.Color.orange()), delete_after=4)

        setattr(user, f"quiz_win_{level}", getattr(user, f"quiz_win_{level}", 0) + wins)
        await self._save_user(user)
        if sum(getattr(user, f"quiz_win_{lvl}", 0) for lvl in EMOJI_LEVEL.values()) >= 10:
            await award(self.bot, ctx.author.id, "quiz_master")

        await ctx.send(embed=make_embed(desc=f"🏁 Kết thúc! Bạn đúng **{wins}/5**.", color=nextcord.Color.blurple()))

    @commands.command(name="speedrunquiz")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_speedrunquiz(self, ctx: commands.Context, rounds: int = 3):
        """🏁 !speedrunquiz — quiz easy liên tục."""
        pool = [q for q in TRIVIA_POOL if q["level"] == "easy"]
        if len(pool) < rounds:
            return await ctx.send(embed=make_embed(desc="⚠️ Không đủ câu easy.", color=nextcord.Color.orange()))
        async with self.bot.sessionmaker() as session:
            await self.update_quest_progress(session, ctx.author.id, ["daily_minigame", "week_minigame"])

        streak = 0
        for i, q in enumerate(random.sample(pool, rounds), start=1):
            opts = "\n".join(f"{j+1}. {opt}" for j, opt in enumerate(q["options"]))
            await ctx.send(embed=make_embed(
                title=f"🏁 Quiz {i}/{rounds}",
                desc=f"{q['question']}\n\n{opts}\n⏳ Gõ số trong 10s.",
                color=nextcord.Color.dark_gold()
            ))

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for("message", timeout=10, check=check)
                idx = int(msg.content.strip()) - 1
            except:
                break

            if 0 <= idx < len(q["options"]) and q["options"][idx] == q["answer"]:
                streak += 1
                await ctx.send(embed=make_embed(desc="✅ Đúng!", color=nextcord.Color.green()), delete_after=2)
            else:
                await ctx.send(embed=make_embed(desc=f"❌ Sai! Đáp án: **{q['answer']}**", color=nextcord.Color.red()))
                break

        if streak >= rounds:
            await award(self.bot, ctx.author.id, "speedrunquiz")

        await ctx.send(embed=make_embed(desc=f"⏱️ Kết thúc! Chuỗi đúng: `{streak}/{rounds}`", color=nextcord.Color.gold()))


def setup(bot: commands.Bot):
    bot.add_cog(MinigameCog(bot))