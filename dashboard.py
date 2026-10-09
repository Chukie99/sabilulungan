import os
import json
import urllib.request
import urllib.error
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import CONFIG, BASE_DIR

PORT = 5050
AGENTS_FILE = os.path.join(BASE_DIR, "agents.json")

# Allowed routes
ALLOWED_GET_ROUTES = ['/', '/index.html', '/api/agents']
ALLOWED_POST_ROUTES = ['/api/chat']

# In-memory simple conversation history
conversation_history = []

class SecureDashboardHandler(BaseHTTPRequestHandler):
    def get_route(self):
        return self.path.split('?')[0]

    def do_GET(self):
        route = self.get_route()
        
        if route in ALLOWED_GET_ROUTES:
            if route == '/' or route == '/index.html':
                self.serve_file('index.html', 'text/html; charset=utf-8')
            elif route == '/api/agents':
                self.serve_file('agents.json', 'application/json')
        else:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Access Denied.")

    def do_POST(self):
        route = self.get_route()
        
        if route == '/api/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                req = json.loads(post_data.decode('utf-8'))
                
                agent_role = req.get('agent', 'manager')
                prompt = req.get('message', '')
                reset = req.get('reset', False)
                
                if reset:
                    global conversation_history
                    conversation_history = []
                    self.send_json({"status": "success", "reply": "Memori percakapan di-reset."})
                    return

                if not os.path.exists(AGENTS_FILE):
                    self.send_json({"status": "error", "message": "File agents.json tidak ditemukan."})
                    return

                with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
                    agents = json.load(f)
                    
                agent_data = agents.get(agent_role, agents.get('manager'))
                
                # Masukkan ke history
                conversation_history.append({"role": "user", "content": prompt})
                
                # Batasi history maksimal 10 pesan terakhir agar tidak overflow
                messages = [{"role": "system", "content": agent_data['prompt']}] + conversation_history[-10:]

                api_payload = {
                    "model": CONFIG["MODEL"],
                    "messages": messages,
                    "temperature": 0.7
                }
                
                api_req = urllib.request.Request(
                    CONFIG["API_URL"],
                    data=json.dumps(api_payload).encode('utf-8'),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CONFIG['API_KEY']}"
                    },
                    method='POST'
                )
                
                # Timeout 30 detik agar server tidak hang
                try:
                    with urllib.request.urlopen(api_req, timeout=30) as res:
                        res_json = json.loads(res.read().decode('utf-8'))
                        bot_reply = res_json['choices'][0]['message']['content']
                        
                        # Simpan balasan ke history
                        conversation_history.append({"role": "assistant", "content": bot_reply})
                        
                        out = {"status": "success", "reply": bot_reply, "agent": agent_role}
                except urllib.error.URLError as e:
                    out = {"status": "error", "message": f"Koneksi ke Gateway ({CONFIG['API_URL']}) gagal: {str(e)}"}
                except socket.timeout:
                    out = {"status": "error", "message": "Gateway timeout (30s). 9Router terlalu lama merespons."}

                self.send_json(out)

            except Exception as e:
                self.send_json({"status": "error", "message": f"Server Error: {str(e)}"})
        else:
            self.send_response(404)
            self.end_headers()

    def serve_file(self, filename, content_type):
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    server = HTTPServer(('127.0.0.1', PORT), SecureDashboardHandler)
    print(f"SECURE DASHBOARD AKTIF: http://127.0.0.1:{PORT}")
    print(f"Using Gateway URL: {CONFIG['API_URL']} | Model: {CONFIG['MODEL']}")
    server.serve_forever()
