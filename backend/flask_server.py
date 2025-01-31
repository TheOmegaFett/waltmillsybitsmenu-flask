from asyncio.log import logger
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
        user = data.get("displayName")
        product = data.get("product", {})
        bits_used = int(product.get("cost", {}).get("amount", 0))
        
        if bits_used == 50:
            def send_command_wrapper():
                send_command('dropbear', {'user': user})
            
            eventlet.spawn(send_command_wrapper)
            socketio.emit('show_dropbear_gif', {'show': True})
            return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})
        
        return jsonify({"status": "error", "message": f"Invalid bits amount: {bits_used}"}), 400
    except Exception as e:
        logger.error(f"Error processing bits: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
