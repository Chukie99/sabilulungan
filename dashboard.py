import os
import json
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 5050
ENV_FILE = ".env"
AGENTS_FILE = "agents.json"

def get_env():
    conf = {"API_KEY": "hermes", "MODEL": "anthropic/claude-3.5-sonnet"}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    conf[k] = v
    return conf

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/api/agents':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            with open(AGENTS_FILE, 'rb') as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            
            agent_role = req.get('agent', 'manager')
            prompt = req.get('message', '')
            
            with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
                agents = json.load(f)
                
            agent_data = agents.get(agent_role, agents.get('manager'))
            conf = get_env()
            
            api_payload = {
                "model": conf.get("MODEL", "anthropic/claude-3.5-sonnet"),
                "messages": [
                    {"role": "system", "content": agent_data['prompt'] + "\nFormat your response cleanly. If you delegate to another team member, write '@Designer', '@Coder', etc."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            api_req = urllib.request.Request(
                "http://localhost:20128/v1/chat/completions",
                data=json.dumps(api_payload).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {conf.get('API_KEY', 'hermes')}"
                },
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(api_req) as res:
                    res_json = json.loads(res.read().decode('utf-8'))
                    bot_reply = res_json['choices'][0]['message']['content']
                    out = {"status": "success", "reply": bot_reply, "agent": agent_role}
            except Exception as e:
                out = {"status": "error", "message": f"Koneksi ke 9Router gagal: {str(e)}"}
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(out).encode('utf-8'))

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    print(f"DASHBOARD AKTIF: http://127.0.0.1:{PORT}")
    server.serve_forever()
