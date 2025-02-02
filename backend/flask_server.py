import eventlet
eventlet.monkey_patch(os=False)  # Don't patch os operations

from asyncio.log import logger
import redis
from redis.exceptions import ConnectionError

redis_client = redis.Redis.from_url('redis://red-cudsn6lds78s73dfsh0g:6379', decode_responses=True)

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from message_handler import send_command
import os

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

@app.route('/bits', methods=['POST'])
def handle_bits():
    try:
        data = request.json
        print(f"[DEBUG] Bits endpoint hit with data: {data}")
        user = data.get("displayName")
        product = data.get("product", {})
        bits_used = int(product.get("cost", {}).get("amount", 0))
        
        if bits_used == 50:
            # Handle both command and WebSocket event together
            def command_wrapper():
                send_command('dropbear', {'user': user})
                socketio.emit('show_dropbear_gif', {'show': True})
                print(f"[DEBUG] Emitted dropbear events for user: {user}")
            
            eventlet.spawn(command_wrapper)
            return jsonify({"status": "success"})
            
        elif bits_used == 1:
            socketio.emit('show_fire_gif', {'show': True})
            print("[DEBUG] Emitted fire gif event")
            return jsonify({"status": "success"})
            
        return jsonify({"status": "error", "message": "Invalid bits amount"}), 400
        
    except Exception as e:
        print(f"[ERROR] Exception in bits handler: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print("[DEBUG] Client connected to WebSocket")

@socketio.on('disconnect')
def handle_disconnect():
    print("[DEBUG] Client disconnected from WebSocket")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, 
                host="0.0.0.0", 
                port=port,
                log_output=True,
                use_reloader=False)  # Disable reloader in production

