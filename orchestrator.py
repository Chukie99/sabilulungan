"""CLI using the same durable task engine as the dashboard."""
import time
from runtime import Runtime


def main():
    runtime = Runtime()
    runtime.start()
    print('Sabilulungan — ketik tugas, atau exit untuk keluar.')
    try:
        while True:
            message = input('Lu > ').strip()
            if message.lower() == 'exit':
                break
            if not message:
                continue
            task = runtime.submit('manager', message)
            while task['status'] in ('queued', 'running', 'waiting_approval'):
                time.sleep(.5)
                task = runtime.get(task['id'])
                for approval in runtime.approvals():
                    print('Kode berjalan langsung di PC, bukan sandbox:\n' + approval['code'])
                    runtime.decide(approval['id'], input('Setujui kode ini? ketik ya > ').strip().lower() == 'ya')
            print(task['reply'] or task['error'] or task['status'])
    finally:
        runtime.stop()

if __name__ == '__main__':
    main()
