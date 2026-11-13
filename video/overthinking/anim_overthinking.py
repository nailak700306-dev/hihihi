"""Overthinking in relationships - animated 9:16 TikTok, drawn procedurally with Skia."""
import json, sys, math, re, subprocess
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
tl = json.load(open('ot/timeline.json'))
TOTAL = tl['total']; LINES = tl['lines']
TF_BLACK = skia.Typeface.MakeFromFile('fonts/Montserrat-Black.ttf')
TF_XB = skia.Typeface.MakeFromFile('fonts/Montserrat-ExtraBold.ttf')
rng = np.random.default_rng(5)


# ------------------------------------------------------------------ helpers
def hexc(h, a=255):
    h = h.lstrip('#')
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(max(0, min(255, a))))


def lerpc(h1, h2, k, a=255):
    a1 = [int(h1.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    a2 = [int(h2.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    k = min(max(k, 0), 1)
    return skia.Color(*[int(x + (y - x) * k) for x, y in zip(a1, a2)], int(max(0, min(255, a))))


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


def glow(c, x, y, r, col, alpha):
    if alpha <= 0 or r <= 0:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [hexc(col, alpha), hexc(col, 0)]))
    c.drawCircle(x, y, r, p)


def lingrad(c, rect, y0, y1, c0, c1):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [c0, c1]))
    c.drawRect(rect, p)


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


def heart_path(cx, cy, s):
    p = skia.Path()
    p.moveTo(cx, cy + 0.9 * s)
    p.cubicTo(cx - 1.3 * s, cy - 0.1 * s, cx - 0.75 * s, cy - 1.15 * s, cx, cy - 0.45 * s)
    p.cubicTo(cx + 0.75 * s, cy - 1.15 * s, cx + 1.3 * s, cy - 0.1 * s, cx, cy + 0.9 * s)
    p.close()
    return p


BIG = skia.Rect.MakeLTRB(-1500, -1500, W + 1500, H + 1500)

# palette
NIGHT, WALL, MOON, GLOW = '#0C1022', '#16203D', '#9DB8FF', '#BFE2FF'
BLANKET, BLANKET_D, SKIN, HAIR = '#3B4C82', '#2C3A68', '#E9B98F', '#24171A'
PINK, WARM = '#FF7AA2', '#FFB46B'

# ------------------------------------------------------------------ environment
RAIN = rng.random((70, 3))


def rain_streaks(c, t, x0, y0, x1, y1, a=120):
    c.save(); c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1))
    for rx, ry, rs in RAIN:
        x = x0 + rx * (x1 - x0)
        y = y0 + ((ry * (y1 - y0) + t * (700 + 500 * rs)) % (y1 - y0 + 80)) - 40
        c.drawLine(x, y, x - 6, y + 34, P(hexc('#C9DAFF', a * (0.4 + 0.6 * rs)), 2))
    c.restore()


def window(c, t, x0, y0, x1, y1, dawn=0.0, rain_a=1.0):
    rrect(c, x0 - 18, y0 - 18, x1 + 18, y1 + 18, 16, P(hexc('#0A0D1A')))
    sky = skia.Paint()
    sky.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                                 [lerpc('#14214A', '#F6A27A', dawn), lerpc('#2E3F78', '#FFD9A0', dawn)]))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), sky)
    mx, my = x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.28
    if dawn < 0.7:
        glow(c, mx, my, 120, '#D6E4FF', 80 * (1 - dawn))
        c.drawCircle(mx, my, 34, P(hexc('#F3F5FF', 255 * (1 - dawn))))
    if dawn > 0:
        sx, sy = x0 + (x1 - x0) * 0.35, y1 - (y1 - y0) * 0.15 * dawn
        glow(c, sx, sy, 260, '#FFE1A8', 200 * dawn)
        c.drawCircle(sx, sy, 50, P(hexc('#FFF1C9', 255 * dawn)))
    # city silhouette
    c.save(); c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1))
    bx = x0
    for i in range(9):
        bw = 40 + (i * 37) % 50; bh = 60 + (i * 53) % 120
        c.drawRect(skia.Rect.MakeLTRB(bx, y1 - bh, bx + bw, y1), P(lerpc('#0B1230', '#7A4A5A', dawn)))
        for wy in range(int(y1 - bh + 15), int(y1 - 10), 26):
            if (wy + i * 7) % 3 == 0:
                c.drawRect(skia.Rect.MakeLTRB(bx + 10, wy, bx + 18, wy + 10), P(hexc('#FFD27A', 160 * (1 - dawn))))
        bx += bw + 6
    c.restore()
    if rain_a > 0:
        rain_streaks(c, t, x0, y0, x1, y1, 120 * rain_a)
    mx2 = (x0 + x1) / 2
    c.drawRect(skia.Rect.MakeLTRB(mx2 - 7, y0, mx2 + 7, y1), P(hexc('#0A0D1A')))


MOTES = rng.random((35, 4))


def motes(c, t, col='#BFD3FF', a=70):
    for mx, my, sp, sz in MOTES:
        x = (mx * W + 30 * math.sin(t * 0.6 + my * 9)) % W
        y = (my * H - t * 18 * (0.4 + sp)) % H
        c.drawCircle(x, y, 2 + sz * 3, P(hexc(col, a), blur=2))


def bedroom(c, t, dawn=0.0):
    c.drawRect(BIG, P(lerpc(NIGHT, '#3A2A38', dawn)))
    lingrad(c, skia.Rect.MakeLTRB(-1500, -1500, W + 1500, 1300), 0, 1300, lerpc('#121A33', '#4A3346', dawn), lerpc('#1C2747', '#6B4652', dawn))
    window(c, t, 620, 330, 980, 820, dawn)
    # moonlight patch on wall
    glow(c, 800, 900, 420, '#7FA0FF', 35 * (1 - dawn))
    # nightstand + clock
    rrect(c, 40, 1080, 230, 1330, 12, P(hexc('#141A2E')))
    rrect(c, 70, 1020, 200, 1080, 10, P(hexc('#0A0E1A')))
    f = skia.Font(TF_XB, 40)
    c.drawString('2:47', 88, 1065, f, P(hexc('#FF6B6B', 230)))
    glow(c, 135, 1050, 90, '#FF6B6B', 40)
    # floor
    lingrad(c, skia.Rect.MakeLTRB(-1500, 1300, W + 1500, H + 1500), 1300, 2000, lerpc('#0F1328', '#3A2A2E', dawn), hexc('#05060C'))


def person_in_bed(c, t, worried=1.0, phone=True, eyes_open=1.0):
    # bed
    rrect(c, 180, 1170, 1060, 1330, 20, P(hexc('#1E2340')))
    rrect(c, 190, 1150, 1050, 1230, 30, P(hexc('#D9DEF0', 60)))
    rrect(c, 160, 960, 210, 1340, 14, P(hexc('#1A1F38')))  # headboard
    oval(c, 320, 1150, 120, 45, P(hexc('#C9D3F0', 140)))  # pillow
    # blanket with slow breathing
    br = 4 * math.sin(t * 1.6)
    bl = skia.Path(); bl.moveTo(360, 1235)
    bl.cubicTo(420, 1090 - br, 600, 1080 - br, 700, 1120 - br)
    bl.cubicTo(800, 1150, 900, 1110 - br, 1040, 1160)
    bl.lineTo(1050, 1240); bl.lineTo(360, 1240); bl.close()
    c.drawPath(bl, P(hexc(BLANKET)))
    for fx in (520, 700, 860):
        fp = skia.Path(); fp.moveTo(fx, 1130 - br); fp.quadTo(fx + 30, 1180, fx + 10, 1235)
        c.drawPath(fp, P(hexc(BLANKET_D), 6))
    # head on pillow (side), face toward camera
    hx, hy = 300, 1095
    if phone:
        glow(c, hx + 60, hy + 10, 230, GLOW, 110)
    c.drawCircle(hx, hy, 72, P(hexc(SKIN)))
    hp = skia.Path(); hp.moveTo(hx - 75, hy + 30)
    hp.cubicTo(hx - 95, hy - 90, hx + 70, hy - 110, hx + 76, hy - 20)
    hp.cubicTo(hx + 40, hy - 60, hx - 20, hy - 50, hx - 40, hy - 10)
    hp.cubicTo(hx - 50, hy + 30, hx - 60, hy + 60, hx - 75, hy + 30); hp.close()
    c.drawPath(hp, P(hexc(HAIR)))
    # eyes
    blink = 0.15 if (t * 0.4) % 1 < 0.04 else 1.0
    for ex in (hx + 8, hx + 44):
        oval(c, ex, hy + 8, 7, 9 * blink * eyes_open, P(hexc('#1A1012')))
        if phone and blink > 0.5:
            c.drawRect(skia.Rect.MakeLTRB(ex - 2, hy + 2, ex + 3, hy + 8), P(hexc('#DDF0FF', 220)))
        c.drawLine(ex - 9, hy - 12 - 5 * worried * (1 if ex < hx + 20 else -1) * -1, ex + 9, hy - 12 + 5 * worried * (1 if ex < hx + 20 else -1) * -1, P(hexc(HAIR), 4))
    mp = skia.Path(); mp.moveTo(hx + 14, hy + 42); mp.quadTo(hx + 26, hy + 42 - 6 * worried + 6 * (1 - worried), hx + 38, hy + 42)
    c.drawPath(mp, P(hexc('#8A4B3A'), 3.5))
    if phone:
        # arm + phone held in front
        ap = skia.Path(); ap.moveTo(400, 1180); ap.quadTo(470, 1170, 470, 1120)
        c.drawPath(ap, P(hexc(SKIN), 34))
        c.save(); c.translate(470, 1075); c.rotate(-8)
        rrect(c, -38, -70, 38, 70, 12, P(hexc('#0B0D14')))
        rrect(c, -32, -64, -26, -50, 3, P(hexc('#333A55')))
        c.restore()
        c.drawCircle(470, 1125, 20, P(hexc(SKIN)))


# ------------------------------------------------------------------ phone UI
F_MSG = skia.Font(TF_XB, 40)
F_SMALL = skia.Font(TF_XB, 28)


def wrap(text, font, maxw):
    words = text.split(' '); lines, cur = [], ''
    for w in words:
        tr = (cur + ' ' + w).strip()
        if cur and font.measureText(tr) > maxw:
            lines.append(cur); cur = w
        else:
            cur = tr
    lines.append(cur)
    return lines


def bubble(c, x0, x1, y, text, mine, a=255, hl=False):
    maxw = (x1 - x0) * 0.7
    ls = wrap(text, F_MSG, maxw - 50)
    tw = max(F_MSG.measureText(l) for l in ls)
    bw, bh = tw + 56, 52 * len(ls) + 34
    bx = x1 - bw - 24 if mine else x0 + 24
    col = hexc('#3D7BFF', a) if mine else hexc('#2C2F3D', a)
    rrect(c, bx, y, bx + bw, y + bh, 30, P(col))
    if hl:
        rrect(c, bx - 10, y - 10, bx + bw + 10, y + bh + 10, 38, P(hexc('#FF5A7A', 220), 6))
    for i, l in enumerate(ls):
        c.drawString(l, bx + 28, y + 56 + i * 52, F_MSG, P(hexc('#FFFFFF', a)))
    return bh


def phone_shell(c, cx, cy, w, h):
    rrect(c, cx - w / 2 - 18, cy - h / 2 - 18, cx + w / 2 + 18, cy + h / 2 + 18, 70, P(hexc('#05060A')))
    glow(c, cx, cy, max(w, h) * 0.8, GLOW, 40)
    scr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 56, 56)
    c.save(); c.clipRRect(scr, True)
    c.drawRect(skia.Rect.MakeLTRB(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), P(hexc('#0E1018')))
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def chat_header(c, x0, y0, x1, status='online'):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y0 + 170), P(hexc('#181B26')))
    c.drawCircle(x0 + 90, y0 + 100, 40, P(hexc('#5A6390')))
    heart = heart_path(x0 + 90, y0 + 102, 18)
    c.drawPath(heart, P(hexc('#FF8FB1')))
    c.drawString('my person', x0 + 150, y0 + 98, skia.Font(TF_BLACK, 40), P(hexc('#FFFFFF')))
    c.drawString(status, x0 + 150, y0 + 138, F_SMALL, P(hexc('#8E96B8')))


def typing_dots(c, x, y, t, a=255):
    rrect(c, x, y, x + 140, y + 70, 35, P(hexc('#2C2F3D', a)))
    for i in range(3):
        k = 0.5 + 0.5 * math.sin(t * 8 - i * 0.9)
        c.drawCircle(x + 40 + i * 30, y + 35 - 6 * k, 9, P(hexc('#AEB4CC', a * (0.5 + 0.5 * k))))


def sc_phone(mode):
    def draw(c, t, u):
        c.drawRect(BIG, P(hexc(NIGHT)))
        glow(c, 540, 960, 900, '#3550A0', 60)
        x0, y0, x1, y1 = phone_shell(c, 540, 980, 700, 1400)
        if mode == 'waiting':
            chat_header(c, x0, y0, x1, 'last seen 10 min ago' if u > 0.5 else 'online')
            y = y0 + 230
            y += bubble(c, x0, x1, y, 'I miss you today', True) + 18
            y += bubble(c, x0, x1, y, 'how was your day?', True) + 10
            st = 'Delivered 11:42 PM' if u < 0.45 else 'Read 11:43 PM'
            c.drawString(st, x1 - 30 - F_SMALL.measureText(st), y + 34, F_SMALL, P(hexc('#8E96B8')))
            if 0.5 < u < 0.8:
                typing_dots(c, x0 + 24, y + 80, t)
        elif mode == 'distant':
            chat_header(c, x0, y0, x1, 'online')
            y = y0 + 220
            c.drawString('LAST MONTH', x0 + 250, y + 20, F_SMALL, P(hexc('#6E7698')))
            y += 50
            y += bubble(c, x0, x1, y, 'omg yesss!! I love you so much', False, 140) + 14
            c.drawString('TODAY', x0 + 290, y + 40, F_SMALL, P(hexc('#6E7698')))
            y += 70
            y += bubble(c, x0, x1, y, 'can we talk later?', True) + 14
            k = ease((u - 0.3) * 4)
            if k > 0:
                bubble(c, x0, x1, y, 'ok.', False, 255 * k, hl=u > 0.6)
        elif mode == 'tired':
            chat_header(c, x0, y0, x1, 'online')
            y = y0 + 240
            y += bubble(c, x0, x1, y, 'are you okay? you seem quiet', True) + 18
            k = ease(u * 4)
            if u < 0.2:
                typing_dots(c, x0 + 24, y, t)
            else:
                bubble(c, x0, x1, y, "I'm just really tired tonight", False, 255 * k)
        elif mode == 'punct':
            chat_header(c, x0, y0, x1, 'online')
            y = y0 + 260
            bubble(c, x0, x1, y, 'sure.', False)
            bubble(c, x0, x1, y + 160, 'k', False)
            bubble(c, x0, x1, y + 320, 'fine', False)
            # magnifier
            mx, my = lerp(x0 + 200, x0 + 230, ease(u)), lerp(y + 60, y + 110, ease(u))
            c.drawCircle(mx, my, 110, P(hexc('#FFFFFF', 40)))
            c.drawCircle(mx, my, 110, P(hexc('#FFFFFF', 230), 12))
            c.drawLine(mx + 80, my + 80, mx + 170, my + 170, P(hexc('#FFFFFF', 230), 26))
            c.drawString('?', mx - 18, my + 30, skia.Font(TF_BLACK, 90), P(hexc('#FF5A7A', 255 * ease(u * 3))))
        elif mode == 'scroll':
            chat_header(c, x0, y0, x1, 'online')
            off = -ease(u) * 1400 + 900
            msgs = [('JUNE 2', None), ('good morning beautiful', False), ('you make me so happy', False), ('MAY 18', None),
                    ('I love you', True), ('I love you more', False), ('APRIL 30', None), ('best night ever', False),
                    ('can not stop smiling', True), ('MARCH 14', None), ('so glad I met you', False), ('me too', True)]
            c.save(); c.clipRect(skia.Rect.MakeLTRB(x0, y0 + 170, x1, y1))
            y = y0 + 200 + off
            for txt, mine in msgs:
                if mine is None:
                    c.drawString(txt, (x0 + x1) / 2 - F_SMALL.measureText(txt) / 2, y + 30, F_SMALL, P(hexc('#6E7698')))
                    y += 60
                else:
                    y += bubble(c, x0, x1, y, txt, mine) + 16
            c.restore()
        elif mode == 'typing':
            chat_header(c, x0, y0, x1, 'online')
            y = y0 + 260
            bubble(c, x0, x1, y, 'goodnight', False)
            # input bar
            iy = y1 - 160
            rrect(c, x0 + 24, iy, x1 - 120, iy + 90, 45, P(hexc('#22263A')))
            c.drawCircle(x1 - 65, iy + 45, 40, P(hexc('#3D7BFF')))
            drafts = ['are we okay?', 'did I do something wrong?']
            ph = u * 2
            idx = min(int(ph), 1); k = ph - idx
            d = drafts[idx]
            n = int(len(d) * min(1, k * 2.2)) if k < 0.6 else int(len(d) * max(0, 1 - (k - 0.6) * 3))
            s = d[:n]
            c.drawString(s, x0 + 60, iy + 58, F_MSG, P(hexc('#FFFFFF')))
            if (t * 2) % 1 < 0.5:
                cx = x0 + 62 + F_MSG.measureText(s)
                c.drawLine(cx, iy + 22, cx, iy + 68, P(hexc('#3D7BFF'), 4))
            if k > 0.6:
                c.drawString('deleting...', x0 + 40, iy - 30, F_SMALL, P(hexc('#FF7A8A', 200)))
        c.restore()
        # notification over phone for 'waiting' start
    return draw


def sc_lockscreen(c, t, u):
    c.drawRect(BIG, P(hexc(NIGHT)))
    x0, y0, x1, y1 = phone_shell(c, 540, 980, 700, 1400)
    lingrad(c, skia.Rect.MakeLTRB(x0, y0, x1, y1), y0, y1, hexc('#1B2450'), hexc('#3A2650'))
    text_center(c, '2:47', 540, y0 + 330, 190, hexc('#FFFFFF', 230), TF_BLACK)
    text_center(c, 'Tuesday, March 4', 540, y0 + 400, 36, hexc('#FFFFFF', 180), TF_XB)
    notes = ['Battery low - 10%', 'Weather: rain tonight', 'No new messages']
    for i, s in enumerate(notes):
        k = ease((u - i * 0.22) * 4)
        if k <= 0:
            continue
        yy = y0 + 520 + i * 150 + (1 - k) * 60
        rrect(c, x0 + 30, yy, x1 - 30, yy + 120, 30, P(hexc('#FFFFFF', 50 * k)))
        c.drawString(s, x0 + 70, yy + 72, F_MSG, P(hexc('#FF9DB5' if i == 2 else '#FFFFFF', 255 * k)))
    c.restore()


def sc_bed_wide(c, t, u):
    bedroom(c, t)
    person_in_bed(c, t)
    motes(c, t)


def sc_bed_close(c, t, u):
    bedroom(c, t)
    person_in_bed(c, t, worried=1.0)
    # floating question marks
    for i in range(5):
        k = (t * 0.3 + i / 5) % 1
        c.drawString('?', 250 + i * 50 + 20 * math.sin(t + i), 980 - k * 220, skia.Font(TF_BLACK, 40 + i * 6),
                     P(hexc('#BFD3FF', 200 * math.sin(math.pi * k))))


def sc_ceiling(c, t, u):
    c.drawRect(BIG, P(hexc('#0D1124')))
    # window light rotating across from above
    glow(c, 540 + 200 * math.sin(t * 0.3), 700, 700, '#3B55A8', 50)
    # bed top-down
    rrect(c, 230, 360, 850, 1700, 40, P(hexc('#1C2240')))
    rrect(c, 250, 380, 830, 1680, 32, P(hexc('#C9D3F0', 40)))
    oval(c, 540, 520, 220, 90, P(hexc('#C9D3F0', 140)))
    # blanket
    bl = skia.Path(); bl.moveTo(260, 820); bl.cubicTo(400, 790, 680, 790, 820, 820)
    bl.lineTo(820, 1670); bl.lineTo(260, 1670); bl.close()
    c.drawPath(bl, P(hexc(BLANKET)))
    for fx in (380, 540, 700):
        c.drawLine(fx, 900, fx + 20, 1600, P(hexc(BLANKET_D), 6))
    # head from above, face up
    hx, hy = 540, 560
    c.drawCircle(hx, hy, 95, P(hexc(SKIN)))
    hp = skia.Path(); hp.moveTo(hx - 110, hy + 10)
    hp.cubicTo(hx - 120, hy - 150, hx + 120, hy - 150, hx + 110, hy + 10)
    hp.cubicTo(hx + 80, hy - 60, hx - 80, hy - 60, hx - 110, hy + 10); hp.close()
    c.drawPath(hp, P(hexc(HAIR)))
    for s in (-1, 1):
        oval(c, hx + s * 34, hy + 10, 10, 12, P(hexc('#1A1012')))
        c.drawCircle(hx + s * 34 - 3, hy + 6, 3, P(hexc('#FFFFFF')))
    c.drawLine(hx - 12, hy + 52, hx + 12, hy + 52, P(hexc('#8A4B3A'), 4))
    # arms + phone on chest (screen up, glowing)
    for s in (-1, 1):
        ap = skia.Path(); ap.moveTo(hx + s * 150, 800); ap.quadTo(hx + s * 140, 900, hx + s * 40, 920)
        c.drawPath(ap, P(hexc(SKIN), 40))
    rrect(c, hx - 55, 850, hx + 55, 1040, 16, P(hexc('#0B0D14')))
    rrect(c, hx - 47, 858, hx + 47, 1032, 10, P(hexc('#BFE2FF', 200 + 40 * math.sin(t * 2))))
    glow(c, hx, 945, 260, GLOW, 70)
    # swirling thoughts above head
    for i in range(14):
        a = t * 0.8 + i * (2 * math.pi / 14)
        r = 210 + 25 * math.sin(t * 2 + i)
        c.drawCircle(hx + r * math.cos(a), hy + r * 0.55 * math.sin(a) - 30, 6, P(hexc('#BFD3FF', 160), blur=2))


THOUGHTS = ["they're bored of me", 'did I say something?', "I'm too much", "they're pulling away",
            'someone else?', 'was it my text?', 'do they still care?', "maybe I'm annoying"]
TH_POS = rng.random((120, 3))


def sc_scenarios(c, t, u):
    c.drawRect(BIG, P(hexc('#0B0E1E')))
    glow(c, 540, 1000, 800, '#3A2A6A', 70)
    # head profile silhouette
    hp = skia.Path(); hp.moveTo(300, 1900)
    hp.cubicTo(300, 1600, 260, 1500, 330, 1400)
    hp.cubicTo(250, 1350, 260, 1230, 330, 1180)
    hp.cubicTo(330, 1000, 520, 920, 650, 1000)
    hp.cubicTo(760, 1070, 780, 1220, 720, 1330)
    hp.cubicTo(700, 1400, 700, 1600, 760, 1900); hp.close()
    c.drawPath(hp, P(hexc('#05060E')))
    c.drawPath(hp, P(hexc('#7A86C8', 120), 4))
    # bubbles multiplying
    n = int(8 + ease(u) * 110)
    for i in range(n):
        bx, by, bs = TH_POS[i]
        x = 120 + bx * 840 + 15 * math.sin(t * 1.5 + i)
        y = 260 + by * 760 + 10 * math.cos(t * 1.3 + i)
        r = 10 + bs * 26
        c.drawCircle(x, y, r, P(hexc('#BFD3FF', 70), 3))
    # labelled thoughts popping
    for i, s in enumerate(THOUGHTS):
        k = ease((u * 1.25 - i * 0.1) * 5)
        if k <= 0:
            continue
        x = 540 + (240 if i % 2 else -240) + 20 * math.sin(t + i)
        y = 330 + (i // 2) * 170 + (60 if i % 2 else 0)
        f = skia.Font(TF_XB, 34)
        tw = f.measureText(s)
        c.save(); c.translate(x, y); c.scale(0.6 + 0.4 * k, 0.6 + 0.4 * k)
        rrect(c, -tw / 2 - 26, -48, tw / 2 + 26, 22, 34, P(hexc('#FFFFFF', 235 * k)))
        c.drawString(s, -tw / 2, -2, f, P(hexc('#1A1A2E', 255 * k)))
        c.restore()
    cnt = int(1 + ease(u) * 99)
    text_center(c, f'SCENARIO #{cnt}', 540, 1140, 64, hexc('#FF7AA2'), stroke=10)


def sc_nothing_wrong(c, t, u):
    # split screen: partner peacefully asleep (top) vs you awake (bottom)
    c.drawRect(BIG, P(hexc('#0B0F20')))
    c.save(); c.clipRect(skia.Rect.MakeLTRB(0, 0, W, 940))
    lingrad(c, skia.Rect.MakeLTRB(0, 0, W, 940), 0, 940, hexc('#1A2550'), hexc('#24315E'))
    rrect(c, 120, 560, 980, 760, 30, P(hexc('#2B3666')))
    oval(c, 300, 590, 110, 40, P(hexc('#C9D3F0', 120)))
    c.drawCircle(300, 560, 60, P(hexc('#E3B48C')))
    oval(c, 300, 525, 64, 34, P(hexc('#4A3226')))
    for s in (-1, 1):
        ap = skia.Path(); ap.moveTo(300 + s * 22 - 10, 568); ap.quadTo(300 + s * 22, 576, 300 + s * 22 + 10, 568)
        c.drawPath(ap, P(hexc('#2A1A12'), 4))
    bl = skia.Path(); bl.moveTo(340, 640); bl.cubicTo(500, 560, 800, 570, 980, 620); bl.lineTo(980, 760); bl.lineTo(340, 760); bl.close()
    c.drawPath(bl, P(hexc('#5B6FB0')))
    rrect(c, 760, 770, 860, 820, 10, P(hexc('#0B0D14')))  # phone face down
    for i in range(3):
        k = (t * 0.5 + i / 3) % 1
        c.drawString('z', 380 + i * 30 + k * 40, 480 - k * 160, skia.Font(TF_BLACK, 50 + i * 10), P(hexc('#FFFFFF', 220 * math.sin(math.pi * k))))
    text_center(c, 'THEM: fast asleep', 540, 200, 52, hexc('#FFFFFF'), stroke=8)
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(0, 932, W, 948), P(hexc('#FFFFFF', 200)))
    c.save(); c.clipRect(skia.Rect.MakeLTRB(0, 948, W, H)); c.translate(0, -60)
    bedroom(c, t); person_in_bed(c, t)
    c.restore()
    text_center(c, 'YOU: wide awake', 540, 1780, 52, hexc('#FF9DB5'), stroke=8)


def silhouette(c, x, y, s, col, lean=0.0, look=0.0, sit=True):
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(lean)
    # body (sitting)
    bp = skia.Path(); bp.moveTo(-80, 0); bp.cubicTo(-95, -150, -70, -260, 0, -270)
    bp.cubicTo(70, -260, 95, -150, 80, 0); bp.close()
    c.drawPath(bp, P(hexc(col)))
    c.drawCircle(look * 10, -330, 62, P(hexc(col)))
    c.restore()


def sc_window_sit(c, t, u):
    c.drawRect(BIG, P(hexc('#0A0D1C')))
    window(c, t, 180, 360, 900, 1240, 0.0)
    glow(c, 540, 900, 600, '#6E8BE0', 60)
    # bed edge + silhouette sitting facing window
    rrect(c, 60, 1420, 1020, 1560, 20, P(hexc('#121733')))
    silhouette(c, 540, 1440, 1.25, '#05060D', lean=-3, look=0)
    # phone glow in lap, small
    glow(c, 470, 1350, 120, GLOW, 70 * (0.6 + 0.4 * math.sin(t * 1.3)))
    lingrad(c, skia.Rect.MakeLTRB(-200, 1560, W + 200, H + 200), 1560, 2000, hexc('#0E1228'), hexc('#05060C'))
    motes(c, t, '#BFD3FF', 50)


def sc_heart_hands(c, t, u):
    c.drawRect(BIG, P(hexc('#0B0A18')))
    glow(c, 540, 900, 700, '#5A2A5A', 80)
    sq = ease(u)
    hx, hy = 540, 880
    pulse = 1 + 0.04 * math.sin(t * 5)
    glow(c, hx, hy, 380 * pulse, PINK, 150 * (1 - 0.4 * sq))
    hp = heart_path(hx, hy, 210 * pulse)
    c.drawPath(hp, P(hexc('#FF6F96')))
    c.drawPath(hp, P(hexc('#FFC2D3', 200), 8))
    # cracks growing as hands squeeze
    cr = skia.Path(); cr.moveTo(hx, hy - 90)
    pts = [(hx - 20, hy - 30), (hx + 25, hy + 20), (hx - 10, hy + 70), (hx + 10, hy + 150)]
    k = int(sq * len(pts))
    for p in pts[:k]:
        cr.lineTo(*p)
    if k:
        c.drawPath(cr, P(hexc('#2A0A18', 230), 9))
    # hands from bottom left/right
    for s in (-1, 1):
        c.save(); c.translate(hx + s * (330 - 90 * sq), hy + 260); c.rotate(s * (-25 + 10 * sq))
        palm = skia.Path(); palm.moveTo(0, 0)
        palm.cubicTo(-s * 40, -200, -s * 130, -260, -s * 190, -200)
        palm.cubicTo(-s * 140, -140, -s * 80, -60, -s * 60, 80)
        palm.lineTo(s * 80, 600); palm.lineTo(s * 220, 600); palm.close()
        c.drawPath(palm, P(hexc('#D8A47D')))
        for f in range(3):
            c.drawLine(-s * (70 + f * 40), -200 + f * 25, -s * (150 + f * 15), -150 + f * 40, P(hexc('#B98361'), 5))
        c.restore()


def sc_apart(c, t, u):
    c.drawRect(BIG, P(hexc('#0E1022')))
    lingrad(c, skia.Rect.MakeLTRB(-200, 0, W + 200, 1500), 0, 1500, hexc('#1B2140'), hexc('#2A2440'))
    window(c, t, 300, 300, 780, 760, 0.0, 0.6)
    rrect(c, 60, 1180, 1020, 1420, 50, P(hexc('#2A3150')))
    rrect(c, 40, 1100, 160, 1440, 40, P(hexc('#232A47')))
    rrect(c, 920, 1100, 1040, 1440, 40, P(hexc('#232A47')))
    # partner laughing (left), you lost in your phone (right)
    bounce = 8 * abs(math.sin(t * 5))
    silhouette(c, 320, 1260 - bounce, 1.0, '#E6A07A', lean=4)
    for i in range(3):
        k = (t * 0.6 + i / 3) % 1
        c.drawPath(heart_path(300 + i * 40, 850 - k * 200, 18), P(hexc('#FF8FB1', 200 * math.sin(math.pi * k))))
    silhouette(c, 760, 1260, 1.0, '#3A4370', lean=-6, look=-1)
    glow(c, 730, 1080, 150, GLOW, 90)
    rrect(c, 705, 1040, 755, 1120, 8, P(hexc('#0B0D14')))
    # desaturating veil on the right side
    c.drawRect(skia.Rect.MakeLTRB(540, -200, W + 200, H + 200), P(hexc('#0A0C18', 90 * ease(u))))
    lingrad(c, skia.Rect.MakeLTRB(-200, 1420, W + 200, H + 200), 1420, 2000, hexc('#121528'), hexc('#05060C'))


def sc_dawn(c, t, u):
    d = ease(u * 1.2)
    bedroom(c, t, d)
    person_in_bed(c, t, worried=1 - d, phone=False, eyes_open=1 - 0.8 * d)
    glow(c, 800, 600, 700, '#FFC58A', 90 * d)
    motes(c, t, '#FFE2B0', 80 * d)


def sc_together(c, t, u):
    c.drawRect(BIG, P(hexc('#2A1E2C')))
    lingrad(c, skia.Rect.MakeLTRB(-200, 0, W + 200, 1500), 0, 1500, hexc('#F3A27E'), hexc('#7A4A62'))
    glow(c, 540, 900, 520, '#FFE1A8', 180)
    c.drawCircle(540, 950, 120, P(hexc('#FFF1C9')))
    # hills
    hp = skia.Path(); hp.moveTo(-200, 1300); hp.cubicTo(200, 1150, 600, 1260, 1300, 1150); hp.lineTo(1300, 2200); hp.lineTo(-200, 2200); hp.close()
    c.drawPath(hp, P(hexc('#3A2438')))
    # couple leaning together
    silhouette(c, 470, 1300, 1.05, '#1A1020', lean=8)
    silhouette(c, 610, 1300, 1.05, '#1A1020', lean=-10)
    hearts_rise(c, t, 540, 820)


def hearts_rise(c, t, x0, y0, a=1.0):
    for i in range(6):
        k = (t * 0.3 + i / 6) % 1
        x = x0 + (i - 2.5) * 50 + 25 * math.sin(t * 2 + i)
        y = y0 - k * 420
        c.drawPath(heart_path(x, y, 20 + 6 * math.sin(i)), P(hexc('#FF8FB1', 220 * a * math.sin(math.pi * k))))


def sc_hands(c, t, u):
    c.drawRect(BIG, P(hexc('#2B1A24')))
    glow(c, 540, 960, 700, '#FFB46B', 140)
    for s in (-1, 1):
        c.save(); c.translate(540 + s * 30, 960); c.rotate(s * 6)
        arm = skia.Path(); arm.moveTo(s * 700, 300); arm.lineTo(s * 700, 120)
        arm.cubicTo(s * 300, 60, s * 120, 0, s * 40, -10)
        arm.cubicTo(-s * 20, -20, -s * 20, 60, s * 30, 80)
        arm.cubicTo(s * 150, 140, s * 400, 260, s * 700, 300); arm.close()
        c.drawPath(arm, P(hexc('#E3B08A' if s < 0 else '#C98F6A')))
        c.restore()
    glow(c, 540, 960, 160, '#FFF1C9', 120 + 40 * math.sin(t * 2))
    hearts_rise(c, t, 540, 780)


def sc_final(c, t, u):
    c.drawRect(BIG, P(hexc('#1A1222')))
    lingrad(c, skia.Rect.MakeLTRB(-200, -200, W + 200, H + 200), 0, H, hexc('#2A1A34'), hexc('#5A3448'))
    glow(c, 540, 820, 600, '#FF9DB5', 90)
    c.drawPath(heart_path(540, 640, 90 + 6 * math.sin(t * 3)), P(hexc('#FF8FB1')))
    k = ease(u * 3)
    text_center(c, 'You deserve', 540, 900, 92, hexc('#FFFFFF', 255 * k), stroke=0)
    text_center(c, 'to feel SAFE.', 540, 1010, 92, hexc('#FF8FB1', 255 * ease(u * 3 - 0.4)), stroke=0)
    k2 = ease((u - 0.45) * 4)
    text_center(c, 'Send this to someone', 540, 1180, 46, hexc('#FFFFFF', 210 * k2), TF_XB)
    text_center(c, 'who overthinks.', 540, 1240, 46, hexc('#FFFFFF', 210 * k2), TF_XB)


# ------------------------------------------------------------------ shots & subtitles
FULL = (540, 960, 1.0)
SHOTS = [
    [(sc_bed_wide, (480, 1110, 1.5), (440, 1110, 1.7)), (sc_bed_close, (340, 1090, 2.6), (360, 1090, 3.0))],
    [(sc_phone('waiting'), (540, 960, 1.0), (540, 980, 1.08))],
    [(sc_phone('distant'), (540, 960, 1.02), (540, 1000, 1.1)), (sc_bed_close, (340, 1080, 3.0), (340, 1090, 3.3))],
    [(sc_phone('tired'), (540, 960, 1.0), (540, 960, 1.06)), (sc_scenarios, FULL, (540, 960, 1.05))],
    [(sc_nothing_wrong, FULL, (540, 960, 1.04))],
    [(sc_phone('punct'), (520, 900, 1.15), (500, 860, 1.3)), (sc_phone('scroll'), FULL, (540, 960, 1.05))],
    [(sc_phone('typing'), (540, 1480, 1.3), (540, 1500, 1.4)), (sc_ceiling, (540, 900, 1.1), (540, 760, 1.4))],
    [(sc_window_sit, (540, 1000, 1.1), (540, 1060, 1.2)), (sc_heart_hands, FULL, (540, 900, 1.1)), (sc_apart, (540, 1100, 1.1), (560, 1150, 1.2))],
    [(sc_dawn, (600, 1000, 1.25), (560, 1000, 1.1))],
    [(sc_together, (540, 1100, 1.15), (540, 1050, 1.0)), (sc_final, FULL, (540, 960, 1.04))],
]

CHUNKS = [
    ["Do you know what's EXHAUSTING", "about being too ATTACHED", "to someone?", "Your mind literally", "NEVER gets a break."],
    ["They take a little", "longer to REPLY?", "You wonder if", "you did something WRONG."],
    ["They seem a little DISTANT?", "You start questioning", "whether they still", "LOVE you the same way."],
    ["They say they're TIRED?", "Somehow, your brain", "creates a HUNDRED", "different SCENARIOS."],
    ["And the WORST part?", "Sometimes, absolutely", "NOTHING is wrong."],
    ["But you're analysing", "every TEXT,", "every PUNCTUATION mark,", "every change in their TONE."],
    ["You constantly", "need REASSURANCE,", "even when everything", "seems perfectly FINE."],
    ["Because when you get", "deeply ATTACHED to someone,", "you can become so AFRAID", "of LOSING them", "that you forget to", "actually ENJOY", "having them in your life."],
    ["But loving someone", "shouldn't mean constantly", "being AFRAID", "that they'll stop loving you."],
    ["You deserve a relationship", "where you feel SAFE,", "not one where your mind", "is always at WAR with itself."],
]


def weight(s):
    w = len(s.replace(' ', '')) + 1.5 * s.count(' ')
    w += 6 * s.count('…') + 4 * len(re.findall(r'[.?]$', s)) + 2.5 * s.count(',')
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
HL = hexc('#FF8FB1'); WHITE = hexc('#FFFFFF')


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
    f = skia.Font(TF_XB, 38); s = 'FOR THE OVERTHINKERS'
    tw = f.measureText(s)
    rrect(c, W / 2 - tw / 2 - 34, 290, W / 2 + tw / 2 + 34, 370, 40, P(hexc('#FF8FB1', 235 * a)))
    c.drawString(s, W / 2 - tw / 2, 344, f, P(hexc('#1A0F18', 255 * a)))


yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)
VIG = np.clip(1 - 0.55 * np.clip(r - 0.55, 0, 1) ** 1.3, 0, 1)[..., None].astype(np.float32)
GR = [(rng.standard_normal((H // 2, W // 2, 1)) * 5).repeat(2, 0).repeat(2, 1).astype(np.float32) for _ in range(4)]
buf = np.zeros((H, W, 4), np.uint8)
surface = skia.Surface(buf)
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
    if t < FINAL_START:
        for st, en, txt in subs:
            if st <= t < en:
                k = (t - st) / 0.16
                sc = 1.0 if k >= 1 else (0.8 + 0.3 * k if k < 0.7 else 1.01 - (k - 0.7) * 0.03)
                draw_sub(c, txt, 1330, sc)
                break
    else:
        for st, en, txt in subs:
            if st <= t < en:
                draw_sub(c, txt, 1560, 0.8)
                break
    if 0.3 < t < LINES[1]['start'] - 0.12:
        badge(c, min(1, (t - 0.3) / 0.25))
    a = buf[..., :3].astype(np.float32) * VIG + GR[fi % 4]
    # soft dip-to-dark crossfade at section starts (cinematic) instead of hard flash
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
        sheet.save('ot/preview.jpg', quality=85)
        sys.exit()
    nf = int(TOTAL * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', 'ot/mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'ot/overthinking_raw.mp4'], stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait(); print('done')
