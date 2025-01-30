import asyncio
import logging
from main import Bot

# Set up detailed debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    bot = Bot()
    logger.debug("Bot instance created")
    
    # Add debug hooks to track command processing
    original_event_message = bot.event_message
    async def debug_event_message(self, message):
        logger.debug(f"Received message: {message.content}")
        await original_event_message(message)
    bot.event_message = debug_event_message.__get__(bot)
    
    original_handle_commands = bot.handle_commands
    async def debug_handle_commands(self, message):
        logger.debug(f"Processing command: {message.content}")
        await original_handle_commands(message)
    bot.handle_commands = debug_handle_commands.__get__(bot)
    
    logger.debug("Starting bot with debug hooks")
    asyncio.run(bot.start())