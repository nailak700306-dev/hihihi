"""Generate several directed voice-over variants (per-line pacing) for comparison."""
import os, sys, wave, subprocess, warnings, numpy as np
warnings.filterwarnings('ignore')
LINES = open('lines_k.txt').read().strip().split('\n')
# per-line pacing (relative speed): hook mysterious, facts lively, ending tender
DIR = [0.94, 1.0, 1.0, 1.08, 1.06, 1.1, 0.93, 0.9, 1.04]

def write(path, s, sr):
    s = np.asarray(s, np.float32)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(s, -1, 1) * 32767).astype(np.int16).tobytes())

def kokoro(outdir, voice, base, pitch=0.0):
    sys.path.insert(0, 'kokoro'); cwd = os.getcwd(); os.chdir('kokoro')
    from kokoro_onnx import Kokoro
    k = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin'); os.chdir(cwd)
    if isinstance(voice, dict):
        v = sum(k.get_voice_style(n) * w for n, w in voice.items())
    else:
        v = voice
    for i, (l, d) in enumerate(zip(LINES, DIR), 1):
        s, sr = k.create(l, voice=v, speed=base * d, lang='fr-fr')
        write(f'{outdir}/{i}.wav', s, sr)

def css(outdir, base):
    from TTS.utils.synthesizer import Synthesizer
    d = 'coqui/tts_models--fr--css10--vits'
    syn = Synthesizer(tts_checkpoint=f'{d}/model_file.pth.tar', tts_config_path=f'{d}/config.json')
    for i, (l, dd) in enumerate(zip(LINES, DIR), 1):
        syn.tts_model.length_scale = 1.0 / (base * dd)
        w = syn.tts(l.replace('…', '...'))
        write(f'{outdir}/{i}.wav', w, syn.output_sample_rate)

name = sys.argv[1]
out = f'variants/{name}'; os.makedirs(out, exist_ok=True)
if name == 'A_narratrice':
    kokoro(out, 'ff_siwis', 1.10)
elif name == 'B_confidence':
    kokoro(out, 'ff_siwis', 1.02)
elif name == 'C_narrateur':
    css(out, 1.18)
elif name == 'D_chaleureuse':
    kokoro(out, {'ff_siwis': 0.8, 'af_heart': 0.2}, 1.10)
print('ok', name)
