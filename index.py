import os
from flask import Flask, render_template_string, jsonify, request
import requests
import time
import re
from threading import Thread

app = Flask(__name__)

# Branding
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
        domains = requests.get(f"{API_BASE}/domains", timeout=10).json()
        domain = domains[0]['domain'] if domains else "@tempmail.lol"
        response = requests.post(f"{API_BASE}/accounts", json={"domain": domain}, timeout=10)
        data = response.json()
        current_email = data['address']
        current_token = data['token']
        print(f"✅ New email: {current_email}")
        return True
    except:
        return False

def fetch_messages():
    global messages
    while True:
        try:
            if current_token:
                resp = requests.get(f"{API_BASE}/accounts/{current_token}/messages", 
                                  headers={'Authorization': f'Bearer {current_token}'}, timeout=10)
                new_messages = resp.json().get('hydra:member', [])
                for msg in new_messages[-3:]:
                    if msg not in messages:
                        messages.append(msg)
                        body = str(msg.get('text', '') + msg.get('html', ''))
                        otp_match = re.search(r'\bd{4,8}\b', body)
                        if otp_match:
                            msg['otp'] = otp_match.group()
                messages[:] = messages[-5:]
        except:
            pass
        time.sleep(5)

Thread(target=fetch_messages, daemon=True).start()
generate_temp_email()

@app.route('/')
def index():
    HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ritish Ower - Temp Mail + OTP</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;}
        .container{max-width:700px;margin:0 auto;background:white;border-radius:20px;padding:30px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}
        .header{text-align:center;padding:30px;background:linear-gradient(45deg,#ff6b6b,#feca57);color:white;border-radius:15px;}
        button{padding:15px 25px;font-size:16px;border:none;border-radius:10px;background:linear-gradient(45deg,#ff6b6b,#feca57);color:white;cursor:pointer;}
        .email-box{background:#f8f9fa;padding:25px;border-radius:15px;margin:20px 0;font-size:18px;}
        .otp-highlight{background:#ffeb3b;font-weight:bold;font-size:24px;padding:15px;border-radius:10px;display:inline-block;}
        .message{border-left:5px solid #4ecdc4;padding:20px;margin:15px 0;background:#f8f9fa;border-radius:10px;}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Unlimited Temp Mail + OTP</h1>
            <h3>👨‍💻 Ritish Ower</h3>
            <p>📧 {{ owner_email }} | 💬 <a href="https://t.me/{{ owner_telegram }}" style="color:white;">@{{ owner_telegram }}</a></p>
        </div>
        
        <button onclick="generateNew()">🔄 New Email</button>
        <div class="email-box">
            <strong>📨 Current Email:</strong><br>
            <span id="email" style="word-break:break-all;font-size:20px;">{{ email or 'Click New Email' }}</span><br>
            <button onclick="copyEmail()" style="background:#28a745;font-size:14px;">📋 Copy</button>
        </div>
        
        <h3>📬 Messages:</h3>
        <div id="messages">Waiting...</div>
    </div>
    <script>
        function generateNew(){fetch('/generate',{method:'POST'}).then(r=>r.json()).then(updateUI);}
        function copyEmail(){navigator.clipboard.writeText(document.getElementById('email').textContent).then(()=>alert('✅ Copied!'));}
        function updateUI(data){
            document.getElementById('email').textContent=data.email||'No email';
            let msgs=document.getElementById('messages');
            msgs.innerHTML=data.messages.length?data.messages.map(m=>`<div class="message"><strong>${m.from}</strong><br>${m.subject||''}<br>${m.otp?'<span class="otp-highlight">OTP: '+m.otp+'</span>':''}</div>`).join(''):'Waiting...';
        }
        setInterval(()=>fetch('/status').then(r=>r.json()).then(updateUI),3000);
    </script>
</body>
</html>'''
    return render_template_string(HTML, email=current_email, owner_email=OWNER_EMAIL, owner_telegram=OWNER_TELEGRAM)

@app.route('/status')
def status():
    return jsonify({'email': current_email, 'messages': messages[-5:]})

@app.route('/generate', methods=['POST'])
def generate():
    generate_temp_email()
    return jsonify({'email': current_email, 'messages': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
