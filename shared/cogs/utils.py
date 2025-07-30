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
DEV_IDS = [1064509322228412416, 1327287076122787940]
SPAM_WINDOW   = 10
SPAM_LIMIT    = 5
SPAM_CHANCE   = 0.3
SPAM_REPLIES = [ "Bot đang thở, đợi xíu đi…", "Nghiện lệnh rồi à? Chill tí nào!", "Bớt spam đi!", "Chậm lại đi, đừng làm bot mệt.", "Bình tĩnh nào, spam nhiều làm gì!" ]

# --------------- Pagination View ---------------
class HelpPageView(nextcord.ui.View):
    """Multi‐page navigation for embeds via buttons."""
    def __init__(self, embeds: list[nextcord.Embed], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.index  = 0
        self._update_buttons()

    def _update_buttons(self):
        """Cập nhật trạng thái của các nút."""
        self.children[0].disabled = self.index == 0
        self.children[2].disabled = self.index == len(self.embeds) - 1
        self.children[1].label = f"Trang {self.index + 1}/{len(self.embeds)}"

    @nextcord.ui.button(label="◀️", style=nextcord.ButtonStyle.secondary)
    async def prev_page(self, button, interaction):
        self.index -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @nextcord.ui.button(label="Trang 1/X", style=nextcord.ButtonStyle.primary, disabled=True)
    async def center(self, *_): 
        pass

    @nextcord.ui.button(label="▶️", style=nextcord.ButtonStyle.secondary)
    async def next_page(self, button, interaction):
        self.index += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

# --------------- Utils Cog ---------------
class UtilsCog(commands.Cog):
    """🧰 Bot utilities: help, info, status, leaderboard, spam‐guard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self._spam: dict[int, list[float]] = {}

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Spam guard listener."""
        now = time.time()
        arr = [t for t in self._spam.get(ctx.author.id, []) if now - t < SPAM_WINDOW]
        arr.append(now)
        self._spam[ctx.author.id] = arr

        if len(arr) > SPAM_LIMIT and random.random() < SPAM_CHANCE:
            await ctx.send(random.choice(SPAM_REPLIES), delete_after=5)

    @commands.command(name="bothelp")
    async def bothelp(self, ctx: commands.Context):
        """📖 Hiển thị danh sách lệnh & hướng dẫn cho phiên bản 3.9."""
        pages: list[nextcord.Embed] = []

        # --- Page 1: Command List (Mới) ---
        e1 = make_embed(title="📖 IminiBot Help (v3.9)", color=nextcord.Color.teal())
        e1.description = "Chào mừng đến với bản cập nhật **The Custom Profile**!"
        e1.add_field(name="👤 Profile & Tùy chỉnh (MỚI!)", value="`!profile`, `!setaboutme`, `!setvibe`, `!setstatus`, `!setavatar`, `!setbanner`, `!setfield`, `!setcolor`, `!setframe`, `!setemoji`, `!settitle`, `!resetprofile`, `!previewcard`", inline=False)
        e1.add_field(name="🎭 Danh tính & Moods (MỚI!)", value="`!requestid`, `!myid`, `!generatetoken`, `!mood save/load/list/delete`", inline=False)
        e1.add_field(name="💼 Job & Skills", value="`!setjob`, `!job`, `!work` (cooldown 30p), `!skills`, `!upgrade_skill`, `!joblist`", inline=False)
        e1.add_field(name="💰 Economy & Shop", value="`!daily`, `!coinflip`, `!beg`, `!crime`, `!give`, `!pray`, `!deposit`, `!withdraw`, `!shop`, `!inventory`", inline=False)
        e1.add_field(name="🎮 Minigame", value="`!guess`, `!inverseguess`, `!oneshot`, `!burncoin`, `!spill`, `!oantutim`, `!quiz`", inline=False)
        e1.add_field(name="🤝 Social & Achievement", value="`!trust` (yêu cầu Imini ID), `!shoutout`, `!setflex`, `!achievements`", inline=False)
        pages.append(e1)

        # --- Page 2: Hướng dẫn Profile Mới ---
        profile_desc = ("**Hệ thống Profile đã được làm lại hoàn toàn!**\n\n"
                        "**1. Profile Đa Trang:**\n"
                        "Dùng `!profile` để mở giao diện mới. Bấm nút `✨ Thông tin thêm` để xem các tùy chỉnh cá nhân.\n\n"
                        "**2. Tùy chỉnh sâu:**\n"
                        "Dùng các lệnh `!set...` để thay đổi mọi thứ, từ avatar, banner, màu sắc, đến các dòng text giới thiệu.\n\n"
                        "**3. Hệ thống Moods:**\n"
                        "Lưu lại toàn bộ 'vibe' profile của bạn với `!mood save <tên>` và tải lại bất cứ lúc nào với `!mood load <tên>`.")
        e2 = make_embed(title="📘 Hướng dẫn Profile v3.9", desc=profile_desc, color=nextcord.Color.green())
        pages.append(e2)

        # --- Page 3: Hướng dẫn Imini ID ---
        id_desc = ("**Imini ID là hệ thống danh tính mới của bạn.**\n\n"
                   "**1. Cách nhận:**\n"
                   "Khi đạt **Level 50**, dùng lệnh `!requestid`. Bot sẽ gửi DM để bạn đọc và đồng ý với các điều khoản.\n\n"
                   "**2. Lợi ích:**\n"
                   "Imini ID là điều kiện cần cho một số tính năng xã hội như `!trust` và sẽ được dùng cho các hệ thống chống gian lận trong tương lai.\n\n"
                   "**3. Bảo mật:**\n"
                   "Dùng `!myid` để xem ID và `!generatetoken` để tạo mã xác thực tạm thời. **Không bao giờ chia sẻ token của bạn cho bất kỳ ai.**")
        e3 = make_embed(title="📘 Hướng dẫn Imini ID", desc=id_desc, color=nextcord.Color.purple())
        pages.append(e3)

        # --- Page 4: Hướng dẫn Quiz (Phục hồi) ---
        quiz_desc = ("**🎮 Cách chơi Quiz:**\n"
                     "Dùng `!quiz`, chọn độ khó bằng emoji, trả lời 5 câu hỏi bằng cách gõ số (1–4).\n\n"
                     "**📈 Mở khóa độ khó:**\n"
                     "🟢 Easy: mặc định mở\n"
                     "🔵 Normal: thắng 10 lần Easy\n"
                     "🔴 Hard: thắng 50 lần Normal\n"
                     "⚫ Extreme: thắng 500 lần Hard\n"
                     "❗ Nightmare: thắng 1000 lần Extreme\n\n"
                     "**⏱️ Speedrun:** Dùng `!speedrunquiz` để chơi Easy liên tục, ghi streak cao nhất.\n"
                     "**🏅 Thành tích:** Mỗi cấp quiz có badge riêng khi hoàn thành đủ số lần thắng.")
        e4 = make_embed(title="📘 Hướng dẫn Quiz", desc=quiz_desc, color=nextcord.Color.blue())
        pages.append(e4)

        # --- Page 5: Hướng dẫn Job & Skill (Phục hồi) ---
        job_desc = ("**💼 Job System:**\n"
                    "Dùng `!joblist` để xem danh sách nghề. Dùng `!setjob <tên>` để chọn nghề nếu đủ level.\n\n"
                    "**🧠 Skills:**\n"
                    "Mỗi job có skill riêng, nâng cấp bằng `!upgrade_skill` (yêu cầu Job Token), xem bằng `!skills`.\n"
                    "Làm việc (`!work`) sẽ tăng Mastery, mỗi 5 Mastery nhận 1 Job Token.")
        e5 = make_embed(title="📘 Hướng dẫn Job & Skill", desc=job_desc, color=nextcord.Color.dark_green())
        pages.append(e5)

        # --- Page 6: Hướng dẫn Hệ thống ẩn (Phục hồi) ---
        hidden_desc = ("**🧪 Hidden Trigger:**\n"
                       "Có các lệnh ẩn ngẫu nhiên — có thể mở badge hoặc phản hồi kỳ quặc.\n\n"
                       "**🕳️ Curse Emoji:**\n"
                       "Spam các emoji đặc biệt sau 5 lệnh khác nhau → có thể bị hệ thống soi và mở badge ẩn.\n"
                       "Không có lệnh tra cứu — chỉ có hành vi bị ghi nhận.")
        e6 = make_embed(title="📘 Hệ thống ẩn & Lời nguyền", desc=hidden_desc, color=nextcord.Color.dark_grey())
        pages.append(e6)

        await ctx.send(embed=pages[0], view=HelpPageView(pages))

    @commands.command(name="botinfo")
    async def botinfo(self, ctx: commands.Context):
        """ℹ️ Hiển thị thông tin cơ bản về bot."""
        uptime = datetime.datetime.now(datetime.timezone.utc) - self.start_time
        embed = make_embed(title="ℹ️ IminiBot Info", color=nextcord.Color.dark_blue())
        embed.add_field(name="📦 Version", value=self.bot.config.get("version", "3.9"), inline=True)
        embed.add_field(name="⏱️ Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="🛠️ Owner", value="irammini", inline=True)
        embed.add_field(name="📚 Servers", value=str(len(self.bot.guilds)), inline=True)
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        embed.add_field(name="👥 Total Users", value=str(total_users), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context, category: str = "cash"):
        """🏆 Xem top 10. Metrics: cash, level, voicetime, streak"""
        METRICS = {
            "cash": (User.wallet, "🪙 Wallet"),
            "level": (User.level, "⭐ Level"),
            "voicetime": (User.voice_time, "🎤 Voice Time"),
            "streak": (User.streak, "🔥 Streak")
        }
        if category not in METRICS:
            return await ctx.send(embed=make_embed(desc="❌ Metric không hợp lệ. Các metric có sẵn là `cash`, `level`, `voicetime`, `streak`.", color=nextcord.Color.red()))

        col, label = METRICS[category]
        async with self.bot.sessionmaker() as session:
            rows = await session.execute(select(User.id, col).order_by(col.desc()).limit(10))
            top = rows.all()

        if not top:
            return await ctx.send(embed=make_embed(desc="📭 Không có dữ liệu để hiển thị.", color=nextcord.Color.dark_gray()))

        text = []
        for i, (uid, val) in enumerate(top):
            if category == "voicetime":
                formatted_val = f"{val:.2f} phút"
            elif category == "cash":
                formatted_val = f"{val:,} 🪙"
            else:
                formatted_val = f"{val:,}"
            text.append(f"**{i+1}.** <@{uid}> — {formatted_val}")

        await ctx.send(embed=make_embed(title=f"🏆 Top 10 {label}", desc="\n".join(text), color=nextcord.Color.gold()))

def setup(bot: commands.Bot):
    bot.add_cog(UtilsCog(bot))
