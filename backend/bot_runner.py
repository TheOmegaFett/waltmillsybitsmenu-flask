import asyncio
from main import Bot

async def main():
    bot = Bot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())