import time
import logging
from functools import lru_cache

from sqlalchemy import select
from shared.db import AsyncSession
from shared.models.achievement import UserAchievement
from shared.models.user import User
from shared.data.achievements import ACH_LIST

logger = logging.getLogger(__name__)

# --------------------
# 🎯 Điều kiện đặc biệt
# --------------------

async def cond_quiz_master(bot, uid: int) -> bool:
    async with bot.sessionmaker() as s:
        user = await s.get(User, uid)
    total = sum(getattr(user, f"quiz_win_{lvl}", 0) for lvl in [
        "easy", "normal", "hard", "extreme", "nightmare"
    ])
    return total >= 10

async def cond_first_give(uid: int) -> bool:
    return True

async def cond_first_repay(uid: int) -> bool:
    return True

ACH_CONDITIONS = {
    "quiz_master": cond_quiz_master,
    "first_give": cond_first_give,
    "first_repay": cond_first_repay,
}
    # Các badge như praybless, speedrunquiz award trực tiếp trong cog

# --------------------
# 🧠 Các key hợp lệ
# --------------------

@lru_cache
def get_valid_keys():
    return {k for k, *_ in ACH_LIST}

def get_display_name(key: str) -> str:
    return next((n for k, n, *_ in ACH_LIST if k == key), key)

# --------------------
# 🏅 Award 1 badge
# --------------------

async def award(bot, uid: int, key: str, announce: bool = True) -> bool:
    """
    Unlock badge `key` cho user `uid`.
    Return True nếu thành công, False nếu đã có hoặc không hợp lệ.
    """
    if key not in get_valid_keys():
        logger.warning(f"[award] Unknown badge key: {key}")
        return False
    async with bot.sessionmaker() as s:
        exists = await s.get(UserAchievement, (uid, key))
        if exists:
            return False

        cond = ACH_CONDITIONS.get(key)
        if cond and not await cond(uid):
            return False

        s.add(UserAchievement(user_id=uid, ach_key=key, unlocked_at=int(time.time())))
        await s.commit()

    # ✅ Gửi thông báo
    if announce:
        try:
            user = bot.get_user(uid)
            if user:
                await user.send(f"🏅 Chúc mừng! Bạn đã mở khóa badge **{get_display_name(key)}**!")
        except Exception:
            pass

    logger.info(f"[award] {uid} unlocked {key}")
    return True

# --------------------
# 🧩 Award nhiều badge cùng lúc
# --------------------

async def unlock_many(bot, uid: int, *keys, announce: bool = True):
    """
    Unlock nhiều badge theo danh sách.
    Trả về list các key được unlock thành công.
    """
    unlocked = []
    for key in keys:
        if await award(bot, uid, key, announce=announce):
            unlocked.append(key)
    return unlocked