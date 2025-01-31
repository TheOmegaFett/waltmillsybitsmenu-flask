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
        logger.info("🎮 Bot listening for Redis commands")
        
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                logger.info(f"🎯 Received command: {data}")
                
                channel = bot.get_channel(os.getenv('TWITCH_CHANNEL'))
                if channel:
                    logger.info(f"📢 Found channel: {channel.name}")
                    # Create a more complete mock context that matches what dropbear expects
                    mock_ctx = type('Context', (), {
                        'send': channel.send,
                        'channel': channel,
                        'view': None,  # Added back the view attribute
                        'author': type('Author', (), {
                            'is_mod': True,
                            'is_broadcaster': True,
                            'name': data['data']['user'],
                            'display_name': data['data']['user']
                        })(),
                        'message': type('Message', (), {
                            'content': '!dropbear',
                            'channel': channel,
                            'author': type('Author', (), {
                                'name': data['data']['user'],
                                'display_name': data['data']['user']
                            })()
                        })()
                    })
                    
                    if data['type'] == 'dropbear':
                        logger.info("🐨 Executing dropbear command")
                        await bot._execute_dropbear(mock_ctx)  # Call the direct method
                        logger.info("🐨 Dropbear command completed")
                    
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"❌ Redis connection error: {e}", exc_info=True)

async def main():
    loop = asyncio.get_event_loop()
    bot = Bot()
    bot.loop = loop
    
    bot_task = bot.start()
    bits_task = listen_for_bits(bot, redis_client)
    await asyncio.gather(bot_task, bits_task)

if __name__ == "__main__":
    asyncio.run(main())