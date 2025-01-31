import asyncio
import logging
import redis
import json
import os
from main import Bot

redis_client = redis.Redis.from_url('redis://red-cudsn6lds78s73dfsh0g:6379')


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def listen_for_bits(bot, redis_client):
    try:
        pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe('bot_commands')
        logger.debug("Successfully connected to Redis pubsub")
        
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                logger.debug(f"Received bits command: {data}")
                
                if data.get('type') == 'dropbear':
                    channel = bot.get_channel(os.getenv('TWITCH_CHANNEL'))
                    mock_ctx = type('Context', (), {
                        'send': channel.send,
                        'author': type('Author', (), {
                            'is_mod': True,
                            'is_broadcaster': True,
                            'name': data['data']['user']
                        })()
                    })()
                    await bot.dropbear(mock_ctx)
                    
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Redis connection error: {e}")

async def main():
    loop = asyncio.get_event_loop()
    bot = Bot()
    bot.loop = loop
    
    bot_task = bot.start()
    bits_task = listen_for_bits(bot, redis_client)
    await asyncio.gather(bot_task, bits_task)

if __name__ == "__main__":
    asyncio.run(main())