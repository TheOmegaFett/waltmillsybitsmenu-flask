import eventlet
eventlet.monkey_patch()

import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from main import Bot, start_bot

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', ping_timeout=10000, ping_interval=5000)

# Initialize bot with the event loop
bot = Bot()
bot.loop = loop

@app.route('/overlay')
def overlay():
    return render_template('overlay.html')

@app.route('/bits', methods=['POST'])
def handle_bits():
    data = request.json
    bits_used = data.get("bits_used", 0)
    user = data.get("user_name", "Unknown")
    
    if bits_used == 1:
        socketio.emit('show_fire_gif', {'show': True})
    elif bits_used == 50:
        socketio.emit('show_dropbear_gif', {'show': True})
        # Trigger the bot's dropbear event
        asyncio.run_coroutine_threadsafe(bot.dropbear(user), bot.loop)
    
    return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)