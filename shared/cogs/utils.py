# cogs/utils.py

import time
import random
import datetime

import nextcord
from nextcord.ext import commands
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from shared.db import AsyncSession
from shared.models.user import User
from shared.utils.embed import make_embed

# --------------- Constants & Config ---------------

# Dev IDs (có thể load từ bot.config)
DEV_IDS = [1064509322228412416, 1327287076122787940]

# Spam‐guard thresholds
SPAM_WINDOW   = 10    # seconds
SPAM_LIMIT    = 5     # commands
SPAM_CHANCE   = 0.3   # 30% chance to reply
SPAM_REPLIES = [
    "Bot đang thở, đợi xíu đi…",
    "Nghiện lệnh rồi à? Chill tí nào!",
    "Bớt spam đi!",
    "Chậm lại đi, đừng làm bot mệt.",
    "Bình tĩnh nào, spam nhiều làm gì!"
]

# --------------- Pagination View ---------------

class HelpPageView(nextcord.ui.View):
    """Multi‐page navigation for embeds via buttons."""
    def __init__(self, embeds: list[nextcord.Embed], timeout: float = 60):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.index  = 0

    @nextcord.ui.button(label="◀️", style=nextcord.ButtonStyle.secondary)
    async def prev_page(self, button, interaction):
        self.index = (self.index - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @nextcord.ui.button(label="📘", style=nextcord.ButtonStyle.primary, disabled=True)
    async def center(self, *_): 
        pass

    @nextcord.ui.button(label="▶️", style=nextcord.ButtonStyle.secondary)
    async def next_page(self, button, interaction):
        self.index = (self.index + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

# --------------- Utils Cog ---------------

class UtilsCog(commands.Cog):
    """🧰 Bot utilities: help, info, status, leaderboard, spam‐guard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self._spam: dict[int, list[float]] = {}

    # ---------- Spam guard ----------
    @commands.Cog.listener()
    async def track_command_spam(bot, self, ctx: commands.Context):
        now = time.time()
        arr = [t for t in self._spam.get(ctx.author.id, []) if now - t < SPAM_WINDOW]
        arr.append(now)
        self._spam[ctx.author.id] = arr

        if len(arr) > SPAM_LIMIT and random.random() < SPAM_CHANCE:
            await ctx.send(random.choice(SPAM_REPLIES), delete_after=5)

    # ---------- Help command ----------
    @commands.command(name="bothelp")
    async def bothelp(self, ctx: commands.Context):
        """📖 Hiển thị danh sách lệnh & hướng dẫn"""
        pages: list[nextcord.Embed] = []

        # Page 1: Command list
        e1 = make_embed(title="📖 IminiBot Help (v3.8)", color=nextcord.Color.teal())
        e1.add_field(name="💼 Job & Skills",
                    value="`i!setjob`, `i!job`, `i!work`, `i!skills`, `i!upgrade_skill`",
                    inline=False)
        e1.add_field(name="🎮 Minigame",
                    value="`i!oneshot`, `i!inverseguess`, `i!burncoin`, `i!spill`",
                    inline=False)
        e1.add_field(name="🧠 Quiz",
                    value="`i!quiz`, `i!speedrunquiz`",
                    inline=False)
        e1.add_field(name="💰 Economy",
                    value="`i!daily`, `i!coinflip`, `i!beg`, `i!crime`, `i!give`, `i!pray`, `i!repay`, `i!deposit`, `i!withdraw`",
                    inline=False)
        e1.add_field(name="🛍️ Shop & Items",
                    value="`i!shop`, `i!sell`, `i!fish`, `i!trash`, `i!inventory`, `i!use`",
                    inline=False)
        e1.add_field(name="📜 Quest & Giftcode",
                    value="`i!quest`, `i!complete`, `i!mygiftcode`, `i!redeemcode`",
                    inline=False)
        e1.add_field(name="🎖️ Achievement",
                    value="`i!achievements`, `i!achievementkeys`",
                    inline=False)
        e1.add_field(name="👤 Profile & Social",
                    value="`i!profile`, `i!trust`, `i!setflex`, `i!unsetflex`, `i!shoutout`",
                    inline=False)
        e1.add_field(name="🧪 BETA Features",
                    value="`i!previewcard`, `i!cardstyle`, `i!setframe`, `i!setcolor`, `i!settheme`, `Còn nữa...`",
                    inline=False)
        pages.append(e1)

        # Page 2: Quiz guide
        quiz_desc = (
            "**🎮 Cách chơi Quiz:**\n"
            "Dùng `i!quiz`, chọn độ khó bằng emoji, trả lời 5 câu hỏi bằng cách gõ số (1–4).\n\n"
            "**📈 Mở khóa độ khó:**\n"
            "🟢 Easy: mặc định mở\n"
            "🔵 Normal: thắng 10 lần Easy\n"
            "🔴 Hard: thắng 50 lần Normal\n"
            "⚫ Extreme: thắng 500 lần Hard\n"
            "❗ Nightmare: thắng 1000 lần Extreme\n\n"
            "**⏱️ Speedrun:** Dùng `i!speedrunquiz` để chơi Easy liên tục, ghi streak cao nhất.\n"
            "**🏅 Thành tích:** Mỗi cấp quiz có badge riêng khi hoàn thành đủ số lần thắng."
        )
        e2 = make_embed(title="📘 Hướng dẫn Quiz", desc=quiz_desc, color=nextcord.Color.blue())
        pages.append(e2)

        # Page 3: Job & Skill guide
        job_desc = (
            "**💼 Job System:**\n"
            "Dùng `!setjob` để chọn nghề, `!work` để làm việc nhận xu.\n\n"
            "**🧠 Skills:**\n"
            "Mỗi job có skill riêng, nâng cấp bằng `!upgrade_skill`, xem bằng `!skills`.\n"
            "Khi đủ mastery → mở hiệu ứng đặc biệt hoặc badge nghề."
        )
        e3 = make_embed(title="📘 Hướng dẫn Job & Skill", desc=job_desc, color=nextcord.Color.green())
        pages.append(e3)

        # Page 4: Hidden & Curse
        hidden_desc = (
            "**🧪 Hidden Trigger:**\n"
            "`Có các lệnh ẩn ngẫu nhiên — có thể mở badge hoặc phản hồi kỳ quặc.\n\n"
            "**🕳️ Curse Emoji:**\n"
            "Spam emoji như `🕳️` sau 5 lệnh khác nhau → có thể bị hệ thống soi và mở badge ẩn.\n"
            "Không có lệnh tra cứu — chỉ có hành vi bị ghi nhận."
        )
        e4 = make_embed(title="📘 Hệ thống ẩn & lời nguyền", desc=hidden_desc, color=nextcord.Color.dark_grey())
        pages.append(e4)

        await ctx.send(embed=pages[0], view=HelpPageView(pages))

    # ---------- Bot info ----------
    @commands.command(name="botinfo")
    async def botinfo(self, ctx: commands.Context):
        """ℹ️ Hiển thị thông tin cơ bản về bot."""
        uptime = datetime.datetime.now(datetime.timezone.utc) - self.start_time
        embed = make_embed(title="ℹ️ IminiBot Info", color=nextcord.Color.dark_blue())
        embed.add_field(name="📦 Version",
                        value=self.bot.config.get("version", "3.8"),
                        inline=True)
        embed.add_field(name="⏱️ Uptime",
                        value=str(uptime).split('.')[0],
                        inline=True)
        embed.add_field(name="🛠️ Owner",
                        value="irammini",
                        inline=True)
        embed.add_field(name="📚 Servers",
                        value=str(len(self.bot.guilds)),
                        inline=True)
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        embed.add_field(name="👥 Total Users",
                        value=str(total_users),
                        inline=True)
        await ctx.send(embed=embed)

    # ---------- Status (dev only) ----------
    @commands.command(name="status")
    async def status(self, ctx: commands.Context, detail: str = None):
        bot = self.bot
        """🧭 Dev-only: giám sát bot & thống kê DB."""
        if ctx.author.id not in DEV_IDS:
            return await ctx.send(embed=make_embed(
                desc="❌ Bạn không có quyền.", color=nextcord.Color.red()
            ), delete_after=5)

        now = datetime.datetime.now(datetime.timezone.utc)
        uptime = now - self.start_time
        embed = make_embed(title="🧭 System Monitor", color=nextcord.Color.blurple())
        embed.add_field(name="⏱️ Uptime",
                        value=str(uptime).split('.')[0],
                        inline=False)
        embed.add_field(name="🛸 Servers",
                        value=str(len(self.bot.guilds)),
                        inline=True)

        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        embed.add_field(name="👥 Users",
                        value=str(total_users),
                        inline=True)

        commands_used = getattr(self.bot, "command_counter", {}).get("total", 0)
        embed.add_field(name="🧠 Commands Used",
                        value=str(commands_used),
                        inline=False)

        cogs_status = "\n".join(f"`{n}`: 🟢 Active" for n in self.bot.cogs)
        embed.add_field(name="📂 Cogs",
                        value=cogs_status or "-",
                        inline=False)

        if detail == "detail":
            try:
                async with bot.sessionmaker() as session:
                    total_u = await session.scalar(select(func.count(User.id)))
                    total_coin = await session.scalar(select(func.sum(User.wallet)))
                    total_voice = await session.scalar(select(func.sum(User.voice_time)))
                embed.add_field(name="📊 DB Users",
                                value=str(total_u),
                                inline=True)
                embed.add_field(name="🪙 Total Coins",
                                value=str(total_coin or 0),
                                inline=True)
                embed.add_field(name="🎤 Total Voice Time",
                                value=f"{(total_voice or 0)/3600:.1f}h",
                                inline=True)
            except SQLAlchemyError:
                embed.add_field(name="⚠️ DB Error",
                                value="Không thể truy vấn",
                                inline=False)

        await ctx.send(embed=embed)

    # ---------- Leaderboard ----------
    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context, category: str = "cash"):
        bot = self.bot
        """
        🏆 !leaderboard <metric> — xem top 10.
        Metrics: cash, level, voicetime, streak
        """
        METRICS = {
            "cash":     (User.wallet,    "🪙 Wallet"),
            "level":    (User.level,     "⭐ Level"),
            "voicetime":(User.voice_time,"🎤 Voice Time"),
            "streak":   (User.streak,    "🔥 Streak")
        }
        if category not in METRICS:
            return await ctx.send(embed=make_embed(
                desc="❌ Metric không hợp lệ, các metric có sẵn là cash, level, voicetime và streak.", color=nextcord.Color.red()
            ), delete_after=5)

        col, label = METRICS[category]
        try:
            async with bot.sessionmaker() as session:
                rows = await session.execute(
                    select(User.id, col).order_by(col.desc()).limit(10)
                )
                top = rows.all()
        except SQLAlchemyError:
            return await ctx.send(embed=make_embed(
                desc="❌ Lỗi DB.", color=nextcord.Color.red()
            ))

        if not top:
            return await ctx.send(embed=make_embed(
                desc="📭 Không có dữ liệu để hiển thị.", color=nextcord.Color.dark_gray()
            ))

        text = "\n".join(f"{i+1}. <@{uid}> — {val}" for i, (uid, val) in enumerate(top))
        await ctx.send(embed=make_embed(
            title=f"🏆 Top {label}", desc=text, color=nextcord.Color.gold()
        ))

# --------------- Setup ---------------

def setup(bot: commands.Bot):
    bot.add_cog(UtilsCog(bot))