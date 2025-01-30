import asyncio
from main import Bot

if __name__ == "__main__":
    bot = Bot()
    # Register commands explicitly
    bot.load_commands()
    # Run bot with command handling enabled
    asyncio.run(bot.start())