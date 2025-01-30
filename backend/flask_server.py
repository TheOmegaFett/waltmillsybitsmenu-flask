import requests
from flask import Flask, render_template, request, jsonify
import json
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)  # Allows Netlify & Twitch Panel to access API

# Add new route for the OBS browser source
@app.route('/overlay')
def overlay():
    return render_template('overlay.html', show_gif=False)

# Add WebSocket support for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print("Client connected to WebSocket!")

def process_bits_event(user, bits):
    print(f"🎉 Processing {bits} Bits from {user}")

    if bits == 1:
        print("🔥 FIRE MODE ACTIVATED!")
        print("Emitting fire_gif event...")
        socketio.emit('show_fire_gif', {'show': True}, broadcast=True)
return True

@app.route('/bits', methods=['POST'])
def handle_bits():
    """Handles Bits transactions from the Twitch Extension."""
    
    data = request.json
    bits_used = data.get("bits_used", 0)
    user = data.get("user_name", "Unknown")

    print(f"💰 {user} spent {bits_used} Bits!")

    # Example: Process Bits transaction
    process_bits_event(user, bits_used)

    return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})

def process_bits_event(user, bits):
    print(f"🎉 Processing {bits} Bits from {user}")
    
    if bits == 1:
        print("🔥 FIRE MODE ACTIVATED!")
        # Emit WebSocket event to trigger the GIF
        socketio.emit('show_fire_gif', {'show': True})
    elif bits == 500:
        print("🎶 SOUND EFFECT TRIGGERED!")
    elif bits == 1000:
        print("⚡ ULTRA HYPE MODE!")
    
    return True
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
