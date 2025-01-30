import os
import asyncio
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet
from main import Bot, main  # Import your Bot class

eventlet.monkey_patch()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', ping_timeout=10000, ping_interval=5000)

# Initialize bot
bot = Bot()

# Create background task for bot
def run_bot():
    asyncio.run(main())  # Your existing main() function

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
    # Start bot in background thread
    from threading import Thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)