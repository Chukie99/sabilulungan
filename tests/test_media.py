import json
import importlib.util
import math
import shutil
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
from runtime import Runtime
from media_tools import render, speak, run


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe') and importlib.util.find_spec('PIL'), 'FFmpeg/ffprobe/Pillow required')
class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'agents.json').write_text('{"manager":{"prompt":"manager"}}')
        self.runtime = Runtime(self.root)
        self.audio = self.runtime.workspace / 'fixture.wav'
        # Synthetic tone fixture tests audio muxing, NOT real narration/TTS.
        with wave.open(str(self.audio), 'w') as f:
            f.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            f.writeframes(b''.join(struct.pack('<h',int(1200*math.sin(2*math.pi*220*i/16000))) for i in range(16000*5)))

    def tearDown(self):
        self.runtime.stop()
        self.temp.cleanup()

    def test_real_mp4_render_probe_and_no_overwrite(self):
        scenes=[{'text':'Lampu lorong padam.'},{'text':'Seseorang memanggil namaku.'}]
        result=render(self.runtime.path, scenes,'fixture.wav','Cerita fiksi','result.mp4',5)
        self.assertEqual((result['width'],result['height']),(720,1280))
        self.assertTrue(result['audio_verified'])
        self.assertAlmostEqual(result['duration'],5,delta=.4)
        self.assertGreater(self.runtime.path('result.mp4').stat().st_size,1000)
        with self.assertRaises(ValueError):
            render(self.runtime.path,scenes,'fixture.wav','Title','result.mp4',5)
        with self.assertRaises(ValueError):
            render(self.runtime.path,scenes,'fixture.wav','Title','../escape.mp4',5)

    def test_bad_duration_and_missing_audio_are_not_success(self):
        for duration in (True,float('nan'),120):
            with self.assertRaises(ValueError):
                render(self.runtime.path,[{'text':'Test'}],'fixture.wav','Title','bad.mp4',duration)
        with self.assertRaises(ValueError):
            render(self.runtime.path,[{'text':'Test'}],'fixture.wav','Title','bad.mp4',30)
        self.assertFalse(self.runtime.path('bad.mp4').exists())

    def test_agent_uses_render_and_inspect_tools(self):
        import time
        actions=iter([
            {'action':'render_short','title':'Test','scenes':[{'text':'Cerita fiksi untuk tes render.'}],
             'narration':'fixture.wav','path':'agent.mp4','duration':5},
            {'action':'inspect_media','path':'agent.mp4'},
            {'action':'complete','reply':'MP4 inspected'}])
        self.runtime.model_call=lambda messages:next(actions)
        self.runtime.start()
        task=self.runtime.submit('manager','Render fixture')
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            result=self.runtime.get(task['id'])
            if result['status'] not in ('queued','running'):
                break
            time.sleep(.05)
        self.assertEqual(result['status'],'completed',result['error'])
        tools=[e['content'] for e in result['events'] if e['kind']=='tool']
        self.assertTrue(any(s.startswith('render_short:') and '"audio_verified": true' in s for s in tools))
        self.assertTrue(any(s.startswith('inspect_media:') and '"codec_type": "audio"' in s for s in tools))

    def test_cancelled_process_is_killed(self):
        import sys
        with self.assertRaises(ValueError):
            run([sys.executable,'-c','import time;time.sleep(5)'],cancelled=lambda:True)

    @unittest.skipUnless(importlib.util.find_spec('edge_tts'), 'edge-tts required')
    def test_tts_failure_leaves_no_partial_audio(self):
        output=self.runtime.path('voice.mp3')
        class FailedVoice:
            def __init__(self,*args,**kwargs): pass
            async def save(self,path):
                Path(path).write_bytes(b'partial')
                raise RuntimeError('offline')
        with patch('edge_tts.Communicate',FailedVoice):
            with self.assertRaises(RuntimeError):
                speak('Test narasi',output)
        self.assertFalse(output.exists())
