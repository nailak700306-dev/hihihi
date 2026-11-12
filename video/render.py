"""Renders the 9:16 TikTok video frames and pipes them into ffmpeg."""
import json, sys, subprocess, re, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
PREVIEW = len(sys.argv) > 1 and sys.argv[1] == 'preview'
tl = json.load(open('timeline.json'))
TOTAL = tl['total']; LINES = tl['lines']
big = open('big.txt').read().split('\n')
FONT = 'fonts/Montserrat-Black.ttf'
FONT2 = 'fonts/Montserrat-ExtraBold.ttf'

# ---- shots per voice line: (image index, focus x, focus y, zoom-in?) ----
SHOTS = [
    [(109, .45, .45, 1), (32, .45, .45, 0)],
    [(18, .55, .45, 1), (235, .5, .4, 0)],
    [(48, .62, .45, 1)],
    [(236, .35, .5, 0), (196, .5, .35, 1)],
    [(115, .55, .45, 1), (174, .55, .5, 0)],
    [(250, .45, .45, 1), (98, .5, .45, 0), (221, .55, .45, 1)],
    [(111, .55, .5, 1), (230, .55, .45, 0)],
    [(2, .5, .45, 1), (192, .45, .55, 0), (245, .5, .5, 1)],
    [(99, .5, .45, 1)],
]

# ---- subtitle chunks per line (UPPERCASE words get highlighted) ----
CHUNKS = [
    ["Ton chien SAIT", "peut-être que tu vas MAL…", "avant même que", "tu t'en RENDES COMPTE."],
    ["Regarde-le bien.", "Il t'OBSERVE.", "Tout le temps.", "Et surtout…", "il te SENT."],
    ["Parce que ton ODEUR", "CHANGE,", "selon ce que tu RESSENS."],
    ["Quand tu es STRESSÉ,", "ton corps modifie", "les COMPOSÉS CHIMIQUES", "de ta TRANSPIRATION…", "et de ton SOUFFLE."],
    ["Pour toi,", "c'est INVISIBLE.", "Mais son ODORAT", "est des MILLIERS de fois", "plus puissant", "que le tien."],
    ["En 2022,", "des chercheurs ont montré", "que des chiens", "reconnaissaient", "l'odeur du STRESS…", ("avec près de 94 %", "avec près de quatre-vingt-quatorze pour cent"), "de RÉUSSITE."],
    ["Alors il s'APPROCHE.", "Doucement.", "Il lit ton ODEUR,", "ta POSTURE,", "ton REGARD."],
    ["Alors la prochaine fois", "que ton chien", "vient se POSER contre toi", "sans raison apparente…", "il a peut-être REMARQUÉ", "quelque chose", "que tu n'avais", "même pas EXPRIMÉ."],
    ["Et toi, ton chien", "l'a déjà fait ?", "Dis-le en COMMENTAIRE."],
]


def weight(s):
    w = len(s.replace(' ', '')) + 1.5 * s.count(' ')
    w += 7 * s.count('…') + 4 * len(re.findall(r'[.?]$', s)) + 2.5 * s.count(',')
    return w


subs = []  # (start, end, text)
for li, (line, chunks) in enumerate(zip(LINES, CHUNKS)):
    ws = [weight(c[1] if isinstance(c, tuple) else c) for c in chunks]
    tot = sum(ws); t = line['start']
    for c, w in zip(chunks, ws):
        d = line['dur'] * w / tot
        subs.append([t, t + d, c[0] if isinstance(c, tuple) else c])
        t += d
# hold each subtitle until the next one starts (no flicker during short gaps)
for a, b in zip(subs, subs[1:]):
    a[1] = b[0]
subs[-1][1] = TOTAL

# ---- shot timeline ----
shots = []  # (start, end, spec, section_start)
for li, line in enumerate(LINES):
    s0 = 0 if li == 0 else line['start'] - 0.12
    s1 = LINES[li + 1]['start'] - 0.12 if li + 1 < len(LINES) else TOTAL
    n = len(SHOTS[li])
    for k, spec in enumerate(SHOTS[li]):
        shots.append((s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n, spec, k == 0))


def grade(im):
    im = ImageEnhance.Color(im).enhance(0.82)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    a = np.asarray(im).astype(np.float32) / 255
    lum = a.mean(2, keepdims=True)
    shadow = np.clip(1 - lum * 2, 0, 1); high = np.clip(lum * 2 - 1, 0, 1)
    a = a + shadow * np.array([-0.03, 0.01, 0.04]) + high * np.array([0.04, 0.015, -0.03])
    a = np.clip(a * 0.95 + 0.01, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


cache = {}


def source(idx):
    if idx not in cache:
        im = Image.open(big[idx]).convert('RGB')
        # upscale so the 9:16 crop is >= output size, then sharpen
        w, h = im.size
        cw = min(w, h * 9 / 16)
        sc = max(1.0, W * 1.2 / cw)
        im = im.resize((int(w * sc), int(h * sc)), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
        cache[idx] = grade(im)
    return cache[idx]


def ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0), 1))


def shot_frame(spec, u, punch):
    idx, fx, fy, zin = spec
    im = source(idx)
    w, h = im.size
    ch = min(h, w * 16 / 9); cw = ch * 9 / 16
    z = 1.0 + 0.13 * (ease(u) if zin else 1 - ease(u))
    z *= 1 + 0.07 * punch
    cw2, ch2 = cw / z, ch / z
    # gentle drift
    dx = (u - 0.5) * 0.06 * cw * (1 if idx % 2 else -1)
    cx = min(max(fx * w + dx, cw2 / 2), w - cw2 / 2)
    cy = min(max(fy * h, ch2 / 2), h - ch2 / 2)
    box = (cx - cw2 / 2, cy - ch2 / 2, cx + cw2 / 2, cy + ch2 / 2)
    return im.transform((W, H), Image.EXTENT, box, Image.BICUBIC)


# vignette + grain
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)
VIG = np.clip(1 - 0.55 * np.clip(r - 0.55, 0, 1) ** 1.4, 0, 1)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GRAIN = [np.asarray(Image.fromarray(((rng.standard_normal((H // 2, W // 2)) * 9) + 128).clip(0, 255).astype(np.uint8)).resize((W, H)), np.float32)[..., None] - 128 for _ in range(6)]
# bottom gradient for subtitle legibility
grad = np.ones((H, 1, 1), np.float32)
g0, g1 = int(H * 0.5), int(H * 0.85)
grad[g0:g1, 0, 0] = np.linspace(1, 0.62, g1 - g0); grad[g1:, 0, 0] = 0.62

YEL = (255, 214, 10, 255); WHITE = (255, 255, 255, 255)
font_main = ImageFont.truetype(FONT, 86)
font_small = ImageFont.truetype(FONT2, 40)
txt_cache = {}


def text_layer(text):
    if text in txt_cache:
        return txt_cache[text]
    words = text.split(' ')
    # wrap
    lines, cur = [], []
    for wd in words:
        trial = ' '.join(cur + [wd])
        if cur and font_main.getlength(trial) > W * 0.84:
            lines.append(cur); cur = [wd]
        else:
            cur.append(wd)
    lines.append(cur)
    lh = 104
    img = Image.new('RGBA', (W, lh * len(lines) + 60), (0, 0, 0, 0))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img); ds = ImageDraw.Draw(sh)
    sp = font_main.getlength(' ')
    for i, ln in enumerate(lines):
        tw = sum(font_main.getlength(w) for w in ln) + sp * (len(ln) - 1)
        x = (W - tw) / 2; y = 30 + i * lh
        for wd in ln:
            core = re.sub(r'[^\wÀ-ÿ%]', '', wd)
            hl = len(core) > 1 and core.upper() == core and not core.isdigit()
            if core == '94': hl = True
            col = YEL if hl else WHITE
            ds.text((x + 4, y + 7), wd, font=font_main, fill=(0, 0, 0, 170), stroke_width=9, stroke_fill=(0, 0, 0, 170))
            d.text((x, y), wd, font=font_main, fill=col, stroke_width=9, stroke_fill=(0, 0, 0, 255))
            x += font_main.getlength(wd) + sp
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    out = Image.alpha_composite(sh, img)
    txt_cache[text] = out
    return out


def badge_layer():
    s = 'LE SAVAIS-TU ?'
    tw = font_small.getlength(s)
    img = Image.new('RGBA', (int(tw) + 70, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), 42, fill=(255, 214, 10, 240))
    d.text((35, 18), s, font=font_small, fill=(15, 15, 15, 255))
    return img


BADGE = badge_layer()


def cta_layer():
    img = Image.new('RGBA', (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FONT, 58); f2 = ImageFont.truetype(FONT2, 42)
    d.rounded_rectangle((90, 20, W - 90, 250), 46, fill=(255, 255, 255, 245))
    d.polygon([(W / 2 - 34, 248), (W / 2 + 34, 248), (W / 2, 300)], fill=(255, 255, 255, 245))
    for s, f, y, c in (("TON CHIEN L'A DÉJÀ FAIT ?", f1, 62, (20, 20, 20, 255)),
                       ("Raconte-le en commentaire", f2, 150, (90, 90, 90, 255))):
        d.text(((W - f.getlength(s)) / 2, y), s, font=f, fill=c)
    return img


CTA = cta_layer()


def paste(base, layer, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        a = np.asarray(layer).copy(); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); layer = Image.fromarray(a)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def frame(t, fi):
    sh = next(s for s in shots if s[0] <= t < s[1] or s is shots[-1])
    s0, s1, spec, sec = sh
    u = (t - s0) / (s1 - s0)
    since = t - s0
    punch = max(0, 1 - since / 0.25) if since < 0.25 else 0
    im = shot_frame(spec, u, punch)
    a = np.asarray(im, np.float32)
    a = a * VIG * grad + GRAIN[fi % 6]
    # flash at section starts (except very first)
    if sec and s0 > 0 and since < 0.12:
        a = a + (1 - since / 0.12) * 120
    if t < 0.25:  # open from black
        a *= t / 0.25
    if t > TOTAL - 0.5:
        a *= max(0, (TOTAL - t) / 0.5)
    base = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGBA')
    # subtitle
    for st, en, txt in subs:
        if st <= t < en:
            k = (t - st) / 0.16
            sc = 1.0 if k >= 1 else (0.78 + 0.34 * k if k < 0.7 else 1.018 - (k - 0.7) * 0.06)
            ty = 1240 if t < LINES[8]['start'] else 1450
            paste(base, text_layer(txt), W / 2, ty, sc)
            break
    # badge during the first section
    if 0.3 < t < LINES[1]['start']:
        al = min(1, (t - 0.3) / 0.2)
        paste(base, BADGE, W / 2, 330, 1.0, al)
    # CTA bubble at the end
    ct = LINES[8]['start']
    if t >= ct:
        k = min(1, (t - ct) / 0.25)
        sc = 0.6 + 0.4 * (1 - (1 - k) ** 3) + 0.02 * math.sin((t - ct) * 6)
        paste(base, CTA, W / 2, 560, sc, k)
    return base.convert('RGB')


if PREVIEW:
    thumbs = []
    for s0, s1, spec, _ in shots:
        tm = (s0 + s1) / 2
        thumbs.append(frame(tm, 0).resize((270, 480)))
    thumbs.append(frame(LINES[8]['start'] + 1, 0).resize((270, 480)))
    cols = 8
    sheet = Image.new('RGB', (270 * cols, 480 * math.ceil(len(thumbs) / cols)))
    for i, th in enumerate(thumbs):
        sheet.paste(th, ((i % cols) * 270, (i // cols) * 480))
    sheet.save('preview.jpg', quality=85)
    sys.exit()

nf = int(TOTAL * FPS)
p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', 'mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                      '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'chiens_stress_tiktok.mp4'], stdin=subprocess.PIPE)
for fi in range(nf):
    p.stdin.write(frame(fi / FPS, fi).tobytes())
    if fi % 150 == 0:
        print(fi, '/', nf, flush=True)
p.stdin.close(); p.wait()
print('done')
