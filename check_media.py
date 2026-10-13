"""Real TTS -> cards -> MP4 -> ffprobe smoke check; isolated temporary workspace."""
import json
import tempfile
from pathlib import Path
from media_tools import status, speak, render


def main():
    info=status()
    print(json.dumps(info,ensure_ascii=False,indent=2),flush=True)
    if not info['ready']:
        print('FAIL: jalankan SETUP_MEDIA.bat; buka ulang CMD setelah instalasi FFmpeg.')
        return 1
    with tempfile.TemporaryDirectory(prefix='sabilulungan-media-check-') as folder:
        root=Path(folder).resolve()
        def resolve(name):
            path=(root/name).resolve()
            if not path.is_relative_to(root) or path==root:
                raise ValueError('Invalid test path')
            return path
        try:
            text='Malam itu, aku mendengar ketukan dari kamar kosong. Saat pintunya kubuka, suara di belakangku berbisik, jangan menoleh.'
            print('[PROGRES] Meminta narasi Edge TTS…',flush=True)
            voice=speak(text,resolve('voice.mp3'))
            duration=float(voice['format']['duration'])
            if not 5<=duration<=60:
                raise ValueError('Durasi audio tes di luar rentang.')
            print('[PROGRES] Render video 9:16 + QA…',flush=True)
            result=render(resolve,[{'text':text}], 'voice.mp3','Tes Short — cerita fiksi','check.mp4',duration)
            print('PASS TTS asli, MP4 720x1280, audio dan durasi terverifikasi.',flush=True)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0
        except Exception as exc:
            print('FAIL:',type(exc).__name__)
            print('TTS membutuhkan internet. Periksa FFmpeg, ffprobe dan dependensi; jangan kirim API key.')
            return 1


if __name__=='__main__':
    raise SystemExit(main())
