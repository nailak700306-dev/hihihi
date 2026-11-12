"""Builds the voice track, an original synthesized score, and the timeline JSON."""
import json, os, subprocess, numpy as np, wave
TTS_DIR = os.environ.get('TTS_DIR', 'tts'); OUT_MIX = os.environ.get('OUT_MIX', 'mix.wav'); OUT_TL = os.environ.get('OUT_TL', 'timeline.json')

SR = 44100
rng = np.random.default_rng(7)


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af',
                          'highpass=f=70,equalizer=f=3500:t=q:w=1:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=80',
                          '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    env = np.abs(x) > 0.01
    idx = np.nonzero(env)[0]
    return x[max(idx[0] - 400, 0): idx[-1] + 2000]


GAPS = [0.10, 0.16, 0.14, 0.14, 0.14, 0.18, 0.22, 0.30, 0.22]  # silence before each line
lines, t = [], 0.0
voice_parts = []
for i in range(9):
    x = load(f'{TTS_DIR}/{i+1}.wav')
    t += GAPS[i]
    lines.append({'start': round(t, 3), 'dur': round(len(x) / SR, 3)})
    voice_parts.append((t, x))
    t += len(x) / SR
TOTAL = t + 0.6
N = int(TOTAL * SR)
voice = np.zeros(N)
for st, x in voice_parts:
    s = int(st * SR)
    voice[s:s + len(x)] += x
voice *= 0.92 / np.max(np.abs(voice))

# ---------------- music ----------------
tt = np.arange(N) / SR


def note(f):  # midi -> hz
    return 440 * 2 ** ((f - 69) / 12)


def adsr(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


music = np.zeros(N)
L = [l['start'] for l in lines]
sec_story = L[1]; sec_study = L[5]; sec_close = L[6]; sec_end = L[7]; sec_cta = L[8]

# chords (A minor: Am F C G / Am F Dm E)
prog = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62], [57, 60, 64], [53, 57, 60], [50, 57, 62], [52, 56, 59]]
BAR = 60 / 72 * 4  # 3.33 s


def pad_layer(start, end, gain, bright=1.0):
    t0 = start
    k = 0
    while t0 < end:
        ch = prog[k % len(prog)]
        n = int(min(BAR, end - t0) * SR)
        s = int(t0 * SR)
        seg = np.zeros(n)
        ts = np.arange(n) / SR
        for m in ch + [ch[0] - 12]:
            for det in (-0.12, 0.12):
                f = note(m + det)
                for h, a in ((1, 1), (2, 0.35 * bright), (3, 0.12 * bright)):
                    seg += a * np.sin(2 * np.pi * f * h * ts + rng.uniform(0, 6))
        seg *= adsr(n, 0.6, 0.6) * (1 + 0.08 * np.sin(2 * np.pi * 0.25 * ts))
        music[s:s + n] += gain * seg / 10
        t0 += BAR
        k += 1


def piano(start, end, gain, step=60 / 72 / 2):
    t0 = start; k = 0
    while t0 < end - 0.05:
        bar = int((t0 - start) // BAR)
        ch = prog[bar % len(prog)]
        pat = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12, ch[1] + 12, ch[2] + 12]
        f = note(pat[k % 8])
        n = int(1.6 * SR); s = int(t0 * SR)
        ts = np.arange(n) / SR
        tone = (np.sin(2 * np.pi * f * ts) + 0.3 * np.sin(4 * np.pi * f * ts) * np.exp(-ts * 6)
                + 0.1 * np.sin(6 * np.pi * f * ts) * np.exp(-ts * 9))
        tone *= np.exp(-ts * 2.8) * adsr(n, 0.004, 0.05)
        e = min(s + n, N)
        music[s:e] += gain * tone[:e - s] * (0.8 + 0.2 * rng.random())
        t0 += step; k += 1


def thump(at, gain):
    n = int(0.45 * SR); s = int(at * SR)
    ts = np.arange(n) / SR
    f = 55 * np.exp(-ts * 6) + 38
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-ts * 9)
    e = min(s + n, N)
    music[s:e] += gain * x[:e - s]


def heartbeat(start, end, gain, period=0.92):
    t0 = start
    while t0 < end:
        thump(t0, gain); thump(t0 + 0.22, gain * 0.6)
        t0 += period


def riser(start, end, gain):
    s, e = int(start * SR), int(end * SR)
    n = e - s
    noise = rng.standard_normal(n)
    # crude band sweep: one-pole lowpass with rising cutoff
    out = np.zeros(n); y = 0.0
    cut = np.linspace(0.01, 0.35, n)
    for i in range(0, n):
        y += cut[i] * (noise[i] - y); out[i] = y
    out *= np.linspace(0, 1, n) ** 2
    music[s:e] += gain * out


def hit(at, gain):
    n = int(2.5 * SR); s = int(at * SR)
    ts = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 45 * ts) * np.exp(-ts * 2.2) + 0.25 * rng.standard_normal(n) * np.exp(-ts * 12))
    for m in (45, 52, 57):
        x += 0.25 * np.sin(2 * np.pi * note(m + 12) * ts) * np.exp(-ts * 1.5)
    e = min(s + n, N)
    music[s:e] += gain * x[:e - s]


def drone(start, end, gain):
    s, e = int(start * SR), int(end * SR)
    ts = tt[s:e]
    x = np.sin(2 * np.pi * note(33) * ts) + 0.5 * np.sin(2 * np.pi * note(45) * ts) + 0.15 * np.sin(2 * np.pi * note(76) * ts) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * ts))
    x *= adsr(e - s, 0.3, 0.8)
    music[s:e] += gain * x


hit(0.0, 0.55)
drone(0.0, sec_story + 0.6, 0.18)
heartbeat(0.35, sec_story, 0.55)
pad_layer(sec_story - 0.3, sec_close, 0.55, 0.7)
piano(sec_story, sec_study, 0.11)
heartbeat(L[3], sec_study, 0.30, 0.83)
piano(sec_study, sec_close, 0.13, step=60 / 72 / 4)
riser(sec_close - 2.2, sec_close, 0.10)
hit(sec_close, 0.45)
pad_layer(sec_close, sec_end - 0.2, 0.75, 1.0)
piano(sec_close, sec_end - 0.3, 0.14)
# conclusion: intimate piano + soft pad
pad_layer(sec_end, TOTAL, 0.45, 0.5)
piano(sec_end, TOTAL - 0.4, 0.12, step=60 / 72)
hit(sec_cta, 0.35)

# whoosh on each line start
for st in L[1:]:
    s = int((st - 0.25) * SR); n = int(0.35 * SR)
    w = rng.standard_normal(n) * np.hanning(n)
    w = np.convolve(w, np.ones(20) / 20, 'same')
    music[s:s + n] += 0.35 * w

# simple reverb (FFT convolution with decaying noise IR)
ir_n = int(2.2 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 3.0)
ir[0] = 0
F = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.fft.irfft(np.fft.rfft(music, F) * np.fft.rfft(ir, F), F)[:N]
music = music + 0.012 * wet
music /= np.max(np.abs(music))

# sidechain ducking under the voice
venv = np.convolve(np.abs(voice), np.ones(2205) / 2205, 'same')
venv = np.clip(venv / 0.05, 0, 1)
venv = np.convolve(venv, np.ones(6615) / 6615, 'same')
duck = 1 - 0.55 * venv
fade = np.ones(N); fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
mix = voice * 1.0 + music * 0.33 * duck * fade
mix /= np.max(np.abs(mix)) / 0.95
st = np.stack([mix, mix], 1)
with wave.open(OUT_MIX, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
json.dump({'total': TOTAL, 'lines': lines}, open(OUT_TL, 'w'), indent=1)
print(TOTAL, lines)
