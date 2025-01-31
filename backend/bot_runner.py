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
        
        # Create a send method that's properly bound to the channel
        async def send_message(content):
            logger.info(f"📨 Sending message to chat: {content}")
            await channel.send(content)
            
        mock_ctx = type('Context', (), {
            'send': send_message,  # Use our new send method
            'channel': channel,
            'view': None,
            'author': type('Author', (), {
                'is_mod': True,
                'is_broadcaster': True,
                'name': user,
                'display_name': user
            })(),
            'message': type('Message', (), {
                'content': '!dropbear',
                'channel': channel,
                'author': type('Author', (), {
                    'name': user,
                    'display_name': user
                })()
            })()
        })
        
        logger.info("🎯 Mock context created")
        await bot.dropbear(mock_ctx)
        logger.info("🎯 Dropbear command executed successfully")
        
    except Exception as e:
        logger.error(f"🚫 Error: {str(e)}", exc_info=True)

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

