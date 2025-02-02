import eventlet
eventlet.monkey_patch(os=False)  # Don't patch os operations

from asyncio.log import logger
import redis
from redis.exceptions import ConnectionError
from collections import deque
import json
import time

redis_client = redis.Redis.from_url('redis://red-cudsn6lds78s73dfsh0g:6379', decode_responses=True)

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from message_handler import send_command
import os

# Add these constants at the top of the file
QUEUE_KEY_DROPBEAR = 'gif_queue_dropbear'
QUEUE_KEY_FIRE = 'gif_queue_fire'
GIF_DURATION_DROPBEAR = 3000  # Duration in ms
GIF_DURATION_FIRE = 2000  # Duration in ms

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

@app.route('/overlay')
def overlay():
    return render_template('overlay.html')

# Add Redis health check endpoint
@app.route('/health')
def health_check():
    try:
        redis_client.ping()
        return jsonify({"status": "healthy", "redis": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)})

# Add this function to process queued gifs
def process_gif_queue(queue_key, duration_ms):
    while True:
        try:
            # Get but don't remove the first item in the queue
            queued_item = redis_client.lindex(queue_key, 0)
            if queued_item:
                gif_data = json.loads(queued_item)
                
                # Add timestamp check to prevent processing old items
                if time.time() - gif_data['timestamp'] > 300:  # 5 minutes timeout
                    redis_client.lpop(queue_key)
                    continue
                
                # Emit event with retry logic
                retry_count = 0
                while retry_count < 3:
                    try:
                        socketio.emit(gif_data['event'], {'show': True})
                        break
                    except Exception as e:
                        print(f"[ERROR] Emit retry {retry_count}: {str(e)}")
                        retry_count += 1
                        eventlet.sleep(0.5)
                
                eventlet.sleep(duration_ms / 1000.0)
                redis_client.lpop(queue_key)
                socketio.emit(gif_data['event'], {'show': False})
            
            eventlet.sleep(0.1)
            
        except Exception as e:
            print(f"[ERROR] Queue processor error: {str(e)}")
            eventlet.sleep(1)

# Modify the handle_bits function@app.route('/bits', methods=['POST'])
def handle_bits():
    try:
        data = request.json
        print(f"[DEBUG] Bits endpoint hit with data: {data}")
        
        if data.get('initiator') != 'current_user':
            return jsonify({"status": "skipped", "reason": "non-primary initiator"})
            
        user = data.get("displayName")
        product = data.get("product", {})
        bits_used = int(product.get("cost", {}).get("amount", 0))
        
        if bits_used == 50:
            print(f"[DEBUG] Processing 50 bits for user: {user}")
            send_command('dropbear', {'user': user})
            # Add to dropbear queue
            redis_client.rpush(QUEUE_KEY_DROPBEAR, json.dumps({
                'event': 'show_dropbear_gif',
                'user': user,
                'timestamp': time.time()
            }))
            return jsonify({"status": "success"})
            
        elif bits_used == 1:
            # Add to fire queue
            redis_client.rpush(QUEUE_KEY_FIRE, json.dumps({
                'event': 'show_fire_gif',
                'timestamp': time.time()
            }))
            print("[DEBUG] Added fire gif to queue")
            return jsonify({"status": "success"})
            
        return jsonify({"status": "error", "message": "Invalid bits amount"}), 400
        
    except Exception as e:
        print(f"[ERROR] Exception in bits handler: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print("[DEBUG] Client connected to WebSocket")
    # Immediately check and process any pending items in queues
    eventlet.spawn(check_pending_queues)

def check_pending_queues():
    try:
        # Check both queues for pending items
        dropbear_pending = redis_client.llen(QUEUE_KEY_DROPBEAR)
        fire_pending = redis_client.llen(QUEUE_KEY_FIRE)
        print(f"[DEBUG] Pending items - Dropbear: {dropbear_pending}, Fire: {fire_pending}")
        
        # If there are pending items, ensure queue processors are running
        if dropbear_pending > 0 or fire_pending > 0:
            start_queue_processors()
    except Exception as e:
        print(f"[ERROR] Queue check failed: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    print("[DEBUG] Client disconnected from WebSocket")

@socketio.on('error')
def handle_error(error):
    print(f"[ERROR] WebSocket error: {error}")
    # Attempt to reconnect or recover
    eventlet.spawn(check_pending_queues)
# Add this before the if __name__ == "__main__": block
def start_queue_processors():
    eventlet.spawn(process_gif_queue, QUEUE_KEY_DROPBEAR, GIF_DURATION_DROPBEAR)
    eventlet.spawn(process_gif_queue, QUEUE_KEY_FIRE, GIF_DURATION_FIRE)

# Modify the main block to start queue processors
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    start_queue_processors()
    socketio.run(app, 
                host="0.0.0.0", 
                port=port,
                log_output=True,
                use_reloader=False)  # Disable reloader in production


