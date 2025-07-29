# cogs/levelsystem.py

import time
import math
import logging
import datetime
import random
import secrets

import nextcord
from nextcord.ext import commands
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from shared.models.achievement import UserAchievement

from shared.db import AsyncSession
from shared.models.user import User
from shared.utils.embed import make_embed

logger = logging.getLogger(__name__)
LEVEL_UP_CHANNEL_ID = 0

# --- View for ID Agreement ---
class IDAgreementView(nextcord.ui.View):
    def __init__(self, bot, author: nextcord.Member):
        super().__init__(timeout=300) # 5 phút để quyết định
        self.bot = bot
        self.author = author
        self.decision = None

    async def _update_user(self, uid: int, **fields):
        async with self.bot.sessionmaker() as session:
            await session.execute(update(User).where(User.id == uid).values(**fields))
            await session.commit()

    @nextcord.ui.button(label="Đồng ý", style=nextcord.ButtonStyle.success)
    async def agree(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Bạn không phải người yêu cầu.", ephemeral=True)

        async with self.bot.sessionmaker() as session:
            # Tạo ID duy nhất theo format IM-XXXX
            while True:
                new_id = f"IM-{random.randint(1000, 9999)}"
                existing = await session.scalar(select(User.id).where(User.imini_id == new_id))
                if not existing:
                    break
            
            await self._update_user(self.author.id, imini_id=new_id)

        embed = make_embed(
            title="✅ Đăng ký thành công!",
            desc=f"Chào mừng bạn đến với hệ thống Imini ID. ID của bạn là: `{new_id}`",
            color=nextcord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.decision = True
        self.stop()

    @nextcord.ui.button(label="Không đồng ý", style=nextcord.ButtonStyle.danger)
    async def disagree(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Bạn không phải người yêu cầu.", ephemeral=True)

        # Đặt cooldown 24 giờ vào templog
        cooldown_until = int(time.time()) + 86400
        async with self.bot.sessionmaker() as s:
            user = await s.get(User, self.author.id)
            if user:
                # Cần đảm bảo templog là một dict
                if not isinstance(user.templog, dict):
                    user.templog = {}
                user.templog['id_request_cooldown'] = cooldown_until
                await s.commit()

        embed = make_embed(
            title="❌ Đã hủy yêu cầu",
            desc=f"Bạn đã từ chối các điều khoản. Bạn có thể yêu cầu lại sau <t:{cooldown_until}:R>.",
            color=nextcord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.decision = False
        self.stop()

class LevelSystemCog(commands.Cog):
    """📈 Hệ thống Level, XP, và Imini ID"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_msg_ts: dict[int, float] = {}
        self.voice_start: dict[int, float] = {}
        self.temp_tokens: dict[int, dict] = {}

    async def _get_user(self, uid: int) -> User | None:
        async with self.bot.sessionmaker() as session:
            return await session.get(User, uid)

    # ... (on_message, on_voice_state_update, _announce_level_up không đổi) ...
    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot or not message.guild: return
        uid = message.author.id
        now = time.time()
        if now - self.last_msg_ts.get(uid, 0) < 60: return
        self.last_msg_ts[uid] = now
        try:
            async with self.bot.sessionmaker() as session:
                user = await session.get(User, uid) or User(id=uid)
                user.level = user.level or 1
                gain = 15 + (user.level * 5)
                user.xp = (user.xp or 0) + gain
                last_day = datetime.date.fromtimestamp(user.last_daily or 0)
                today = datetime.date.today()
                if today != last_day:
                    user.streak = (user.streak or 0) + 1
                    user.last_daily = int(now)
                req = 50 + (user.level * 25)
                if user.xp >= req:
                    user.xp -= req
                    user.level += 1
                    await session.commit()
                    await self._announce_level_up(message.author, user.level)
                else:
                    await session.commit()
        except SQLAlchemyError as e:
            logger.exception(f"LevelSystem on_message DB error: {e}")
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or not member.guild: return
        uid = member.id
        now = time.time()
        if after.channel and not before.channel:
            self.voice_start[uid] = now
            return
        if before.channel and not after.channel and uid in self.voice_start:
            start = self.voice_start.pop(uid)
            duration_minutes = (now - start) / 60
            try:
                async with self.bot.sessionmaker() as session:
                    user = await session.get(User, uid) or User(id=uid)
                    user.voice_time = (user.voice_time or 0) + duration_minutes
                    session.add(user)
                    await session.commit()
            except SQLAlchemyError:
                logger.exception("LevelSystem on_voice DB error")
    async def _announce_level_up(self, member: nextcord.Member, new_level: int):
        ch_id = self.bot.config.get("levelup_channel", LEVEL_UP_CHANNEL_ID)
        ch = self.bot.get_channel(ch_id)
        if not ch: return
        embed = make_embed(title="🎉 Level Up!", desc=f"{member.mention} đã lên **Level {new_level}**", color=nextcord.Color.gold())
        await ch.send(embed=embed)
        roles_map = self.bot.config.get("level_roles", {})
        role_id_to_add = roles_map.get(str(new_level))
        if role_id_to_add:
            try:
                role = member.guild.get_role(int(role_id_to_add))
                if role: await member.add_roles(role, reason=f"Đạt Level {new_level}")
            except (ValueError, nextcord.HTTPException) as e:
                logger.warning(f"Không thể gán role level up: {e}")

    # --- Imini ID Commands ---
    @commands.command(name="requestid")
    async def cmd_requestid(self, ctx: commands.Context):
        uid = ctx.author.id
        user = await self._get_user(uid)

        if not user:
            return await ctx.send(embed=make_embed(desc="❌ Không tìm thấy hồ sơ của bạn.", color=nextcord.Color.red()))
        if user.imini_id:
            return await ctx.send(embed=make_embed(desc=f"✅ Bạn đã có Imini ID rồi: `{user.imini_id}`", color=nextcord.Color.blue()))
        if user.level < 50:
            return await ctx.send(embed=make_embed(desc="❌ Bạn cần đạt **Level 50** để có thể yêu cầu Imini ID.", color=nextcord.Color.red()))
        
        cooldown = user.templog.get('id_request_cooldown', 0)
        if time.time() < cooldown:
            return await ctx.send(embed=make_embed(desc=f"⏳ Bạn đang trong thời gian chờ. Vui lòng thử lại sau <t:{int(cooldown)}:R>.", color=nextcord.Color.orange()))

        rules_desc = (
            "Chào mừng bạn đến với hệ thống Imini ID. Vui lòng đọc kỹ và đồng ý với các điều khoản sau:\n\n"
            "**Luật 1:** Không mua bán, trao đổi ID số đẹp bằng tài khoản discord.\n"
            "**Luật 2:** Không tạo tài khoản clone để kiếm thêm Imini ID.\n"
            "**Luật 3:** Bạn phải chịu trách nhiệm bảo mật token nếu đã tạo, không được chia sẻ cho bất kỳ ai. Dev không bao giờ yêu cầu bạn cung cấp token.\n\n"
            "*Lưu ý: Imini ID chỉ là ảo, không sử dụng cho mục đích ngoài đời thực.*"
        )
        embed = make_embed(title="📜 Điều khoản đăng ký Imini ID", desc=rules_desc, color=nextcord.Color.blurple())
        view = IDAgreementView(self.bot, ctx.author)
        
        try:
            await ctx.author.send(embed=embed, view=view)
            await ctx.message.add_reaction("✅")
            await ctx.send("Vui lòng kiểm tra tin nhắn riêng (DM) để hoàn tất đăng ký.", delete_after=10)
        except nextcord.Forbidden:
            await ctx.send("❌ Tôi không thể gửi tin nhắn riêng cho bạn. Vui lòng kiểm tra cài đặt quyền riêng tư.")

    @commands.command(name="myid")
    async def cmd_myid(self, ctx: commands.Context):
        user = await self._get_user(ctx.author.id)
        try:
            if user and user.imini_id:
                await ctx.author.send(f"Imini ID của bạn là: `{user.imini_id}`")
            else:
                await ctx.author.send("Bạn chưa có Imini ID. Dùng `!requestid` để nhận.")
            await ctx.message.add_reaction("✅")
        except nextcord.Forbidden:
            await ctx.send("❌ Tôi không thể gửi tin nhắn riêng cho bạn. Vui lòng kiểm tra cài đặt quyền riêng tư.")

    @commands.command(name="generatetoken")
    async def cmd_generatetoken(self, ctx: commands.Context):
        uid = ctx.author.id
        now = time.time()
        
        existing_token = self.temp_tokens.get(uid)
        if existing_token:
            if now < existing_token["expires_at"]:
                await ctx.author.send("❌ Bạn đã có một token đang hoạt động. Vui lòng đợi nó hết hạn.")
                await ctx.message.add_reaction("⚠️")
                return
            if now < existing_token["expires_at"] + 120: # 2 phút cooldown
                wait_time = int(existing_token["expires_at"] + 120 - now)
                await ctx.author.send(f"⏳ Vui lòng đợi **{wait_time} giây** nữa để tạo token mới.")
                await ctx.message.add_reaction("⏳")
                return

        token = secrets.token_hex(16)
        expires_at = now + 300 # 5 phút
        self.temp_tokens[uid] = {"token": token, "expires_at": expires_at}
        
        try:
            await ctx.author.send(f"🔑 Token tạm thời của bạn là:\n```\n{token}\n```\nNó sẽ hết hạn sau 5 phút.")
            await ctx.message.add_reaction("✅")
        except nextcord.Forbidden:
            await ctx.send("❌ Tôi không thể gửi tin nhắn riêng cho bạn. Vui lòng kiểm tra cài đặt quyền riêng tư.")
    
    # ... (setflex, unsetflex không đổi) ...
    @commands.command(name="setflex")
    async def set_flex(self, ctx: commands.Context, ach_key: str):
        bot = self.bot
        uid = ctx.author.id
        try:
            async with bot.sessionmaker() as session:
                result = await session.execute(select(UserAchievement).where(UserAchievement.user_id == uid, UserAchievement.ach_key == ach_key))
                exists = result.scalar_one_or_none() is not None
            if not exists:
                return await ctx.send(embed=make_embed(desc="❌ Bạn chưa mở badge này hoặc nhập sai key.", color=nextcord.Color.red()), delete_after=6)
            async with bot.sessionmaker() as session:
                await session.execute(update(User).where(User.id == uid).values(flex_key=ach_key))
                await session.commit()
            await ctx.send(embed=make_embed(desc=f"🎉 Đã đặt Flex Badge `{ach_key}`.", color=nextcord.Color.green()))
        except Exception:
            logger.exception("❌ setflex exception")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi đặt Flex Badge.", color=nextcord.Color.red()), delete_after=6)
    @commands.command(name="unsetflex")
    async def unset_flex(self, ctx: commands.Context):
        bot = self.bot
        uid = ctx.author.id
        try:
            async with bot.sessionmaker() as session:
                await session.execute(update(User).where(User.id == uid).values(flex_key=None))
                await session.commit()
            await ctx.send(embed=make_embed(desc="✅ Đã gỡ Flex Badge.", color=nextcord.Color.green()))
        except SQLAlchemyError:
            logger.exception("unsetflex DB error")
            await ctx.send(embed=make_embed(desc="❌ Lỗi khi gỡ flex badge.", color=nextcord.Color.red()), delete_after=5)

def setup(bot: commands.Bot):
    bot.add_cog(LevelSystemCog(bot))
