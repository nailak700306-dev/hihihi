"""Do dogs dream of their owners? - animated 9:16 TikTok reusing the dog/owner character kit from anim.py."""
import json, sys, math, re, subprocess
import numpy as np
import skia
import anim as A
from anim import hexc, lerpc, P, oval, rrect, glow, ease, lerp, text_center, TF_BLACK, TF_XB, W, H, FPS

tl = json.load(open('dr/timeline.json'))
TOTAL = tl['total']; LINES = tl['lines']
rng = np.random.default_rng(13)
BIG = skia.Rect.MakeLTRB(-2000, -2000, W + 2000, H + 2000)


def heart_path(cx, cy, s):
    p = skia.Path()
    p.moveTo(cx, cy + 0.9 * s)
    p.cubicTo(cx - 1.3 * s, cy - 0.1 * s, cx - 0.75 * s, cy - 1.15 * s, cx, cy - 0.45 * s)
    p.cubicTo(cx + 0.75 * s, cy - 1.15 * s, cx + 1.3 * s, cy - 0.1 * s, cx, cy + 0.9 * s)
    p.close()
    return p


# ------------------------------------------------------------------ sleeping dog
DOG_X, DOG_Y = 560, 1730


def dog_sleep(c, x, y, s, t, kick=0.0, ear=0.0, smile=0.0):
    # bed
    oval(c, x + 10 * s, y - 5 * s, 360 * s, 85 * s, P(hexc('#5A3A4E')))
    oval(c, x + 10 * s, y - 25 * s, 320 * s, 60 * s, P(hexc('#7A5068')))
    c.save(); c.translate(x, y); c.scale(s, s)
    br = 1 + 0.025 * math.sin(t * 2.2)
    burst = 0.5 + 0.5 * math.sin(t * 1.7)  # dreams come in bursts
    kk = kick * (0.4 + 0.6 * burst)
    # tail
    w = 6 * math.sin(t * 4) * smile
    tp = skia.Path(); tp.moveTo(200, -70); tp.cubicTo(280, -60, 300 + w, -10, 250 + w, 20)
    c.drawPath(tp, P(hexc(A.FUR_D), 30))
    # back legs
    for px, off in ((130, 0.0), (175, 1.6)):
        c.save(); c.translate(px, -40); c.rotate(-55 + kk * 24 * math.sin(t * 13 + off))
        rrect(c, -20, 0, 20, 125, 20, P(hexc(A.FUR_D)))
        oval(c, 0, 124, 26, 15, P(hexc(A.CREAM)))
        c.restore()
    # body
    c.save(); c.scale(1, br)
    oval(c, 40, -95, 215, 98, P(hexc(A.FUR)))
    oval(c, 50, -52, 150, 38, P(hexc(A.CREAM)))
    c.restore()
    # front legs reaching forward (left)
    for px, off in ((-110, 2.4), (-70, 3.9)):
        c.save(); c.translate(px, -40); c.rotate(68 + kk * 20 * math.sin(t * 13 + off))
        rrect(c, -19, 0, 19, 135, 19, P(hexc(A.FUR)))
        oval(c, 0, 134, 25, 15, P(hexc(A.CREAM)))
        c.restore()
    c.restore()
    # head resting, eyes closed (rapid eye movement flutter)
    et = 0.5 + 0.5 * math.sin(t * 9)
    A.dog_head(c, x - 220 * s, y - 120 * s, 0.82 * s, t, look=(0, 0), tilt=-14,
               ears=-0.25 + 0.5 * ear * max(0, math.sin(t * 7)), blink=0.06 + 0.04 * ear * et, mouth=0.25 * smile)


def zzz(c, x, y, t, a=1.0):
    for i in range(3):
        k = (t * 0.45 + i / 3) % 1
        c.drawString('z', x + i * 26 + k * 50, y - k * 180, skia.Font(TF_BLACK, 40 + i * 12),
                     P(hexc('#E6ECFF', 220 * a * math.sin(math.pi * k))))


def night(c, t, warm=0.0, beam=1.0):
    A.room(c, t, warm)
    c.drawRect(BIG, P(hexc('#070A18', 110 * (1 - warm))))
    # moonbeam from the window onto the dog bed
    bp = skia.Path(); bp.moveTo(705, 345); bp.lineTo(985, 345); bp.lineTo(900, 1800); bp.lineTo(220, 1800); bp.close()
    pt = skia.Paint(AntiAlias=True)
    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 345), skia.Point(0, 1800)], [hexc('#CFE0FF', 0), hexc('#CFE0FF', 60 * beam)]))
    c.drawPath(bp, pt)
    glow(c, DOG_X, DOG_Y - 80, 420, '#AFC6FF', 50 * beam)


def sc_wide_sleep(c, t, u):
    night(c, t)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=ease((u - 0.55) * 4) * 0.6)
    zzz(c, DOG_X - 260, DOG_Y - 260, t)
    A.motes(c, t, '#BFD3FF', 50)


def sc_face(c, t, u, smile=0.0, ear=1.0):
    night(c, t, 0.2 * smile)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=0.8, ear=ear, smile=smile)
    zzz(c, DOG_X - 230, DOG_Y - 230, t)


def sc_paws(c, t, u):
    night(c, t)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=1.0, ear=0.5)
    # motion arcs near paws
    for px in (DOG_X + 150, DOG_X - 120):
        k = 0.5 + 0.5 * math.sin(t * 13)
        c.drawArc(skia.Rect.MakeLTRB(px - 90, DOG_Y - 60, px + 90, DOG_Y + 120), 20, 60, False, P(hexc('#FFFFFF', 120 * k), 5))


def sc_sounds(c, t, u):
    night(c, t)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=0.5, ear=0.8)
    for i, s in enumerate(['wouf…', 'mmh…']):
        k = ease((u * 1.6 - i * 0.45) * 3)
        if k > 0:
            text_center(c, s, DOG_X - 330 + i * 60, DOG_Y - 250 - i * 70 - k * 30, 44, hexc('#FFFFFF', 220 * k), TF_XB)


NODES = rng.random((60, 2))


def sc_brain(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 900), 1300, [hexc('#2A1A4A'), hexc('#07061A')]))
    c.drawPaint(bg)
    # brain-shaped cloud of neurons
    pts = []
    for nx, ny in NODES:
        a = nx * 2 * math.pi; r = math.sqrt(ny)
        pts.append((540 + 330 * r * math.cos(a), 880 + 240 * r * math.sin(a)))
    act = ease(u * 1.5)
    for i, (x1, y1) in enumerate(pts):
        for j in range(i + 1, min(i + 4, len(pts))):
            x2, y2 = pts[j]
            if (x1 - x2) ** 2 + (y1 - y2) ** 2 < 200 ** 2:
                c.drawLine(x1, y1, x2, y2, P(hexc('#8E7CFF', 70 + 80 * act), 2))
    for i, (x, y) in enumerate(pts):
        fl = 0.5 + 0.5 * math.sin(t * 6 + i * 1.7)
        glow(c, x, y, 26 + 20 * fl * act, '#FF9DE2', 120 * act * fl)
        c.drawCircle(x, y, 6, P(hexc('#E9E4FF')))
    # travelling sparks
    for k in range(12):
        i = (k * 7 + int(t * 4)) % (len(pts) - 1)
        f = (t * 4) % 1
        x = lerp(pts[i][0], pts[i + 1][0], f); y = lerp(pts[i][1], pts[i + 1][1], f)
        glow(c, x, y, 30, '#FFE27A', 200 * act)
    text_center(c, 'CERVEAU EN ACTIVITÉ', 540, 520, 52, hexc('#FFFFFF', 220 * act), TF_XB)


def sc_graph(c, t, u):
    c.drawPaint(P(hexc('#0C0F24')))
    f = skia.Font(TF_XB, 34)
    labels = ['Éveil', 'Sommeil léger', 'Sommeil profond']
    ys = [560, 760, 960]
    for s, y in zip(labels, ys):
        c.drawString(s, 70, y + 12, f, P(hexc('#9AA3C8')))
        c.drawLine(360, y, 1020, y, P(hexc('#2E3460'), 2))
    c.drawString('Paradoxal', 70, 412, f, P(hexc('#FF9DE2')))
    c.drawLine(360, 400, 1020, 400, P(hexc('#FF9DE2', 90), 2))
    seq = [0, 1, 2, 2, 1, 3, 3, 1, 2, 1, 3, 3, 3, 1]
    yv = {0: 560, 1: 760, 2: 960, 3: 400}
    prog = ease(u * 1.3)
    nseg = len(seq) - 1
    pth = skia.Path(); pth.moveTo(360, yv[seq[0]])
    for i in range(nseg):
        x0 = 360 + 660 * i / nseg; x1 = 360 + 660 * (i + 1) / nseg
        if (i + 1) / nseg > prog:
            break
        pth.lineTo(x1, yv[seq[i]]); pth.lineTo(x1, yv[seq[i + 1]])
        if seq[i] == 3:
            rrect(c, x0, 380, x1, 420, 8, P(hexc('#FF7ACB', 200)))
            glow(c, (x0 + x1) / 2, 400, 90, '#FF7ACB', 120)
    c.drawPath(pth, P(hexc('#BFD3FF'), 6))
    text_center(c, 'SOMMEIL PARADOXAL', 540, 280, 60, hexc('#FF9DE2', 255 * ease(u * 3)), TF_BLACK, 8)
    text_center(c, '= les rêves', 540, 1090, 54, hexc('#FFFFFF', 220 * ease(u * 2.5 - 0.6)), TF_XB)


def sc_bubble(c, t, u):
    night(c, t, 0.1)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=0.7, ear=0.6, smile=0.5)
    hx, hy = DOG_X - 220, DOG_Y - 200
    k = ease(u * 2.2)
    for i, (dx, dy, r) in enumerate(((40, -90, 18), (90, -170, 30))):
        c.drawCircle(hx + dx, hy + dy, r * k, P(hexc('#FFFFFF', 200)))
    bx, by, br = hx + 230, hy - 470, 260 * k
    if br > 5:
        glow(c, bx, by, br * 1.4, '#FFE6F2', 120)
        c.drawCircle(bx, by, br, P(hexc('#FFF4F8', 230)))
        c.save(); c.clipPath(skia.Path.Circle(bx, by, br - 8), skia.ClipOp.kIntersect, True)
        meadow(c, t, bx - 300, by - 300, 600)
        A.dog_walk(c, bx + 40 + 30 * math.sin(t * 2), by + 170, 0.45, t, phase_speed=14, facing=1, look=(1, 0), mouth=0.6, ears=0.6)
        c.restore()


def meadow(c, t, x0, y0, size):
    sky = skia.Paint(); sky.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y0 + size * 0.7)], [hexc('#FFC8B8'), hexc('#BFD8FF')]))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + size, y0 + size), sky)
    glow(c, x0 + size * 0.7, y0 + size * 0.3, size * 0.4, '#FFF1C9', 200)
    c.drawCircle(x0 + size * 0.7, y0 + size * 0.3, size * 0.08, P(hexc('#FFF6DD')))
    for i, (col, h) in enumerate((('#9BD08A', 0.55), ('#7DBE6E', 0.65), ('#68A85C', 0.78))):
        hp = skia.Path(); hp.moveTo(x0 - 50, y0 + size * h)
        hp.cubicTo(x0 + size * 0.3, y0 + size * (h - 0.08), x0 + size * 0.6, y0 + size * (h + 0.06), x0 + size + 50, y0 + size * (h - 0.04))
        hp.lineTo(x0 + size + 50, y0 + size + 50); hp.lineTo(x0 - 50, y0 + size + 50); hp.close()
        c.drawPath(hp, P(hexc(col)))


FLOWERS = rng.random((50, 3))


def dream_world(c, t):
    meadow(c, t, -700, -300, 2500)
    for fx, fy, fc in FLOWERS:
        x = -100 + fx * 1300; y = 1250 + fy * 700
        c.drawCircle(x, y, 8 + 6 * fc, P(hexc(['#FFFFFF', '#FFD6E8', '#FFE27A'][int(fc * 3)])))
    for i in range(30):
        gx = (i * 41) % 1100
        sway = 10 * math.sin(t * 2 + i)
        c.drawLine(gx, 1900, gx + sway, 1780, P(hexc('#5E9A52'), 6))


def dream_overlay(c, t):
    pt = skia.Paint()
    pt.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 960), 1150, [hexc('#FFE6F2', 0), hexc('#FFE6F2', 0), hexc('#FFE6F2', 150)], [0, 0.6, 1]))
    c.drawRect(BIG, pt)
    for i in range(18):
        k = (t * 0.25 + i / 18) % 1
        x = (i * 157) % W; y = H - k * H
        c.drawCircle(x, y, 4 + (i % 3) * 2, P(hexc('#FFFFFF', 200 * math.sin(math.pi * k)), blur=2))


def sc_dream_run(c, t, u):
    dream_world(c, t)
    A.dog_walk(c, lerp(-150, 1000, u), 1640, 1.0, t, phase_speed=15, facing=1, look=(1, 0), mouth=0.7, ears=0.7)
    dream_overlay(c, t)


def sc_dream_ball(c, t, u):
    dream_world(c, t)
    bx = lerp(200, 880, u); by = 1500 - 700 * math.sin(math.pi * min(1, u * 1.1))
    c.drawCircle(bx, by, 36, P(hexc('#E8423F')))
    c.drawArc(skia.Rect.MakeLTRB(bx - 36, by - 36, bx + 36, by + 36), 200, 140, False, P(hexc('#FFFFFF', 200), 6))
    A.dog_walk(c, lerp(120, 760, u), 1700, 0.95, t, phase_speed=15, facing=1, look=(1, -1), mouth=0.6, ears=0.8)
    dream_overlay(c, t)


def sc_dream_friends(c, t, u):
    dream_world(c, t)
    old = (A.FUR, A.FUR_D, A.CREAM)
    A.FUR, A.FUR_D, A.CREAM = '#5B4636', '#3E2F25', '#E8D8C4'
    A.dog_walk(c, lerp(-50, 820, u), 1600, 0.85, t + 0.3, phase_speed=14, facing=1, look=(1, 0), mouth=0.5)
    A.FUR, A.FUR_D, A.CREAM = old
    A.dog_walk(c, lerp(-250, 650, u), 1720, 1.0, t, phase_speed=15, facing=1, look=(1, 0), mouth=0.7, ears=0.7)
    dream_overlay(c, t)


def sc_dream_pet(c, t, u):
    dream_world(c, t)
    rrect(c, 280, 1240, 680, 1290, 16, P(hexc('#8A5A3C')))
    for lx in (310, 650):
        c.drawRect(skia.Rect.MakeLTRB(lx - 10, 1290, lx + 10, 1520), P(hexc('#6A4430')))
    px = 600 + 22 * math.sin(t * 3.2)
    A.owner(c, 470, 1245, t, 0.0, 'pet', pet=(px, 1190 + 8 * math.cos(t * 3.2)), mood=1.0)
    A.dog_sit(c, 610, 1610, 1.0, t, wag=1.3, look=(-0.4, -1), tilt=8, ears=-0.2, blink=0.55, mouth=0.4)
    c.drawCircle(px, 1190 + 8 * math.cos(t * 3.2), 25, P(hexc(A.SKIN)))
    A.hearts(c, t, 560, 900)
    dream_overlay(c, t)


def sc_warm_sleep(c, t, u):
    night(c, t, 0.7, 0.6)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=1.0, ear=0.4, smile=1.0)
    zzz(c, DOG_X - 260, DOG_Y - 260, t, 0.8)


def human_hand(c, hx, hy, t):
    ap = skia.Path(); ap.moveTo(1250, -200); ap.cubicTo(1100, hy - 600, hx + 250, hy - 250, hx + 60, hy - 20)
    c.drawPath(ap, P(hexc(A.SHIRT), 90))
    c.save(); c.translate(hx, hy); c.rotate(-20)
    oval(c, 0, 0, 80, 62, P(hexc(A.SKIN)))
    for i, fx in enumerate((-60, -25, 12, 48)):
        rrect(c, fx - 17, 20, fx + 17, 105 - abs(i - 1.5) * 10, 17, P(hexc(A.SKIN)))
    c.restore()


def sc_hand(c, t, u, close=False):
    night(c, t, 0.85, 0.4)
    dog_sleep(c, DOG_X, DOG_Y, 1.0, t, kick=0.2 * (1 - u), ear=0.2, smile=1.0)
    k = ease(u * 1.6)
    hx = DOG_X + 40 + 12 * math.sin(t * 2.4) * k
    hy = lerp(900, DOG_Y - 175, k)
    human_hand(c, hx, hy, t)
    if k > 0.9:
        glow(c, hx, hy, 260, '#FFB46B', 120)
        A.hearts(c, t, DOG_X - 100, DOG_Y - 330, 0.9)


def sc_final(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [hexc('#2A1A34'), hexc('#5A3448')]))
    c.drawPaint(bg)
    glow(c, 540, 860, 700, '#FF9DB5', 90)
    s = 1 + 0.06 * math.sin(t * 3)
    c.drawPath(heart_path(540, 1180, 110 * s), P(hexc('#FF5A7A')))
    glow(c, 540, 1180, 260, '#FF5A7A', 120)
    k1, k2 = ease(u * 3), ease(u * 3 - 0.4)
    text_center(c, "Tu crois qu'il", 540, 820, 96, hexc('#FFFFFF', 255 * k1))
    f = skia.Font(TF_BLACK, 96)
    w1 = f.measureText('rêve de '); w2 = f.measureText('TOI ?')
    x = 540 - (w1 + w2) / 2
    c.drawString('rêve de ', x, 940, f, P(hexc('#FFFFFF', 255 * k2)))
    c.drawString('TOI ?', x + w1, 940, f, P(hexc('#FFD60A', 255 * k2)))
    k3 = ease((u - 0.45) * 4)
    text_center(c, 'Dis-le en commentaire', 540, 1440, 48, hexc('#FFFFFF', 220 * k3), TF_XB)
    text_center(c, "et partage à quelqu'un qui aime son chien", 540, 1505, 36, hexc('#FFFFFF', 190 * k3), TF_XB)


FACE = (DOG_X - 220, DOG_Y - 130)
SHOTS = [
    [(sc_wide_sleep, (560, 1560, 1.35), (560, 1620, 1.75))],
    [(sc_paws, (DOG_X + 120, DOG_Y - 40, 1.7), (DOG_X + 140, DOG_Y - 30, 1.95)), (lambda c, t, u: sc_face(c, t, u, 0.0, 1.0), (FACE[0], FACE[1], 3.0), (FACE[0], FACE[1], 3.4))],
    [(sc_sounds, (DOG_X - 220, DOG_Y - 200, 2.4), (DOG_X - 240, DOG_Y - 210, 2.7))],
    [(sc_wide_sleep, (560, 1600, 1.6), (560, 1600, 1.3)), (sc_graph, (540, 960, 1.0), (540, 940, 1.05))],
    [(sc_brain, (540, 900, 1.0), (540, 900, 1.12)), (sc_bubble, (520, 1350, 1.25), (500, 1300, 1.35))],
    [(sc_dream_run, (540, 1300, 1.05), (540, 1300, 1.15)), (sc_dream_ball, (540, 1300, 1.05), (560, 1300, 1.1))],
    [(sc_dream_friends, (540, 1350, 1.05), (560, 1350, 1.12)), (sc_dream_pet, (560, 1250, 1.35), (560, 1250, 1.5))],
    [(sc_warm_sleep, (560, 1600, 1.4), (560, 1640, 1.65)), (lambda c, t, u: sc_face(c, t, u, 1.0, 0.5), (FACE[0], FACE[1], 3.0), (FACE[0], FACE[1], 3.3))],
    [(sc_hand, (580, 1450, 1.3), (580, 1550, 1.5)), (sc_hand, (DOG_X - 40, DOG_Y - 180, 2.2), (DOG_X - 40, DOG_Y - 180, 2.4))],
    [(sc_final, (540, 960, 1.0), (540, 960, 1.04))],
]

CHUNKS = [
    ["Et si ton chien", "RÊVAIT de TOI", "pendant qu'il dort… ?"],
    ["Tu l'as peut-être", "déjà remarqué :", "parfois, ton chien", "bouge les PATTES,", "remue les OREILLES…"],
    ["ou fait même", "de petits BRUITS", "pendant son sommeil."],
    ["Ce n'est pas un hasard.", "Comme nous, les chiens", "connaissent des phases de", "SOMMEIL PARADOXAL…"],
    ["une période pendant laquelle", "le CERVEAU est", "particulièrement ACTIF,", "et où les RÊVES", "sont fréquents."],
    ["Des chercheurs pensent", "que leurs RÊVES", "pourraient reprendre", "des moments", "de leur quotidien :"],
    ["COURIR, JOUER,", "retrouver leurs proches…", "et passer du temps", "avec leur HUMAIN préféré."],
    ["Alors peut-être que", "lorsque ton chien", "remue les pattes", "dans son sommeil…"],
    ["il est simplement", "en train de revivre", "l'un de ses plus", "beaux moments avec TOI."],
    ["Et toi, tu crois", "qu'il rêve de TOI ?"],
]


def weight(s):
    w = len(s.replace(' ', '')) + 1.5 * s.count(' ')
    w += 6 * s.count('…') + 4 * len(re.findall(r'[.?:]$', s)) + 2.5 * s.count(',')
    return w


subs = []
for line, chunks in zip(LINES, CHUNKS):
    ws = [weight(ch) for ch in chunks]
    tot = sum(ws); t0 = line['start']
    for ch, w in zip(chunks, ws):
        d = line['dur'] * w / tot
        subs.append([t0, t0 + d, ch]); t0 += d
for a, b in zip(subs, subs[1:]):
    a[1] = b[0]
subs[-1][1] = TOTAL

shots = []
for li, line in enumerate(LINES):
    s0 = 0 if li == 0 else line['start'] - 0.12
    s1 = LINES[li + 1]['start'] - 0.12 if li + 1 < len(LINES) else TOTAL
    n = len(SHOTS[li])
    for k, sp in enumerate(SHOTS[li]):
        shots.append((s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n, sp, k == 0))

FINAL_START = shots[-1][0]
surface, buf = A.surface, A.buf


def frame(t, fi):
    c = surface.getCanvas()
    c.clear(hexc('#000000'))
    sh = next((s for s in shots if s[0] <= t < s[1]), shots[-1])
    s0, s1, spec, sec = sh
    scene, cam0, cam1 = spec[0], spec[1], spec[2]
    u = (t - s0) / (s1 - s0)
    since = t - s0
    punch = max(0, 1 - since / 0.3)
    e = ease(u)
    cx, cy, z = (lerp(a, b, e) for a, b in zip(cam0, cam1))
    z *= 1 + 0.04 * punch
    c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-cx, -cy)
    scene(c, t, u)
    c.restore()
    if t < FINAL_START:
        for st, en, txt in subs:
            if st <= t < en:
                k = (t - st) / 0.16
                sc = 1.0 if k >= 1 else (0.8 + 0.3 * k if k < 0.7 else 1.01 - (k - 0.7) * 0.03)
                A.draw_sub(c, txt, 1300, sc)
                break
    if 0.3 < t < LINES[1]['start'] - 0.12:
        A.badge(c, min(1, (t - 0.3) / 0.25))
    a = buf[..., :3].astype(np.float32) * A.VIG + A.GR[fi % 4]
    if sec and s0 > 0 and since < 0.18:
        a *= 0.55 + 0.45 * since / 0.18
    if t < 0.3:
        a *= t / 0.3
    if t > TOTAL - 0.6:
        a *= max(0, (TOTAL - t) / 0.6)
    return a.clip(0, 255).astype(np.uint8)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        from PIL import Image
        ths = [Image.fromarray(frame(s0 + (s1 - s0) * 0.7, 0)).resize((270, 480)) for s0, s1, _, _ in shots]
        cols = 6
        sheet = Image.new('RGB', (270 * cols, 480 * math.ceil(len(ths) / cols)))
        for i, th in enumerate(ths):
            sheet.paste(th, ((i % cols) * 270, (i // cols) * 480))
        sheet.save('dr/preview.jpg', quality=85)
        sys.exit()
    nf = int(TOTAL * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', 'dr/mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'dr/dream_raw.mp4'], stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait(); print('done')
