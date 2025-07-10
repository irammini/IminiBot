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

    DEV_IDS = [1064509322228412416, 1327287076122787940]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _gen_code(self, length=8):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    @commands.command(name="creategift")
    async def create_gift(self, ctx: commands.Context,
                          code: str = "",
                          coin: int = 0,
                          items: str = "",
                          usages: int = 1,
                          expires: int = 0,
                          target_ids: str = ""):
        """🔧 !creategift CODE [coin] [items_csv] [usages] [expires_ts] [allowed_ids_csv]"""
        if ctx.author.id not in self.DEV_IDS:
            return await ctx.send(embed=make_embed(desc="❌ Không quyền.", color=nextcord.Color.red()))

        code = code.strip().upper() if code else self._gen_code()
        item_list = [i.strip() for i in items.split(",") if i.strip()]
        allowed_ids = [int(i.strip()) for i in target_ids.split(",") if i.strip()] if target_ids else []

        gc = GiftCode(
            code=code,
            coin=coin,
            items=item_list,
            expires_at=expires or None,
            max_usage=usages,
            creator_id=ctx.author.id,
            allowed_user_ids=allowed_ids
        )

        async with self.bot.sessionmaker() as session:
            session.add(gc)
            await session.commit()

        desc = f"✅ GiftCode tạo: **{code}**\n🪙 {coin} coin\n🎁 {', '.join(item_list) or 'Không có item'}\n🔄 Dùng được: {usages} lần"
        if allowed_ids:
            desc += f"\n🔒 Chỉ dùng cho: {', '.join(str(i) for i in allowed_ids)}"
        await ctx.send(embed=make_embed(desc=desc, color=nextcord.Color.green()))

    @commands.command(name="redeemcode")
    async def redeem_code(self, ctx: commands.Context, code: str):
        """🎫 !redeemcode <code> — dùng giftcode."""
        now = int(time.time())
        async with self.bot.sessionmaker() as session:
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
            user.wallet = (user.wallet or 0) + gc.coin

            # apply items
            for it in gc.items or []:
                inv = await session.get(Inventory, (ctx.author.id, it))
                if inv:
                    inv.amount += 1
                else:
                    new_inv = Inventory(user_id=ctx.author.id, item_id=it, amount=1)
                    session.add(new_inv)

            session.add_all([user, UserGiftCode(user_id=ctx.author.id, code=code, used_at=now)])
            await session.commit()

        txt = f"🎉 Redeem thành công: +{gc.coin} 🪙"
        if gc.items:
            txt += "\n" + " ".join(f"🎁 `{i}`" for i in gc.items)
        await ctx.send(embed=make_embed(desc=txt, color=nextcord.Color.green()))

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