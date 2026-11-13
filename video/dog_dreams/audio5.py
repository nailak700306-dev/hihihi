"""Overthinking video: voice track + soft emotional night score + timeline."""
import json, os, subprocess, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(21)
TTS_DIR = os.environ.get('TTS_DIR', 'dre/el')
OUT_MIX = os.environ.get('OUT_MIX', 'dre/mix.wav')
OUT_TL = os.environ.get('OUT_TL', 'dre/timeline.json')
NL = 10
GAPS = [0.15, 0.45, 0.15, 0.50, 0.15, 0.50, 0.15, 0.60, 0.20, 0.50]


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af',
                          'highpass=f=60,acompressor=threshold=-22dB:ratio=2:attack=15:release=200,equalizer=f=2800:t=q:w=1.5:g=1.5',
                          '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    idx = np.nonzero(np.abs(x) > 0.01)[0]
    s0 = max(idx[0] - 400, 0)
    return x[s0: idx[-1] + 2000], s0 / SR


lines, parts, t = [], [], 0.0
for i in range(NL):
    x, trim = load(f'{TTS_DIR}/{i + 1}.mp3')
    t += GAPS[i]
    lines.append({'start': round(t, 4), 'dur': round(len(x) / SR, 4), 'trim': round(trim, 4)})
    parts.append((t, x))
    t += len(x) / SR
TOTAL = t + 2.0
N = int(TOTAL * SR)
voice = np.zeros(N)
for st, x in parts:
    s = int(st * SR); voice[s:s + len(x)] += x
voice *= 0.92 / np.max(np.abs(voice))
L = [l['start'] for l in lines]

music = np.zeros(N)


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def env(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


BPM = 68
BEAT = 60 / BPM
BAR = BEAT * 4
# Am  F  C  G  /  Am  F  C  E(sus)
PROG = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62], [57, 60, 64], [53, 57, 60], [48, 55, 64], [52, 56, 59]]


def chord_at(tm):
    return PROG[int(tm // BAR) % len(PROG)]


def pad(start, end, gain, bright=0.6):
    t0 = (start // BAR) * BAR
    while t0 < end:
        a, b = max(t0, start), min(t0 + BAR, end)
        n = int((b - a) * SR)
        if n > 100:
            ts = np.arange(n) / SR
            seg = np.zeros(n)
            for m in chord_at(t0 + 0.01) + [chord_at(t0 + 0.01)[0] - 12]:
                for det in (-0.08, 0.08):
                    f = note(m + det)
                    seg += np.sin(2 * np.pi * f * ts + rng.uniform(0, 6)) + bright * 0.3 * np.sin(4 * np.pi * f * ts)
            seg *= env(n, 0.8, 0.8) * (1 + 0.1 * np.sin(2 * np.pi * 0.2 * ts))
            s = int(a * SR); music[s:s + n] += gain * seg / 10
        t0 += BAR


def pluck(at, m, gain, decay=2.4):
    n = int(2.2 * SR); s = int(at * SR)
    if s >= N: return
    ts = np.arange(n) / SR
    f = note(m)
    x = (np.sin(2 * np.pi * f * ts) + 0.35 * np.sin(4 * np.pi * f * ts) * np.exp(-ts * 5)
         + 0.12 * np.sin(6 * np.pi * f * ts) * np.exp(-ts * 8)) * np.exp(-ts * decay) * env(n, 0.003, 0.05)
    e = min(s + n, N); music[s:e] += gain * x[:e - s]


def piano(start, end, gain, sub=2, pattern=(0, 1, 2, 1, 12, 2, 1, 2)):
    step = BEAT / sub
    t0 = np.ceil(start / step) * step; k = 0
    while t0 < end - 0.05:
        ch = chord_at(t0)
        tones = [ch[0] + 12, ch[1] + 12, ch[2] + 12]
        p = pattern[k % len(pattern)]
        m = tones[0] + 12 if p == 12 else tones[p]
        pluck(t0, m, gain * (0.85 + 0.15 * rng.random()))
        t0 += step; k += 1


def melody(start, end, gain):
    # slow, sparse top line
    seq = [76, 74, 72, 71, 72, 69, 67, 69]
    t0 = np.ceil(start / (BEAT * 2)) * BEAT * 2; k = 0
    while t0 < end - 0.3:
        pluck(t0, seq[k % len(seq)], gain, decay=1.4); t0 += BEAT * 2; k += 1


def tick(start, end, gain):
    t0 = start
    while t0 < end:
        n = int(0.02 * SR); s = int(t0 * SR)
        x = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 400)
        x = np.diff(np.concatenate([[0], x]))
        music[s:s + n] += gain * x; t0 += BEAT


def thump(at, gain):
    n = int(0.45 * SR); s = int(at * SR)
    ts = np.arange(n) / SR
    f = 52 * np.exp(-ts * 6) + 38
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-ts * 9)
    e = min(s + n, N); music[s:e] += gain * x[:e - s]


def heartbeat(start, end, gain):
    t0 = start
    while t0 < end:
        thump(t0, gain); thump(t0 + 0.22, gain * 0.6); t0 += BEAT


def riser(start, end, gain):
    s, e = int(start * SR), int(end * SR); n = e - s
    noise = rng.standard_normal(n); out = np.zeros(n); y = 0.0
    cut = np.linspace(0.01, 0.3, n)
    for i in range(n):
        y += cut[i] * (noise[i] - y); out[i] = y
    music[s:e] += gain * out * np.linspace(0, 1, n) ** 2


def swell(at, gain):
    n = int(3.0 * SR); s = int(at * SR)
    ts = np.arange(n) / SR
    x = np.zeros(n)
    for m in (45, 57, 64, 69):
        x += np.sin(2 * np.pi * note(m) * ts)
    x *= np.exp(-ts * 1.2) * env(n, 0.02, 0.3)
    e = min(s + n, N); music[s:e] += gain * x[:e - s]


def rain(gain):
    # soft rain: low-passed noise bed + sparse droplets
    noise = rng.standard_normal(N)
    k = np.ones(40) / 40
    bed = np.convolve(noise, k, 'same') - np.convolve(noise, np.ones(400) / 400, 'same')
    music[:] += gain * bed
    for _ in range(int(TOTAL * 6)):
        at = rng.uniform(0, TOTAL - 0.1); n = int(0.03 * SR); s = int(at * SR)
        x = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 200)
        music[s:s + n] += gain * 0.8 * np.diff(np.concatenate([[0], x]))


def musicbox(start, end, gain, density=2.0):
    scale = [69, 72, 74, 76, 79, 81, 84, 86]
    t0 = start
    while t0 < end:
        pluck(t0, scale[int(rng.integers(0, len(scale)))] + 12, gain * (0.6 + 0.4 * rng.random()), decay=3.5)
        t0 += BEAT / density * (1 if rng.random() > 0.3 else 2)


def drone(start, end, gain):
    s0, e0 = int(start * SR), int(end * SR)
    ts = np.arange(e0 - s0) / SR
    x = np.sin(2 * np.pi * note(45) * ts) + 0.5 * np.sin(2 * np.pi * note(52) * ts) + 0.2 * np.sin(2 * np.pi * note(64) * ts) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * ts))
    music[s0:e0] += gain * x * env(e0 - s0, 0.5, 1.0)


# intrigue: drone + music box
drone(0, L[3], 0.16)
musicbox(0.2, L[3], 0.07)
pad(L[1] - 0.2, L[3], 0.3, 0.3)
# science / wonder: shimmering arpeggio
swell(L[3], 0.1)
pad(L[3] - 0.2, L[5], 0.45, 0.6)
piano(L[3], L[5], 0.08, sub=4)
riser(L[5] - 1.6, L[5] - 0.05, 0.06)
# dreams: bright and tender
pad(L[5] - 0.2, L[7], 0.5, 0.7)
piano(L[5], L[7], 0.10)
melody(L[5] + 0.2, L[7], 0.09)
musicbox(L[5], L[7], 0.04, 1.0)
# emotional ending
swell(L[7], 0.1)
pad(L[7] - 0.2, TOTAL, 0.6, 0.5)
piano(L[7] + 0.2, TOTAL - 1.0, 0.10)
melody(L[8], TOTAL - 1.0, 0.09)

# reverb
ir_n = int(2.4 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 2.6); ir[0] = 0
F = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.fft.irfft(np.fft.rfft(music, F) * np.fft.rfft(ir, F), F)[:N]
music = music + 0.015 * wet
music /= np.max(np.abs(music))

venv = np.convolve(np.abs(voice), np.ones(2205) / 2205, 'same')
venv = np.clip(venv / 0.05, 0, 1)
venv = np.convolve(venv, np.ones(6615) / 6615, 'same')
fade = np.ones(N); fn = int(1.2 * SR); fade[-fn:] = np.linspace(1, 0, fn)
fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
mix = voice + music * 0.24 * (1 - 0.6 * venv) * fade
mix /= np.max(np.abs(mix)) / 0.95
st = np.stack([mix, mix], 1)
with wave.open(OUT_MIX, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
json.dump({'total': TOTAL, 'lines': lines}, open(OUT_TL, 'w'), indent=1)
print(round(TOTAL, 2), [l['start'] for l in lines])
