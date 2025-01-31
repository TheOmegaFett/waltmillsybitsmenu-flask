import eventlet
eventlet.monkey_patch()

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

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
@app.route('/health')
def health_check():
    try:
        redis_client.ping()
        return jsonify({"status": "healthy", "redis": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)})


@app.route('/bits', methods=['POST'])
def handle_bits():
    print("🔍 Incoming Twitch Transaction:")
    print(f"Raw Data: {request.get_data(as_text=True)}")
    
    try:
        data = request.json
        user = data.get("displayName")
        product = data.get("product", {})
        
        # Convert bits amount to integer
        bits_used = int(product.get("cost", {}).get("amount", 0))
        
        print(f"💰 Bits Amount Found: {bits_used}")

        if bits_used == 1:
            print("🔥 Triggering fire gif")
            socketio.emit('show_fire_gif', {'show': True})
            send_command('!hello', {'user': user})
            return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})
        elif bits_used == 50:
            print("🐨 Starting dropbear command flow")
            socketio.emit('show_dropbear_gif', {'show': True})
            with app.app_context():  # Ensure Flask app context is active
                send_command('dropbear', {'user': user})
            print("🐨 Dropbear command completed")
            return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})
        
        return jsonify({"status": "error", "message": f"Invalid bits amount: {bits_used}"}), 400
    except Exception as e:
        print(f"❌ Error processing request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

