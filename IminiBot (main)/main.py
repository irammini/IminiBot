import asyncio
import logging
from shared.bot import BotClient

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 🔧 Khởi tạo loop rõ ràng
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(True)
    loop.slow_callback_duration = 0.1

    # 📦 Khởi chạy bot với config và env đúng đường dẫn
    client = BotClient(
        config_path="./IminiBot (main)/config.json",
        env_path="./IminiBot (main)/.env")
    loop.run_until_complete(client.start())