import redis
import json
import os

# Default to local Redis if no URL provided
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url)

def send_command(command_type, data):
    message = {
        'type': command_type,
        'data': data
    }
    redis_client.publish('bot_commands', json.dumps(message))
