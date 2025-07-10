import os
import json
import logging
import datetime
import asyncio
import aiohttp
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands

from shared.db import init_engine, Base
from shared.data.seed_items import seed_items

logger = logging.getLogger("bot")

COGS = [
    "shared.cogs.utils", "shared.cogs.levelsystem", "shared.cogs.achievement",
    "shared.cogs.minigame", "shared.cogs.quest", "shared.cogs.shop",
    "shared.cogs.admin", "shared.cogs.job", "shared.cogs.giftcode",
    "shared.cogs.event", "shared.cogs.social", "shared.cogs.profile",
    "shared.cogs.chaos_game", "shared.cogs.hidden_trigger",
    "shared.cogs.secret_quest", "shared.cogs.economy"
]

class BotClient:
    def __init__(self, config_path: str, env_path: str):
        # Load .env
        load_dotenv(env_path)
        self.token = os.getenv("BOT_TOKEN")
        self.db_url = os.getenv("DATABASE_URL")
        if not self.token or not self.db_url:
            raise RuntimeError("❌ Thiếu BOT_TOKEN hoặc DATABASE_URL trong .env")

        # Load config JSON
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.prefix = self.config.get("default_prefix", "!")

        # Database
        self.engine, self.sessionmaker = init_engine(self.db_url)

        # Bot instance
        self.bot = commands.Bot(
            command_prefix=self.prefix,
            intents=self._build_intents(),
            help_command=None
        )

        # Gắn dữ liệu dùng chung
        self.bot.config = self.config
        self.bot.sessionmaker = self.sessionmaker
        self.bot.engine = self.engine
        self.bot.start_time = datetime.datetime.now(datetime.timezone.utc)

        self._inject_events()

    def _build_intents(self) -> nextcord.Intents:
        intents = nextcord.Intents.default()
        intents.guilds = intents.members = intents.message_content = True
        intents.reactions = intents.voice_states = True
        return intents

    async def setup(self):
        # Tạo database nếu chưa có
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database schema ready")

        # Load cogs
        for ext in COGS:
            try:
                self.bot.load_extension(ext)
                logger.info(f"✅ Loaded: {ext}")
            except Exception:
                logger.exception(f"❌ Failed to load: {ext}")

    async def start(self):
        await self.setup()

        # Tự reconnect khi mất kết nối
        while True:
            try:
                await self.bot.start(self.token)
                break
            except (aiohttp.ClientConnectorError, OSError) as e:
                logger.warning(f"⚠️ Mất kết nối: {e}, thử lại sau 10s…")
                await asyncio.sleep(10)
            except Exception:
                logger.exception("🚨 Bot crash nghiêm trọng")
                break

    def _inject_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f"✅ Logged in as {self.bot.user} (ID: {self.bot.user.id})")
            await seed_items(self.bot.sessionmaker)

        @self.bot.event
        async def on_message(message: nextcord.Message):
            if not message.author.bot:
                await self.bot.process_commands(message)

        @self.bot.event
        async def track_command_error(ctx, error):
            from shared.utils.embed import make_embed
            from nextcord import Color

            if not isinstance(ctx, commands.Context) or ctx.command is None:
                return

            embed = None
            if isinstance(error, commands.CommandOnCooldown):
                embed = make_embed(f"⏳ Cooldown: **{int(error.retry_after)}s**.", color=Color.red())
            elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
                sig = ctx.command.signature or ""
                embed = make_embed(f"❗ Sai cú pháp.\n`{ctx.prefix}{ctx.command.name} {sig}`", color=Color.orange())
                try: ctx.command.reset_cooldown(ctx)
                except: pass
            elif isinstance(error, commands.MissingPermissions):
                embed = make_embed("🚫 Bạn không có quyền.", color=Color.red())
            elif isinstance(error, commands.BotMissingPermissions):
                embed = make_embed("🚫 Bot thiếu quyền.", color=Color.red())
            else:
                import traceback
                trace = "".join(traceback.format_exception(error, error, error.__traceback__))
                logger.error(f"❌ Unhandled error in `{ctx.command}`:\n{trace}")
                embed = make_embed("❌ Đã xảy ra lỗi nội bộ.", color=Color.red())

            if embed:
                try:
                    await ctx.send(embed=embed, delete_after=8)
                except Exception as e:
                    logger.warning(f"⚠️ Không thể gửi lỗi tới user: {e}")
