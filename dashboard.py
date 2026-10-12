import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from pathlib import Path
from config import BASE_DIR, CONFIG
from runtime import Runtime

PORT = 5050

class SecureDashboardHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def allowed(self):
        hosts = {'localhost:' + str(self.server.server_port), '127.0.0.1:' + str(self.server.server_port)}
        host = self.headers.get('Host')
        origin = self.headers.get('Origin')
        if host not in hosts or (origin and origin != 'http://' + host):
            self.send_json({'message': 'Host atau Origin tidak diizinkan.'}, 403)
            return False
        return True

    def do_GET(self):
        if not self.allowed():
            return
        url = urlsplit(self.path)
        route = url.path
        query = parse_qs(url.query)
        runtime = self.server.runtime
        try:
            if route in ('/', '/index.html'):
                payload = (Path(BASE_DIR) / 'index.html').read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                self.wfile.write(payload)
            elif route == '/api/agents':
                self.send_json(runtime.agents())
            elif route == '/api/tasks':
                self.send_json(runtime.tasks(query.get('agent', [None])[0]))
            elif route == '/api/task':
                self.send_json(runtime.get(query.get('id', [''])[0]))
            elif route == '/api/memory':
                self.send_json(runtime.memories(query.get('agent', ['manager'])[0]))
            elif route == '/api/files':
                self.send_json(runtime.files())
            elif route == '/api/file':
                path = runtime.path(query.get('path', [''])[0])
                if path.stat().st_size > 1000000:
                    raise ValueError('File terlalu besar.')
                # JSON/text only; never execute generated HTML in the dashboard origin.
                self.send_json({'path': str(path.relative_to(runtime.workspace)),
                                'content': path.read_text(encoding='utf-8')})
            elif route == '/api/approvals':
                self.send_json(runtime.approvals())
            elif route == '/api/routines':
                self.send_json(runtime.routines())
            elif route == '/api/status':
                self.send_json({'model': CONFIG['MODEL'], 'provider': CONFIG['PROVIDER']})
            else:
                self.send_json({'message': 'Rute tidak ditemukan.'}, 404)
        except (KeyError, FileNotFoundError):
            self.send_json({'message': 'Tidak ditemukan.'}, 404)
        except (ValueError, OSError, UnicodeError) as exc:
            self.send_json({'message': str(exc)}, 400)

    def do_POST(self):
        if not self.allowed():
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.send_json({'message': 'Gunakan application/json.'}, 415)
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length <= 0 or length > 100000:
                raise ValueError('Ukuran request tidak valid.')
            req = json.loads(self.rfile.read(length))
            if not isinstance(req, dict):
                raise ValueError('Request harus objek JSON.')
            route = urlsplit(self.path).path
            runtime = self.server.runtime
            if route in ('/api/tasks', '/api/chat') and not req.get('reset'):
                self.send_json(runtime.submit(req.get('agent', 'manager'), req.get('message')), 202)
            elif route == '/api/memory/reset' or (route == '/api/chat' and req.get('reset')):
                runtime.forget(req.get('agent', 'manager'))
                self.send_json({'status': 'success'})
            elif route == '/api/approval':
                if not isinstance(req.get('allow'), bool):
                    raise ValueError('allow harus boolean.')
                runtime.decide(req.get('id',''), req['allow'])
                self.send_json({'status':'success'})
            elif route == '/api/routines':
                ident = runtime.add_routine(req.get('agent','manager'), req.get('message'), req.get('interval'))
                self.send_json({'id':ident}, 201)
            elif route == '/api/routine/toggle':
                if not isinstance(req.get('enabled'), bool):
                    raise ValueError('enabled harus boolean.')
                runtime.toggle_routine(req.get('id',''),req['enabled'])
                self.send_json({'status':'success'})
            elif route == '/api/task/cancel':
                self.send_json(runtime.cancel(req.get('id', '')))
            else:
                self.send_json({'message': 'Rute tidak ditemukan.'}, 404)
        except KeyError as exc:
            self.send_json({'message': str(exc)}, 404)
        except (ValueError, TypeError) as exc:
            self.send_json({'message': str(exc)}, 400)


def make_server(port=PORT, runtime=None):
    server = ThreadingHTTPServer(('127.0.0.1', port), SecureDashboardHandler)
    server.runtime = runtime or Runtime()
    server.runtime.start()
    return server

if __name__ == '__main__':
    server = make_server()
    print(f'SABILULUNGAN: http://127.0.0.1:{PORT}')
    print(f"Gateway: {CONFIG['PROVIDER']} | Model: {CONFIG['MODEL']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.runtime.stop()
