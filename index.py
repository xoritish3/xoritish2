import os
from flask import Flask, render_template_string, jsonify, request
import requests
import time
import re
from threading import Thread

app = Flask(__name__)

# Your Branding
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
    except Exception as e:
        print(f"❌ Email gen error: {e}")
        return False

def fetch_messages():
    global messages
    while True:
        try:
            if current_token:
                resp = requests.get(
                    f"{API_BASE}/accounts/{current_token}/messages", 
                    headers={'Authorization': f'Bearer {current_token}'},
                    timeout=10
                )
                new_messages = resp.json().get('hydra:member', [])
                for msg in new_messages[-3:]:
                    if 'id' not in msg or msg not in messages:
                        messages.append(msg)
                        body = (msg.get('text', '') + msg.get('html', '')).lower()
                        otp_match = re.search(r'\bd{4,8}\b', body)
                        if otp_match:
                            msg['otp'] = otp_match.group()
                messages[:] = messages[-5:]  # Keep last 5
        except:
            pass
        time.sleep(5)

# Start background poller
Thread(target=fetch_messages, daemon=True).start()
generate_temp_email()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Ritish Ower - Temp Mail + OTP</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
        .container{max-width:700px;margin:0 auto;background:white;border-radius:20px;padding:30px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}
        .header{text-align:center;padding:30px 20px;background:linear-gradient(45deg,#ff6b6b,#feca57);color:white;border-radius:15px;margin:-30px -30px 30px -30px;}
        .owner-info{padding:15px;background:linear-gradient(45deg,#4ecdc4,#44a08d);border-radius:10px;margin:20px 0;color:white;}
        button{padding:15px 25px;font-size:16px;border:none;border-radius:10px;cursor:pointer;font-weight:bold;margin:10px;background:linear-gradient(45deg,#ff6b6b,#feca57);color:white;box-shadow:0 5px 15px rgba(0,0,0,0.2);}
        button:hover{transform:translateY(-2px);}
        .email-box{background:#f8f9fa;padding:25px;border-radius:15px;margin:20px 0;font-size:18px;border-left:5px solid #007bff;}
        .otp-highlight{background:#ffeb3b!important;font-weight:bold;font-size:24px;padding:15px;border-radius:10px;display:inline-block;color:#333;box-shadow:0 5px 15px rgba(255,235,59,0.4);}
        .message{border-left:5px solid #4ecdc4;padding:20px;margin:15px 0;background:#f8f9fa;border-radius:10px;}
        .copy-btn{background:#28a745!important;font-size:14px;padding:10px 20px;}
        .telegram-btn{background:#0088cc!important;}
        h3{margin:25px 0 15px 0;color:#333;}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Unlimited Temp Mail + OTP</h1>
            <div class="owner-info">
                <h3>👨‍💻 Ritish Ower</h3>
                <p>📧 {{ owner_email }} | 💬 <a href="https://t.me/{{ owner_telegram }}" target="_blank" class="telegram-btn" style="color:white;text-decoration:none;">@{{ owner_telegram }}</a></p>
            </div>
        </div>
        
        <button onclick="generateNew()" style="width:250px;font-size:18px;">🔄 Generate New Email</button>
        
        <div class="email-box">
            <strong>📨 Current Email:</strong><br>
            <span id="email" style="word-break:break-all;color:#2c3e50;font-size:20px;">{{ email or 'Click New Email' }}</span><br><br>
            <button class="copy-btn" onclick="copyEmail()">📋 Copy Email</button>
            <small>Auto-refreshes every 3s 👀</small>
        </div>
        
        <h3>📬 Messages & OTPs:</h3>
        <div id="messages">Waiting for emails...</div>
    </div>

    <script>
        function generateNew(){fetch('/generate',{method:'POST'}).then(r=>r.json()).then(updateUI);}
        function copyEmail(){navigator.clipboard.writeText(document.getElementById('email').textContent).then(()=>alert('✅ Email copied!'));}
        function updateUI(data){
            document.getElementById('email').textContent=data.email||'No email';
            let msgs=document.getElementById('messages');
            if(!data.messages?.length) msgs.innerHTML='<div style="text-align:center;color:#666;padding:30px;">📨 Waiting for OTPs...</div>';
            else msgs.innerHTML=data.messages.map(m=>`
                <div class="message">
                    <strong>👤 ${m.from||'Unknown'}</strong> 
                    <span style="float:right;color:#666;font-size:14px;">${new Date(m.date||Date.now()).toLocaleString()}</span><br>
                    <strong>📋 ${m.subject||'No subject'}</strong><br>
                    ${m.otp?`<span class="otp-highlight">🔑 OTP: ${m.otp}</span>`:'🔍 No OTP found'}
                </div>`).join('');
        }
        setInterval(()=>fetch('/status').then(r=>r.json()).then(updateUI),3000);
        updateUI({email:'{{ email or "" }}',messages:[]});
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                email=current_email, 
                                owner_email=OWNER_EMAIL,
                                owner_telegram=OWNER_TELEGRAM)

@app.route('/status')
def status():
    return jsonify({'email': current_email, 'messages': messages})

@app.route('/generate', methods=['POST'])
def generate():
    generate_temp_email()
    return jsonify({'email': current_email, 'messages': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌟 Ritish Ower's Temp Mail LIVE on port {port}")
    print(f"📧 xoritish@gmail.com | 💬 @xoritish")
    app.run(host='0.0.0.0', port=port, debug=False)