import redis
import json
import asyncio
from main import Bot

async def listen_for_commands(bot):
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
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
