# cogs/giftcode.py

import time
import random
import string

import nextcord
from nextcord.ext import commands
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from shared.db import AsyncSession
from shared.models.giftcode import GiftCode, UserGiftCode
from shared.models.user import User
from shared.models.inventory import Inventory
from shared.utils.embed import make_embed

class GiftCodeCog(commands.Cog):
    """🎁 GiftCode: creategift (dev), redeemcode, mygiftcode."""

    DEV_IDS = [1064509322228412416, 1327287076122787940, 1204490429727244301]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _gen_code(self, length=8):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    @commands.command(name="creategift")
    async def create_gift(self, ctx: commands.Context,
                          code: str = "",
                          coin: int = None,
                          items: str = "",
                          usages: int = None,
                          expires: int = None,
                          target_ids: str = ""):
        """🔧 !creategift CODE COIN [items_csv] [usages] [expires_ts] [allowed_ids_csv]"""
        if ctx.author.id not in self.DEV_IDS:
            return await ctx.send(embed=make_embed(desc="❌ Không quyền.", color=nextcord.Color.red()))

        # Kiểm tra code
        code = code.strip().upper()
        if not code:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Bạn phải nhập CODE (không được để trống).", color=nextcord.Color.orange()))

        # Kiểm tra coin
        if coin is None:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Bạn phải nhập số coin (không được để trống).", color=nextcord.Color.orange()))
        try:
            coin = int(coin)
        except Exception:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Coin phải là số nguyên.", color=nextcord.Color.orange()))
        if coin < 0:
            return await ctx.send(embed=make_embed(
                desc="⚠️ Coin phải >= 0.", color=nextcord.Color.orange()))

        # Kiểm tra usages (nếu nhập)
        if usages is not None:
            try:
                usages = int(usages)
                if usages < 1:
                    return await ctx.send(embed=make_embed(
                        desc="⚠️ usages phải >= 1 hoặc để trống để không giới hạn.", color=nextcord.Color.orange()))
            except Exception:
                return await ctx.send(embed=make_embed(
                    desc="⚠️ usages phải là số nguyên hoặc để trống.", color=nextcord.Color.orange()))
        # Kiểm tra expires (nếu nhập)
        if expires is not None:
            try:
                expires = int(expires)
                if expires < 0:
                    return await ctx.send(embed=make_embed(
                        desc="⚠️ expires phải >= 0 hoặc để trống.", color=nextcord.Color.orange()))
            except Exception:
                return await ctx.send(embed=make_embed(
                    desc="⚠️ expires phải là số nguyên hoặc để trống.", color=nextcord.Color.orange()))

        item_list = [i.strip() for i in items.split(",") if i.strip()]
        allowed_ids = [int(i.strip()) for i in target_ids.split(",") if i.strip()] if target_ids else None

        async with self.bot.sessionmaker() as session:
            exists = await session.get(GiftCode, code)
            if exists:
                return await ctx.send(embed=make_embed(desc="⚠️ Code đã tồn tại.", color=nextcord.Color.orange()))

            # Validate: item tồn tại (nếu có)
            from shared.models.item import Item
            for item_id in item_list:
                item = await session.get(Item, item_id)
                if not item:
                    return await ctx.send(embed=make_embed(
                        desc=f"⚠️ Item `{item_id}` không tồn tại.", color=nextcord.Color.orange()))

            gc = GiftCode(
                code=code,
                coin=coin,
                items=item_list,
                expires_at=expires,
                max_usage=usages,
                creator_id=ctx.author.id,
                allowed_user_ids=allowed_ids
            )

            session.add(gc)
            await session.commit()

        desc = f"✅ GiftCode tạo: **{code}**\n🪙 {coin} coin\n🎁 {', '.join(item_list) or 'Không có item'}"
        if usages:
            desc += f"\n🔄 Dùng được: {usages} lần"
        else:
            desc += "\n🔄 Không giới hạn lượt dùng"
        if expires:
            desc += f"\n⏳ Hết hạn: <t:{expires}:R>"
        else:
            desc += "\n⏳ Không giới hạn thời gian"
        if allowed_ids:
            desc += f"\n🔒 Chỉ dùng cho: {', '.join(str(i) for i in allowed_ids)}"
        await ctx.send(embed=make_embed(desc=desc, color=nextcord.Color.green()))

    @commands.command(name="listcode")
    async def list_code(self, ctx: commands.Context):
        """🗂️ !listcode — Liệt kê tất cả giftcode (dev only)"""
        if ctx.author.id not in self.DEV_IDS:
            return await ctx.send(embed=make_embed(desc="❌ Không quyền.", color=nextcord.Color.red()))
        async with self.bot.sessionmaker() as session:
            codes = (await session.execute(select(GiftCode))).scalars().all()
        if not codes:
            return await ctx.send(embed=make_embed(desc="📭 Không có giftcode nào.", color=nextcord.Color.dark_gray()))
        lines = []
        for c in codes:
            status = "✅" if c.enabled else "❌"
            lines.append(f"{status} `{c.code}` — {c.coin}🪙, {', '.join(c.items) or 'no item'}, max: {c.max_usage or '∞'}")
        await ctx.send(embed=make_embed(title="🗂️ Danh sách GiftCode", desc="\n".join(lines), color=nextcord.Color.blue()))

    @commands.command(name="editcode")
    async def edit_code(self, ctx: commands.Context, code: str, field: str, *, value: str):
        """✏️ !editcode CODE FIELD VALUE — Sửa giftcode (dev only)"""
        if ctx.author.id not in self.DEV_IDS:
            return await ctx.send(embed=make_embed(desc="❌ Không quyền.", color=nextcord.Color.red()))
        async with self.bot.sessionmaker() as session:
            gc = await session.get(GiftCode, code.upper())
            if not gc:
                return await ctx.send(embed=make_embed(desc="❌ Code không tồn tại.", color=nextcord.Color.red()))
            try:
                if field == "coin":
                    gc.coin = int(value)
                elif field == "items":
                    gc.items = [i.strip() for i in value.split(",") if i.strip()]
                elif field == "max_usage":
                    gc.max_usage = int(value) if value.isdigit() else None
                elif field == "expires_at":
                    gc.expires_at = int(value) if value.isdigit() else None
                elif field == "enabled":
                    gc.enabled = value.lower() in ("1", "true", "yes", "on", "enable")
                elif field == "allowed_user_ids":
                    gc.allowed_user_ids = [int(i.strip()) for i in value.split(",") if i.strip()]
                else:
                    return await ctx.send(embed=make_embed(desc="⚠️ Field không hợp lệ.", color=nextcord.Color.orange()))
                await session.commit()
                await ctx.send(embed=make_embed(desc=f"✅ Đã sửa `{field}` cho code `{code}`.", color=nextcord.Color.green()))
            except Exception as e:
                await session.rollback()
                await ctx.send(embed=make_embed(desc=f"❌ Lỗi khi sửa: {e}", color=nextcord.Color.red()))

    @commands.command(name="deletecode")
    async def delete_code(self, ctx: commands.Context, code: str):
        """🗑️ !deletecode CODE — Xóa giftcode (dev only)"""
        if ctx.author.id not in self.DEV_IDS:
            return await ctx.send(embed=make_embed(desc="❌ Không quyền.", color=nextcord.Color.red()))
        async with self.bot.sessionmaker() as session:
            gc = await session.get(GiftCode, code.upper())
            if not gc:
                return await ctx.send(embed=make_embed(desc="❌ Code không tồn tại.", color=nextcord.Color.red()))
            await session.delete(gc)
            await session.commit()
        await ctx.send(embed=make_embed(desc=f"🗑️ Đã xóa code `{code}`.", color=nextcord.Color.green()))

    @commands.command(name="redeemcode")
    async def redeem_code(self, ctx: commands.Context, code: str):
        """🎫 !redeemcode <code> — dùng giftcode."""
        now = int(time.time())
        async with self.bot.sessionmaker() as session:
            try:
                gc = await session.get(GiftCode, code.upper())
                if not gc or not gc.enabled:
                    return await ctx.send(embed=make_embed(desc="❌ Code không tồn tại.", color=nextcord.Color.red()))
                if gc.expires_at and now > gc.expires_at:
                    return await ctx.send(embed=make_embed(desc="⌛ Code đã hết hạn.", color=nextcord.Color.orange()))
                if gc.allowed_user_ids and ctx.author.id not in gc.allowed_user_ids:
                    return await ctx.send(embed=make_embed(desc="🚫 Mã này không dành cho bạn.", color=nextcord.Color.red()))

                total = await session.scalar(
                    select(func.count()).select_from(UserGiftCode).where(UserGiftCode.code == code)
                )
                if total >= gc.max_usage:
                    return await ctx.send(embed=make_embed(desc="❌ Code đã hết lượt.", color=nextcord.Color.red()))

                used = await session.get(UserGiftCode, (ctx.author.id, code))
                if used:
                    return await ctx.send(embed=make_embed(desc="🪫 Bạn đã dùng mã này rồi.", color=nextcord.Color.dark_gray()))

                user = await session.get(User, ctx.author.id)
                if not user:
                    user = User(id=ctx.author.id)
                    session.add(user)

                # Thưởng coin
                if gc.coin:
                    user.wallet = (user.wallet or 0) + gc.coin

                # Thưởng item
                from shared.models.item import Item
                for it in gc.items or []:
                    item = await session.get(Item, it)
                    if not item:
                        await session.rollback()
                        return await ctx.send(embed=make_embed(desc=f"🎁 Item `{it}` không tồn tại.", color=nextcord.Color.red()))
                    inv = await session.get(Inventory, (ctx.author.id, it))
                    if inv:
                        inv.amount += 1
                    else:
                        session.add(Inventory(user_id=ctx.author.id, item_id=it, amount=1))

                session.add_all([user, UserGiftCode(user_id=ctx.author.id, code=code, used_at=now)])
                await session.commit()

                txt = f"🎉 Redeem thành công: +{gc.coin} 🪙"
                if gc.items:
                    txt += "\n" + " ".join(f"🎁 `{i}`" for i in gc.items)
                await ctx.send(embed=make_embed(desc=txt, color=nextcord.Color.green()))
            except Exception as e:
                await session.rollback()
                await ctx.send(embed=make_embed(desc=f"❌ Lỗi khi redeem: {e}", color=nextcord.Color.red()))

    @commands.command(name="mygiftcode")
    async def my_giftcode(self, ctx: commands.Context):
        """📜 !mygiftcode — xem mã bạn đã dùng."""
        async with self.bot.sessionmaker() as session:
            rows = await session.execute(
                select(UserGiftCode.code, UserGiftCode.used_at)
                .where(UserGiftCode.user_id == ctx.author.id)
            )
            data = rows.all()

        if not data:
            return await ctx.send(embed=make_embed(desc="🪫 Bạn chưa dùng mã nào.", color=nextcord.Color.dark_gray()))

        lines = [f"🎫 `{code}` — <t:{used}:R>" for code, used in data]
        await ctx.send(embed=make_embed(title="📜 Lịch sử Redeem", desc="\n".join(lines), color=nextcord.Color.blue()))

def setup(bot: commands.Bot):
    bot.add_cog(GiftCodeCog(bot))