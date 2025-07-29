# cogs/profilecard.py

import os
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import nextcord
from nextcord.ext import commands

from shared.models.user import User
from shared.models.achievement import Achievement as AchModel

# --- Constants ---
# SỬA LỖI: Di chuyển định nghĩa FRAMES vào đây để cog tự hoạt động
FRAMES = {
    "bronze":   {"emoji": "🟦", "name": "Bronze Frame",   "min_level": 25, "color": "#c28e5c"},
    "silver":   {"emoji": "🟨", "name": "Silver Frame",   "min_level": 50, "color": "#c0c0c0"},
    "gold":     {"emoji": "🟥", "name": "Gold Frame",     "min_level": 75, "color": "#ffd700"},
    "platinum": {"emoji": "🟪", "name": "Platinum Frame", "min_level": 100, "color": "#e5e4e2"},
    "mythic":   {"emoji": "🌈", "name": "Mythic Frame",   "min_level": 150, "color": "#a020f0"},
}

BASE_DIR  = os.path.dirname(__file__)
FONTS_DIR = os.path.join(BASE_DIR, "..", "fonts")

# --- Profile Card Cog ---
class ProfileCardCog(commands.Cog):
    """Cog render ảnh Profile Card PNG với banner, frame, và các tùy chỉnh mới."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Helper Methods ---
    async def _get_user(self, uid: int) -> User | None:
        async with self.bot.sessionmaker() as sess:
            return await sess.get(User, uid)

    async def _fetch_bytes(self, url: str) -> bytes | None:
        """Fetch bytes from a URL, returns None on failure."""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url) as r:
                    if r.status == 200:
                        return await r.read()
        except Exception:
            return None
        return None

    def _load_font(self, name: str, size: int) -> ImageFont.FreeTypeFont:
        """Loads a font file, with a fallback."""
        path = os.path.join(FONTS_DIR, name)
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except IOError:
                return ImageFont.load_default()

    def _get_effective_frame_key(self, user: User) -> str:
        """Chọn frame override hoặc auto theo level."""
        if user.profile_frame in FRAMES:
            return user.profile_frame
        
        # SỬA LỖI: Sắp xếp frame bằng cách dùng hằng số FRAMES cục bộ
        sorted_frames = sorted(
            FRAMES.items(),
            key=lambda item: item[1]["min_level"],
            reverse=True
        )

        for key, cfg in sorted_frames:
            if user.level >= cfg["min_level"]:
                return key
        return "bronze" # Mặc định

    def _draw_text_with_shadow(self, draw, pos, text, font, fill="white", shadow_color="black"):
        """Vẽ chữ với bóng đổ để dễ đọc trên mọi background."""
        x, y = pos
        draw.text((x+2, y+2), text, font=font, fill=shadow_color)
        draw.text(pos, text, font=font, fill=fill)

    async def render_card_image(self, user: User, member: nextcord.Member) -> BytesIO | None:
        """Render full PNG profile card, now with banner support."""
        W, H = 800, 300 # Kích thước mới cho banner
        
        bg_image = None
        if user.profile_banner_url:
            banner_bytes = await self._fetch_bytes(user.profile_banner_url)
            if banner_bytes:
                try:
                    bg_image = Image.open(BytesIO(banner_bytes)).convert("RGBA")
                    bg_image = bg_image.resize((W, int(W * bg_image.height / bg_image.width)), Image.Resampling.LANCZOS)
                    top = (bg_image.height - H) / 2
                    bg_image = bg_image.crop((0, top, W, top + H))
                except Exception:
                    bg_image = None
        
        if not bg_image:
            bg_color = user.accent_color or "#2c3e50"
            bg_image = Image.new("RGBA", (W, H), bg_color)
            
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 128))
        img = Image.alpha_composite(bg_image, overlay)
        draw = ImageDraw.Draw(img)

        font_name = self._load_font("Roboto-Bold.ttf", 48)
        font_stats = self._load_font("Roboto-Bold.ttf", 24)
        font_level = self._load_font("Roboto-Bold.ttf", 32)
        font_xp = self._load_font("NotoSans-Regular.ttf", 18)
        font_emoji = self._load_font("NotoColorEmoji.ttf", 48)

        avatar_url = user.custom_avatar_url or member.display_avatar.with_size(256).url
        avatar_bytes = await self._fetch_bytes(avatar_url)
        if not avatar_bytes: return None

        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((128, 128), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (128, 128), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 128, 128), fill=255)
        
        img.paste(avatar, (50, 86), mask)

        display_name = member.display_name
        emoji = user.profile_emoji or ""
        self._draw_text_with_shadow(draw, (210, 80), display_name, font_name)
        if emoji:
            name_width = font_name.getlength(display_name)
            draw.text((210 + name_width + 10, 80), emoji, font=font_emoji, embedded_color=True)

        self._draw_text_with_shadow(draw, (210, 140), f"Level {user.level}", font_level)
        
        xp_goal = 50 + (user.level * 25)
        xp_progress = (user.xp / xp_goal) if xp_goal > 0 else 0
        xp_progress = min(xp_progress, 1.0)
        
        bar_x, bar_y, bar_w, bar_h = 210, 185, 450, 25
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), fill="#4f545c")
        draw.rectangle((bar_x, bar_y, bar_x + int(bar_w * xp_progress), bar_y + bar_h), fill="#ffffff")
        self._draw_text_with_shadow(draw, (bar_x + 5, bar_y + 2), f"{user.xp:,} / {xp_goal:,} XP", font_xp, fill="black", shadow_color="white")

        frame_key = self._get_effective_frame_key(user)
        frame_color = FRAMES[frame_key]["color"]
        draw.rectangle([(0, 0), (W-1, H-1)], outline=frame_color, width=10)

        buf = BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        buf.seek(0)
        return buf

    @commands.command(name="previewcard")
    async def cmd_previewcard(self, ctx: commands.Context):
        """🔍 Hiển thị ảnh profile card PNG đã được làm lại."""
        async with ctx.typing():
            user = await self._get_user(ctx.author.id)
            if not user:
                return await ctx.send("❌ Không tìm thấy hồ sơ.")
            
            buf = await self.render_card_image(user, ctx.author)
            
            if buf:
                await ctx.send(file=nextcord.File(buf, "profile_card.png"))
            else:
                await ctx.send("❌ Đã xảy ra lỗi khi tạo ảnh profile card.")

def setup(bot: commands.Bot):
    bot.add_cog(ProfileCardCog(bot))
