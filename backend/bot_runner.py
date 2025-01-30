import asyncio
import logging
import redis
import json
import os
from main import Bot

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def listen_for_bits(bot, redis_client):
    try:
        pubsub = redis_client.pubsub()
        pubsub.subscribe('bot_commands')
        logger.debug("Successfully connected to Redis pubsub")
        
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                logger.debug(f"Received bits command: {data}")
                
                if data.get('type') == 'dropbear':
                    user = data.get('data', {}).get('user')
                    logger.debug(f"Triggering dropbear for user: {user}")
                    await bot.dropbear(user)
                    
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Redis connection error: {e}")

async def main():
    loop = asyncio.get_event_loop()
    bot = Bot()
    bot.loop = loop
    
    redis_url = os.environ.get('REDIS_URL')
    logger.debug(f"Using Redis URL: {redis_url}")
    redis_client = redis.from_url(redis_url)
    
    await asyncio.gather(
        bot.start(),
        listen_for_bits(bot, redis_client)
    )

if __name__ == "__main__":
    asyncio.run(main())