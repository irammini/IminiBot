# cogs/profilecard.py

import os
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import nextcord
from nextcord.ext import commands
from shared.db import AsyncSession
from shared.models.user import User
from shared.models.achievement import Achievement as AchModel

# Định nghĩa FRAMES với mã màu cho khung
FRAMES = {
    "bronze":   {"emoji": "🟦", "name": "Bronze Frame",   "min_level": 25,  "color": "#c28e5c"},
    "silver":   {"emoji": "🟨", "name": "Silver Frame",   "min_level": 50,  "color": "#c0c0c0"},
    "gold":     {"emoji": "🟥", "name": "Gold Frame",     "min_level": 75,  "color": "#ffd700"},
    "platinum": {"emoji": "🟪", "name": "Platinum Frame", "min_level": 100, "color": "#e5e4e2"},
    "mythic":   {"emoji": "🌈", "name": "Mythic Frame",   "min_level": 150, "color": "#a020f0"},
}

BASE_DIR  = os.path.dirname(__file__)
FONTS_DIR = os.path.join(BASE_DIR, "..", "fonts")

FONT_FILES = {
    "default": "Roboto-Bold.ttf",
    "pixel":   "PressStart2P-Regular.ttf",
    "neon":    "Bungee-Regular.ttf",
    "unicode": "NotoSans-Regular.ttf",
    "emoji":   "NotoColorEmoji.ttf"  # nếu có, hoặc fallback NotoSans-Regular.ttf
}

def auto_fix_color(bg_color: str):
    """
    Phân tích độ sáng nền để quyết định có cần stroke cho chữ không.
    Trả về dict: {"valid": bool, "need_stroke": bool}
    """
    try:
        r, g, b = ImageColor.getrgb(bg_color)
    except Exception:
        return {"valid": False, "need_stroke": False}
    lum = (r*299 + g*587 + b*114) / 1000
    return {"valid": True, "need_stroke": lum >= 200}

class ProfileCardCog(commands.Cog):
    """Cog render ảnh Profile Card PNG với theme, frame, emoji, glow."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")

    async def _get_user(self, uid: int) -> User | None:
        async with self.bot.sessionmaker() as sess:
            return await sess.get(User, uid)

    async def _fetch_bytes(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                return await r.read()

    def _load_font(self, key: str, size: int) -> ImageFont.FreeTypeFont:
        fname = FONT_FILES.get(key, FONT_FILES["default"])
        path = os.path.join(FONTS_DIR, fname)
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            # fallback
            return ImageFont.truetype("arial.ttf", size)

    def _get_effective_frame(self, user: User) -> str:
        """Chọn frame override hoặc auto theo level."""
        if user.profile_frame in FRAMES:
            return user.profile_frame
        # auto-lựa chọn frame lớn nhất theo level
        for key, cfg in sorted(FRAMES.items(), key=lambda x: x[1]["min_level"], reverse=True):
            if user.level >= cfg["min_level"]:
                return key
        return "bronze"

    def _apply_frame(self, img: Image.Image, frame_key: str, color_hex: str, level: int):
        """Vẽ khung và glow aura theo frame và level."""
        w, h = img.size
        draw = ImageDraw.Draw(img)
        rgb = ImageColor.getrgb(color_hex)

        # viền chính
        draw.rectangle([(8, 8), (w-8, h-8)], outline=rgb, width=6)

        # effect mythic / high-level
        if frame_key == "mythic" or level >= 50:
            aura = Image.new("RGBA", img.size, (*rgb, 80))
            ad = ImageDraw.Draw(aura)
            ad.rectangle([(8, 8), (w-8, h-8)], outline=rgb, width=12)
            glow = aura.filter(ImageFilter.GaussianBlur(6))
            img.paste(glow, (0, 0), glow)

        # legendary glow nếu level quá cao
        if level >= 1000:
            gold = ImageColor.getrgb("#ffe100")
            aura2 = Image.new("RGBA", img.size, (*gold, 100))
            ad2 = ImageDraw.Draw(aura2)
            ad2.rectangle([(4, 4), (w-4, h-4)], outline=gold, width=18)
            glow2 = aura2.filter(ImageFilter.GaussianBlur(10))
            img.paste(glow2, (0, 0), glow2)

    async def render_card_image(self, user: User, name: str, avatar_url: str) -> BytesIO:
        """
        Render full PNG profile card.
        Trả về BytesIO chứa ảnh PNG.
        """
        W, H = 600, 260
        bg        = user.accent_color or "#2c3e50"
        theme     = (user.profile_theme or "default").lower()
        frame_key = self._get_effective_frame(user)
        fcolor    = FRAMES[frame_key]["color"]
        emoji     = user.profile_emoji or ""
        title     = user.custom_title or ""

        # badge từ db
        badge_name = ""
        if user.flex_key:
            async with self.bot.sessionmaker() as sess:
                ach = await sess.get(AchModel, user.flex_key)
            badge_name = ach.name if ach else ""

        # fetch avatar
        raw = await self._fetch_bytes(avatar_url)
        avatar = Image.open(BytesIO(raw)).convert("RGBA")
        avatar = avatar.resize((96, 96), Image.Resampling.LANCZOS)

        # chuẩn bị canvas
        img = Image.new("RGB", (W, H), bg)
        draw = ImageDraw.Draw(img)

        # load fonts
        font_name  = self._load_font(theme, 32)
        font_emoji = self._load_font("emoji", 32)
        font_title = self._load_font(theme, 24)
        font_stat  = self._load_font(theme, 20)

        # stroke cho chữ nếu cần
        fix = auto_fix_color(bg)
        stroke = {"stroke_width": 2, "stroke_fill": "black"} if fix["need_stroke"] else {}

        # dán avatar
        img.paste(avatar, (30, 30), avatar)

        # render emoji + tên
        if emoji:
            draw.text((150, 35), emoji, font=font_emoji, fill="white")
            ew = font_emoji.getlength(emoji)
            draw.text((150 + ew + 8, 35), name, font=font_name, fill="white", **stroke)
        else:
            draw.text((150, 35), name, font=font_name, fill="white", **stroke)

        # tiêu đề & badge
        draw.text((150, 80), title, font=font_title, fill="white", **stroke)
        if badge_name:
            draw.text((150, 110), f"🎖️ {badge_name}", font=font_title, fill="white", **stroke)

        # stats bên trái
        draw.text((30, 150), f"💰 {user.wallet:,} xu", font=font_stat, fill="white", **stroke)
        draw.text((30, 175), f"⭐ Level {user.level}", font=font_stat, fill="white", **stroke)
        draw.text((30, 200), f"🔥 Streak: {user.streak:,}", font=font_stat, fill="white", **stroke)
        draw.text((30, 225), "🎖️ BETA Emoji", font=font_stat, fill="white", **stroke)

        # stats bên phải
        draw.text((320, 150), f"📈 XP: {user.xp:,}", font=font_stat, fill="white", **stroke)
        draw.text((320, 175), f"⚔️ PVP: {getattr(user, 'rank', 'Unranked')}", font=font_stat, fill="white", **stroke)
        draw.text((320, 200), f"🎖️ Titles: {len(user.items)}", font=font_stat, fill="white", **stroke)
        draw.text((320, 225), f"🤝 Trust: {user.trust_points:,}", font=font_stat, fill="white", **stroke)

        # vẽ khung + glow
        self._apply_frame(img, frame_key, fcolor, user.level)

        # xuất BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    @commands.command(name="previewcard")
    async def cmd_previewcard(self, ctx: commands.Context):
        """
        🔍 Hiển thị ảnh profile card PNG.
        🧪 Tính năng đang ở giai đoạn BETA — sẽ cải tiến trong tương lai gần.
        """

        user = await self._get_user(ctx.author.id)
        if not user:
            return await ctx.send("❌ Không tìm thấy hồ sơ.")
        url = ctx.author.display_avatar.with_size(128).url
        buf = await self.render_card_image(user, ctx.author.display_name, url)
        await ctx.send(file=nextcord.File(buf, "profile_card.png"))

    @commands.command(name="stylecard")
    async def cmd_stylecard(self, ctx: commands.Context, theme: str):
        """🎭 Đổi theme font cho ảnh profile card."""
        t = theme.lower()
        if t not in FONT_FILES:
            valid = ", ".join(FONT_FILES.keys())
            return await ctx.send(
                f"⚠️ Theme không hợp lệ. Hợp lệ: `{valid}`"
            )
        async with self.bot.sessionmaker() as sess:
            u = await sess.get(User, ctx.author.id)
            if not u:
                return await ctx.send("❌ Không tìm thấy hồ sơ.")
            u.profile_theme = t
            await sess.commit()
        await ctx.send(f"✅ Theme đã chuyển sang **{t}**. Gõ `!previewcard` để xem.")

    @commands.command(name="debugfonts")
    async def cmd_debugfonts(self, ctx: commands.Context):
        """
        🔧 Kiểm tra khả năng load tất cả các font .ttf trong thư mục fonts/.
        """
        files = [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(".ttf")]
        if not files:
            return await ctx.send("⚠️ Không tìm thấy font .ttf nào trong fonts/.")
        report = []
        for f in files:
            try:
                ImageFont.truetype(os.path.join(FONTS_DIR, f), 24)
                report.append(f"✅ {f}")
            except Exception as e:
                report.append(f"❌ {f} → {type(e).__name__}")
        await ctx.send("📋 Debug fonts:\n```\n" + "\n".join(report) + "\n```")

def setup(bot: commands.Bot):
    bot.add_cog(ProfileCardCog(bot))