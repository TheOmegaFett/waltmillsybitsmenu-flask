import redis
import json
import asyncio
import os
from main import Bot

async def main():
    # Initialize bot
    bot = Bot()
    
    # Set up Redis listener
    redis_url = os.getenv('REDIS_URL')
    redis_client = redis.from_url(redis_url)
    pubsub = redis_client.pubsub()
    pubsub.subscribe('bot_commands')
    
    # Start bot first
    bot_task = asyncio.create_task(bot.start())
    
    # Listen for Redis messages while bot runs
    while True:
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            data = json.loads(message['data'])
            if data['type'] == 'dropbear':
                await bot.dropbear(data['data']['user'])
        await asyncio.sleep(0.1)  # Prevent CPU spinning

if __name__ == "__main__":
    asyncio.run(main())