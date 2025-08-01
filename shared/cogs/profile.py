# cogs/profile.py

import re
import asyncio
import nextcord
from nextcord.ext import commands
from sqlalchemy import select, update, func, desc

# --- Local Imports ---
from shared.models.user import User
from shared.models.inventory import Inventory
from shared.models.achievement import Achievement as AchModel
from shared.data.fish import FISH_ITEMS
from shared.data.job_data import JOB_DATA
from shared.utils.embed import make_embed
from shared.utils.achievement import award

# --- Constants ---
HEX_COLOR_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}){1,2}$")
FRAMES = { "bronze": {"emoji": "🟦", "name": "Bronze Frame", "min_level": 25}, "silver": {"emoji": "🟨", "name": "Silver Frame", "min_level": 50}, "gold": {"emoji": "🟥", "name": "Gold Frame", "min_level": 75}, "platinum": {"emoji": "🟪", "name": "Platinum Frame", "min_level": 100}, "mythic": {"emoji": "👑", "name": "Mythic Frame", "min_level": 150} }
ITEM_PROFILE_EMOJI = "profile_emoji"
ITEM_FRAME_OVERRIDE = "frame_override"
ITEM_TITLE_CUSTOMIZE = "title_customizer"
ITEM_COLOR_ACCENT = "color_accent"
ITEM_CUSTOM_AVATAR = "custom_avatar"
ITEM_PROFILE_BANNER = "profile_banner"
ITEM_CUSTOM_FIELD = "custom_field"

# --- Profile View (Không thay đổi nhiều) ---
class ProfileView(nextcord.ui.View):
    def __init__(self, bot: commands.Bot, original_author: nextcord.Member, user_data: User, target: nextcord.Member, is_top_level: bool, frame_text: str):
        super().__init__(timeout=180)
        self.bot = bot
        self.original_author = original_author
        self.user = user_data
        self.target = target
        self.is_top_level = is_top_level
        self.frame_text = frame_text
        self.current_page = 1

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message("Đây là hồ sơ của người khác, bạn không thể tương tác.", ephemeral=True)
            return False
        return True

    async def _get_total_fish(self) -> int:
        fish_ids = [fid for fid, *_ in FISH_ITEMS]
        async with self.bot.sessionmaker() as s:
            q = await s.execute(
                select(func.sum(Inventory.quantity)).where(
                    Inventory.user_id == self.user.id,
                    Inventory.item_id.in_(fish_ids)
                )
            )
            return q.scalar() or 0

    def _get_base_embed(self, page_title: str) -> nextcord.Embed:
        ec = nextcord.Color.teal()
        if self.user.accent_color and HEX_COLOR_RE.match(self.user.accent_color):
            try:
                hex_value = self.user.accent_color.lstrip('#')
                ec = nextcord.Color(int(hex_value, 16))
            except (ValueError, TypeError): pass
        top_1_emoji = "🥇" if self.is_top_level else ""
        profile_emoji = self.user.profile_emoji or ""
        title_suffix = f" • {self.user.custom_title}" if self.user.custom_title else ""
        embed = make_embed(title=f"{page_title}: {self.target.display_name} {top_1_emoji}{profile_emoji}{title_suffix}", color=ec)
        avatar_url = self.user.custom_avatar_url or self.target.display_avatar.url
        embed.set_thumbnail(url=avatar_url)
        return embed

    async def create_main_embed(self) -> nextcord.Embed:
        embed = self._get_base_embed("📋 Hồ sơ chính")
        if self.user.profile_banner_url:
            embed.set_image(url=self.user.profile_banner_url)

        def target_xp(lv): return 50 + lv * 25
        xp_goal = target_xp(self.user.level)
        progress_pct = min(self.user.xp / xp_goal * 100, 100) if xp_goal > 0 else 0
        xp_display = f"{self.user.xp:,} / {xp_goal:,} XP ({progress_pct:.0f}%)"
        job_text = "Thất nghiệp"
        if self.user.job and self.user.job in JOB_DATA:
            job_meta = JOB_DATA[self.user.job]
            job_text = f"{job_meta['emoji']} {job_meta['name']}"
        embed.add_field(name="💰 Ví", value=f"{self.user.wallet:,} xu", inline=True)
        embed.add_field(name="🏦 Ngân hàng", value=f"{self.user.bank_balance:,} / {self.user.bank_limit:,} xu", inline=True)
        embed.add_field(name="💼 Công việc", value=job_text, inline=True)
        embed.add_field(name="🏷️ Level", value=str(self.user.level), inline=True)
        embed.add_field(name="⭐ XP", value=xp_display, inline=True)
        embed.add_field(name="🔥 Streak", value=f"{self.user.streak:,} ngày", inline=True)
        if self.user.voice_time and self.user.voice_time >= 1:
            embed.add_field(name="🎤 Voice", value=f"{self.user.voice_time:.2f} phút", inline=True)
        total_fish = await self._get_total_fish()
        embed.add_field(name="🐟 Tổng cá", value=f"{total_fish:,}", inline=True)
        embed.add_field(name="🤝 Trust", value=f"{self.user.trust_points or 0}", inline=True)
        embed.set_footer(text=f"Imini ID: {self.user.imini_id or 'Chưa có'} • Trang 1/2")
        return embed

    async def create_extra_embed(self) -> nextcord.Embed:
        embed = self._get_base_embed("✨ Thông tin thêm")
        embed.add_field(name="💬 Giới thiệu", value=f"```{self.user.about_me or 'Chưa có gì...'}```", inline=False)
        embed.add_field(name="💖 Vibe", value=f"_{self.user.vibe_text or 'Chưa set...'}_", inline=False)
        if self.user.custom_field_title and self.user.custom_field_value:
            embed.add_field(name=self.user.custom_field_title, value=self.user.custom_field_value, inline=False)
        flex_text = "—"
        if self.user.flex_key:
            async with self.bot.sessionmaker() as s:
                badge = await s.get(AchModel, self.user.flex_key)
            flex_text = badge.name if badge else "—"
        embed.add_field(name="🎖️ Flex Badge", value=flex_text, inline=True)
        embed.add_field(name="🎨 Frame", value=self.frame_text, inline=True)
        embed.set_footer(text=f"Status: {self.user.custom_status or 'Không có'} • Trang 2/2")
        return embed

    @nextcord.ui.button(label="Trang chính", style=nextcord.ButtonStyle.primary, emoji="📋", row=0)
    async def show_main_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page == 1: return await interaction.response.defer()
        self.current_page = 1
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Thông tin thêm", style=nextcord.ButtonStyle.secondary, emoji="✨", row=0)
    async def show_extra_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page == 2: return await interaction.response.defer()
        self.current_page = 2
        embed = await self.create_extra_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Làm mới", style=nextcord.ButtonStyle.success, emoji="🔃", row=1)
    async def refresh_profile(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer() # Phản hồi ngay để không bị timeout
        async with self.bot.sessionmaker() as s:
            fresh_user_data = await s.get(User, self.target.id)
        if not fresh_user_data:
            await interaction.followup.send("❌ Không thể làm mới, hồ sơ không tồn tại.", ephemeral=True)
            return
        self.user = fresh_user_data
        if self.current_page == 1:
            embed = await self.create_main_embed()
        else:
            embed = await self.create_extra_embed()
        await interaction.edit_original_message(embed=embed, view=self)

# --- Profile Cog (Đã Refactor) ---
class ProfileCog(commands.Cog):
    """📋 Quản lý hồ sơ, tích hợp hệ thống tùy chỉnh mới."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Helper Functions ---
    async def _get_user(self, uid: int) -> User | None:
        async with self.bot.sessionmaker() as s: return await s.get(User, uid)

    async def _update_user(self, uid: int, **fields):
        async with self.bot.sessionmaker() as s:
            await s.execute(update(User).where(User.id == uid).values(**fields))
            await s.commit()

    async def _has_item(self, uid: int, item_key: str) -> bool:
        async with self.bot.sessionmaker() as s:
            q = await s.execute(select(Inventory.quantity).where(Inventory.user_id == uid, Inventory.item_id == item_key))
            return (q.scalar() or 0) > 0

    def get_effective_frame(self, user: User) -> str:
        key_to_check = user.profile_frame
        if not key_to_check:
            for key, cfg in sorted(FRAMES.items(), key=lambda x: x[1]["min_level"], reverse=True):
                if user.level >= cfg["min_level"]:
                    key_to_check = key
                    break
        if key_to_check and key_to_check in FRAMES:
            cfg = FRAMES[key_to_check]
            return f"{cfg['emoji']} {cfg['name']}"
        return "Không có"

    async def _get_top_user_id(self, metric_column) -> int | None:
        async with self.bot.sessionmaker() as session:
            result = await session.execute(select(User.id).order_by(desc(metric_column)).limit(1))
            return result.scalar_one_or_none()

    async def _generate_profile_view_and_embed(self, author: nextcord.Member, target: nextcord.Member):
        """Hàm trợ giúp tạo embed và view, trả về (embed, view) hoặc (embed, None) nếu lỗi."""
        user = await self._get_user(target.id)
        if not user:
            return make_embed(desc="❌ Không tìm thấy hồ sơ, hãy thử kiếm chút tiền.", color=nextcord.Color.red()), None
        if user.profile_is_private and author.id != target.id:
            return make_embed(desc="🔒 Hồ sơ này ở chế độ riêng tư.", color=nextcord.Color.red()), None
        
        # Logic tính toán và trao thưởng
        top_level_user_id = await self._get_top_user_id(User.level)
        is_top_level = target.id == top_level_user_id
        if user.level >= 50: await award(self.bot, user.id, "lv50")
        if user.streak >= 7: await award(self.bot, user.id, "daily7")
        
        frame_text = self.get_effective_frame(user)
        view = ProfileView(self.bot, author, user, target, is_top_level, frame_text)
        initial_embed = await view.create_main_embed()
        return initial_embed, view

    # --- Commands ---
    @commands.command(name="profile", aliases=["p"])
    async def cmd_profile(self, ctx: commands.Context, member: nextcord.Member = None):
        """Hiển thị hồ sơ người dùng với thông báo chờ được nâng cấp."""
        target = member or ctx.author
        loading_message = await ctx.send("🔍 **Đang khởi tạo...**")

        try:
            await loading_message.edit(content="🗃️ **Đang truy vấn và xử lý dữ liệu...**")
            embed, view = await self._generate_profile_view_and_embed(ctx.author, target)
            
            await loading_message.delete()
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            try:
                await loading_message.delete()
            except nextcord.NotFound:
                pass # Tin nhắn đã bị xóa
            await ctx.send(embed=make_embed(desc=f"❌ Đã xảy ra lỗi khi tạo profile: {e}", color=nextcord.Color.red()))
            print(f"Lỗi trong lệnh profile: {e}")

    @commands.command(name="previewcombo")
    async def cmd_previewcombo(self, ctx: commands.Context):
        """Hiển thị combo profile embed và profile card với thông báo chờ."""
        loading_message = await ctx.send("🎨 **Đang chuẩn bị combo preview...**")
        try:
            # --- Phần 1: Profile Embed ---
            await loading_message.edit(content="📋 **Đang tải Profile Embed...** (1/2)")
            embed, view = await self._generate_profile_view_and_embed(ctx.author, ctx.author)
            await ctx.send(embed=embed, view=view)

            # --- Phần 2: Profile Card ---
            await loading_message.edit(content="🖼️ **Đang tải Profile Card...** (2/2)")
            profile_card_cog = self.bot.get_cog("ProfileCardCog")
            if profile_card_cog:
                # Giả sử cmd_previewcard sẽ gửi tin nhắn riêng
                await profile_card_cog.cmd_previewcard(ctx)
                await loading_message.delete()
            else:
                await loading_message.edit(content=None, embed=make_embed(desc="⚠️ Không thể tải được Profile Card.", color=nextcord.Color.orange()))

        except Exception as e:
            try:
                await loading_message.delete()
            except nextcord.NotFound:
                pass
            await ctx.send(embed=make_embed(desc=f"❌ Đã xảy ra lỗi khi tạo preview: {e}", color=nextcord.Color.red()))
            print(f"Lỗi trong lệnh previewcombo: {e}")

    # --- Các lệnh set đơn giản được refactor ---
    async def _simple_update_command(self, ctx, check_func, update_data, success_msg, failure_msg):
        """Hàm trợ giúp cho các lệnh set đơn giản."""
        if check_func and not await check_func():
            return await ctx.send(embed=make_embed(desc=failure_msg, color=nextcord.Color.red()))

        msg = await ctx.send("💾 **Đang lưu...**")
        try:
            await self._update_user(ctx.author.id, **update_data)
            await msg.edit(content=None, embed=make_embed(desc=success_msg, color=nextcord.Color.green()))
        except Exception as e:
            await msg.edit(content=None, embed=make_embed(desc=f"❌ Lỗi khi cập nhật: {e}", color=nextcord.Color.red()))

    @commands.command(name="setprivate")
    async def cmd_setprivate(self, ctx):
        user = await self._get_user(ctx.author.id)
        if not user: return
        new_status = not user.profile_is_private
        success_msg = f"✅ Hồ sơ của bạn giờ đã là **{'riêng tư' if new_status else 'công khai'}**."
        await self._simple_update_command(ctx, None, {"profile_is_private": new_status}, success_msg, "")

    @commands.command(name="setaboutme")
    async def cmd_setaboutme(self, ctx, *, text: str):
        if len(text) > 250: return await ctx.send(embed=make_embed(desc=f"❌ Giới thiệu quá dài! (Tối đa 250 ký tự)", color=nextcord.Color.red()))
        check = lambda: self._get_user(ctx.author.id).then(lambda u: u.level >= 15)
        await self._simple_update_command(ctx, None, {"about_me": text}, "✅ Đã cập nhật 'About Me'.", "❌ Bạn cần đạt **Level 15**.")

    @commands.command(name="setstatus")
    async def cmd_setstatus(self, ctx, *, text: str):
        if len(text) > 100: return await ctx.send(embed=make_embed(desc=f"❌ Status quá dài! (Tối đa 100 ký tự)", color=nextcord.Color.red()))
        await self._simple_update_command(ctx, None, {"custom_status": text}, "✅ Đã cập nhật status.", "")
    
    # ... (Bạn có thể áp dụng hàm _simple_update_command cho các lệnh set khác như setvibe, setavatar, setemoji, setcolor...)
    # Ví dụ cho setvibe:
    @commands.command(name="setvibe")
    async def cmd_setvibe(self, ctx, *, text: str):
        if len(text) > 100: return await ctx.send(embed=make_embed(desc=f"❌ Vibe quá dài! (Tối đa 100 ký tự)", color=nextcord.Color.red()))
        await self._simple_update_command(ctx, None, {"vibe_text": text}, "✅ Đã cập nhật vibe.", "")

    # Các lệnh mood và reset có thể giữ nguyên hoặc refactor tương tự nếu cần
    # ... (Code cho các lệnh mood, resetprofile, setframe, settitle... giữ nguyên như cũ để tránh quá phức tạp)
    # ... (Phần code còn lại của bạn)
    @commands.command(name="setavatar")
    async def cmd_setavatar(self, ctx, url: str = None):
        uid = ctx.author.id
        if not await self._has_item(uid, ITEM_CUSTOM_AVATAR): return await ctx.send(embed=make_embed(desc=f"❌ Bạn không có item `{ITEM_CUSTOM_AVATAR}`.", color=nextcord.Color.red()))
        avatar_url = url
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if not attachment.content_type.startswith('image/'): return await ctx.send(embed=make_embed(desc="❌ File đính kèm phải là ảnh.", color=nextcord.Color.red()))
            avatar_url = attachment.url
        if not avatar_url: return await ctx.send(embed=make_embed(desc="❌ Vui lòng cung cấp URL hoặc đính kèm một ảnh.", color=nextcord.Color.red()))
        await self._simple_update_command(ctx, None, {"custom_avatar_url": avatar_url}, "✅ Đã cập nhật avatar tùy chỉnh.", "")

    @commands.command(name="setemoji")
    async def cmd_setemoji(self, ctx, emoji: str):
        uid = ctx.author.id
        check = lambda: self._has_item(uid, ITEM_PROFILE_EMOJI)
        await self._simple_update_command(ctx, check, {"profile_emoji": emoji}, f"✅ Đã đặt emoji `{emoji}`.", f"❌ Bạn không có item `{ITEM_PROFILE_EMOJI}`.")

    @commands.command(name="setcolor")
    async def cmd_setcolor(self, ctx, hex_color: str):
        uid = ctx.author.id
        if not HEX_COLOR_RE.match(hex_color): return await ctx.send(embed=make_embed(desc="❌ Mã màu không hợp lệ. Ví dụ: #ffcc00", color=nextcord.Color.red()))
        check = lambda: self._has_item(uid, ITEM_COLOR_ACCENT)
        await self._simple_update_command(ctx, check, {"accent_color": hex_color}, f"✅ Đã đặt accent color `{hex_color}`.", f"❌ Bạn không có item `{ITEM_COLOR_ACCENT}`.")

    @commands.command(name="setframe")
    async def cmd_setframe(self, ctx, key: str):
        uid = ctx.author.id
        key = key.lower()
        if key not in FRAMES: return await ctx.send(embed=make_embed(desc="❌ Key frame không hợp lệ.", color=nextcord.Color.red()))
        user = await self._get_user(uid)
        has_item = await self._has_item(uid, ITEM_FRAME_OVERRIDE)
        if user.level < FRAMES[key]["min_level"] and not has_item: return await ctx.send(embed=make_embed(desc=f"❌ Cần level ≥{FRAMES[key]['min_level']} hoặc item Frame Override.", color=nextcord.Color.red()))
        await self._simple_update_command(ctx, None, {"profile_frame": key}, f"✅ Đã chọn frame `{key}`.", "")

    @commands.command(name="settitle")
    async def cmd_settitle(self, ctx, *, title: str):
        uid = ctx.author.id
        if len(title) > 50: return await ctx.send(embed=make_embed(desc=f"❌ Title quá dài! (Tối đa 50 ký tự)", color=nextcord.Color.red()))
        check = lambda: self._has_item(uid, ITEM_TITLE_CUSTOMIZE)
        await self._simple_update_command(ctx, check, {"custom_title": title}, f"✅ Đã đặt title `{title}`.", f"❌ Bạn không có item `{ITEM_TITLE_CUSTOMIZE}`.")

    @commands.command(name="setbanner")
    async def cmd_setbanner(self, ctx, url: str = None):
        uid = ctx.author.id
        if not await self._has_item(uid, ITEM_PROFILE_BANNER): return await ctx.send(embed=make_embed(desc=f"❌ Bạn không có item `{ITEM_PROFILE_BANNER}`.", color=nextcord.Color.red()))
        banner_url = url
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if not attachment.content_type.startswith('image/'): return await ctx.send(embed=make_embed(desc="❌ File đính kèm phải là ảnh.", color=nextcord.Color.red()))
            banner_url = attachment.url
        if not banner_url: return await ctx.send(embed=make_embed(desc="❌ Vui lòng cung cấp URL hoặc đính kèm một ảnh.", color=nextcord.Color.red()))
        await self._simple_update_command(ctx, None, {"profile_banner_url": banner_url}, "✅ Đã cập nhật banner.", "")

    @commands.command(name="setfield")
    async def cmd_setfield(self, ctx, *, content: str):
        uid = ctx.author.id
        if '|' not in content: return await ctx.send(embed=make_embed(desc="❌ Sai cú pháp. Dùng: `!setfield Tiêu đề | Nội dung`", color=nextcord.Color.red()))
        title, value = [part.strip() for part in content.split('|', 1)]
        if not title or not value: return await ctx.send(embed=make_embed(desc="❌ Tiêu đề và nội dung không được để trống.", color=nextcord.Color.red()))
        if len(title) > 50: return await ctx.send(embed=make_embed(desc=f"❌ Tiêu đề quá dài!", color=nextcord.Color.red()))
        if len(value) > 250: return await ctx.send(embed=make_embed(desc=f"❌ Nội dung quá dài!", color=nextcord.Color.red()))
        check = lambda: self._has_item(uid, ITEM_CUSTOM_FIELD)
        await self._simple_update_command(ctx, check, {"custom_field_title": title, "custom_field_value": value}, "✅ Đã cập nhật field tùy chỉnh.", f"❌ Bạn không có item `{ITEM_CUSTOM_FIELD}`.")

    @commands.group(name="mood", invoke_without_command=True)
    async def cmd_mood(self, ctx):
        await ctx.send_help(ctx.command)

    @cmd_mood.command(name="save")
    async def mood_save(self, ctx, name: str):
        user = await self._get_user(ctx.author.id)
        if len(user.profile_moods) >= 5: return await ctx.send(embed=make_embed(desc="❌ Bạn chỉ có thể lưu tối đa 5 mood.", color=nextcord.Color.red()))
        mood_data = {
            "profile_emoji": user.profile_emoji, "profile_frame": user.profile_frame,
            "custom_title": user.custom_title, "accent_color": user.accent_color,
            "custom_avatar_url": user.custom_avatar_url, "profile_banner_url": user.profile_banner_url,
            "about_me": user.about_me, "custom_status": user.custom_status, "vibe_text": user.vibe_text,
            "custom_field_title": user.custom_field_title, "custom_field_value": user.custom_field_value
        }
        user.profile_moods[name] = mood_data
        await self._simple_update_command(ctx, None, {"profile_moods": user.profile_moods}, f"✅ Đã lưu mood `{name}`.", "")

    @cmd_mood.command(name="load")
    async def mood_load(self, ctx, name: str):
        user = await self._get_user(ctx.author.id)
        mood_data = user.profile_moods.get(name)
        if not mood_data: return await ctx.send(embed=make_embed(desc=f"❌ Không tìm thấy mood `{name}`.", color=nextcord.Color.red()))
        await self._simple_update_command(ctx, None, mood_data, f"✅ Đã tải mood `{name}`.", "")

    @cmd_mood.command(name="list")
    async def mood_list(self, ctx):
        user = await self._get_user(ctx.author.id)
        if not user.profile_moods: return await ctx.send(embed=make_embed(desc="Bạn chưa lưu mood nào.", color=nextcord.Color.blue()))
        mood_list = "\n".join(f"- `{name}`" for name in user.profile_moods.keys())
        await ctx.send(embed=make_embed(title="🎭 Moods đã lưu", desc=mood_list, color=nextcord.Color.purple()))

    @cmd_mood.command(name="delete")
    async def mood_delete(self, ctx, name: str):
        user = await self._get_user(ctx.author.id)
        if name not in user.profile_moods: return await ctx.send(embed=make_embed(desc=f"❌ Không tìm thấy mood `{name}`.", color=nextcord.Color.red()))
        del user.profile_moods[name]
        await self._simple_update_command(ctx, None, {"profile_moods": user.profile_moods}, f"✅ Đã xóa mood `{name}`.", "")

    @commands.command(name="resetprofile")
    async def cmd_resetprofile(self, ctx):
        update_data = {
            "profile_emoji": None, "profile_frame": None, "custom_title": None, "accent_color": None,
            "custom_avatar_url": None, "profile_banner_url": None, "about_me": None, 
            "custom_status": None, "vibe_text": None, "custom_field_title": None, "custom_field_value": None
        }
        await self._simple_update_command(ctx, None, update_data, "✅ Đã reset profile của bạn về mặc định.", "")

def setup(bot: commands.Bot):
    bot.add_cog(ProfileCog(bot))
