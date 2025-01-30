import redis
import json
import asyncio
import os
from main import Bot

async def listen_for_commands(bot):
    redis_url = os.getenv('REDIS_URL')
    redis_client = redis.from_url(redis_url)
    pubsub = redis_client.pubsub()
    pubsub.subscribe('bot_commands')
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            if data['type'] == 'dropbear':
                await bot.dropbear(data['data']['user'])

if __name__ == "__main__":
    bot = Bot()
    loop = asyncio.get_event_loop()
    loop.create_task(listen_for_commands(bot))
    loop.run_until_complete(bot.start())
