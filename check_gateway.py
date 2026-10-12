"""Live gateway acceptance test; isolated from the user's tasks and files."""
import shutil
import tempfile
import time
from pathlib import Path
from config import BASE_DIR, CONFIG
from runtime import Runtime, gateway


def check(model_call=gateway, timeout=600):
    with tempfile.TemporaryDirectory(prefix='sabilulungan-check-') as folder:
        root = Path(folder)
        shutil.copyfile(Path(BASE_DIR) / 'agents.json', root / 'agents.json')
        runtime = Runtime(root, model_call)
        task = None
        runtime.start()
        try:
            task = runtime.submit('manager',
                'Tes integrasi. Delegasikan ke coder: buat file acceptance.txt dengan isi '
                'SABILULUNGAN_OK, baca ulang file tersebut, lalu simpan memori '
                'SABILULUNGAN_ACCEPTANCE. Setelah coder selesai, Manager wajib membaca '
                'acceptance.txt dan melaporkan hasil. Jangan gunakan run_python atau read_url.')
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                task = runtime.get(task['id'])
                if task['status'] not in ('queued', 'running', 'waiting_approval'):
                    break
                if task['status'] == 'waiting_approval':
                    raise ValueError('Model meminta eksekusi kode yang tidak diperlukan.')
                time.sleep(.2)
            else:
                raise ValueError('Tes melebihi batas waktu.')
            if task['status'] != 'completed':
                raise ValueError(task['error'] or task['status'])
            events = task['events']
            path = runtime.workspace / 'acceptance.txt'
            checks = {
                'task_completed': True,
                'delegation': any(e['kind'] == 'delegate' and e['content'].startswith('coder:') for e in events),
                'file_content': path.exists() and path.read_text(encoding='utf-8').strip() == 'SABILULUNGAN_OK',
                'coder_read': any(e['agent'] == 'coder' and e['kind'] == 'tool' and e['content'].startswith('read_file:') and 'SABILULUNGAN_OK' in e['content'] for e in events),
                'manager_read': any(e['agent'] == 'manager' and e['kind'] == 'tool' and e['content'].startswith('read_file:') and 'SABILULUNGAN_OK' in e['content'] for e in events),
                'memory': any('SABILULUNGAN_ACCEPTANCE' in m for m in runtime.memories('coder')),
            }
            runtime.stop()
            restored = Runtime(root, model_call)
            checks['persistence'] = restored.get(task['id'])['status'] == 'completed' and any('SABILULUNGAN_ACCEPTANCE' in m for m in restored.memories('coder'))
            return checks
        finally:
            if task:
                runtime.cancel(task['id'])
            runtime.stop()


def main():
    print('Tes LIVE:', CONFIG['PROVIDER'], '| model:', CONFIG['MODEL'])
    print('Database dan file tes terpisah; API key tidak ditampilkan.')
    try:
        checks = check()
        for name, passed in checks.items():
            print(('PASS' if passed else 'FAIL') + ' ' + name)
        return 0 if all(checks.values()) else 1
    except Exception as exc:
        # Do not print raw gateway errors, URLs, headers, or credentials.
        print('FAIL:', type(exc).__name__)
        print('Periksa apakah 9Router hidup, API_URL benar, API_KEY valid, dan MODEL tersedia.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
