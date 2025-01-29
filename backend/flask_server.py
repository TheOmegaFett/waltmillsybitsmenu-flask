import requests
from flask import Flask, request, jsonify
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows Netlify & Twitch Panel to access API

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
    """Processes the Bits event (e.g., logs it, updates a database, triggers OBS)."""

    # Log the event
    print(f"🎉 Processing {bits} Bits from {user}")

    # (Optional) Add Database Logging Here
    # save_to_database(user, bits)

    # (Optional) Trigger OBS Overlays or Alerts
    # trigger_obs_overlay(bits, user)

    # (Optional) Send a Webhook or Discord Alert
    # send_discord_alert(f"{user} just spent {bits} Bits!")

    # (Optional) Display Custom Graphics
    if bits == 100:
        print("🔥 FIRE MODE ACTIVATED!")
    elif bits == 500:
        print("🎶 SOUND EFFECT TRIGGERED!")
    elif bits == 1000:
        print("⚡ ULTRA HYPE MODE!")
    
    return True

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render assigns a port dynamically
    app.run(host="0.0.0.0", port=port, debug=True)
