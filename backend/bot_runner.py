import asyncio
import logging
from main import Bot

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Create event loop first
    loop = asyncio.get_event_loop()
    
    # Initialize bot with the loop
    bot = Bot()
    bot.loop = loop
    logger.debug("Bot initialized with event loop")
    
    # Start the bot
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())