import asyncio
from main import Bot

async def main():
    bot = Bot()
    
    # Create event loop and run bot
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start())
    
    # Keep the bot running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())