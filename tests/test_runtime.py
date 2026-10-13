import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from runtime import Runtime
from dashboard import make_server

class StaffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'agents.json').write_text(json.dumps({
            'manager': {'prompt': 'manager'}, 'coder': {'prompt': 'coder'}}))
        self.runtime = None

    def tearDown(self):
        if self.runtime:
            self.runtime.stop()
        self.temp.cleanup()

    def wait(self, task):
        end = time.monotonic() + 3
        while time.monotonic() < end:
            result = self.runtime.get(task['id'])
            if result['status'] not in ('queued', 'running', 'waiting_approval'):
                return result
            time.sleep(.01)
        self.fail('Task did not finish')

    def runtime_with(self, actions):
        iterator = iter(actions)
        self.runtime = Runtime(self.root, lambda messages: next(iterator))
        self.runtime.start()
        return self.runtime

    def test_delegation_file_memory_and_restart(self):
        runtime = self.runtime_with([
            {'action':'delegate','agent':'coder','instructions':'Bikin file'},
            {'action':'write_file','path':'demo/result.txt','content':'hasil nyata'},
            {'action':'read_file','path':'demo/result.txt'},
            {'action':'remember','content':'Gunakan Bahasa Indonesia'},
            {'action':'complete','reply':'Spesialis selesai'},
            {'action':'complete','reply':'Manager memeriksa hasil'}])
        task = self.wait(runtime.submit('manager', 'Buat hasil'))
        self.assertEqual(task['status'], 'completed')
        self.assertEqual((runtime.workspace/'demo/result.txt').read_text(), 'hasil nyata')
        self.assertIn('coder', [e['agent'] for e in task['events']])
        runtime.stop()
        restored = Runtime(self.root)
        self.assertEqual(restored.get(task['id'])['reply'], 'Manager memeriksa hasil')
        self.assertEqual(restored.memories('coder'), ['Gunakan Bahasa Indonesia'])
        self.assertEqual(restored.memories('manager'), [])
        restored.forget('coder')
        self.assertEqual(restored.memories('coder'), [])

    def test_escape_symlink_and_overwrite_are_blocked(self):
        self.runtime = Runtime(self.root)
        for name in ('../secret', '/etc/passwd', 'C:\\Windows\\secret'):
            with self.assertRaises(ValueError):
                self.runtime.path(name)
        outside = self.root/'outside'
        outside.mkdir()
        (self.runtime.workspace/'link').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.runtime.path('link/a.txt')
        (self.runtime.workspace/'old.txt').write_text('old')
        actions = iter([{'action':'write_file','path':'old.txt','content':'new'},
                        {'action':'complete','reply':'Existing file retained'}])
        self.runtime.model_call = lambda m: next(actions)
        self.runtime.start()
        task = self.wait(self.runtime.submit('coder','Write'))
        self.assertEqual((self.runtime.workspace/'old.txt').read_text(),'old')
        self.assertIn('Tool gagal', task['events'][1]['content'])

    def test_cancel_prevents_tools_after_model_returns(self):
        entered, release = threading.Event(), threading.Event()
        def model(messages):
            entered.set()
            release.wait(2)
            return {'action':'write_file','path':'cancelled.txt','content':'bad'}
        self.runtime = Runtime(self.root, model)
        self.runtime.start()
        task = self.runtime.submit('manager','Test cancellation')
        self.assertTrue(entered.wait(1))
        self.runtime.cancel(task['id'])
        release.set()
        self.runtime.stop()
        self.assertEqual(self.runtime.get(task['id'])['status'],'cancelled')
        self.assertFalse((self.runtime.workspace/'cancelled.txt').exists())

    def test_invalid_model_output_and_budget_fail_honestly(self):
        runtime = self.runtime_with([{'action':'complete','reply':''}])
        task = self.wait(runtime.submit('manager','Empty'))
        self.assertEqual(task['status'],'failed')
        runtime.model_call = lambda m: {'action':'list_files'}
        task = self.wait(runtime.submit('manager','Infinite loop'))
        self.assertEqual(task['status'],'failed')
        self.assertIn('24 langkah',task['error'])

    def test_restart_marks_inflight_interrupted(self):
        self.runtime = Runtime(self.root)
        task = self.runtime.submit('manager','Restart')
        with self.runtime.connect() as db:
            db.execute("UPDATE tasks SET status='running' WHERE id=?", (task['id'],))
        restored = Runtime(self.root)
        self.assertEqual(restored.get(task['id'])['status'],'interrupted')

    def test_office_tracks_delegated_agent_and_terminal_state(self):
        self.runtime = Runtime(self.root)
        task = self.runtime.submit('manager', 'Office test')
        self.assertEqual(self.runtime.office()['manager']['status'], 'queued')
        with self.runtime.connect() as db:
            db.execute("UPDATE tasks SET status='running' WHERE id=?", (task['id'],))
        self.runtime.event(task['id'], 'coder', 'thinking', 'Working')
        state = self.runtime.office()
        self.assertEqual(state['coder']['status'], 'running')
        self.assertEqual(state['manager']['status'], 'delegated')
        self.runtime.event(task['id'], 'manager', 'thinking', 'Review')
        self.assertEqual(self.runtime.office()['manager']['status'], 'running')
        self.assertNotEqual(self.runtime.office()['coder']['status'], 'running')
        self.runtime.cancel(task['id'])
        self.assertEqual(self.runtime.office()['coder']['status'], 'cancelled')

    def test_media_status_distinguishes_integrated_tools_and_readiness(self):
        runtime = self.runtime_with([
            {'action': 'media_status'},
            {'action': 'complete', 'reply': 'Capability checked'}])
        task = self.wait(runtime.submit('manager', 'Check tools'))
        event = next(e for e in task['events'] if e['kind'] == 'tool')
        status = json.loads(event['content'].split(': ', 1)[1])
        self.assertTrue(status['render_tool_integrated'])
        self.assertTrue(status['tts_integrated'])
        self.assertFalse(status['asset_search_download_integrated'])

    def test_python_requires_approval_and_returns_output(self):
        runtime = self.runtime_with([
            {'action':'run_python','code':'print(6 * 7)'},
            {'action':'complete','reply':'42'}])
        task = runtime.submit('manager','Hitung')
        end=time.monotonic()+2
        while not runtime.approvals() and time.monotonic()<end:
            time.sleep(.01)
        approvals=runtime.approvals()
        self.assertEqual(len(approvals),1)
        self.assertEqual(runtime.get(task['id'])['status'],'waiting_approval')
        runtime.decide(approvals[0]['id'],True)
        result=self.wait(task)
        self.assertEqual(result['status'],'completed')
        self.assertTrue(any('Exit code: 0\n42' in e['content'] for e in result['events']))
        with self.assertRaises(ValueError):
            runtime.decide(approvals[0]['id'],True)

    def test_rejected_python_never_runs(self):
        runtime = self.runtime_with([
            {'action':'run_python','code':"open('bad.txt','w').write('bad')"},
            {'action':'complete','reply':'Tidak dijalankan'}])
        task=runtime.submit('manager','Reject')
        end=time.monotonic()+2
        while not runtime.approvals() and time.monotonic()<end:
            time.sleep(.01)
        runtime.decide(runtime.approvals()[0]['id'],False)
        self.assertEqual(self.wait(task)['status'],'completed')
        self.assertFalse((runtime.workspace/'bad.txt').exists())

    def test_routine_persistence_no_backlog_and_pause(self):
        self.runtime=Runtime(self.root)
        ident=self.runtime.add_routine('coder','Laporan',60)
        with self.runtime.connect() as db:
            db.execute('UPDATE routines SET next_run=0 WHERE id=?',(ident,))
        self.runtime.schedule()
        self.runtime.schedule()
        self.assertEqual(len(self.runtime.tasks()),1)
        restored=Runtime(self.root)
        self.assertEqual(restored.routines()[0]['id'],ident)
        restored.toggle_routine(ident,False)
        with restored.connect() as db:
            db.execute('UPDATE routines SET next_run=0')
        restored.schedule()
        self.assertEqual(len(restored.tasks()),1)
        with self.assertRaises(ValueError):
            restored.add_routine('coder','Invalid',0)

    def test_web_tools_reject_private_targets(self):
        from web_tools import read_url, TextParser, download_image_bytes
        for url in ('http://example.com','https://127.0.0.1','https://localhost','https://example.com:8080','https://user:pass@example.com'):
            with self.assertRaises(ValueError):
                read_url(url)
            with self.assertRaises(ValueError):
                download_image_bytes(url)
        parser=TextParser()
        parser.feed('<h1>Useful</h1><script>bad()</script><style>hidden</style><p>Text</p>')
        self.assertEqual(parser.parts,['Useful','Text'])

    def test_http_real_routes_and_origin(self):
        runtime = self.runtime_with([{'action':'complete','reply':'OK'}])
        server = make_server(0, runtime)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        def request(path, body=None, origin=None, host=None):
            headers = {'Content-Type':'application/json'}
            if origin: headers['Origin']=origin
            if host: headers['Host']=host
            req = Request(base+path, data=None if body is None else json.dumps(body).encode(),headers=headers)
            with urlopen(req,timeout=2) as res:
                return res.status,json.load(res)
        try:
            status,task = request('/api/tasks',{'agent':'manager','message':'Test'},base)
            self.assertEqual(status,202)
            self.wait(task)
            self.assertEqual(request('/api/task?id='+task['id'])[1]['reply'],'OK')
            self.assertEqual(request('/api/office')[1]['manager']['status'], 'completed')
            data = b'\x00\x01\xff\xfe'
            (runtime.workspace / 'binary.mp4').write_bytes(data)
            with urlopen(base + '/api/download?path=binary.mp4', timeout=2) as response:
                self.assertEqual(response.read(), data)
                self.assertEqual(response.headers['Content-Disposition'], 'attachment')
            for path, kind in [('/office.js', 'text/javascript'), ('/office.css', 'text/css')]:
                with urlopen(base + path, timeout=2) as response:
                    self.assertEqual(response.status, 200)
                    self.assertTrue(response.headers['Content-Type'].startswith(kind))
                    self.assertGreater(len(response.read()), 100)
            for origin,host in [('http://evil.test',None),(None,'evil.test')]:
                with self.assertRaises(HTTPError) as exc:
                    request('/api/tasks',{'message':'bad'},origin,host)
                self.assertEqual(exc.exception.code,403)
            with self.assertRaises(HTTPError) as exc:
                request('/api/file?path=../agents.json')
            self.assertEqual(exc.exception.code,400)
            with self.assertRaises(HTTPError) as exc:
                request('/api/tasks',{'agent':'missing','message':'bad'},base)
            self.assertEqual(exc.exception.code,400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

if __name__ == '__main__':
    unittest.main()
