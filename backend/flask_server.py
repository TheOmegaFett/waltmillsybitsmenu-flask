import eventlet
eventlet.monkey_patch()

import redis

redis_client = redis.Redis.from_url('redis://red-cudsn6lds78s73dfsh0g:6379')


from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from message_handler import send_command
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

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
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
        
    data = request.json
    bits_used = data.get("bits_used", 0)
    user = data.get("user_name", "Unknown")
    sku = data.get("sku")
    
    print(f"💰 Processed data: User={user}, Bits={bits_used}, SKU={sku}")

    if bits_used == 1:
        socketio.emit('show_fire_gif', {'show': True})
        send_command('hello', {'user': user})
        return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})
    elif bits_used == 50:
        print("🐨 Starting dropbear command flow")
        print(f"🐨 Emitting dropbear gif for user: {user}")
        socketio.emit('show_dropbear_gif', {'show': True})
        print("🐨 Sending dropbear command to Redis")
        send_command('dropbear', {'user': user})
        print("🐨 Dropbear command sent successfully")
        return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})
    
    return jsonify({"status": "error", "message": "Invalid bits amount"}), 400
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

