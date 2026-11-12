import sys, wave, numpy as np
from kokoro_onnx import Kokoro
k = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin')
def say(text, out, voice='ff_siwis', speed=1.0):
    s, sr = k.create(text, voice=voice, speed=speed, lang='fr-fr')
    s = np.asarray(s, np.float32)
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(s, -1, 1) * 32767).astype(np.int16).tobytes())
    return len(s) / sr
if __name__ == '__main__':
    print([v for v in k.get_voices() if v[0] in 'f'])
    print(say("Ton chien sait peut-être que tu vas mal… avant même que tu t'en rendes compte.", 't.wav'))
    k2 = None
