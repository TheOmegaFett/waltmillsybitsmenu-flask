import redis
import json
import os

# Use internal Redis connection for Render
redis_client = redis.Redis(host='bot-redis', port=6379, db=0)

def send_command(command_type, data):
    message = {
        'type': command_type,
        'data': data
    }
    redis_client.publish('bot_commands', json.dumps(message))
