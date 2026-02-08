import os
from flask import Flask, render_template, request, jsonify
from cryptography.fernet import Fernet
from datetime import datetime

app = Flask(__name__)

# Encryption Key Management
KEY_FILE = "secret.key"
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f: f.write(Fernet.generate_key())
cipher = Fernet(open(KEY_FILE, "rb").read())

# Database in RAM
rooms_db = {}
story_tracker = {} 
active_users = {} 

COVER_STORIES = [
    "Did you see the notes for the exam?", "I think we should study the third chapter first.",
    "The weather is quite nice today.", "Do you have the link for the online class?",
    "History projects are time-consuming.", "Let's meet at the library around 5 PM."
]

@app.route('/')
def index(): return render_template('chat.html')

@app.route('/dashboard')
def dashboard_page(): return render_template('dashboard.html')

@app.route('/join', methods=['POST'])
def join():
    data = request.json
    rid, name = data.get('room_id'), data.get('user_name')
    if rid not in active_users: active_users[rid] = []
    active_users[rid] = [u for u in active_users[rid] if u['name'] != name]
    active_users[rid].append({"name": name, "time": datetime.now().strftime("%H:%M:%S")})
    return jsonify({"status": "ok"})

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    rid, txt, name = data.get('room_id'), data.get('message'), data.get('sender_name')
    if rid not in rooms_db: 
        rooms_db[rid] = []
        story_tracker[rid] = {}
    
    idx = story_tracker[rid].get(name, 0)
    story_line = COVER_STORIES[idx % len(COVER_STORIES)]
    story_tracker[rid][name] = idx + 1

    entry = {
        "id": len(rooms_db[rid]), "sender": name, "story": story_line,
        "encrypted": cipher.encrypt(txt.encode()).decode()
    }
    rooms_db[rid].append(entry)
    return jsonify({"status": "success"})

@app.route('/fetch', methods=['POST'])
def fetch():
    rid = request.json.get('room_id')
    return jsonify(rooms_db.get(rid, []))

@app.route('/decrypt', methods=['POST'])
def decrypt():
    data = request.json
    if data.get('password') != "11": return jsonify({"error": "Wrong"}), 403
    try:
        msg = rooms_db[data['room_id']][int(data['msg_id'])]
        return jsonify({"original": cipher.decrypt(msg['encrypted'].encode()).decode()})
    except: return jsonify({"error": "Fail"}), 404

@app.route('/get_admin_data', methods=['POST'])
def get_admin_data():
    if request.json.get('password') == "123":
        total = sum(len(u) for u in active_users.values())
        return jsonify({"users": active_users, "chats": rooms_db, "total_active": total})
    return jsonify({"error": "Unauthorized"}), 403

if __name__ == '__main__':
    app.run(debug=True, port=5000)