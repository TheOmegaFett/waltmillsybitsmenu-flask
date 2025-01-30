import asyncio
from main import Bot

if __name__ == "__main__":
    bot = Bot()
    # Commands are automatically registered through the @commands.command() decorators
    asyncio.run(bot.start())