"""Bounded media tools. No shell commands or arbitrary ffmpeg filters from models."""
import asyncio
import importlib.util
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def status():
    return {
        'ffmpeg_detected': bool(shutil.which('ffmpeg')),
        'ffprobe_detected': bool(shutil.which('ffprobe')),
        'pillow_installed': importlib.util.find_spec('PIL') is not None,
        'edge_tts_installed': importlib.util.find_spec('edge_tts') is not None,
        'render_tool_integrated': True,
        'tts_integrated': True,
        'tts_provider': 'Edge TTS online; needs internet; no successful live connection implied',
        'supertonic_integrated': False,
        'asset_search_download_integrated': False,
        'image_download_integrated': True,
        'asset_search_integrated': False,
        'visuals': 'Original local caption cards or images already in workspace',
        'ready': all([shutil.which('ffmpeg'), shutil.which('ffprobe'), importlib.util.find_spec('PIL'), importlib.util.find_spec('edge_tts')]),
    }


def run(args, cancelled=lambda: False, timeout=180, cwd=None):
    # Temporary file prevents an unbounded captured pipe / pipe deadlock.
    with tempfile.TemporaryFile() as log:
        env = {k: v for k, v in os.environ.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'HOME', 'USERPROFILE', 'SSL_CERT_FILE', 'SSL_CERT_DIR')}
        process = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if cancelled() or time.monotonic() >= deadline:
                process.kill()
                process.wait()
                raise ValueError('Media dihentikan atau timeout.')
            time.sleep(.1)
        log.seek(0)
        output = log.read(40000).decode('utf-8', errors='replace')
        if process.returncode:
            raise ValueError('Proses media gagal: ' + output[-2000:])
        return output


def probe(path, cancelled=lambda: False):
    exe = shutil.which('ffprobe')
    if not exe:
        raise ValueError('ffprobe belum tersedia. Jalankan SETUP_MEDIA.bat.')
    return json.loads(run([exe, '-v', 'error', '-protocol_whitelist', 'file', '-format_whitelist', 'mov,mp3,wav', '-show_entries', 'format=duration:stream=codec_type,width,height,codec_name', '-of', 'json', str(path)], cancelled, 20))


def _output(path, suffix):
    if path.suffix.lower() != suffix:
        raise ValueError('Output harus berakhiran ' + suffix)
    if path.exists():
        raise ValueError('Output sudah ada. Pilih nama versi baru.')
    path.parent.mkdir(parents=True, exist_ok=True)


def speak(text, output, cancelled=lambda: False):
    if not isinstance(text, str) or not text.strip() or len(text) > 2500:
        raise ValueError('Narasi harus teks 1–2500 karakter.')
    if not importlib.util.find_spec('edge_tts'):
        raise ValueError('edge-tts belum terpasang. Jalankan SETUP_MEDIA.bat.')
    _output(output, '.mp3')
    # Network coroutine runs in this worker, polled for cancellation and timeout.
    async def synth():
        import edge_tts
        async def write():
            await edge_tts.Communicate(text, voice='id-ID-ArdiNeural', rate='+5%').save(str(output))
        task = asyncio.create_task(write())
        deadline = time.monotonic() + 90
        try:
            while not task.done():
                if cancelled() or time.monotonic() >= deadline:
                    task.cancel()
                    raise ValueError('TTS dihentikan atau timeout 90 detik.')
                await asyncio.sleep(.1)
            await task
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    try:
        asyncio.run(synth())
        data = probe(output, cancelled)
        if not any(s.get('codec_type') == 'audio' for s in data.get('streams', [])):
            raise ValueError('TTS tidak menghasilkan audio valid.')
        return data
    except Exception:
        output.unlink(missing_ok=True)
        raise


def _font(size):
    from PIL import ImageFont
    for name in ('C:/Windows/Fonts/arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def card(text, title, image, number, total, target):
    from PIL import Image, ImageDraw, ImageOps
    if image:
        with Image.open(image) as source:
            if source.width * source.height > 20000000:
                raise ValueError('Resolusi gambar terlalu besar (maksimal 20 MP).')
            source.load()
            bg = ImageOps.fit(source.convert('RGB'), (720, 1280))
        shade = Image.new('RGBA', bg.size, (5, 8, 16, 160))
        bg = Image.alpha_composite(bg.convert('RGBA'), shade).convert('RGB')
    else:
        bg = Image.new('RGB', (720, 1280), '#0c1320')
    draw = ImageDraw.Draw(bg)
    if not image:
        # Original shapes: a dark doorway, dim light and corridor, not stock footage.
        draw.polygon([(0, 1250), (260, 270), (460, 270), (720, 1250)], fill='#152735')
        draw.rectangle((240, 210, 480, 850), fill='#28343d')
        draw.rectangle((266, 235, 455, 850), fill='#080d15')
        draw.rectangle((302, 192, 420, 201), fill='#bf9b62')
        draw.ellipse((435, 537, 443, 546), fill='#d8bd78')
    draw.rectangle((44, 48, 50, 96), fill='#e8c284')
    draw.text((66, 58), f'CERITA FIKSI  /  {number:02d}', font=_font(20), fill='#e8c284')
    font = _font(43)
    lines = []
    current = ''
    for word in text.split():
        trial = (current + ' ' + word).strip()
        if draw.textlength(trial, font=font) > 602 and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    if len(lines) > 9 or any(draw.textlength(line, font=font) > 620 for line in lines):
        raise ValueError('Caption adegan terlalu panjang. Maksimal sekitar 160 karakter, hindari kata sangat panjang.')
    y = 860 - len(lines) * 29
    for line in lines:
        draw.text((56, y), line, font=font, fill='#f4efe2', stroke_width=2, stroke_fill='#0a111a')
        y += 59
    title_font = _font(19)
    short_title = title[:55]
    while draw.textlength(short_title, font=title_font) > 608:
        short_title = short_title[:-1]
    draw.text((56, 1146), short_title, font=title_font, fill='#c2c7c9')
    draw.rectangle((56, 1197, 664, 1202), fill='#39444d')
    draw.rectangle((56, 1197, 56 + int(608 * number / total), 1202), fill='#e8c284')
    bg.save(target, 'PNG')


def render(path_resolver, scenes, narration, title, output, duration=30, cancelled=lambda: False):
    exe = shutil.which('ffmpeg')
    if not exe or not importlib.util.find_spec('PIL'):
        raise ValueError('FFmpeg/Pillow belum tersedia. Jalankan SETUP_MEDIA.bat.')
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(duration) or not 5 <= duration <= 60:
        raise ValueError('Durasi wajib 5–60 detik.')
    if not isinstance(title, str) or not title.strip() or len(title) > 150:
        raise ValueError('Judul wajib 1–150 karakter.')
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 10:
        raise ValueError('Gunakan 1–10 adegan.')
    validated = []
    for scene in scenes:
        if not isinstance(scene, dict) or not isinstance(scene.get('text'), str) or not scene['text'].strip() or len(scene['text']) > 240:
            raise ValueError('Setiap adegan wajib text 1–240 karakter.')
        image = path_resolver(scene['image']) if scene.get('image') else None
        if image and (image.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp') or image.stat().st_size > 15000000):
            raise ValueError('Aset wajib gambar PNG/JPG/WebP maksimal 15 MB.')
        validated.append((scene['text'], image))
    audio = path_resolver(narration)
    if audio.suffix.lower() not in ('.mp3', '.wav', '.m4a') or audio.stat().st_size > 30000000:
        raise ValueError('Narasi wajib audio lokal maksimal 30 MB.')
    audio_info = probe(audio, cancelled)
    if not any(s.get('codec_type') == 'audio' for s in audio_info.get('streams', [])):
        raise ValueError('File narasi tidak memiliki audio.')
    audio_duration = float(audio_info['format']['duration'])
    tempo = audio_duration / duration
    if not .75 <= tempo <= 1.33:
        raise ValueError(f'Narasi {audio_duration:.1f} detik terlalu jauh dari target {duration}. Sesuaikan panjang naskah; jangan isi video dengan hening.')
    target = path_resolver(output)
    _output(target, '.mp4')
    total_weight = sum(len(text.split()) for text, _ in validated)
    # Temp outputs reside in workspace but have random names; publish only after QA.
    with tempfile.TemporaryDirectory(prefix='media-', dir=target.parent) as tmp:
        work = Path(tmp)
        entries = ['ffconcat version 1.0']
        for index, (text, image) in enumerate(validated):
            if cancelled():
                raise ValueError('Tugas dihentikan saat menyiapkan adegan.')
            filename = f'scene{index:02d}.png'
            card(text, title, image, index + 1, len(validated), work / filename)
            entries += [f"file '{filename}'", f'duration {duration * len(text.split()) / total_weight:.6f}']
        entries += [f"file 'scene{len(validated)-1:02d}.png'"]
        (work / 'scenes.ffconcat').write_text('\n'.join(entries) + '\n', encoding='utf-8')
        pending = work / 'render.mp4'
        run([exe, '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-protocol_whitelist', 'file', '-f', 'concat', '-safe', '1', '-i', 'scenes.ffconcat', '-protocol_whitelist', 'file', '-i', str(audio), '-vf', 'fps=24,format=yuv420p', '-af', f'atempo={tempo:.6f},apad', '-t', str(duration), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-threads', '2', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(pending)], cancelled, 240, work)
        result = probe(pending, cancelled)
        streams = result['streams']
        if not any(s.get('codec_type') == 'video' and s.get('width') == 720 and s.get('height') == 1280 for s in streams) or not any(s.get('codec_type') == 'audio' for s in streams) or abs(float(result['format']['duration']) - duration) > .4:
            raise ValueError('QA gagal: rasio, audio atau durasi tidak sesuai.')
        if cancelled():
            raise ValueError('Tugas dihentikan sebelum publikasi MP4.')
        # Hard link prevents overwriting a file created concurrently; same volume.
        os.link(pending, target)
    return {'path': output, 'width': 720, 'height': 1280, 'duration': float(result['format']['duration']), 'audio_verified': True, 'caption_timing': 'Estimated per scene by word count, not word-aligned', 'visuals': 'Local images/original graphic cards; no stock-video editing'}
