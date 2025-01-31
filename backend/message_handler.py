import redis
import json
import os

redis_client = redis.Redis(
    host='redis',  
    port=6379,
    decode_responses=True
)

def send_command(command_type, data):
    message = {
        'type': command_type,
        'data': data
    }
    redis_client.publish('bot_commands', json.dumps(message))
