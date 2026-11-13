"""Anger & emotional maturity in relationships - animated 9:16 TikTok (reuses the overthinking drawing kit)."""
import json, sys, math, re, subprocess
import numpy as np
import skia
import anim2 as K
from anim2 import (hexc, lerpc, P, oval, rrect, glow, lingrad, ease, lerp, text_center, heart_path, window, motes,
                   silhouette, hearts_rise, phone_shell, chat_header, bubble, F_MSG, F_SMALL, TF_BLACK, TF_XB, BIG, W, H, FPS)

tl = json.load(open('ag/timeline.json'))
TOTAL = tl['total']; LINES = tl['lines']
rng = np.random.default_rng(9)
WARM, ROSE, AMBER = '#FFB46B', '#FF8FB1', '#FFC36B'
SIL = '#120E18'


# ------------------------------------------------------------------ environment
def living(c, t, warm=0.5, rain=1.0):
    c.drawRect(BIG, P(lerpc('#121729', '#2A1E26', warm)))
    lingrad(c, skia.Rect.MakeLTRB(-1500, -1500, W + 1500, 1420), 0, 1420, lerpc('#151B33', '#3A2A30', warm), lerpc('#20263F', '#5A3C3C', warm))
    window(c, t, 640, 300, 980, 780, 0.0, rain)
    # lamp
    glow(c, 150, 760, 760, WARM, 70 + 90 * warm)
    c.drawRect(skia.Rect.MakeLTRB(142, 760, 158, 1420), P(hexc('#0E0F18')))
    sh = skia.Path(); sh.moveTo(70, 760); sh.lineTo(230, 760); sh.lineTo(195, 650); sh.lineTo(105, 650); sh.close()
    c.drawPath(sh, P(lerpc('#C98A4E', '#FFD08A', warm)))
    # couch
    rrect(c, 200, 1060, 960, 1300, 60, P(hexc('#3A3348')))
    rrect(c, 180, 1250, 980, 1420, 40, P(hexc('#2F2A3D')))
    rrect(c, 150, 1150, 270, 1440, 50, P(hexc('#2A2538')))
    rrect(c, 900, 1150, 1020, 1440, 50, P(hexc('#2A2538')))
    lingrad(c, skia.Rect.MakeLTRB(-1500, 1420, W + 1500, H + 1500), 1420, 2000, lerpc('#10121F', '#2A1E1E', warm), hexc('#05060A'))
    oval(c, 560, 1620, 480, 90, P(lerpc('#1A1C2E', '#4A3030', warm)))


def rim_sil(c, x, y, s, lean, rim=WARM, a=150):
    silhouette(c, x + 4, y, s * 1.03, rim, lean=lean)
    c.drawRect(BIG, P(hexc('#000000', 0)))
    silhouette(c, x, y, s, SIL, lean=lean)
    glow(c, x, y - 330 * s, 90 * s, rim, a * 0.3)


def stand_fig(c, x, y, s, col):
    c.save(); c.translate(x, y); c.scale(s, s)
    for lx in (-28, 28):
        rrect(c, lx - 22, -330, lx + 22, 0, 20, P(hexc(col)))
    bp = skia.Path(); bp.moveTo(-85, -300); bp.cubicTo(-95, -480, -70, -620, 0, -630)
    bp.cubicTo(70, -620, 95, -480, 85, -300); bp.close()
    c.drawPath(bp, P(hexc(col)))
    c.drawCircle(0, -700, 70, P(hexc(col)))
    c.restore()


def hand(c, x, y, s, rot, col='#D9A47E'):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    oval(c, 0, 0, 70, 85, P(hexc(col)))
    for i, (fx, fl) in enumerate(((-48, 95), (-16, 120), (16, 125), (46, 105))):
        rrect(c, fx - 15, -fl - 40, fx + 15, -40, 15, P(hexc(col)))
    rrect(c, -95, -20, -55, 60, 20, P(hexc(col)))
    rrect(c, -60, 60, 60, 260, 40, P(hexc('#3B3550')))
    c.restore()


# ------------------------------------------------------------------ scenes
def sc_couch_apart(c, t, u):
    living(c, t, 0.35)
    rim_sil(c, 330, 1290, 1.0, -12)
    rim_sil(c, 800, 1290, 1.0, 12, '#9DB8FF', 120)
    motes(c, t, '#FFE2B0', 50)


def sc_gap(c, t, u):
    c.drawRect(BIG, P(hexc('#2A2538')))
    for i in range(14):
        c.drawLine(-100, 300 + i * 120, W + 100, 280 + i * 120, P(hexc('#352F45'), 6))
    glow(c, 540, 900, 700, WARM, 50)
    hand(c, 230, 1050, 1.15, 70)
    hand(c, 860 + 4 * math.sin(t * 6), 1060, 1.15, -70, '#C99470')
    c.drawLine(380, 1000, 700, 1000, P(hexc('#FFFFFF', 40 + 30 * math.sin(t * 2)), 3))
    text_center(c, 'silence.', 540, 700, 60, hexc('#FFFFFF', 140 * ease(u * 3)), TF_XB)


def sc_window_away(c, t, u):
    living(c, t, 0.25)
    glow(c, 810, 640, 380, '#9DB8FF', 60)
    stand_fig(c, 810, 1440, 1.0, SIL)
    c.save()
    p = P(hexc('#1C1626')); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    c.restore()
    silhouette(c, 300, 1290, 0.9, '#1E1828', lean=-6)


SHARDS = None


def sc_shatter(c, t, u):
    global SHARDS
    c.drawRect(BIG, P(hexc('#120A12')))
    glow(c, 540, 860, 650, '#FF4D5E', 70)
    cx, cy = 540, 840
    n = 16
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 300 if i % 2 == 0 else 230
        pts.append((cx + r * math.cos(a) * 1.15, cy + r * math.sin(a) * 0.8))
    k = ease((u - 0.4) * 2.2)
    for i in range(n):
        p1, p2 = pts[i], pts[(i + 1) % n]
        mx, my = (p1[0] + p2[0] + cx) / 3, (p1[1] + p2[1] + cy) / 3
        dx, dy = mx - cx, my - cy
        off = k * 2.2
        c.save(); c.translate(dx * off, dy * off + 300 * k * k)
        c.translate(mx, my); c.rotate(k * (i * 37 % 90 - 45)); c.translate(-mx, -my)
        tri = skia.Path(); tri.moveTo(cx, cy); tri.lineTo(*p1); tri.lineTo(*p2); tri.close()
        c.drawPath(tri, P(hexc('#E63B4F', 255 * (1 - k))))
        c.drawPath(tri, P(hexc('#FF8A95', 200 * (1 - k)), 3))
        c.restore()
    if k < 0.3:
        shake = 6 * math.sin(t * 60) if u > 0.25 else 0
        text_center(c, '!!!', cx + shake, cy + 50, 170, hexc('#FFFFFF', 255 * (1 - k / 0.3)))
    if k > 0.4:
        text_center(c, "words you don't mean", 540, 380, 52, hexc('#FFFFFF', 220 * ease((k - 0.4) * 3)), TF_XB)


def sc_loud(c, t, u):
    c.drawRect(BIG, P(hexc('#140C14')))
    glow(c, 360, 900, 500, '#FF5A4D', 50)
    # profile silhouette facing right
    hp = skia.Path(); hp.moveTo(80, 1900)
    hp.cubicTo(90, 1500, 120, 1300, 200, 1180)
    hp.cubicTo(130, 1050, 160, 840, 330, 780)
    hp.cubicTo(470, 740, 560, 830, 560, 930)
    hp.lineTo(600, 1010); hp.lineTo(560, 1030)
    hp.cubicTo(570, 1080, 540, 1120, 500, 1130)
    hp.cubicTo(480, 1200, 470, 1500, 520, 1900); hp.close()
    c.drawPath(hp, P(hexc('#05040A')))
    c.drawPath(hp, P(hexc('#FF7A6B', 150), 4))
    for i in range(6):
        k = (t * 0.9 + i / 6) % 1
        r = 60 + k * 620
        rect = skia.Rect.MakeLTRB(600 - r, 1000 - r, 600 + r, 1000 + r)
        c.drawArc(rect, -40, 80, False, P(hexc('#FF6B5B', 230 * (1 - k)), 10))
    words = ['YOU NEVER...', 'WHY DO YOU ALWAYS', 'WHATEVER.']
    for i, s in enumerate(words):
        k = ease((u * 1.4 - i * 0.25) * 3)
        if k > 0:
            text_center(c, s, 700 + 15 * i, 560 + i * 130, 48 + 6 * i, hexc('#FF8A7A', 255 * k), TF_BLACK, 8)


OLD = [('MARCH', 'you forgot AGAIN'), ('LAST YEAR', 'you ALWAYS do this'), ('JUNE', 'remember last time?'), ('2 MONTHS AGO', "this is just like before")]


def sc_old_args(c, t, u):
    c.drawRect(BIG, P(hexc('#121220')))
    glow(c, 540, 960, 800, '#5A4A7A', 50)
    for i, (d, s) in enumerate(OLD):
        k = ease((u * 1.3 - i * 0.18) * 3)
        if k <= 0:
            continue
        y = 1300 - i * 230 - u * 120
        x = 540 + (130 if i % 2 else -130)
        f = skia.Font(TF_XB, 42); tw = f.measureText(s)
        c.save(); c.translate(x, y); c.scale(0.7 + 0.3 * k, 0.7 + 0.3 * k)
        rrect(c, -tw / 2 - 34, -60, tw / 2 + 34, 30, 40, P(hexc('#3A3550', 230 * k)))
        rrect(c, -tw / 2 - 34, -60, tw / 2 + 34, 30, 40, P(hexc('#8E86B8', 160 * k), 3))
        c.drawString(s, -tw / 2, -2, f, P(hexc('#E6E2F5', 255 * k)))
        c.drawString(d, -tw / 2, -78, F_SMALL, P(hexc('#8E86B8', 220 * k)))
        c.restore()
    text_center(c, 'old arguments', 540, 360, 60, hexc('#FFFFFF', 170), TF_XB)


def sc_unfinished(c, t, u):
    c.drawRect(BIG, P(hexc('#0E0C16')))
    glow(c, 540, 960, 900, '#4A3A6A', 60)
    x0, y0, x1, y1 = phone_shell(c, 540, 980, 700, 1400)
    chat_header(c, x0, y0, x1, 'online')
    bubble(c, x0, x1, y0 + 260, 'can we talk?', False)
    iy = y1 - 170
    rrect(c, x0 + 24, iy, x1 - 120, iy + 90, 45, P(hexc('#22263A')))
    c.drawCircle(x1 - 65, iy + 45, 40, P(hexc('#3D4566')))
    full = "I'm sorry, I didn't"
    n = int(len(full) * min(1, u * 1.8))
    if u > 0.75:
        n = len(full) - int((u - 0.75) * 30)
    s = full[:max(0, n)]
    c.drawString(s, x0 + 60, iy + 58, F_MSG, P(hexc('#FFFFFF')))
    if (t * 2) % 1 < 0.5:
        cx = x0 + 62 + F_MSG.measureText(s)
        c.drawLine(cx, iy + 22, cx, iy + 68, P(hexc('#3D7BFF'), 4))
    c.drawString('not sent', x0 + 40, iy - 30, F_SMALL, P(hexc('#FF8A95', 200)))
    c.restore()


def floor_sit(c, x, y, s, col, breath=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    tor = skia.Path(); tor.moveTo(-70, 0); tor.cubicTo(-90, -160, -60, -300, 10, -310)
    tor.cubicTo(80, -300, 90, -160, 70, 0); tor.close()
    c.save(); c.scale(1 + 0.02 * breath, 1 + 0.03 * breath)
    c.drawPath(tor, P(hexc(col)))
    c.restore()
    c.drawCircle(15, -370, 64, P(hexc(col)))
    leg = skia.Path(); leg.moveTo(40, -20); leg.lineTo(230, -200); leg.lineTo(320, 0)
    c.drawPath(leg, P(hexc(col), 70))
    arm = skia.Path(); arm.moveTo(40, -240); arm.quadTo(160, -200, 225, -200)
    c.drawPath(arm, P(hexc(col), 46))
    c.restore()


def sc_alone_calm(c, t, u):
    c.drawRect(BIG, P(hexc('#11131F')))
    lingrad(c, skia.Rect.MakeLTRB(-1500, -1500, W + 1500, 1500), 0, 1500, hexc('#1A1D2E'), hexc('#262338'))
    # closed door with warm light under it
    rrect(c, 560, 380, 960, 1500, 8, P(hexc('#2A2638')))
    rrect(c, 590, 420, 930, 900, 6, P(hexc('#24213A')))
    rrect(c, 590, 960, 930, 1440, 6, P(hexc('#24213A')))
    c.drawCircle(890, 1000, 16, P(hexc('#8E86B8')))
    c.drawRect(skia.Rect.MakeLTRB(560, 1496, 960, 1510), P(hexc(WARM, 230)))
    glow(c, 760, 1520, 300, WARM, 90)
    lingrad(c, skia.Rect.MakeLTRB(-1500, 1500, W + 1500, H + 1500), 1500, 2000, hexc('#15131F'), hexc('#05060A'))
    br = math.sin(t * 2 * math.pi / 4.0)
    glow(c, 270, 1350, 420, '#6A7AB8', 90)
    floor_sit(c, 260, 1560, 1.0, SIL, br)
    glow(c, 280, 1330, 170 + 40 * br, '#9DD6FF', 60 + 30 * br)
    motes(c, t, '#BFD3FF', 40)


def sc_heart_storm(c, t, u):
    c.drawRect(BIG, P(hexc('#0E1020')))
    glow(c, 540, 900, 700, '#3A4A8A', 70)
    hx, hy, hs = 540, 900, 330
    hp = heart_path(hx, hy, hs)
    calm = ease(u * 1.3)
    c.drawPath(hp, P(lerpc('#2A2E48', '#FF8FB1', calm, 255)))
    c.save(); c.clipPath(hp, skia.ClipOp.kIntersect, True)
    for i, (cx, cy, r) in enumerate(((440, 760, 110), (560, 720, 140), (680, 770, 110), (520, 820, 120), (630, 830, 110))):
        c.drawCircle(cx + 10 * math.sin(t + i), cy, r, P(lerpc('#4A4F6E', '#FFD6E2', calm, 255 * (1 - 0.7 * calm))))
    if calm < 0.6 and (t * 3) % 1 < 0.15:
        lb = skia.Path(); lb.moveTo(560, 860); lb.lineTo(510, 980); lb.lineTo(570, 980); lb.lineTo(520, 1100)
        c.drawPath(lb, P(hexc('#FFE27A'), 12))
    for i in range(18):
        k = (t * 1.2 + i / 18) % 1
        c.drawLine(380 + i * 18, 880 + k * 300, 376 + i * 18, 900 + k * 300, P(hexc('#9DB8FF', 160 * (1 - calm)), 3))
    c.restore()
    c.drawPath(hp, P(hexc('#FFFFFF', 120), 6))
    glow(c, hx, hy, 500, ROSE, 90 * calm)


def sc_hand_chest(c, t, u):
    c.drawRect(BIG, P(hexc('#1A1420')))
    glow(c, 540, 820, 600, WARM, 80)
    bp = skia.Path(); bp.moveTo(140, 1900); bp.cubicTo(150, 1350, 300, 1180, 540, 1170)
    bp.cubicTo(780, 1180, 930, 1350, 940, 1900); bp.close()
    c.drawPath(bp, P(hexc(SIL)))
    c.drawRect(skia.Rect.MakeLTRB(490, 1000, 590, 1200), P(hexc(SIL)))
    c.drawCircle(540, 880, 170, P(hexc(SIL)))
    pulse = 0.5 + 0.5 * math.sin(t * 3)
    glow(c, 470, 1420, 260 + 30 * pulse, ROSE, 120 + 60 * pulse)
    hand(c, 470, 1430, 0.95, -20, '#D9A47E')


def sc_breathe(c, t, u):
    lingrad(c, BIG, -200, H + 200, hexc('#10333A'), hexc('#0C1426'))
    cyc = (t % 8.0) / 8.0
    k = ease(cyc * 2) if cyc < 0.5 else 1 - ease((cyc - 0.5) * 2)
    r = 180 + 200 * k
    glow(c, 540, 900, r * 1.8, '#7FE0D0', 80)
    c.drawCircle(540, 900, r, P(hexc('#7FE0D0', 60)))
    c.drawCircle(540, 900, r, P(hexc('#BFF5EA', 220), 6))
    c.drawCircle(540, 900, 180, P(hexc('#BFF5EA', 80), 3))
    text_center(c, 'breathe in' if cyc < 0.5 else 'breathe out', 540, 920, 64, hexc('#FFFFFF', 230), TF_XB)
    for i in range(24):
        a = i / 24 * 2 * math.pi + t * 0.2
        rr = r + 60 + 20 * math.sin(t * 2 + i)
        c.drawCircle(540 + rr * math.cos(a), 900 + rr * math.sin(a), 4, P(hexc('#BFF5EA', 150)))


def sc_msg_moment(c, t, u):
    c.drawRect(BIG, P(hexc('#14101A')))
    glow(c, 540, 960, 900, WARM, 50)
    x0, y0, x1, y1 = phone_shell(c, 540, 980, 700, 1400)
    chat_header(c, x0, y0, x1, 'online')
    y = y0 + 240
    msgs = [('I need a moment to calm down.', True, 0.0), ("I love you. I'll come back and we'll talk.", True, 0.22), ('take your time', False, 0.55)]
    for s, mine, st in msgs:
        k = ease((u - st) * 6)
        if k <= 0:
            continue
        h = bubble(c, x0, x1, y + (1 - k) * 30, s, mine, 255 * k)
        if not mine:
            c.drawPath(heart_path(x0 + 24 + F_MSG.measureText(s) + 90, y + h / 2 + 4, 22), P(hexc('#FF5A7A', 255 * k)))
        y += h + 20
    c.restore()


def sc_same_team(c, t, u):
    c.drawRect(BIG, P(hexc('#1A1420')))
    glow(c, 540, 700, 700, WARM, 70)
    k = ease((u - 0.3) * 3)
    text_center(c, 'ME', 220, 560, 120, hexc('#FFFFFF', 255 * (1 - k)))
    text_center(c, 'YOU', 860, 560, 120, hexc('#FFFFFF', 255 * (1 - k)))
    text_center(c, 'vs', 540, 560, 90, hexc('#FF6B6B', 255 * (1 - k)))
    if 0.15 < u:
        sk = ease((u - 0.15) * 6)
        c.drawLine(470, 525, 470 + 140 * sk, 525, P(hexc('#FFFFFF', 255 * (1 - k)), 10))
    text_center(c, 'US', 540, 520, 140, hexc(AMBER, 255 * k))
    text_center(c, 'vs THE PROBLEM', 540, 650, 72, hexc('#FFFFFF', 255 * k))
    # two figures walk to the same side
    xa = lerp(220, 430, ease(u * 1.5)); xb = lerp(860, 600, ease(u * 1.5))
    stand_fig(c, xa, 1500, 0.85, SIL)
    stand_fig(c, xb, 1500, 0.85, SIL)
    if u > 0.6:
        c.drawLine(xa + 60, 1180, xb - 60, 1180, P(hexc(SIL), 26))
        glow(c, (xa + xb) / 2, 1180, 120, AMBER, 120 * ease((u - 0.6) * 4))


def sc_kitchen(c, t, u):
    c.drawRect(BIG, P(hexc('#1E1618')))
    lingrad(c, skia.Rect.MakeLTRB(-1500, -1500, W + 1500, 1300), 0, 1300, hexc('#2A1E22'), hexc('#4A3030'))
    c.drawLine(540, -200, 540, 520, P(hexc('#0E0A0C'), 6))
    sh = skia.Path(); sh.moveTo(440, 600); sh.lineTo(640, 600); sh.lineTo(590, 520); sh.lineTo(490, 520); sh.close()
    c.drawPath(sh, P(hexc('#E3A35B')))
    glow(c, 540, 820, 700, WARM, 160)
    silhouette(c, 250, 1300, 1.0, SIL, lean=8)
    silhouette(c, 830, 1300, 1.0, SIL, lean=-8)
    rrect(c, 120, 1180, 960, 1240, 14, P(hexc('#5A3A2E')))
    c.drawRect(skia.Rect.MakeLTRB(170, 1240, 200, 1600), P(hexc('#3A2620')))
    c.drawRect(skia.Rect.MakeLTRB(880, 1240, 910, 1600), P(hexc('#3A2620')))
    for mx in (440, 640):
        rrect(c, mx - 40, 1100, mx + 40, 1182, 14, P(hexc('#E9DCCB')))
        for i in range(3):
            k = (t * 0.5 + i / 3) % 1
            sp = skia.Path(); sp.moveTo(mx - 10 + i * 10, 1090)
            sp.cubicTo(mx - 30 + i * 10, 1040 - k * 60, mx + 20 + i * 10, 1000 - k * 80, mx + i * 10, 940 - k * 100)
            c.drawPath(sp, P(hexc('#FFFFFF', 90 * (1 - k)), 5))
    talker = int(t / 1.2) % 2
    bx = 330 if talker == 0 else 750
    rrect(c, bx - 70, 820, bx + 70, 890, 35, P(hexc('#FFFFFF', 210)))
    for i in range(3):
        kk = 0.5 + 0.5 * math.sin(t * 6 - i)
        c.drawCircle(bx - 35 + i * 35, 855, 8, P(hexc('#5A4040', 150 + 100 * kk)))
    lingrad(c, skia.Rect.MakeLTRB(-1500, 1600, W + 1500, H + 1500), 1600, 2000, hexc('#2A1E1E'), hexc('#0A0708'))


def sc_reconnect(c, t, u):
    living(c, t, 1.0, rain=0.0)
    silhouette(c, 470, 1290, 1.0, SIL, lean=10)
    silhouette(c, 620, 1290, 1.0, SIL, lean=-12)
    glow(c, 545, 960, 200, AMBER, 120)
    hearts_rise(c, t, 545, 880)
    motes(c, t, '#FFE2B0', 80)


def sc_final(c, t, u):
    lingrad(c, BIG, -200, H + 200, hexc('#2A1A22'), hexc('#5A3A30'))
    glow(c, 540, 760, 650, AMBER, 90)
    c.drawPath(heart_path(540, 560, 80 + 5 * math.sin(t * 3)), P(hexc(ROSE)))
    k1, k2, k3 = ease(u * 3), ease(u * 3 - 0.3), ease(u * 3 - 0.6)
    text_center(c, 'Even in your', 540, 790, 84, hexc('#FFFFFF', 255 * k1))
    text_center(c, 'worst moments,', 540, 890, 84, hexc('#FFFFFF', 255 * k1))
    text_center(c, "remember who", 540, 1010, 84, hexc('#FFFFFF', 255 * k2))
    text_center(c, "you're talking to.", 540, 1110, 84, hexc(AMBER, 255 * k3))
    k4 = ease((u - 0.5) * 4)
    text_center(c, 'Save this for the next argument.', 540, 1290, 42, hexc('#FFFFFF', 215 * k4), TF_XB)
    text_center(c, 'Send it to your person.', 540, 1350, 42, hexc('#FFFFFF', 215 * k4), TF_XB)


# ------------------------------------------------------------------ shots & subtitles
FULL = (540, 960, 1.0)
SHOTS = [
    [(sc_couch_apart, (560, 1080, 1.35), (560, 1080, 1.5)), (sc_gap, FULL, (540, 1000, 1.12))],
    [(sc_window_away, (640, 1050, 1.3), (700, 1050, 1.45)), (sc_shatter, FULL, (540, 900, 1.05))],
    [(sc_loud, FULL, (500, 940, 1.06)), (sc_old_args, FULL, (540, 960, 1.05)), (sc_unfinished, (540, 1480, 1.3), (540, 1500, 1.4))],
    [(sc_alone_calm, (560, 1200, 1.15), (500, 1250, 1.3)), (sc_alone_calm, (300, 1360, 2.2), (290, 1360, 2.4))],
    [(sc_heart_storm, FULL, (540, 920, 1.08)), (sc_hand_chest, (540, 1100, 1.1), (520, 1200, 1.25))],
    [(sc_breathe, FULL, (540, 920, 1.05))],
    [(sc_msg_moment, (540, 760, 1.15), (540, 820, 1.2))],
    [(sc_same_team, FULL, (540, 960, 1.04)), (sc_kitchen, (540, 1080, 1.2), (540, 1050, 1.35))],
    [(sc_reconnect, (545, 1100, 1.45), (545, 1060, 1.6))],
    [(K.sc_hands, FULL, (540, 960, 1.1)), (sc_final, FULL, (540, 960, 1.03))],
]

CHUNKS = [
    ["One of the HARDEST things", "to learn in a relationship", "is how to be ANGRY", "without becoming HURTFUL."],
    ["Because when you're angry,", "you sometimes say things", "you don't actually MEAN."],
    ["You RAISE your voice,", "bring up OLD arguments,", "or say something", "just to HURT them,", "because you're hurting too."],
    ["But here's something", "you need to understand:", "being upset doesn't give you", "PERMISSION", "to DISRESPECT someone."],
    ["Your feelings are VALID,", "but the way you express them", "is still YOUR responsibility."],
    ["Sometimes, the healthiest thing", "you can do is PAUSE.", "Take a BREATH."],
    ["Tell your partner", "you need a MOMENT,", "instead of saying something", "you'll REGRET."],
    ["You don't have to", "WIN every argument.", "You have to remember", "you're on the SAME TEAM."],
    ["Because a healthy relationship", "isn't about NEVER getting angry."],
    ["It's about making sure", "that even in your WORST moments,", "you don't forget", "you're talking to", "someone you LOVE."],
]


def weight(s):
    w = len(s.replace(' ', '')) + 1.5 * s.count(' ')
    w += 4 * len(re.findall(r'[.?:]$', s)) + 2.5 * s.count(',')
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

FONT_SUB = skia.Font(TF_BLACK, 80)
HL = hexc(AMBER); WHITE = hexc('#FFFFFF')


def draw_sub(c, text, cy, sc):
    words = text.split(' ')
    sp = FONT_SUB.measureText(' ')
    lines, cur = [], []
    for wd in words:
        if cur and FONT_SUB.measureText(' '.join(cur + [wd])) > W * 0.86:
            lines.append(cur); cur = [wd]
        else:
            cur.append(wd)
    lines.append(cur)
    c.save(); c.translate(W / 2, cy); c.scale(sc, sc)
    lh = 98; y0 = -lh * (len(lines) - 1) / 2 + 28
    for i, ln in enumerate(lines):
        tw = sum(FONT_SUB.measureText(w) for w in ln) + sp * (len(ln) - 1)
        x = -tw / 2; y = y0 + i * lh
        for wd in ln:
            core = re.sub(r"[^A-Za-z']", '', wd)
            hl = len(core) > 1 and core.upper() == core
            c.drawString(wd, x + 3, y + 8, FONT_SUB, P(hexc('#000000', 150), 14, blur=6))
            c.drawString(wd, x, y, FONT_SUB, P(hexc('#000000'), 14))
            c.drawString(wd, x, y, FONT_SUB, P(HL if hl else WHITE))
            x += FONT_SUB.measureText(wd) + sp
    c.restore()


def badge(c, a):
    f = skia.Font(TF_XB, 38); s = 'COUPLES NEED TO HEAR THIS'
    tw = f.measureText(s)
    rrect(c, W / 2 - tw / 2 - 34, 290, W / 2 + tw / 2 + 34, 370, 40, P(hexc(AMBER, 235 * a)))
    c.drawString(s, W / 2 - tw / 2, 344, f, P(hexc('#1A0F0A', 255 * a)))


surface = K.surface; buf = K.buf
FINAL_START = shots[-1][0]


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
    for st, en, txt in subs:
        if st <= t < en:
            if t < FINAL_START:
                k = (t - st) / 0.16
                sc = 1.0 if k >= 1 else (0.8 + 0.3 * k if k < 0.7 else 1.01 - (k - 0.7) * 0.03)
                draw_sub(c, txt, 1330, sc)
            else:
                draw_sub(c, txt, 1600, 0.75)
            break
    if 0.3 < t < LINES[1]['start'] - 0.12:
        badge(c, min(1, (t - 0.3) / 0.25))
    a = buf[..., :3].astype(np.float32) * K.VIG + K.GR[fi % 4]
    if sec and s0 > 0 and since < 0.18:
        a *= 0.55 + 0.45 * since / 0.18
    if t < 0.25:
        a *= t / 0.25
    if t > TOTAL - 0.8:
        a *= max(0, (TOTAL - t) / 0.8)
    return a.clip(0, 255).astype(np.uint8)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        from PIL import Image
        ths = [Image.fromarray(frame(s0 + (s1 - s0) * 0.7, 0)).resize((270, 480)) for s0, s1, _, _ in shots]
        cols = 7
        sheet = Image.new('RGB', (270 * cols, 480 * math.ceil(len(ths) / cols)))
        for i, th in enumerate(ths):
            sheet.paste(th, ((i % cols) * 270, (i // cols) * 480))
        sheet.save('ag/preview.jpg', quality=85)
        sys.exit()
    nf = int(TOTAL * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', 'ag/mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'ag/anger_raw.mp4'], stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait(); print('done')
