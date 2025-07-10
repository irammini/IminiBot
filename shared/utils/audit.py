# utils/audit.py

import time
import logging
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

from shared.db import AsyncSession
from shared.models.audit import AuditLog

logger = logging.getLogger(__name__)

def admin_audit(func):
    """
    Decorator để ghi log admin action vào bảng audit_logs.
    Ghi lại user_id, action name, thời gian và tham số gọi command.
    """
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        bot = self.bot
        uid = ctx.author.id
        command = ctx.command.qualified_name
        details = f"args={args}, kwargs={kwargs}"

        try:
            async with bot.sessionmaker() as session:
                session.add(AuditLog(
                    user_id=uid,
                    action=command,
                    details=details,
                    timestamp=int(time.time())
                ))
                await session.commit()
                logger.info(f"🔍 Audit: {uid} used '{command}'")
        except SQLAlchemyError:
            logger.exception("❌ Error logging admin audit")

        return await func(self, ctx, *args, **kwargs)
    return wrapper