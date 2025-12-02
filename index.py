import os
from flask import Flask, render_template_string, jsonify, request
import requests
import time
import re
from threading import Thread

app = Flask(__name__)

OWNER_NAME = "Ritish Ower"
OWNER_EMAIL = "xoritish@gmail.com"
OWNER_TELEGRAM = "xoritish"

API_BASE = "https://tempmail.lol/api"
current_email = None
current_token = None
messages = []

def generate_temp_email():
    global current_email, current_token
    try:
        domains = requests.get(f"{API_BASE}/domains", timeout=5).json()
        domain = domains[0]['domain'] if domains else "@tempmail.lol"
        response = requests.post(f"{API_BASE}/accounts", json={"domain": domain}, timeout=5)
        data = response.json()
        current_email = data['address']
        current_token = data['token']
        print(f"✅ New email: {current_email}")
        return True
    except:
        current_email = "temp@tempmail.lol"
        return False

def fetch_messages():
    global messages
    while True:
        try:
            if current_token:
                resp = requests.get(f"{API_BASE}/accounts/{current_token}/messages", 
                    headers={'Authorization': f'Bearer {current_token}'}, timeout=5)
                new_messages = resp.json().get('hydra:member', [])
                for msg in new_messages[-1:]:
                    if msg not in messages:
                        messages.append(msg)
                        body = str(msg.get('text', '') + msg.get('html', ''))
                        otp = re.search(r'\bd{4,8}\b', body)
                        if otp:
                            msg['otp'] = otp.group()
        except:
            pass
        time.sleep(10)
        if len(messages) > 10:
            messages.clear()

Thread(target=fetch_messages, daemon=True).start()
generate_temp_email()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Ritish Ower - Temp Mail</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width">
    <style>
        body{font-family:Arial;background:#f0f2f5;padding:20px;margin:0;}
        .container{max-width:600px;margin:auto;background:white;border-radius:10px;padding:30px;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
        .header{background:linear-gradient(45deg,#ff6b6b,#feca57);color:white;padding:20px;border-radius:10px;text-align:center;}
        button{padding:12px 24px;border:none;border-radius:8px;background:#ff6b6b;color:white;font-weight:bold;cursor:pointer;margin:10px;}
        .email-box{background:#f8f9fa;padding:20px;border-radius:10px;margin:20px 0;}
        .otp-highlight{background:#ffeb3b;font-weight:bold;font-size:22px;padding:10px;border-radius:8px;display:inline-block;}
        .message{padding:15px;margin:10px 0;background:#f8f9fa;border-radius:8px;border-left:4px solid #4ecdc4;}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Temp Mail + OTP</h1>
            <h3>Ritish Ower</h3>
            <p>{{owner_email}} | <a href="https://t.me/{{owner_telegram}}" style="color:white;">@{{owner_telegram}}</a></p>
        </div>
        
        <button onclick="generateNew()">🔄 New Email</button>
        <div class="email-box">
            <strong>📧 Email:</strong> <span id="email" style="font-size:18px;word-break:break-all;">{{email or "Click New Email"}}</span><br>
            <button onclick="copyEmail()" style="background:#28a745;font-size:14px;">📋 Copy</button>
        </div>
        
        <h3>📬 Messages:</h3>
        <div id="messages">Waiting for emails...</div>
    </div>
    
    <script>
    function generateNew(){fetch('/generate',{method:'POST'}).then(r=>r.json()).then(updateUI);}
    function copyEmail(){navigator.clipboard.writeText(document.getElementById('email').textContent);alert('✅ Copied!');}
    function updateUI(data){
        document.getElementById('email').textContent = data.email||'No email';
        let msgs = document.getElementById('messages');
        if(!data.messages.length) return msgs.innerHTML = 'Waiting...';
        msgs.innerHTML = data.messages.map(m=>`
            <div class="message">
                <strong>${m.from||'Unknown'}</strong><br>
                ${m.subject||'No subject'}<br>
                ${m.otp ? `<span class="otp-highlight">OTP: ${m.otp}</span>` : 'No OTP'}
            </div>`).join('');
    }
    setInterval(()=>fetch('/status').then(r=>r.json()).then(updateUI),5000);
    </script>
</body>
</html>'''.format(email=current_email, owner_email=OWNER_EMAIL, owner_telegram=OWNER_TELEGRAM)

@app.route('/status')
def status():
    return jsonify({'email': current_email, 'messages': messages[-3:]})

@app.route('/generate', methods=['POST'])
def generate():
    generate_temp_email()
    return jsonify({'email': current_email, 'messages': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
