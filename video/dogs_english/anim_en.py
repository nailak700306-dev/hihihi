"""Animated (illustrated) version of the TikTok video, drawn procedurally with Skia."""
import json, sys, math, re, subprocess
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
tl = json.load(open('en/timeline.json'))
TOTAL = tl['total']; LINES = tl['lines']
TF_BLACK = skia.Typeface.MakeFromFile('fonts/Montserrat-Black.ttf')
TF_XB = skia.Typeface.MakeFromFile('fonts/Montserrat-ExtraBold.ttf')
rng = np.random.default_rng(11)


# ------------------------------------------------------------------ helpers
def hexc(h, a=255):
    h = h.lstrip('#')
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(a))


def lerpc(h1, h2, k, a=255):
    a1 = [int(h1.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    a2 = [int(h2.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    k = min(max(k, 0), 1)
    return skia.Color(*[int(x + (y - x) * k) for x, y in zip(a1, a2)], int(a))


def P(color, stroke=None, blur=None, cap=True):
    p = skia.Paint(AntiAlias=True, Color=color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def oval(c, x, y, rx, ry, p):
    c.drawOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry), p)


def rrect(c, l, t, r, b, rad, p):
    c.drawRoundRect(skia.Rect.MakeLTRB(l, t, r, b), rad, rad, p)


def glow(c, x, y, r, color_hex, alpha):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [hexc(color_hex, alpha), hexc(color_hex, 0)]))
    c.drawCircle(x, y, r, p)


def ease(x):
    x = min(max(x, 0), 1)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def lerp(a, b, k):
    return a + (b - a) * k


def text_center(c, s, x, y, size, color, tf=TF_BLACK, stroke=0, stroke_col=None):
    f = skia.Font(tf, size)
    w = f.measureText(s)
    if stroke:
        c.drawString(s, x - w / 2, y, f, P(stroke_col or hexc('#000000'), stroke))
    c.drawString(s, x - w / 2, y, f, P(color))


# ------------------------------------------------------------------ palette
FUR, FUR_D, CREAM, NOSE = '#E3A35B', '#B9763A', '#F7E0B5', '#2B1E1A'
SKIN, HAIR, SHIRT, PANTS = '#F2C493', '#3A2419', '#5E7FA8', '#2F3653'

# ------------------------------------------------------------------ characters


def dog_head(c, x, y, s, t, look=(0, 0), tilt=0, ears=0.0, blink=None, sniff=0.0, mouth=0.0, brows=0.0):
    c.save(); c.translate(x, y); c.rotate(tilt); c.scale(s, s)
    # ears (floppy) - ears>0 lifts them
    for side in (-1, 1):
        c.save(); c.translate(side * 78, -55); c.rotate(side * (12 - 28 * ears + 3 * math.sin(t * 2.1 + side)))
        pth = skia.Path(); pth.moveTo(0, -10)
        pth.cubicTo(side * 55, -20, side * 70, 90, side * 30, 120)
        pth.cubicTo(side * 5, 135, side * -25, 90, side * -15, 20); pth.close()
        c.drawPath(pth, P(hexc(FUR_D)))
        c.restore()
    oval(c, 0, 0, 102, 96, P(hexc(FUR)))
    oval(c, 0, -60, 40, 30, P(hexc('#EDB572')))  # forehead light
    # muzzle
    sn = 1 + 0.05 * sniff * math.sin(t * 38)
    oval(c, 0, 48, 64 * sn, 46 * sn, P(hexc(CREAM)))
    oval(c, -40, 35, 28, 20, P(hexc(CREAM)))
    oval(c, 40, 35, 28, 20, P(hexc(CREAM)))
    # eyes
    bl = 1.0
    if blink is None:
        ph = (t * 0.55 + x * 0.001) % 1
        bl = 0.1 if ph < 0.035 else 1.0
    else:
        bl = blink
    for side in (-1, 1):
        ex, ey = side * 40, -12
        oval(c, ex, ey, 19, 21 * bl, P(hexc('#24160F')))
        if bl > 0.4:
            c.drawCircle(ex + look[0] * 6 - 5, ey + look[1] * 6 - 7, 6.5, P(hexc('#FFFFFF')))
            c.drawCircle(ex + look[0] * 6 + 5, ey + look[1] * 6 + 6, 2.6, P(hexc('#FFFFFF', 200)))
        # brows (worry when brows>0)
        c.drawLine(ex - 14, ey - 34 + side * 0 - brows * (8 if side < 0 else -8) * -1, ex + 14, ey - 34 - brows * (8 if side < 0 else -8) * -1,
                   P(hexc(FUR_D), 6))
    # nose
    ny = 22 + 2 * sniff * math.sin(t * 38)
    pth = skia.Path(); pth.moveTo(-22, ny); pth.cubicTo(-24, ny - 18, 24, ny - 18, 22, ny)
    pth.cubicTo(18, ny + 16, -18, ny + 16, -22, ny); pth.close()
    c.drawPath(pth, P(hexc(NOSE)))
    oval(c, -7, ny - 6, 7, 4, P(hexc('#FFFFFF', 120)))
    # mouth
    mp = skia.Path(); mp.moveTo(0, ny + 10); mp.lineTo(0, 62)
    mp.moveTo(-26, 60); mp.quadTo(-13, 74, 0, 62); mp.quadTo(13, 74, 26, 60)
    c.drawPath(mp, P(hexc('#5A3A2A'), 4.5))
    if mouth > 0:
        tg = skia.Path(); tg.moveTo(-14, 66); tg.cubicTo(-16, 66 + 40 * mouth, 16, 66 + 40 * mouth, 14, 66); tg.close()
        c.drawPath(tg, P(hexc('#F07C86')))
    c.restore()


def dog_sit(c, x, y, s, t, wag=1.0, **kw):
    c.save(); c.translate(x, y); c.scale(s, s)
    br = 1 + 0.012 * math.sin(t * 3)
    # tail
    w = math.sin(t * 9) * 30 * wag
    tp = skia.Path(); tp.moveTo(80, -50); tp.cubicTo(150, -60, 170 + w * 0.3, -130, 150 + w, -190)
    c.drawPath(tp, P(hexc(FUR_D), 34))
    oval(c, -95, -70, 78, 70, P(hexc(FUR_D)))
    oval(c, 95, -70, 78, 70, P(hexc(FUR_D)))
    oval(c, 0, -165, 118 * br, 165 * br, P(hexc(FUR)))
    oval(c, 0, -215, 64, 110, P(hexc(CREAM)))
    for side in (-1, 1):
        rrect(c, side * 38 - 26, -190, side * 38 + 26, -10, 26, P(hexc(FUR)))
        oval(c, side * 40, -12, 36, 20, P(hexc(CREAM)))
    c.restore()
    dog_head(c, x, y - 330 * s, s, t, **kw)


def dog_walk(c, x, y, s, t, phase_speed=7.0, facing=-1, **kw):
    c.save(); c.translate(x, y); c.scale(-s if facing < 0 else s, s)  # drawn facing right, mirrored when facing left
    ph = t * phase_speed
    bob = 6 * abs(math.sin(ph))
    for i, (lx, off) in enumerate(((-110, 0), (95, math.pi), (-80, math.pi), (125, 0))):
        a = 25 * math.sin(ph + off)
        c.save(); c.translate(lx, -170 - bob); c.rotate(a)
        rrect(c, -22, 0, 22, 170, 22, P(hexc(FUR_D if i < 2 else FUR)))
        oval(c, 4, 168, 30, 15, P(hexc(CREAM)))
        c.restore()
    tp = skia.Path(); tp.moveTo(-150, -230 - bob); tp.cubicTo(-210, -250, -220, -320 + 25 * math.sin(t * 10), -190, -350)
    c.drawPath(tp, P(hexc(FUR_D), 32))
    oval(c, 0, -230 - bob, 175, 85, P(hexc(FUR)))
    oval(c, 20, -195 - bob, 120, 40, P(hexc(CREAM)))
    oval(c, 140, -300 - bob, 60, 80, P(hexc(FUR)))
    c.restore()
    dog_head(c, x + facing * 150 * s,
             y - (370 + 6 * abs(math.sin(ph))) * s, s * 0.85, t, **kw)


def owner(c, x, hip, t, stress=1.0, pose='phone', pet=None, mood=None, lap_dog=None):
    """Seated owner, front view. stress 0..1. pose: phone/head/pet."""
    hunch = 22 * stress
    head_y = hip - 430 + hunch + 3 * math.sin(t * 2.2)
    sh_y = hip - 320 + hunch * 0.6
    # legs
    for side in (-1, 1):
        rrect(c, x + side * 48 - 38, hip - 30, x + side * 48 + 38, hip + 90, 34, P(hexc(PANTS)))
        rrect(c, x + side * 52 - 33, hip + 60, x + side * 52 + 33, hip + 255, 30, P(hexc('#283048')))
        oval(c, x + side * 58, hip + 262, 48, 22, P(hexc('#1C1F2B')))
    # torso
    c.save(); c.translate(x, hip)
    tor = skia.Path(); tor.moveTo(-100, sh_y - hip + 20)
    tor.cubicTo(-110, -150, -95, -40, -88, 20); tor.lineTo(88, 20)
    tor.cubicTo(95, -40, 110, -150, 100, sh_y - hip + 20)
    tor.cubicTo(60, sh_y - hip - 18, -60, sh_y - hip - 18, -100, sh_y - hip + 20); tor.close()
    c.drawPath(tor, P(hexc(SHIRT)))
    c.restore()
    rrect(c, x - 26, head_y + 50, x + 26, sh_y + 10, 14, P(hexc('#E0AE7E')))
    # hands target
    if pose == 'phone':
        hl, hr = (x - 30, hip - 150), (x + 30, hip - 150)
    elif pose == 'head':
        hl, hr = (x - 78, head_y - 10), (x + 78, head_y - 10)
    else:  # pet
        hl = (x - 40, hip - 40)
        hr = pet if pet else (x + 120, hip - 40)
    # arms
    for side, hpos in ((-1, hl), (1, hr)):
        sx, sy = x + side * 98, sh_y + 30
        ex = (sx + hpos[0]) / 2 + side * 55; ey = (sy + hpos[1]) / 2 + 40
        ap = skia.Path(); ap.moveTo(sx, sy); ap.quadTo(ex, ey, *hpos)
        c.drawPath(ap, P(hexc('#4F6E95'), 46))
    if pose == 'phone':
        rrect(c, x - 38, hip - 235, x + 38, hip - 105, 12, P(hexc('#11131A')))
        rrect(c, x - 32, hip - 229, x + 32, hip - 111, 8, P(hexc('#BFE3FF')))
    for hpos in (hl, hr):
        c.drawCircle(hpos[0], hpos[1], 25, P(hexc(SKIN)))
    # head
    c.drawCircle(x, head_y, 88, P(hexc(SKIN)))
    oval(c, x - 88, head_y + 8, 14, 20, P(hexc('#E8B582')))
    oval(c, x + 88, head_y + 8, 14, 20, P(hexc('#E8B582')))
    hp = skia.Path(); hp.moveTo(x - 94, head_y + 20)
    hp.cubicTo(x - 110, head_y - 120, x + 110, head_y - 130, x + 95, head_y + 10)
    hp.cubicTo(x + 70, head_y - 45, x + 10, head_y - 70, x - 60, head_y - 40)
    hp.cubicTo(x - 75, head_y - 20, x - 85, head_y, x - 94, head_y + 20); hp.close()
    c.drawPath(hp, P(hexc(HAIR)))
    if pose == 'head':  # hands over hair
        for hpos in (hl, hr):
            c.drawCircle(hpos[0], hpos[1], 25, P(hexc(SKIN)))
    m = (1 - stress) if mood is None else mood
    look_down = 10 if pose == 'phone' else 0
    for side in (-1, 1):
        ex, ey = x + side * 32, head_y + 8 + look_down
        if m > 0.75:
            ap = skia.Path(); ap.moveTo(ex - 13, ey + 3); ap.quadTo(ex, ey - 10, ex + 13, ey + 3)
            c.drawPath(ap, P(hexc('#2A1A12'), 5))
        else:
            oval(c, ex, ey, 9, 11, P(hexc('#2A1A12')))
            c.drawCircle(ex - 3, ey - 4, 3, P(hexc('#FFFFFF')))
        # brows: worried = inner ends up
        wy = 14 * stress
        c.drawLine(ex - side * 16, ey - 24 - wy, ex + side * 14, ey - 24 + wy * 0.3, P(hexc(HAIR), 6))
    my = head_y + 50
    curve = lerp(-12, 14, m)
    mp = skia.Path(); mp.moveTo(x - 22, my); mp.quadTo(x, my + curve, x + 22, my)
    c.drawPath(mp, P(hexc('#8A4B3A'), 5))
    if m > 0.6:
        glow(c, x - 52, head_y + 32, 26, '#FF8A8A', 120 * (m - 0.6) / 0.4)
        glow(c, x + 52, head_y + 32, 26, '#FF8A8A', 120 * (m - 0.6) / 0.4)
    return head_y


def stress_scribble(c, x, y, t, a):
    if a <= 0:
        return
    pth = skia.Path()
    for i in range(60):
        ang = i * 0.55 + t * 4
        r = 30 + 8 * math.sin(i * 1.7 + t * 9)
        px, py = x + r * math.cos(ang) * 1.3 + i * 0.4 - 12, y + r * math.sin(ang) * 0.6
        pth.moveTo(px, py) if i == 0 else pth.lineTo(px, py)
    c.drawPath(pth, P(hexc('#FF5A5A', 200 * a), 5))


def sweat(c, x, y, t, a=1.0):
    k = (t * 0.6) % 1
    yy = y + k * 60
    pth = skia.Path(); pth.moveTo(x, yy - 22); pth.cubicTo(x + 16, yy, x + 14, yy + 14, x, yy + 14)
    pth.cubicTo(x - 14, yy + 14, x - 16, yy, x, yy - 22)
    c.drawPath(pth, P(hexc('#9AD8FF', 230 * a * (1 - k * 0.5))))


def scent_wisps(c, x, y, t, color_k, n=4, spread=120, height=520, alpha=1.0, target=None):
    for i in range(n):
        ox = (i - (n - 1) / 2) * spread / max(n - 1, 1)
        pth = skia.Path()
        for j in range(40):
            v = j / 39
            px = x + ox + 40 * math.sin(v * 7 + t * 2.4 + i * 1.3) * v
            py = y - v * height
            if target is not None:
                px = lerp(px, target[0], v ** 1.6); py = lerp(py, target[1], v ** 1.6)
            pth.moveTo(px, py) if j == 0 else pth.lineTo(px, py)
        col = lerpc('#7FD6FF', '#FF6A4D', color_k, 150 * alpha)
        c.drawPath(pth, P(col, 14, blur=6))
        c.drawPath(pth, P(lerpc('#D6F3FF', '#FFC0A8', color_k, 160 * alpha), 4))


MOTES = rng.random((40, 4))


def motes(c, t, col='#FFE2B0', a=90):
    for mx, my, sp, sz in MOTES:
        x = (mx * W + 30 * math.sin(t * 0.7 + my * 9)) % W
        y = (my * H - t * 25 * (0.4 + sp)) % H
        c.drawCircle(x, y, 2 + sz * 4, P(hexc(col, a), blur=2))


def room(c, t, warm=0.0):
    c.drawPaint(P(lerpc('#141A2C', '#2B2230', warm)))
    wall = skia.Paint()
    wall.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 1500)],
                                                 [lerpc('#1A2440', '#3A2C3A', warm), lerpc('#26324F', '#5A4048', warm)]))
    c.drawRect(skia.Rect.MakeLTRB(-600, -400, W + 600, 1500), wall)
    # window with moon
    rrect(c, 690, 330, 1000, 760, 18, P(hexc('#0D1222')))
    sky = skia.Paint(); sky.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 340), skia.Point(0, 750)], [hexc('#1B2C55'), hexc('#3B4C7E')]))
    rrect(c, 705, 345, 985, 745, 10, sky)
    glow(c, 900, 440, 110, '#CFE3FF', 70)
    c.drawCircle(900, 440, 38, P(hexc('#F2F4FF')))
    for i in range(7):
        sx, sy = 730 + (i * 97) % 240, 380 + (i * 61) % 330
        c.drawCircle(sx, sy, 2.5 + 1.5 * math.sin(t * 3 + i), P(hexc('#FFFFFF', 200)))
    c.drawRect(skia.Rect.MakeLTRB(838, 345, 852, 745), P(hexc('#0D1222')))
    c.drawRect(skia.Rect.MakeLTRB(705, 538, 985, 552), P(hexc('#0D1222')))
    # frame on wall
    rrect(c, 300, 430, 520, 600, 10, P(hexc('#11182B')))
    rrect(c, 315, 445, 505, 585, 6, P(lerpc('#2C3D63', '#6B4E52', warm)))
    # floor
    fl = skia.Paint(); fl.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1500), skia.Point(0, 2100)], [lerpc('#1E1A26', '#3A2A28', warm), hexc('#0E0C12')]))
    c.drawRect(skia.Rect.MakeLTRB(-600, 1500, W + 600, 2400), fl)
    oval(c, 520, 1690, 520, 120, P(lerpc('#2A2F48', '#5A3A3E', warm)))
    # lamp (left)
    lamp_a = 0.55 + 0.45 * warm
    glow(c, 120, 900, 700, '#FFB36B', 110 * lamp_a)
    c.drawRect(skia.Rect.MakeLTRB(112, 900, 128, 1500), P(hexc('#0F1220')))
    oval(c, 120, 1500, 70, 14, P(hexc('#0F1220')))
    sh = skia.Path(); sh.moveTo(50, 900); sh.lineTo(190, 900); sh.lineTo(160, 790); sh.lineTo(80, 790); sh.close()
    c.drawPath(sh, P(lerpc('#E7A35C', '#FFD08A', warm)))
    # couch
    rrect(c, 190, 1010, 890, 1270, 60, P(hexc('#36456A')))
    rrect(c, 230, 1050, 520, 1250, 40, P(hexc('#3F5079')))
    rrect(c, 560, 1050, 850, 1250, 40, P(hexc('#3F5079')))
    rrect(c, 160, 1225, 920, 1400, 40, P(hexc('#2F3C5E')))
    rrect(c, 120, 1120, 250, 1420, 50, P(hexc('#2B3858')))
    rrect(c, 830, 1120, 960, 1420, 50, P(hexc('#2B3858')))
    for lx in (200, 880):
        c.drawRect(skia.Rect.MakeLTRB(lx - 12, 1420, lx + 12, 1470), P(hexc('#151A2A')))


def couch_front(c):
    # seat front edge drawn over legs bottom for depth
    pass


def molecule(c, x, y, s, rot, col, a=255):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    pts = [(40 * math.cos(math.pi / 3 * i), 40 * math.sin(math.pi / 3 * i)) for i in range(6)]
    pth = skia.Path(); pth.moveTo(*pts[0])
    for p in pts[1:]:
        pth.lineTo(*p)
    pth.close()
    c.drawPath(pth, P(hexc(col, a * 0.5), 10, blur=6))
    c.drawPath(pth, P(hexc('#FFFFFF', a * 0.9), 4))
    c.drawLine(pts[0][0], pts[0][1], 85, 0, P(hexc('#FFFFFF', a * 0.9), 4))
    c.drawLine(pts[3][0], pts[3][1], -75, -30, P(hexc('#FFFFFF', a * 0.9), 4))
    for p in pts + [(85, 0), (-75, -30)]:
        c.drawCircle(p[0], p[1], 10, P(hexc(col, a)))
    c.restore()


def hearts(c, t, x0, y0, a=1.0):
    for i in range(7):
        k = ((t * 0.35 + i / 7) % 1)
        x = x0 + (i - 3) * 60 + 30 * math.sin(t * 2 + i)
        y = y0 - k * 500
        s = 0.6 + 0.4 * math.sin(i)
        al = 220 * a * math.sin(math.pi * k)
        c.save(); c.translate(x, y); c.scale(s, s)
        hp = skia.Path(); hp.moveTo(0, 18); hp.cubicTo(-40, -10, -20, -40, 0, -18); hp.cubicTo(20, -40, 40, -10, 0, 18)
        c.drawPath(hp, P(hexc('#FF7A90', al)))
        c.restore()


# ------------------------------------------------------------------ scenes
# Each scene: fn(c, t_global, u_local) -> draws in world coords. Camera given separately.
OWN_X, OWN_HIP = 470, 1245


def sc_hook_wide(c, t, u):
    room(c, t, 0)
    hy = owner(c, OWN_X, OWN_HIP, t, 1.0, 'phone')
    glow(c, OWN_X, OWN_HIP - 170, 230, '#9FD4FF', 90)
    stress_scribble(c, OWN_X + 10, hy - 140, t, 1)
    # dog in the foreground, darker, eyes glinting
    dog_sit(c, 860, 1880, 1.05, t, look=(-1, -0.6), wag=0.0, ears=0.1)
    c.drawRect(skia.Rect.MakeLTRB(-600, -400, W + 600, 2400), P(hexc('#0A0E1C', 60)))
    motes(c, t, '#BFD8FF', 60)


def sc_dog_eyes(c, t, u):
    room(c, t, 0)
    dog_sit(c, 540, 1650, 1.0, t, look=(lerp(0.2, -1, ease(u * 1.6)), -0.5), wag=0.0, blink=1.0, brows=0.5)


def sc_dog_tilt(c, t, u):
    room(c, t, 0)
    owner(c, OWN_X, OWN_HIP, t, 1.0, 'phone')
    dog_sit(c, 700, 1760, 1.0, t, look=(-1, -0.6), tilt=lerp(0, -14, ease(u * 2)), ears=ease(u * 2) * 0.8, wag=0.15, brows=0.6)


def hud(c, x, y, w, h, u, t, labels):
    a = 255 * ease(u * 3)
    L = 50
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cy = x + sx * w / 2, y + sy * h / 2
        pth = skia.Path(); pth.moveTo(cx, cy - sy * L); pth.lineTo(cx, cy); pth.lineTo(cx - sx * L, cy)
        c.drawPath(pth, P(hexc('#FFD60A', a), 7, cap=False))
    scan = y - h / 2 + (t * 400 % h)
    c.drawLine(x - w / 2, scan, x + w / 2, scan, P(hexc('#FFD60A', a * 0.5), 3, blur=2))
    f = skia.Font(TF_XB, 34)
    for i, s in enumerate(labels):
        k = ease((u - 0.15 - i * 0.18) * 4)
        if k <= 0:
            continue
        yy = y + h / 2 + 70 + i * 62
        tw = f.measureText(s)
        rrect(c, x - tw / 2 - 20, yy - 42, x - tw / 2 - 20 + (tw + 40) * k, yy + 14, 12, P(hexc('#000000', 150)))
        if k > 0.6:
            c.drawString(s, x - tw / 2, yy, f, P(hexc('#FFD60A')))


def sc_scan(c, t, u):
    room(c, t, 0)
    hy = owner(c, OWN_X, OWN_HIP, t, 1.0, 'phone')
    glow(c, OWN_X, OWN_HIP - 170, 230, '#9FD4FF', 90)


def sc_scan_overlay(c, t, u):  # screen space overlay for scan shot
    hud(c, W / 2, 640, 520, 560, u, t, ['BREATHING: CHANGED', 'SWEAT: CHANGED', 'SCENT: ???'])


def sc_wisps(c, t, u):
    room(c, t, 0)
    hy = owner(c, OWN_X, OWN_HIP, t, lerp(0.3, 1.0, ease(u)), 'phone' if u < 0.5 else 'head')
    scent_wisps(c, OWN_X, OWN_HIP - 300, t, ease(u * 1.3), n=5, spread=260, height=700)


def sc_sweat(c, t, u):
    room(c, t, 0)
    hy = owner(c, OWN_X, OWN_HIP, t, 1.0, 'head')
    sweat(c, OWN_X + 70, hy - 30, t)
    sweat(c, OWN_X - 75, hy - 10, t + 0.5)
    # breath puffs
    for i in range(3):
        k = (t * 0.8 + i / 3) % 1
        glow(c, OWN_X + 10 + k * 90, hy + 70 + k * 10, 20 + 40 * k, '#DDEBFF', 120 * (1 - k))
    for i in range(6):
        k = (t * 0.35 + i / 6) % 1
        molecule(c, OWN_X + 80 + k * 220 + 30 * math.sin(i), hy - 40 - k * 260 + i * 25, 0.28 + 0.1 * k, t * 40 + i * 50, '#FF8A5B', 255 * math.sin(math.pi * k))


def sc_molecules(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 900), 1200, [hexc('#3A1830'), hexc('#0B0A16')]))
    c.drawPaint(bg)
    for i in range(14):
        rx, ry, rs = rng_m[i]
        x = rx * W + 60 * math.sin(t * 0.8 + i)
        y = (ry * H - t * 60 * (0.5 + rs)) % (H + 300) - 150
        molecule(c, x, y, 0.6 + rs, t * (20 + 20 * rs) * (1 if i % 2 else -1), '#FF6A4D' if i % 3 else '#FFD60A', 230)
    molecule(c, 540, 820, 2.0 + 0.1 * math.sin(t * 2), t * 12, '#FF6A4D')
    text_center(c, 'THE CHEMICAL', 540, 380, 64, hexc('#FFFFFF', 255 * ease(u * 3)), stroke=10)
    text_center(c, 'SIGNATURE OF STRESS', 540, 460, 64, hexc('#FFD60A', 255 * ease(u * 3 - 0.3)), stroke=10)


rng_m = rng.random((20, 3))


def sc_nose(c, t, u):
    room(c, t, 0)
    # particles into nose
    nx, ny = 540, 1000
    for i in range(40):
        k = (t * 0.5 + i / 40) % 1
        ang = i * 2.4
        r = 700 * (1 - k)
        px, py = nx + r * math.cos(ang), ny + 40 + r * math.sin(ang) * 0.8
        c.drawCircle(px, py, 6 + 6 * (1 - k), P(lerpc('#FF6A4D', '#FFD60A', i % 2, 220 * min(1, k * 3)), blur=3))
    dog_head(c, 540, 1000 - 22 * 3.2, 3.2, t, look=(0, 0.2), sniff=1.0, blink=1.0)


def sc_bars(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [hexc('#1B2440'), hexc('#0C0F1C')]))
    c.drawPaint(bg)
    text_center(c, 'SCENT RECEPTORS', 540, 280, 58, hexc('#FFFFFF'), stroke=8)
    base = 1060
    k1 = ease(u * 3); k2 = ease((u - 0.15) * 1.8)
    # human
    rrect(c, 230, base - 120 * k1, 450, base, 20, P(hexc('#7FA8D8')))
    text_center(c, '6 million', 340, base - 120 * k1 - 30, 46, hexc('#FFFFFF'), TF_XB, 7)
    text_center(c, 'YOU', 340, base + 80, 56, hexc('#BFD3EE'), stroke=8)
    # dog
    rrect(c, 630, base - 640 * k2, 850, base, 20, P(hexc('#FFD60A')))
    glow(c, 740, base - 640 * k2, 200, '#FFD60A', 120 * k2)
    text_center(c, f'{int(300 * k2)} million', 740, base - 640 * k2 - 30, 52, hexc('#FFD60A'), TF_BLACK, 8)
    text_center(c, 'YOUR DOG', 740, base + 80, 56, hexc('#FFD60A'), stroke=8)
    dog_head(c, 740, 1600, 0.8, t, look=(0, -0.5), mouth=0.5)
    c.drawCircle(340, 1600, 70, P(hexc(SKIN)))
    oval(c, 340, 1555, 74, 34, P(hexc(HAIR)))
    for s in (-1, 1):
        c.drawCircle(340 + s * 25, 1605, 8, P(hexc('#2A1A12')))


def sc_2022(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [hexc('#13263A'), hexc('#08111C')]))
    c.drawPaint(bg)
    for i in range(12):  # grid
        c.drawLine(0, i * 170 + (t * 30 % 170), W, i * 170 + (t * 30 % 170), P(hexc('#3A6A8A', 40), 2))
        c.drawLine(i * 100, 0, i * 100, H, P(hexc('#3A6A8A', 40), 2))
    k = ease(u * 2.5)
    c.save(); c.translate(540, 860); c.rotate(-4 + 4 * k); c.scale(0.8 + 0.2 * k, 0.8 + 0.2 * k)
    rrect(c, -260, -330, 260, 330, 24, P(hexc('#F4F1E8')))
    rrect(c, -90, -360, 90, -300, 16, P(hexc('#7A8899')))
    text_center(c, 'SCIENTIFIC', 0, -190, 62, hexc('#1A2533'))
    text_center(c, 'STUDY', 0, -115, 62, hexc('#1A2533'))
    for i in range(4):
        rrect(c, -190, -40 + i * 60, -190 + (380 - i * 50) * ease(u * 3 - i * 0.2), -18 + i * 60, 10, P(hexc('#B7C2CE')))
    # flask
    fp = skia.Path(); fp.moveTo(-30, 180); fp.lineTo(-30, 240); fp.lineTo(-80, 310); fp.lineTo(80, 310); fp.lineTo(30, 240); fp.lineTo(30, 180); fp.close()
    c.drawPath(fp, P(hexc('#6FC3E8')))
    c.restore()
    s = '2022'
    sz = 220 * (0.7 + 0.3 * ease(u * 4))
    text_center(c, s, 540, 400, sz, hexc('#FFD60A'), stroke=16)


def sc_jars(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [hexc('#1D2A3A'), hexc('#0E141E')]))
    c.drawPaint(bg)
    rrect(c, -100, 1180, W + 100, 1260, 10, P(hexc('#4A3A30')))
    c.drawRect(skia.Rect.MakeLTRB(-100, 1260, W + 100, H + 100), P(hexc('#2A211C')))
    jars = [(200, False), (540, True), (880, False)]
    dx = lerp(150, 560, ease(u * 1.5))
    found = u > 0.55
    for jx, hot in jars:
        if hot and found:
            glow(c, jx, 1040, 260, '#FF5A4A', 150 + 50 * math.sin(t * 10))
        rrect(c, jx - 95, 920, jx + 95, 1180, 30, P(hexc('#CFE6F2', 110)))
        rrect(c, jx - 85, 1010, jx + 85, 1170, 24, P(hexc('#FF7A5A' if hot else '#9FD0FF', 170)))
        rrect(c, jx - 105, 880, jx + 105, 930, 14, P(hexc('#8E9AA8')))
        for i in range(3):
            k = (t * 0.7 + i / 3) % 1
            glow(c, jx + 20 * math.sin(t * 3 + i), 860 - k * 200, 30, '#FF7A5A' if hot else '#9FD0FF', 120 * (1 - k))
    dog_head(c, dx, 640 + 15 * math.sin(t * 8), 1.3, t, look=(0, 1), sniff=0 if found else 1, ears=0.5 if found else 0.0, mouth=0.6 if found else 0.0)
    if found:
        k = ease((u - 0.55) * 5)
        c.drawCircle(540, 420, 80 * k, P(hexc('#3DDC84')))
        ck = skia.Path(); ck.moveTo(505, 420); ck.lineTo(530, 448); ck.lineTo(578, 395)
        c.drawPath(ck, P(hexc('#FFFFFF', 255 * k), 14))
        text_center(c, 'STRESS DETECTED', 540, 1620, 70, hexc('#FF7A5A', 255 * k), stroke=10)


def sc_ring(c, t, u):
    bg = skia.Paint(); bg.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 820), 1100, [hexc('#24304F'), hexc('#0B0E1A')]))
    c.drawPaint(bg)
    k = ease(u * 1.6)
    val = 94 * k
    rect = skia.Rect.MakeLTRB(540 - 300, 820 - 300, 540 + 300, 820 + 300)
    c.drawArc(rect, 0, 360, False, P(hexc('#FFFFFF', 40), 46))
    glow(c, 540, 820, 420, '#FFD60A', 50 * k)
    c.drawArc(rect, -90, 360 * val / 100, False, P(hexc('#FFD60A'), 46))
    text_center(c, f'{int(round(val))}%', 540, 870, 170, hexc('#FFFFFF'), stroke=0)
    for i in range(3):
        dog_head(c, 340 + i * 200, 1620, 0.6, t + i, look=(0, -0.3), mouth=0.4, ears=0.3)


def sc_walk(c, t, u):
    room(c, t, 0.1)
    owner(c, OWN_X, OWN_HIP, t, 1.0, 'head')
    stress_scribble(c, OWN_X, OWN_HIP - 600, t, 0.8)
    x = lerp(1250, 760, ease(u))
    dog_walk(c, x, 1780, 0.95, t, phase_speed=8 * (1 - ease(u) * 0.6), facing=-1, look=(-1, -0.4), brows=0.5)


def sc_arrive(c, t, u):
    room(c, t, 0.15)
    owner(c, OWN_X, OWN_HIP, t, lerp(1.0, 0.8, u), 'head')
    dog_sit(c, 660, 1700, 1.0, t, look=(-1, -0.8), tilt=-10 * ease(u * 2), ears=0.3, wag=0.4, brows=0.6)


def sc_lap(c, t, u, stress0=0.7, stress1=0.35):
    room(c, t, lerp(0.3, 0.6, u))
    st = lerp(stress0, stress1, ease(u))
    pet_x = 600 + 22 * math.sin(t * 3.2)
    owner(c, OWN_X, OWN_HIP, t, st, 'pet', pet=(pet_x, 1190 + 8 * math.cos(t * 3.2)))
    dog_sit(c, 610, 1610, 1.0, t, look=(-0.4, -1), tilt=8, ears=-0.2, wag=0.7, blink=lerp(1, 0.55, ease(u)))
    # redraw petting hand on top of the head
    c.drawCircle(pet_x, 1190 + 8 * math.cos(t * 3.2), 25, P(hexc(SKIN)))


def sc_face_calm(c, t, u):
    room(c, t, 0.6)
    st = lerp(0.35, 0.0, ease(u * 1.3))
    pet_x = 600 + 22 * math.sin(t * 3.2)
    hy = owner(c, OWN_X, OWN_HIP, t, st, 'pet', pet=(pet_x, 1190 + 8 * math.cos(t * 3.2)))
    dog_sit(c, 610, 1610, 1.0, t, look=(-0.4, -1), tilt=8, ears=-0.2, wag=1.0, blink=0.55)
    c.drawCircle(pet_x, 1190 + 8 * math.cos(t * 3.2), 25, P(hexc(SKIN)))
    scent_wisps(c, OWN_X, hy - 60, t, 1 - ease(u * 1.5), n=3, spread=140, height=400, alpha=0.7)


def sc_warm_wide(c, t, u):
    room(c, t, 1.0)
    pet_x = 600 + 22 * math.sin(t * 3.2)
    owner(c, OWN_X, OWN_HIP, t, 0.0, 'pet', pet=(pet_x, 1190 + 8 * math.cos(t * 3.2)))
    dog_sit(c, 610, 1610, 1.0, t, look=(-0.4, -1), tilt=8, ears=-0.2, wag=1.2, blink=0.55)
    c.drawCircle(pet_x, 1190 + 8 * math.cos(t * 3.2), 25, P(hexc(SKIN)))
    hearts(c, t, 560, 900)
    motes(c, t)


# shots per voice line: (scene, cam_start(cx,cy,zoom), cam_end, overlay)
FULL = (540, 960, 1.0)
SHOTS = [
    [(sc_hook_wide, (600, 1150, 1.35), (620, 1200, 1.5)), (sc_dog_eyes, (540, 1300, 3.0), (540, 1310, 3.6))],
    [(sc_dog_tilt, (680, 1350, 1.9), (690, 1390, 2.2)), (sc_scan, (OWN_X, 900, 1.6), (OWN_X, 900, 1.75), sc_scan_overlay)],
    [(sc_wisps, (500, 900, 1.15), (500, 860, 1.3))],
    [(sc_sweat, (OWN_X + 40, 820, 2.1), (OWN_X + 60, 800, 2.4)), (sc_molecules, FULL, (540, 960, 1.08))],
    [(sc_nose, (540, 1000, 1.0), (540, 1000, 1.15)), (sc_bars, FULL, (540, 960, 1.04))],
    [(sc_2022, FULL, (540, 960, 1.05)), (sc_jars, (540, 960, 1.0), (540, 960, 1.07)), (sc_ring, FULL, (540, 900, 1.06))],
    [(sc_walk, (700, 1250, 1.1), (680, 1300, 1.25)), (sc_arrive, (600, 1250, 1.45), (580, 1200, 1.6))],
    [(sc_lap, (560, 1250, 1.9), (560, 1220, 2.1)), (sc_face_calm, (OWN_X + 40, 880, 2.0), (OWN_X + 40, 900, 1.7)), (sc_warm_wide, (540, 1150, 1.6), (540, 1100, 1.1))],
    [(sc_warm_wide, (540, 1100, 1.1), (540, 1080, 1.0))],
]

CHUNKS = [
    ["Your dog might KNOW", "you're not okay…", "before you even", "REALISE it yourself."],
    ["Look closely.", "They're WATCHING you.", "All the time.", "And more than anything…", "they're SMELLING you."],
    ["Because your SCENT", "CHANGES", "with the way you FEEL."],
    ["When you're STRESSED,", "your body changes", "the CHEMICAL compounds", "in your SWEAT…", "and in your BREATH."],
    ["To you,", "it's INVISIBLE.", "But your dog's sense of SMELL", "is THOUSANDS of times", "stronger than yours."],
    ["In 2022,", "researchers showed", "that dogs could recognise", "the smell of STRESS…", ("with almost 94%", "with almost ninety-four percent"), "ACCURACY."],
    ["So they come CLOSER.", "Gently.", "Reading your SCENT,", "your POSTURE,", "your EYES."],
    ["So next time your dog", "comes and LEANS against you", "for no obvious reason…", "they might have NOTICED", "something you never", "even said OUT LOUD."],
    ["Has your dog", "ever done this?", "Tell me in the COMMENTS."],
]


def weight(s):
    w = len(s.replace(' ', '')) + 1.5 * s.count(' ')
    w += 7 * s.count('…') + 4 * len(re.findall(r'[.?]$', s)) + 2.5 * s.count(',')
    return w


subs = []
for line, chunks in zip(LINES, CHUNKS):
    ws = [weight(c[1] if isinstance(c, tuple) else c) for c in chunks]
    tot = sum(ws); t0 = line['start']
    for ch, w in zip(chunks, ws):
        d = line['dur'] * w / tot
        subs.append([t0, t0 + d, ch[0] if isinstance(ch, tuple) else ch]); t0 += d
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

FONT_SUB = skia.Font(TF_BLACK, 84)
YEL = hexc('#FFD60A'); WHITE = hexc('#FFFFFF')


def draw_sub(c, text, cy, sc):
    words = text.split(' ')
    sp = FONT_SUB.measureText(' ')
    lines, cur = [], []
    for wd in words:
        trial = ' '.join(cur + [wd])
        if cur and FONT_SUB.measureText(trial) > W * 0.84:
            lines.append(cur); cur = [wd]
        else:
            cur.append(wd)
    lines.append(cur)
    c.save(); c.translate(W / 2, cy); c.scale(sc, sc)
    lh = 102
    y0 = -lh * (len(lines) - 1) / 2 + 30
    for i, ln in enumerate(lines):
        tw = sum(FONT_SUB.measureText(w) for w in ln) + sp * (len(ln) - 1)
        x = -tw / 2; y = y0 + i * lh
        for wd in ln:
            core = re.sub(r'[^\wÀ-ÿ%]', '', wd)
            hl = (len(core) > 1 and core.upper() == core and not core.isdigit()) or core == '94'
            c.drawString(wd, x + 3, y + 8, FONT_SUB, P(hexc('#000000', 150), 14, blur=6))
            c.drawString(wd, x, y, FONT_SUB, P(hexc('#000000'), 14))
            c.drawString(wd, x, y, FONT_SUB, P(YEL if hl else WHITE))
            x += FONT_SUB.measureText(wd) + sp
    c.restore()


def badge(c, a):
    f = skia.Font(TF_XB, 40); s = 'DID YOU KNOW?'
    tw = f.measureText(s)
    rrect(c, W / 2 - tw / 2 - 35, 290, W / 2 + tw / 2 + 35, 372, 41, P(hexc('#FFD60A', 240 * a)))
    c.drawString(s, W / 2 - tw / 2, 346, f, P(hexc('#111111', 255 * a)))


def cta(c, k, t):
    sc = 0.6 + 0.4 * (1 - (1 - k) ** 3) + 0.02 * math.sin(t * 6)
    c.save(); c.translate(W / 2, 560); c.scale(sc, sc)
    a = 245 * k
    rrect(c, -450, -120, 450, 110, 46, P(hexc('#FFFFFF', a)))
    tri = skia.Path(); tri.moveTo(-34, 108); tri.lineTo(34, 108); tri.lineTo(0, 160); tri.close()
    c.drawPath(tri, P(hexc('#FFFFFF', a)))
    text_center(c, 'HAS YOUR DOG DONE THIS?', 0, -20, 56, hexc('#141414', 255 * k))
    text_center(c, 'Tell me in the comments', 0, 60, 42, hexc('#666666', 255 * k), TF_XB)
    c.restore()


yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)
VIG = np.clip(1 - 0.5 * np.clip(r - 0.6, 0, 1) ** 1.3, 0, 1)[..., None].astype(np.float32)
GR = [(rng.standard_normal((H // 2, W // 2, 1)) * 5).repeat(2, 0).repeat(2, 1).astype(np.float32) for _ in range(4)]
buf = np.zeros((H, W, 4), np.uint8)
surface = skia.Surface(buf)


def frame(t, fi):
    c = surface.getCanvas()
    c.clear(hexc('#000000'))
    sh = next((s for s in shots if s[0] <= t < s[1]), shots[-1])
    s0, s1, spec, sec = sh
    scene, cam0, cam1 = spec[0], spec[1], spec[2]
    u = (t - s0) / (s1 - s0)
    since = t - s0
    punch = max(0, 1 - since / 0.25)
    e = ease(u)
    cx, cy, z = (lerp(a, b, e) for a, b in zip(cam0, cam1))
    z *= 1 + 0.06 * punch
    c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-cx, -cy)
    scene(c, t, u)
    c.restore()
    if len(spec) > 3:
        spec[3](c, t, u)
    # subtitles
    for st, en, txt in subs:
        if st <= t < en:
            k = (t - st) / 0.16
            sc = 1.0 if k >= 1 else (0.78 + 0.34 * k if k < 0.7 else 1.018 - (k - 0.7) * 0.06)
            draw_sub(c, txt, 1300 if t < LINES[8]['start'] else 1480, sc)
            break
    if 0.3 < t < LINES[1]['start'] - 0.12:
        badge(c, min(1, (t - 0.3) / 0.2))
    ct = LINES[8]['start']
    if t >= ct:
        cta(c, min(1, (t - ct) / 0.25), t)
    a = buf[..., :3].astype(np.float32) * VIG + GR[fi % 4]
    if sec and s0 > 0 and since < 0.12:
        a += (1 - since / 0.12) * 110
    if t < 0.2:
        a *= t / 0.2
    if t > TOTAL - 0.5:
        a *= max(0, (TOTAL - t) / 0.5)
    return a.clip(0, 255).astype(np.uint8)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        from PIL import Image
        ths = []
        for s0, s1, sp, _ in shots:
            ths.append(Image.fromarray(frame(s0 + (s1 - s0) * 0.7, 0)).resize((270, 480)))
        cols = 8
        sheet = Image.new('RGB', (270 * cols, 480 * math.ceil(len(ths) / cols)))
        for i, th in enumerate(ths):
            sheet.paste(th, ((i % cols) * 270, (i // cols) * 480))
        sheet.save('en/preview.jpg', quality=85)
        sys.exit()
    nf = int(TOTAL * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', 'en/mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'en/dog_raw.mp4'], stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
        if fi % 300 == 0:
            print(fi, '/', nf, flush=True)
    p.stdin.close(); p.wait(); print('done')
