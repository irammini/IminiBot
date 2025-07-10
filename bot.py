import logging
import asyncio
from shared.bot_client import BotClient  # 📥 Import đúng từ file kia

def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = BotClient(config_path="config.json", env_path=".env")
    loop.run_until_complete(client.start())

if __name__ == "__main__":
    main()
