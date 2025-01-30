from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Add new route for the OBS browser source
@app.route('/overlay')
def overlay():
    return render_template('overlay.html', show_gif=False)

@app.route('/bits', methods=['POST'])
def handle_bits():
    data = request.json
    bits_used = data.get("bits_used", 0)
    user = data.get("user_name", "Unknown")
    
    if bits_used == 1:
        socketio.emit('show_fire_gif', {'show': True}, namespace='/')
    
    return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)