# cogs/job.py

import random
import nextcord
from nextcord.ext import commands

from shared.db import AsyncSession
from shared.data.job_data import JOB_DATA
from shared.models.user import User
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements
from shared.utils.achievement import award

class JobCog(commands.Cog):
    """💼 Job & Work & Skills: setjob, job, work, mastery, skills, upgrade_skill"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_user(self, uid: int) -> User:
        """Fetch or create user, ensure skills dict exists."""
        async with self.bot.sessionmaker() as sess:
            user = await sess.get(User, uid)
            if not user:
                user = User(id=uid)
                sess.add(user)
                await sess.commit()

            if user.skills is None:
                user.skills = {}
                sess.add(user)
                await sess.commit()

            return user

    @commands.command(name="setjob")
    @with_achievements("setjob")
    async def cmd_setjob(self, ctx: commands.Context, key: str):
        """
        ⚙️ !setjob <key> — chọn nghề nếu đủ Level ≥ level_required.
        Lấy level_required trực tiếp từ JOB_DATA[key]["level_required"].
        """
        key = key.lower()
        if key not in JOB_DATA:
            return await ctx.send(embed=make_embed(
                desc="❌ Nghề không tồn tại.", color=nextcord.Color.red()
            ))

        meta = JOB_DATA[key]
        req_level = meta.get("level_required", 0)

        user = await self._get_user(ctx.author.id)
        if user.level < req_level:
            return await ctx.send(embed=make_embed(
                desc=(
                    f"⚠️ Bạn cần Level ≥{req_level} "
                    f"để chọn nghề **{meta['name']}**."
                ),
                color=nextcord.Color.orange()
            ))

        # reset mastery & tokens & skills on job change
        user.job = key
        user.mastery = 0
        user.job_tokens = 0
        user.skills = {}
        async with self.bot.sessionmaker() as sess:
            sess.add(user)
            await sess.commit()

        await ctx.send(embed=make_embed(
            desc=f"✅ Bạn đã chọn nghề **{meta['name']}** {meta['emoji']}",
            color=nextcord.Color.green()
        ))

    @commands.command(name="job")
    async def cmd_job(self, ctx: commands.Context):
        """ℹ️ !job — xem nghề hiện tại, mastery, tokens, base pay."""
        user = await self._get_user(ctx.author.id)
        if not user.job:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Bạn chưa chọn nghề nào.", color=nextcord.Color.orange()
            ))

        meta = JOB_DATA[user.job]
        desc = (
            f"**{meta['name']}** {meta['emoji']}\n"
            f"Mastery: **{user.mastery or 0}**\n"
            f"Tokens: **{user.job_tokens or 0}**\n"
            f"Base Pay: **{meta['base_pay']}** 🪙\n"
            f"Requires Level: **{meta.get('level_required', 0)}**"
        )
        await ctx.send(embed=make_embed(
            title="💼 Thông tin nghề", desc=desc, color=nextcord.Color.blue()
        ))

    @commands.command(name="work")
    @with_achievements("work")
    async def cmd_work(self, ctx: commands.Context):
        user = await self._get_user(ctx.author.id)
        job_meta = JOB_DATA.get(user.job)

        if not job_meta:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Bạn chưa chọn nghề nào.", color=nextcord.Color.orange()
            ))

        base = job_meta.get("base_pay", 50)
        mult = 1
        buff_note = ""

        # Tính buff
        p = random.random()
        if p < 0.01:
            mult = 3
            buff_note = "🔧 Tăng ca x3"
        elif p < 0.10:
            mult = 2
            buff_note = "💪 Chăm chỉ x2"

        reward = base * mult
        user.wallet = (user.wallet or 0) + reward
        user.mastery = (user.mastery or 0) + 1

        note_lines = []
        if buff_note:
            note_lines.append(buff_note)

        if user.mastery % 5 == 0:
            user.job_tokens = (user.job_tokens or 0) + 1
            note_lines.append("🎟️ +1 Job Token")

        # Award badge nếu mastery đạt 100
        if user.mastery == 100 and user.job:
            badge_key = f"master_{user.job}"
            await award(self.bot, ctx.author.id, badge_key)

        # Lưu lại
        async with self.bot.sessionmaker() as sess:
            sess.add(user)
            await sess.commit()

        note = "\n".join(note_lines)
        msg = f"✅ Bạn làm việc và nhận **{reward}** 🪙"
        if note:
            msg += f"\n{note}"

        await ctx.send(embed=make_embed(desc=msg, color=nextcord.Color.green()))

    @commands.command(name="skills")
    async def cmd_skills(self, ctx: commands.Context):
        """🧠 !skills — xem kỹ năng của nghề & cấp hiện tại."""
        user = await self._get_user(ctx.author.id)
        if not user.job:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Bạn chưa chọn nghề.", color=nextcord.Color.orange()
            ))

        job_meta = JOB_DATA[user.job]
        skills = job_meta.get("skills", {})
        if not skills:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Nghề này chưa có kỹ năng nào.", color=nextcord.Color.orange()
            ))

        embed = nextcord.Embed(
            title=f"🧠 Kỹ năng nghề {job_meta['name']}",
            color=nextcord.Color.purple()
        )
        for skill_id, (name, desc, max_lv) in skills.items():
            cur_lv = user.skills.get(skill_id, 0)
            embed.add_field(
                name=f"{name} [{cur_lv}/{max_lv}]",
                value=desc,
                inline=False
            )

        embed.set_footer(text=f"Bạn có {user.job_tokens or 0} Job Tokens để nâng cấp.")
        await ctx.send(embed=embed)

    @commands.command(name="upgrade_skill")
    async def cmd_upgrade_skill(self, ctx: commands.Context, skill_id: str):
        """⬆️ !upgrade_skill <skill_id> — dùng 1 token để tăng 1 cấp skill."""
        user = await self._get_user(ctx.author.id)
        if not user.job:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Bạn chưa chọn nghề.", color=nextcord.Color.orange()
            ))

        job_meta = JOB_DATA[user.job]
        skills = job_meta.get("skills", {})
        if skill_id not in skills:
            return await ctx.send(embed=make_embed(
                desc="❌ Kỹ năng không tồn tại cho nghề này.", color=nextcord.Color.red()
            ))

        if (user.job_tokens or 0) < 1:
            return await ctx.send(embed=make_embed(
                desc="❌ Bạn không có đủ Job Tokens.", color=nextcord.Color.red()
            ))

        name, desc, max_lv = skills[skill_id]
        cur_lv = user.skills.get(skill_id, 0)
        if cur_lv >= max_lv:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Kỹ năng đã đạt cấp tối đa.", color=nextcord.Color.orange()
            ))

        # nâng cấp
        user.job_tokens -= 1
        user.skills[skill_id] = cur_lv + 1

        async with self.bot.sessionmaker() as sess:
            sess.add(user)
            await sess.commit()

        await ctx.send(embed=make_embed(
            desc=(f"✅ Bạn đã nâng `{name}` lên cấp **{cur_lv+1}/{max_lv}**.\n"
                  f"Còn lại **{user.job_tokens}** Job Tokens."),
            color=nextcord.Color.green()
        ))

        # gợi award achievement nếu cần
        if skill_id == "minigame_mastery" and user.skills[skill_id] == max_lv:
            await award(self.bot, ctx.author.id, "skill_master_gamer")

    @commands.command(name="joblist")
    async def cmd_joblist(self, ctx: commands.Context):
        """📋 !joblist — xem toàn bộ nghề có thể chọn."""
        user = await self._get_user(ctx.author.id)
        embed = nextcord.Embed(
            title="📋 Danh sách nghề nghiệp",
            description="Danh sách tất cả job có thể chọn bằng `!setjob <key>` nếu đủ level.",
            color=nextcord.Color.dark_gold()
        )

        # Nhóm nghề theo category
        categorized_jobs = {}
        for key, meta in JOB_DATA.items():
            cat = meta.get("category", "other")
            categorized_jobs.setdefault(cat, []).append((key, meta))

        # Lặp từng category
        for cat, jobs in categorized_jobs.items():
            group_lines = []
            for key, meta in sorted(jobs, key=lambda x: x[1].get("level_required", 0)):
                is_current = "🟢" if user.job == key else "⚪"
                line = (
                    f"{is_current} `{key}` — **{meta['name']}** {meta['emoji']} "
                    f"(L:{meta.get('level_required',0)} / 💰 {meta.get('base_pay',0)})"
                )
                group_lines.append(line)
            cat_label = {
                "industry": "⚒️ Sản xuất & Công nghiệp",
                "office": "💼 Văn phòng",
                "creative": "🎨 Sáng tạo",
                "entertainment": "🎮 Giải trí",
                "technical": "🔧 Kỹ thuật",
                "management": "🗂️ Quản lý",
                "scholar": "📚 Học thuật",
                "economy": "💰 Thương mại"
            }.get(cat, f"📦 {cat.capitalize()}")

            embed.add_field(name=cat_label, value="\n".join(group_lines), inline=False)

        await ctx.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(JobCog(bot))