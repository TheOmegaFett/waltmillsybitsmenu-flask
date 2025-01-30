from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app)
sock = Sock(app)

clients = set()

@app.route('/overlay')
def overlay():
    return render_template('overlay.html')

@app.route('/bits', methods=['POST'])
def handle_bits():
    data = request.json
    bits_used = data.get("bits_used", 0)
    user = data.get("user_name", "Unknown")
    
    # Broadcast to all connected clients
    for client in clients:
        try:
            client.send('show_fire')
        except:
            clients.remove(client)
    
    return jsonify({"status": "success", "message": f"{user} spent {bits_used} Bits!"})

@sock.route('/ws')
def ws(sock):
    clients.add(sock)
    while True:
        data = sock.receive()
        print(f"Received websocket message: {data}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)