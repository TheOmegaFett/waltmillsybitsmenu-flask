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

async def execute_dropbear_event(bot, channel, user):
    try:
        logger.info(f"🎯 Starting dropbear execution for user: {user}")
        
        # Create author with WebSocket connection
        author = type('Author', (), {
            'name': user,
            'display_name': user,
            'is_mod': True,
            'is_broadcaster': True,
            '_ws': channel._ws  # Use channel's WebSocket connection
        })
        
        # Create message with all required attributes
        message = type('Message', (), {
            'content': '!dropbear',
            'channel': channel,
            'author': author,
            'tags': {},
            'echo': False,
            'raw_data': None,
            'timestamp': None,
            '_ws': channel._ws  # Use channel's WebSocket connection
        })
        
        ctx = await bot.get_context(message)
        logger.info("🎯 Using bot's native context")
        logger.info("🎯 Executing dropbear command...")
        
        await bot.dropbear(ctx)
        logger.info("🎯 Dropbear command completed")
        
    except Exception as e:
        logger.error(f"🚫 Error in dropbear execution: {str(e)}", exc_info=True)
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
                
                if data['type'] == 'dropbear':
                    channel = bot.get_channel(os.getenv('TWITCH_CHANNEL'))
                    if channel:
                        logger.info(f"📢 Found channel: {channel.name}")
                        await execute_dropbear_event(bot, channel, data['data']['user'])
                    
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

