import eventlet
import redis
import json
import os

redis_client = redis.Redis.from_url('redis://red-cudsn6lds78s73dfsh0g:6379')


def send_command(command_type, data):
    message = {
        'type': command_type,
        'data': data
    }
    # Ensure Redis publish is wrapped in an eventlet-friendly way
    with eventlet.Timeout(5, False):  # 5 second timeout
        redis_client.publish('bot_commands', json.dumps(message))
