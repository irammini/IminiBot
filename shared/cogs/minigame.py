# cogs/minigame.py

import random
import asyncio
import time
import logging

import nextcord
from nextcord.ext import commands
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

# --- Local Imports ---
from shared.models.user import User
from shared.models.quest import UserQuest
from shared.data.trivia_pool import TRIVIA_POOL
from shared.utils.embed import make_embed
from shared.utils.achievement import award

logger = logging.getLogger(__name__)

# --- Constants ---
EMOJI_LEVEL = {"🟢": "easy", "🔵": "normal", "🔴": "hard", "⚫": "extreme", "❗": "nightmare"}
UNLOCK_REQ = {"normal": 10, "hard": 50, "extreme": 500, "nightmare": 1000}

class MinigameCog(commands.Cog):
    """🎲 Minigame: guess, coinflip, oantutim, quiz..."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.blink_cache: dict[int, dict] = {}

    # --- Error Handling ---
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Bắt các lỗi chung của cog và gửi thông báo thân thiện."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=make_embed(desc=f"❌ Thiếu tham số bắt buộc: `{error.param.name}`. Dùng `!help {ctx.command.name}` để xem chi tiết.", color=nextcord.Color.red()))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=make_embed(desc=f"❌ Tham số không hợp lệ. Vui lòng kiểm tra lại loại dữ liệu bạn nhập (ví dụ: số, chữ...).", color=nextcord.Color.red()))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=make_embed(desc=f"⏳ Lệnh đang trong thời gian hồi chiêu! Vui lòng thử lại sau **{error.retry_after:.2f} giây**.", color=nextcord.Color.orange()))
        elif isinstance(error, commands.CheckFailure):
             await ctx.send(embed=make_embed(desc=str(error), color=nextcord.Color.red()))
        else:
            logger.error(f"Lỗi không xác định trong MinigameCog lệnh '{ctx.command.name}': {error}", exc_info=True)
            await ctx.send(embed=make_embed(desc="🐞 Đã xảy ra lỗi không mong muốn. Vui lòng báo cho dev.", color=nextcord.Color.dark_red()))

    # --- Helper Functions ---
    async def _get_user(self, session, uid: int) -> User:
        """Lấy hoặc tạo user mới trong cùng một session."""
        user = await session.get(User, uid)
        if not user:
            user = User(id=uid)
            session.add(user)
            await session.flush()
        return user

    async def update_quest_progress(self, session, uid: int, keys: list[str], period="daily", amount=1):
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
        
    # --- Minigame Commands ---
    @commands.command(name="guess")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def cmd_guess(self, ctx: commands.Context, low: int = 1, high: int = 10):
        """🎯 Đoán số, có xác suất funni-guess."""
        if low >= high:
            return await ctx.send(embed=make_embed(desc="⚠️ Khoảng đoán không hợp lệ (số đầu phải nhỏ hơn số sau).", color=nextcord.Color.red()))

        funni_trigger = random.random() < 0.000000001
        target = random.randint(1, 1_000_000_000) if funni_trigger else random.randint(low, high)
        
        desc = f"Tôi vừa nghĩ đến một số trong khoảng **[{low}, {high}]**. Bạn có 20 giây để đoán!"
        if funni_trigger:
            desc = "🌀 Bạn vừa chạm vào chiều không gian funni-guess... Hãy đoán một con số!"
        
        await ctx.send(embed=make_embed(title="🎯 Đoán số", desc=desc, color=nextcord.Color.blurple()))

        def check(m: nextcord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for("message", timeout=20.0, check=check)
            guess = int(msg.content)
        except asyncio.TimeoutError:
            return await ctx.send(embed=make_embed(desc=f"⌛ Hết giờ! Đáp án đúng là **{target}**.", color=nextcord.Color.orange()))
        except (ValueError, TypeError):
            return await ctx.send(embed=make_embed(desc="❌ Bạn phải nhập một con số hợp lệ.", color=nextcord.Color.red()))

        if guess == target:
            if funni_trigger:
                try:
                    async with self.bot.sessionmaker() as session:
                        user = await self._get_user(session, ctx.author.id)
                        user.wallet += 1_000_000_000_000
                        await session.commit()
                    await award(self.bot, ctx.author.id, "funni")
                    await ctx.send(embed=make_embed(desc="🤯 Bạn vừa phá vỡ xác suất! **+1 triệu tỷ** 🪙 rơi xuống!", color=nextcord.Color.gold()))
                except SQLAlchemyError as e:
                    logger.error(f"Lỗi DB trong funni-guess: {e}")
                    await ctx.send(embed=make_embed(desc="❌ Lỗi khi cộng tiền thưởng funni.", color=nextcord.Color.red()))
            else:
                await ctx.send(embed=make_embed(desc="🎉 Chính xác! Bạn đã đoán đúng!", color=nextcord.Color.green()))
        else:
            await ctx.send(embed=make_embed(desc=f"😢 Sai rồi. Đáp án đúng là **{target}**.", color=nextcord.Color.orange()))

    @commands.command(name="inverseguess")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_inverseguess(self, ctx: commands.Context, number: int):
        """🃏 Để bot đoán ngược bạn! Nếu trùng → bạn nhận thưởng."""
        if not 1 <= number <= 100:
            return await ctx.send(embed=make_embed(desc="⚠️ Số phải nằm trong khoảng 1–100.", color=nextcord.Color.red()))

        await ctx.send(embed=make_embed(desc=f"🤔 Hmm... bạn đã chọn số **{number}**. Để tôi thử đoán xem...", color=nextcord.Color.blurple()))
        await asyncio.sleep(2)
        guess = random.randint(1, 100)

        try:
            async with self.bot.sessionmaker() as session:
                user = await self._get_user(session, ctx.author.id)
                if guess == number:
                    user.wallet += 10_000
                    await award(self.bot, ctx.author.id, "uno_reverse")
                    await session.commit()
                    await ctx.send(embed=make_embed(title="🔮 Sự trùng hợp thần thánh!", desc=f"Tôi đoán là **{guess}** — và bạn cũng thế!\n**+10.000 🪙** đã về tay.", color=nextcord.Color.green()))
                else:
                    await ctx.send(embed=make_embed(desc=f"Tôi đoán là **{guess}** — tiếc quá không trùng rồi �", color=nextcord.Color.greyple()))
        except SQLAlchemyError as e:
            logger.error(f"Lỗi DB trong inverseguess: {e}")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi cập nhật ví.", color=nextcord.Color.red()))

    @commands.command(name="oneshot")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def cmd_oneshot(self, ctx: commands.Context, number: int):
        """🎯 Đoán trúng trong một lần duy nhất. Không được chơi lại."""
        if not 1 <= number <= 100:
            return await ctx.send(embed=make_embed(desc="⚠️ Chỉ được đoán số trong khoảng 1–100.", color=nextcord.Color.red()))

        try:
            async with self.bot.sessionmaker() as session:
                user = await self._get_user(session, ctx.author.id)
                if user.flex_key == "oneshot_played":
                    return await ctx.send(embed=make_embed(desc="🚫 Bạn đã chơi rồi. `!oneshot` chỉ dùng được một lần duy nhất.", color=nextcord.Color.red()))

                user.flex_key = "oneshot_played"
                target = random.randint(1, 100)

                if number == target:
                    user.wallet += 1_000_000
                    await award(self.bot, ctx.author.id, "oneshot_hit")
                    await session.commit()
                    await ctx.send(embed=make_embed(title="🎯 Trúng phát ăn ngay!", desc="Bạn vừa đoán đúng duy nhất một lần!\n**+1.000.000 🪙** đã bay về ví.", color=nextcord.Color.green()))
                else:
                    await session.commit()
                    await ctx.send(embed=make_embed(title="😢 Sai rồi...", desc=f"Bạn chọn **{number}** — nhưng số đúng là **{target}**.\nKhông còn cơ hội thứ hai.", color=nextcord.Color.greyple()))
        except SQLAlchemyError as e:
            logger.error(f"Lỗi DB trong oneshot: {e}")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi lưu trạng thái trò chơi.", color=nextcord.Color.red()))

    @commands.command(name="burncoin")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def cmd_burncoin(self, ctx: commands.Context, amount: int):
        """🔥 Đốt tiền vì bạn ngầu hoặc không còn cảm xúc."""
        if amount <= 0:
            return await ctx.send(embed=make_embed(desc="❌ Số tiền phải là một số dương.", color=nextcord.Color.red()))
        try:
            async with self.bot.sessionmaker() as session:
                user = await self._get_user(session, ctx.author.id)
                if user.wallet < amount:
                    return await ctx.send(embed=make_embed(desc=f"❌ Bạn không đủ tiền để đốt. Bạn chỉ có **{user.wallet:,}** 🪙.", color=nextcord.Color.red()))
                user.wallet -= amount
                if amount >= 1_000_000:
                    await award(self.bot, ctx.author.id, "burncoin_maniac")
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"🔥 **{amount:,}** 🪙 đã bị thiêu rụi. Không còn gì ngoài tro tàn.", color=nextcord.Color.dark_red()))
        except SQLAlchemyError as e:
            logger.error(f"Lỗi DB trong burncoin: {e}")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi cập nhật ví.", color=nextcord.Color.red()))

    @commands.command(name="spill")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def cmd_spill(self, ctx: commands.Context):
        """💦 Làm đổ thứ gì đó ngẫu nhiên. Có thể nhận item hoặc chỉ bị troll."""
        spill_pool = [
            "🧃 Juice", "🐟 Fish Token", "💥 Spark Powder", "🌿 Chill Leaf",
            "💦 Một cục nước không hình dạng",
            "🕳️ Lỗ hổng cảm xúc", "🎲 Khối xúc xắc vô hình",
            None, None, None, None
        ]
        result = random.choice(spill_pool)
        try:
            async with self.bot.sessionmaker() as session:
                user = await self._get_user(session, ctx.author.id)
                if result:
                    if "Token" in result or "Powder" in result:
                        user.wallet += 500
                        await session.commit()
                    await ctx.send(embed=make_embed(desc=f"😮 Bạn vừa làm rơi... **{result}**!", color=nextcord.Color.random()))
                    if result == "🕳️ Lỗ hổng cảm xúc":
                        await award(self.bot, ctx.author.id, "spill_darkhole")
                else:
                    await ctx.send(embed=make_embed(desc="🙃 Bạn làm đổ gì đó... nhưng chả ai thấy gì cả.", color=nextcord.Color.greyple()))
        except SQLAlchemyError as e:
            logger.error(f"Lỗi DB trong spill: {e}")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi cập nhật ví.", color=nextcord.Color.red()))

    @commands.command(name="coinflip")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cmd_coinflip(self, ctx: commands.Context, choice: str):
        """🪙 Tung xu, thắng +10 xu."""
        choice = choice.lower()
        if choice not in ("head", "tail", "h", "t", "ngửa", "sấp"):
            return await ctx.send(embed=make_embed(desc="❌ Lựa chọn không hợp lệ. Vui lòng chọn `head` hoặc `tail`.", color=nextcord.Color.red()))
        if choice in ['h', 'ngửa']: choice = 'head'
        if choice in ['t', 'sấp']: choice = 'tail'
        flip = random.choice(("head", "tail"))
        try:
            async with self.bot.sessionmaker() as session:
                user = await self._get_user(session, ctx.author.id)
                if choice == flip:
                    user.wallet += 10
                    desc = f"🎉 Bạn đoán đúng! Nó là **{flip}**. **+10 🪙**"
                    color = nextcord.Color.green()
                else:
                    desc = f"😢 Sai rồi. Nó là **{flip}**."
                    color = nextcord.Color.orange()
                await session.commit()
            await ctx.send(embed=make_embed(desc=desc, color=color))
            await award(self.bot, ctx.author.id, "coinflip")
        except SQLAlchemyError as e:
            logger.error(f"Lỗi DB trong coinflip: {e}")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi cập nhật ví.", color=nextcord.Color.red()))

    @commands.command(name="oantutim")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cmd_oantutim(self, ctx: commands.Context, choice: str):
        """✂️ Oẳn tù tì, thắng +10 xu."""
        choice = choice.lower()
        valid_choices = {"rock": "✊", "paper": "✋", "scissors": "✌️", "kéo": "✌️", "búa": "✊", "bao": "✋"}
        if choice not in valid_choices:
            return await ctx.send(embed=make_embed(desc="❌ Lựa chọn không hợp lệ. Vui lòng chọn `rock`, `paper`, hoặc `scissors`.", color=nextcord.Color.red()))
        user_choice_icon = valid_choices[choice]
        if choice in ["kéo", "búa", "bao"]:
            choice = {"kéo": "scissors", "búa": "rock", "bao": "paper"}[choice]
        bot_choice = random.choice(("rock", "paper", "scissors"))
        bot_choice_icon = valid_choices[bot_choice]
        try:
            async with self.bot.sessionmaker() as session:
                user = await self._get_user(session, ctx.author.id)
                if choice == bot_choice:
                    result, color = "Hòa!", nextcord.Color.blurple()
                elif (choice, bot_choice) in [("rock","scissors"), ("scissors","paper"), ("paper","rock")]:
                    user.wallet += 10
                    result, color = "Bạn thắng! **+10 🪙**", nextcord.Color.green()
                else:
                    result, color = "Bạn thua!", nextcord.Color.orange()
                await session.commit()
            desc = f"Bạn chọn {user_choice_icon} vs {bot_choice_icon} Bot → {result}"
            await ctx.send(embed=make_embed(desc=desc, color=color))
            await award(self.bot, ctx.author.id, "oantutim")
        except SQLAlchemyError as e:
            logger.error(f"Lỗi DB trong oantutim: {e}")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi cập nhật ví.", color=nextcord.Color.red()))

    @commands.command(name="quiz")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_quiz(self, ctx: commands.Context):
        """❓ Làm 5 câu hỏi tùy độ khó."""
        async with self.bot.sessionmaker() as session:
            user = await self._get_user(session, ctx.author.id)
            desc = ""
            for em, lvl in EMOJI_LEVEL.items():
                unlocked = getattr(user, f"quiz_win_{lvl}", 0) >= UNLOCK_REQ.get(lvl, 0)
                desc += f"{em} → {lvl.capitalize()}{'' if unlocked or lvl == 'easy' else ' 🔒'}\n"
            menu = await ctx.send(embed=make_embed(title="❓ Chọn độ khó Quiz", desc=desc, color=nextcord.Color.blue()))
            for em in EMOJI_LEVEL:
                await menu.add_reaction(em)
            def check_react(r, u):
                return u.id == ctx.author.id and r.message.id == menu.id and str(r.emoji) in EMOJI_LEVEL
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check_react)
                level = EMOJI_LEVEL[str(reaction.emoji)]
                await menu.delete()
            except asyncio.TimeoutError:
                return await menu.edit(embed=make_embed(desc="⌛ Hết giờ chọn!", color=nextcord.Color.red()), view=None)
            if level != "easy" and getattr(user, f"quiz_win_{level}", 0) < UNLOCK_REQ[level]:
                return await ctx.send(embed=make_embed(desc=f"🔒 Bạn cần thắng **{UNLOCK_REQ[level]}** câu hỏi ở độ khó trước đó để mở khóa `{level}`.", color=nextcord.Color.orange()))
            pool = [q for q in TRIVIA_POOL if q["level"] == level]
            if len(pool) < 5:
                return await ctx.send(embed=make_embed(desc="⚠️ Không đủ câu hỏi cho độ khó này.", color=nextcord.Color.orange()))
            questions = random.sample(pool, 5)
            wins = 0
            for idx, q in enumerate(questions, start=1):
                opts = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(q["options"]))
                prompt = make_embed(title=f"❓ Câu {idx}/5", desc=f"{q['question']}\n\n{opts}\n⏳ Gõ số trong 15s.", color=nextcord.Color.teal())
                await ctx.send(embed=prompt)
                def check_msg(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    msg = await self.bot.wait_for("message", timeout=15, check=check_msg)
                    choice = int(msg.content.strip()) - 1
                except (asyncio.TimeoutError, ValueError, TypeError):
                    await ctx.send(embed=make_embed(desc="⌛ Hết giờ hoặc sai định dạng.", color=nextcord.Color.red()), delete_after=3)
                    continue
                if 0 <= choice < len(q["options"]) and q["options"][choice] == q["answer"]:
                    wins += 1
                    await ctx.send(embed=make_embed(desc="✅ Chính xác!", color=nextcord.Color.green()), delete_after=2)
                else:
                    await ctx.send(embed=make_embed(desc=f"❌ Sai! Đáp án: **{q['answer']}**", color=nextcord.Color.orange()), delete_after=4)
            setattr(user, f"quiz_win_{level}", getattr(user, f"quiz_win_{level}", 0) + wins)
            await session.commit()
            if sum(getattr(user, f"quiz_win_{lvl}", 0) for lvl in EMOJI_LEVEL.values()) >= 10:
                await award(self.bot, ctx.author.id, "quiz_master")
            await ctx.send(embed=make_embed(desc=f"🏁 Kết thúc! Bạn đúng **{wins}/5**.", color=nextcord.Color.blurple()))

    @commands.command(name="speedrunquiz")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cmd_speedrunquiz(self, ctx: commands.Context, rounds: int = 3):
        """🏁 Quiz easy liên tục, sai một câu là dừng."""
        if not 1 <= rounds <= 10:
            return await ctx.send(embed=make_embed(desc="⚠️ Số vòng phải từ 1 đến 10.", color=nextcord.Color.red()))
        
        pool = [q for q in TRIVIA_POOL if q["level"] == "easy"]
        if len(pool) < rounds:
            return await ctx.send(embed=make_embed(desc="⚠️ Không đủ câu hỏi easy để chạy speedrun.", color=nextcord.Color.orange()))
        
        streak = 0
        questions = random.sample(pool, rounds)
        for i, q in enumerate(questions, start=1):
            opts = "\n".join(f"{j+1}. {opt}" for j, opt in enumerate(q["options"]))
            await ctx.send(embed=make_embed(title=f"🏁 Quiz {i}/{rounds}", desc=f"{q['question']}\n\n{opts}\n⏳ Gõ số trong 10s.", color=nextcord.Color.dark_gold()))
            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
            try:
                msg = await self.bot.wait_for("message", timeout=10.0, check=check)
                idx = int(msg.content.strip()) - 1
            except (asyncio.TimeoutError, ValueError, TypeError):
                await ctx.send(embed=make_embed(desc="⌛ Hết giờ hoặc sai định dạng! Speedrun kết thúc.", color=nextcord.Color.red()))
                break
            if 0 <= idx < len(q["options"]) and q["options"][idx] == q["answer"]:
                streak += 1
                await ctx.send(embed=make_embed(desc="✅ Đúng!", color=nextcord.Color.green()), delete_after=2)
            else:
                await ctx.send(embed=make_embed(desc=f"❌ Sai! Đáp án đúng là: **{q['answer']}**. Speedrun kết thúc.", color=nextcord.Color.red()))
                break
        
        if streak >= rounds:
            await award(self.bot, ctx.author.id, "speedrunquiz")
        
        await ctx.send(embed=make_embed(desc=f"⏱️ Kết thúc! Chuỗi đúng của bạn: `{streak}/{rounds}`", color=nextcord.Color.gold()))

def setup(bot: commands.Bot):
    bot.add_cog(MinigameCog(bot))
