"""Live gateway acceptance test; isolated from the user's tasks and files."""
import shutil
import tempfile
import time
from pathlib import Path
from config import BASE_DIR, CONFIG
from runtime import Runtime, gateway


def check(model_call=gateway, timeout=600, progress=lambda message: None):
    with tempfile.TemporaryDirectory(prefix='sabilulungan-check-') as folder:
        root = Path(folder)
        shutil.copyfile(Path(BASE_DIR) / 'agents.json', root / 'agents.json')
        runtime = Runtime(root, model_call)
        task = None
        runtime.start()
        deadline = time.monotonic() + timeout
        def wait(current):
            seen = 0
            while time.monotonic() < deadline:
                current = runtime.get(current['id'])
                for event in current['events'][seen:]:
                    label = event['kind']
                    if label == 'tool':
                        label = event['content'].split(':', 1)[0]
                    progress(event['agent'] + ': ' + label)
                seen = len(current['events'])
                if current['status'] not in ('queued', 'running', 'waiting_approval'):
                    if current['status'] != 'completed':
                        raise ValueError('Tugas tes gagal; jenis error: ' + current['status'])
                    return current
                if current['status'] == 'waiting_approval':
                    raise ValueError('Model meminta eksekusi kode yang tidak diperlukan.')
                time.sleep(.2)
            raise ValueError('Tes melebihi batas waktu.')
        try:
            task = runtime.submit('manager',
                'Tes integrasi. Delegasikan ke coder: buat file acceptance.txt dengan isi '
                'SABILULUNGAN_OK dan baca ulang file tersebut. Setelah coder selesai, Manager wajib membaca '
                'acceptance.txt dan melaporkan hasil. Jangan gunakan run_python atau read_url.')
            task = wait(task)
            events = task['events']
            path = runtime.workspace / 'acceptance.txt'
            checks = {
                'task_completed': True,
                'delegation': any(e['kind'] == 'delegate' and e['content'].startswith('coder:') for e in events),
                'file_content': path.exists() and path.read_text(encoding='utf-8').strip() == 'SABILULUNGAN_OK',
                'coder_read': any(e['agent'] == 'coder' and e['kind'] == 'tool' and e['content'].startswith('read_file:') and 'SABILULUNGAN_OK' in e['content'] for e in events),
                'manager_read': any(e['agent'] == 'manager' and e['kind'] == 'tool' and e['content'].startswith('read_file:') and 'SABILULUNGAN_OK' in e['content'] for e in events),
            }
            file_task = task
            progress('Tes memori langsung ke coder (terpisah dari delegasi).')
            task = runtime.submit('coder',
                'Simpan memori persis SABILULUNGAN_ACCEPTANCE memakai action remember '
                'dengan content SABILULUNGAN_ACCEPTANCE. Setelah tool berhasil baru complete. '
                'Jangan buat file atau delegasikan. Menulis teks jawaban saja tidak menyimpan memori.')
            task = wait(task)
            checks['memory'] = any(m == 'SABILULUNGAN_ACCEPTANCE' for m in runtime.memories('coder')) and any(
                e['kind'] == 'tool' and e['content'] == 'remember: Memori agen tersimpan.' for e in task['events'])
            if not checks['memory']:
                progress('Memori gagal: tidak ada bukti tool remember sukses dengan isi persis yang diminta.')
            runtime.stop()
            restored = Runtime(root, model_call)
            checks['persistence'] = restored.get(file_task['id'])['reply'] == file_task['reply'] and restored.get(task['id'])['events'] == task['events']
            checks['memory_persistence'] = checks['memory'] and 'SABILULUNGAN_ACCEPTANCE' in restored.memories('coder')
            return checks
        finally:
            if task:
                runtime.cancel(task['id'])
            runtime.stop()


def main():
    print('Tes LIVE:', CONFIG['PROVIDER'], '| model:', CONFIG['MODEL'])
    print('Database dan file tes terpisah; API key tidak ditampilkan.')
    try:
        checks = check(progress=lambda message: print('[PROGRES]', message, flush=True))
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
