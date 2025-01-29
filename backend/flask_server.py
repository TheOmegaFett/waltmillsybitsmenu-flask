import requests
from flask import Flask, request, jsonify
import asyncio
import websockets
import json
from flask_cors import CORS



app = Flask(__name__)

CORS(app)  # Allows Netlify & Twitch Panel to access API

BOT_SERVER_URL = "http://localhost:6000/bits_event"

@app.route('/bits', methods=['POST'])
def handle_bits():
    data = request.json
    bits_used = data.get("bits_used", 0)
    user = data.get("user_name", "Unknown")

    print(f"{user} spent {bits_used} Bits!")

    # Send event to bot API
    response = requests.post(BOT_SERVER_URL, json={
        "bits_used": bits_used,
        "user_name": user
    })

    return jsonify(response.json())

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render assigns a port dynamically
    app.run(host="0.0.0.0", port=port, debug=True)
