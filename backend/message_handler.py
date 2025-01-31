import redis
import json
import os

redis_client = redis.Redis.from_url('redis://red-cudsn6lds78s73dfsh0g:6379')


def send_command(command_type, data):
    message = {
        'type': command_type,
        'data': data
    }
    # Add logging to track message publishing
    print(f"Publishing command to Redis: {message}")
    redis_client.publish('bot_commands', json.dumps(message))
