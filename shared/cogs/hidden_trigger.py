import nextcord
from nextcord.ext import commands
from shared.utils.embed import make_embed
from shared.utils.decorators import with_achievements
from shared.utils.achievement import award
from shared.models.user import User

HIDDEN_RESPONSES = {
    "mirror": ("Bạn thấy chính mình...", nextcord.Color.teal()),
    "echo":   (None,                     nextcord.Color.teal()),
    "meow":   ("Meow meow! 😺",         nextcord.Color.purple()),
    "unlocked": ("🔓 Bạn mở khóa quest ẩn!", nextcord.Color.green()),
}

class HiddenTriggerCog(commands.Cog):
    """🔒 Lệnh ẩn: mirror, echo, meow, unlock"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def track_command_spam(self, ctx):
        print(f"🔥 Lệnh vừa được gọi: {ctx.command}")
    
    async def _get_user(self, uid: int) -> User:
        async with self.bot.sessionmaker() as sess:
            user = await sess.get(User, uid)
            return user
        
    async def _save_user(self, user: User):
        async with self.bot.sessionmaker() as sess:
            sess.add(user)
            await sess.commit()

    @commands.command()
    @with_achievements("mirror")
    async def mirror(self, ctx: commands.Context):
        """🪞 !mirror — gõ càng nhiều lần càng lệch chính mình."""

        uid = ctx.author.id

        # lấy user & templog từ DB (luôn reload bản mới)
        async with self.bot.sessionmaker() as sess:
            user = await sess.get(User, uid)
            templog = user.templog or {}

            count = templog.get("mirror_count", 0) + 1
            templog["mirror_count"] = count
            user.templog = templog

            sess.add(user)
            await sess.commit()

        # bảng phản hồi theo trigger
        TRIGGERS = {
            3:  "🪞 Gương bắt đầu rung nhẹ.",
            5:  "🪞 Hình ảnh bạn bị lệch khỏi không gian hiện tại.",
            7:  "🪞 Bạn không còn là bạn nữa...",
            10: "🪞 Một bản thể khác mỉm cười từ phía gương.",
            15: "🪞 Gương không còn phản chiếu ánh sáng… chỉ phản ứng.",
            25: "🪞 Bạn cảm thấy bị quan sát. Từ phía gương?",
            30: "🪞 Bạn không thể kiểm soát bản thể phản chiếu nữa.",
            50: "🪞 Gương đã nhận diện bạn.",
        }

        extra = TRIGGERS.get(count, "")

        # mốc đặc biệt
        if count == 50:
            await award(self.bot, uid, "mirrorloop")
        elif count == 66:
            await ctx.send(embed=make_embed(
                desc="Haha... Bạn vẫn tiếp tục soi chính mình?",
                color=nextcord.Color.dark_grey()
            ))
        elif count == 100:
            await ctx.send(embed=make_embed(
                desc="🪞 ...Gương biến mất. Để lại tấm gương nhỏ.",
                color=nextcord.Color.greyple()
            ))
        elif count > 100:
            await ctx.send(embed=make_embed(
                desc="Bạn thấy chính mình, luôn luôn là vậy mà?",
                color=nextcord.Color.greyple()
            ))
            return

        # phản hồi chính
        txt, col = HIDDEN_RESPONSES.get("mirror", ("Bạn thấy chính mình...", nextcord.Color.greyple()))
        await ctx.send(embed=make_embed(
            desc=f"{txt}\n{extra}",
            color=col
        ))

    @commands.command()
    @with_achievements("echo")
    async def echo(self, ctx: commands.Context, *, content: str):
        _, col = HIDDEN_RESPONSES["echo"]
        await ctx.send(embed=make_embed(desc=content, color=col))

    @commands.command()
    @with_achievements("meow")
    async def meow(self, ctx: commands.Context):
        txt, col = HIDDEN_RESPONSES["meow"]
        await ctx.send(embed=make_embed(desc=txt, color=col))

    @commands.command()
    @with_achievements("unlock")
    async def unlocksmth(bot, self, ctx: commands.Context):
        txt, col = HIDDEN_RESPONSES["unlocked"]
        await ctx.send(embed=make_embed(desc=txt, color=col))

def setup(bot: commands.Bot):
    bot.add_cog(HiddenTriggerCog(bot))