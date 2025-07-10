# cogs/achievement.py

import logging
import nextcord
from nextcord import Embed, Color
from nextcord.ext import commands
from sqlalchemy import select
from shared.db import AsyncSession
from shared.models.achievement import Achievement as AchModel, UserAchievement
from shared.data.achievements import ACH_LIST
from shared.utils.embed import make_embed
from shared.utils.achievement import award
from nextcord.ui import View, Button
from nextcord import Interaction, Embed, ButtonStyle

logger = logging.getLogger(__name__)

class AchievementPaginatorView(View):
    def __init__(self, embeds: list[Embed], timeout=120):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.index = 0

        self.prev_btn = Button(emoji="⬅️", style=ButtonStyle.secondary)
        self.next_btn = Button(emoji="➡️", style=ButtonStyle.secondary)
        self.stop_btn = Button(emoji="⏹️", style=ButtonStyle.red)

        self.prev_btn.callback = self.prev
        self.next_btn.callback = self.next
        self.stop_btn.callback = self.stop

        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)
        self.add_item(self.stop_btn)

    async def prev(self, interaction: Interaction):
        self.index = (self.index - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    async def next(self, interaction: Interaction):
        self.index = (self.index + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    async def stop(self, interaction: Interaction):
        await interaction.response.edit_message(view=None)

class AchievementCog(commands.Cog):
    """🎖️ Seed, cache và list badges."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.badge_names: dict[str, str] = {}
        self._initialized = False
        bot.badge_names = self.badge_names

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    @staticmethod
    def build_achievement_embeds(
        fields: list[tuple[str, str]],
        title: str = "🎖️ Thành tích",
        color: nextcord.Color = nextcord.Color.green()
    ) -> list[nextcord.Embed]:
        embeds = []
        for i in range(0, len(fields), 25):
            chunk = fields[i:i+25]
            eb = make_embed(title=title, color=color)
            for name, value in chunk:
                eb.add_field(name=name, value=value, inline=False)
            embeds.append(eb)
        return embeds

    @commands.Cog.listener()
    async def on_ready(self):
        if self._initialized:
            return
        self._initialized = True
        await self._seed_achievements()
        await self._load_cache()
        logger.info("✅ AchievementCog ready")

    async def _seed_achievements(self):
        async with self.bot.sessionmaker() as s:
            for key, name, desc, hidden in ACH_LIST:
                if not await s.get(AchModel, key):
                    s.add(AchModel(key=key, name=name, description=desc, hidden=hidden))
            await s.commit()
        logger.info("✅ Seed achievements complete")

    async def _load_cache(self):
        async with self.bot.sessionmaker() as s:
            rows = await s.execute(select(AchModel.key, AchModel.name))
        self.badge_names = {k: n for k, n in rows.all()}

    @commands.command(name="achievements")
    async def list_unlocked(self, ctx: commands.Context):
        """📜 Xem danh sách badges đã mở khóa (gọn từng trang)."""
        uid = ctx.author.id
        async with self.bot.sessionmaker() as s:
            rows = await s.execute(
                select(AchModel.name, UserAchievement.unlocked_at)
                .join(UserAchievement, AchModel.key == UserAchievement.ach_key)
                .where(UserAchievement.user_id == uid)
                .order_by(UserAchievement.unlocked_at)
            )
            items = rows.all()

        if not items:
            return await ctx.send(embed=make_embed(
                desc="📭 Bạn chưa mở khóa badge nào.",
                color=nextcord.Color.dark_gray()
            ))

        fields = [(name, f"<t:{ts}:R>") for name, ts in items]

        # Gói 10 badge mỗi embed
        embeds = []
        for i in range(0, len(fields), 10):
            eb = Embed(title="🏅 Badges đã mở", color=nextcord.Color.gold())
            for name, val in fields[i:i+10]:
                eb.add_field(name=name, value=val, inline=False)
            eb.set_footer(text=f"Trang {i//10+1}/{(len(fields)-1)//10+1}")
            embeds.append(eb)

        await ctx.send(embed=embeds[0], view=AchievementPaginatorView(embeds))

    @commands.command(name="achievementkeys")
    async def list_keys(self, ctx: commands.Context):
        """📜 Danh sách badge public."""
        public = [f"`{k}` → {n}" for k, n, _, hidden in ACH_LIST if not hidden]
        await ctx.send(embed=make_embed(
            title="🔑 Public Badge Keys",
            desc="\n".join(public) or "Không có badge public.",
            color=nextcord.Color.teal()
        ))

    @commands.command(name="unlock")
    async def manual_unlock(self, ctx: commands.Context, key: str):
        """🔓 Dev-only: unlock badge cho tester."""
        ok = await award(self.bot, ctx.author.id, key)
        if not ok:
            return await ctx.send(embed=make_embed(desc=f"Không unlock được `{key}`.", color=nextcord.Color.red()))
        await ctx.send(embed=make_embed(desc=f"✅ Đã unlock `{key}`!", color=nextcord.Color.green()))

def setup(bot: commands.Bot):
    bot.add_cog(AchievementCog(bot))