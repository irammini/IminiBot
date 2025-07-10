import functools
from shared.utils.achievement_triggers import ach_triggers
from shared.utils.achievement import award

def with_achievements(cmd_name: str):
    """
    Decorator: sau khi command cmd_name hoàn thành,
    tự động award tất cả badge đã đăng ký cho lệnh đó.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            result = await func(self, ctx, *args, **kwargs)
            uid = ctx.author.id
            for key in ach_triggers.get(cmd_name):
                # bỏ qua key động như secret_<key>
                if "<" in key:
                    continue
                await award(self.bot, uid, key)
            return result
        return wrapper
    return decorator