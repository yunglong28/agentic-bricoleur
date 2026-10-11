"""The Agentic Bricoleur, second state: the structures collide, the red is cut and torn,
and every line changes ink when it crosses into the red.
Usage: python3 bricoleur2.py OUTDIR [SEED]
"""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from bricoleur import (W, H, S, PAPER, RED, INK, SPR, sprite, sprite_size, line, arrow, circ, rect,
                       diamond, dashed, blob, bez, smooth_noise, fbm, finish, tangle, mast, poly_rot)

OUT = sys.argv[1]
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
os.makedirs(OUT, exist_ok=True)
P = lambda *v: tuple(x * S for x in v)          # design px → canvas px


def M():
    m = Image.new('L', (W, H), 0)
    return m, ImageDraw.Draw(m)


def b(m):
    return np.asarray(m) > 127


def rough(m, nr, amt=0.55, speck=0.18):
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(2.2 * S)), np.float32) / 255
    v = a + (nr.random(a.shape, np.float32) - 0.5) * amt - (smooth_noise(nr, W, H, (220, 275)) > 1 - speck) * 0.35 * a
    return v > 0.5


def torn(m, nr, edge=14):
    """A red field with a torn edge and a stochastic screen where it meets the paper."""
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(edge * S)), np.float32) / 255
    wob = (smooth_noise(nr, W, H, (40, 50)) - 0.5) * 0.5
    return (a + wob) > nr.random(a.shape, np.float32) * 0.9 + 0.05


def shift(mask, dx, dy):
    return np.roll(np.roll(mask, int(dy * S), 0), int(dx * S), 1)


def compose(field, layers, nr, name):
    a = np.empty((H, W, 3), np.uint8); a[:] = PAPER; a[field] = RED
    for mask, on_paper, on_red in layers:
        if on_paper is not None: a[mask & ~field] = on_paper
        if on_red is not None: a[mask & field] = on_red
    finish(Image.fromarray(a), nr, name)

# ----------------------------------------------------------------- the vocabulary


def xerox(nr, yc, sig, base=4, lo=0.27, hi=0.33):
    n = fbm(nr, W, H, base, 6)
    yy = np.linspace(0, 1, H)[:, None]
    v = n * np.exp(-((yy - yc) / sig) ** 2) * (0.6 + 0.6 * smooth_noise(nr, W, H, (5, 6)))
    fine = nr.random((H, W), np.float32)
    return (np.abs(v - hi) < 0.012) | (np.abs(v - lo) < 0.008) | ((v > hi + 0.07) & (fine < (v - hi - 0.07) * 9)) | ((v > hi + 0.03) & (v < hi + 0.07) & (fine < 0.08))


def flowchart(d, ox, oy, k, rng, names=('alien', 'heart', 'ship')):
    q = lambda x, y: (ox + x * k * S, oy + y * k * S)
    w = max(3, int(2 * k))
    for y0 in (0, 86):
        d.rectangle([*q(-34, y0), *q(34, y0 + 50)], outline=255, width=w)
    arrow(d, q(-8, 50), q(-8, 86), 255, w); arrow(d, q(8, 86), q(8, 50), 255, w)
    arrow(d, q(0, 136), q(0, 180), 255, w)
    diamond(d, q(0, 208), 40 * k * S, 28 * k * S, 255, w)
    line(d, [q(0, 236), q(0, 530)], 255, w)
    line(d, [q(60, 206), q(82, 206), q(82, 568)], 255, w)
    for i, y in enumerate([308, 410, 533]):
        c = q(-84, y)
        circ(d, c, 42 * k * S, 255, w)
        sw, sh = sprite_size(names[i], int(5 * k * S))
        sprite(d, names[i], c[0] - sw // 2, c[1] - sh // 2, int(5 * k * S), 255)
        d.rectangle([*q(-30, y - 18), *q(2, y + 14)], outline=255, width=w)
        arrow(d, q(-42, y - 2), q(-30, y - 2), 255, w)
        line(d, [q(2, y - 2), q(82, y - 2)], 255, w)
        arrow(d, q(-126, y - 10), q(-184, y - 10), 255, w); arrow(d, q(-184, y + 6), q(-126, y + 6), 255, w)
        if i < 2: line(d, [q(-84, y + 42), q(-84, y + (60 if i == 0 else 81))], 255, w)
    blob(d, *q(-210, 410), 44 * k * S, 190 * k * S, rng, 255, w)
    for nm, yy in [('coin', 290), ('key', 360), ('T', 438), ('hero', 500)]:
        sprite(d, nm, *q(-228, yy), int(3 * k * S), 255)
    return q


def level(d, gx, gy, t, w=3):
    for i in range(14): d.rectangle([gx + i * t, gy, gx + (i + 1) * t, gy + t], outline=255, width=w)
    for (i, j, n) in [(2, 5, 3), (7, 9, 4), (1, 13, 2), (6, 15, 3)]:
        for k in range(n): d.rectangle([gx + (i + k) * t, gy - j * t, gx + (i + k + 1) * t, gy - j * t + t], outline=255, width=w)
    d.rectangle([gx + 11 * t, gy - 3 * t, gx + 13 * t, gy], outline=255, width=w)
    d.rectangle([gx + 10.7 * t, gy - 3.6 * t, gx + 13.3 * t, gy - 3 * t], outline=255, width=w)
    for k in range(8): line(d, [(gx + 5 * t, gy - k * t), (gx + 6 * t, gy - k * t)], 255, 2)
    line(d, [(gx + 5 * t, gy), (gx + 5 * t, gy - 8 * t)], 255, w); line(d, [(gx + 6 * t, gy), (gx + 6 * t, gy - 8 * t)], 255, w)
    px = max(2, int(t / 7))
    sprite(d, 'hero', gx + 8 * t, gy - 7 * px, px, 255)
    sprite(d, 'coin', gx + 2.2 * t, gy - 7 * t, px, 255); sprite(d, 'coin', gx + 7.6 * t, gy - 11 * t, px, 255)
    sprite(d, 'alien', gx + 1.2 * t, gy - 15 * t - 8 * px, px, 255)
    return (gx + 8.5 * t, gy - 8.5 * t)


def mashup(d, ox, oy, px):
    sprite(d, 'alien', ox + 2 * px, oy, px, 255)
    sprite(d, 'heart', ox + 4 * px, oy + 7 * px + 6 * S, px, 255)
    sprite(d, 'sword', ox + 11 * px + 6 * S, oy + 6 * px, px, 255)
    sprite(d, 'ship', ox + 1 * px, oy + 13 * px + 12 * S, px, 255)
    sprite(d, 'L', ox - 1 * px - 6 * S, oy + 8 * px, px, 255)
    sprite(d, 'I', ox + 10 * px, oy + 17 * px + 18 * S, px, 255)


def datasheet(d, rng, x0, x1, y0, y1, n_lead=30, n_blocks=8):
    for _ in range(n_lead):
        y = rng.uniform(y0, y1) * S; a = rng.uniform(x0, x0 + (x1 - x0) * 0.4) * S; e = rng.uniform(x0 + (x1 - x0) * 0.6, x1) * S
        line(d, [(a, y), (e, y)], 255, 2); d.ellipse([a - 4, y - 4, a + 4, y + 4], fill=255)
    for _ in range(n_blocks):
        bx = rng.uniform(x0 + (x1 - x0) * 0.5, x1 - 60) * S; by = rng.uniform(y0, y1 - 100) * S
        for k in range(rng.randint(4, 12)):
            d.rectangle([bx, by + k * 9 * S, bx + rng.uniform(20, 70) * S, by + k * 9 * S + 4 * S], fill=255)


def wing(d, root, ctrl, tip, flip=1, scale=1.0):
    bone = bez(root, ctrl, tip, 60)
    for i, (bx, by) in enumerate(bone[4:], 4):
        t = i / len(bone)
        a = (-0.35 + t * 1.25) if flip > 0 else (math.pi + 0.35 - t * 1.25)
        L = (110 + 230 * t) * S * scale
        p1 = (bx + L * math.cos(a), by + L * math.sin(a))
        line(d, bez((bx, by), (bx + L * .5 * math.cos(a - .25 * flip), by + L * .5 * math.sin(a - .25 * flip)), p1, 20), 255, 2 if i % 2 else 3)
    line(d, bone, 255, 5)
    for row in range(3):
        for i in range(6, len(bone) - 2, 3):
            bx, by = bone[i]; r = (26 - row * 4) * S * scale
            ox, oy = bx + flip * (row + 1) * 26 * S * scale, by + (row + 1) * 22 * S * scale
            d.arc([ox - r, oy - r, ox + r, oy + r], 20, 160, fill=255, width=3)


def ascii_mask(nr, rng, shapes, cell=12):
    """Density marks, no letters: a body printed the way a terminal would print it."""
    dens = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(dens)
    shapes(dd)
    dn = np.asarray(dens.filter(ImageFilter.GaussianBlur(9 * S)), np.float32) / 255
    shade = fbm(nr, W, H, 5, 4)
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', cell * S)
    ramp = " .,:;-=+*#%@"
    m, d = M(); cw, ch = cell * 0.61 * S, cell * 1.04 * S
    y = 0.0
    while y < H - ch:
        x = 0.0
        while x < W - cw:
            v = dn[int(y + ch / 2), int(x + cw / 2)]
            if v > 0.04:
                v = min(1, v * (0.75 + 0.6 * shade[int(y), int(x)]))
                c = ramp[min(len(ramp) - 1, int(v * len(ramp)))]
                if c != ' ': d.text((x, y), c, font=font, fill=255)
            x += cw
        y += ch
    return b(m)


def hexplan(d, C, R, rng, w=3):
    ang = [math.pi / 6 + k * math.pi / 3 - math.pi / 2 + math.pi / 6 for k in range(7)]
    for RR in (R, R - 15 * S):
        pts = [(C[0] + RR * math.cos(a), C[1] + RR * math.sin(a)) for a in ang]
        for k in range(6):
            p, q = pts[k], pts[k + 1]
            if k == 3:
                line(d, [p, (p[0] + (q[0] - p[0]) * .35, p[1] + (q[1] - p[1]) * .35)], 255, w)
                line(d, [(p[0] + (q[0] - p[0]) * .6, p[1] + (q[1] - p[1]) * .6), q], 255, w)
            else:
                line(d, [p, q], 255, w)
    cab = []; Rc = R - 45 * S
    for k in range(6):
        a0, a1 = ang[k], ang[k + 1]
        for f in (0.3, 0.7):
            if k == 3 and f == 0.3: continue
            p = (C[0] + Rc * ((1 - f) * math.cos(a0) + f * math.cos(a1)), C[1] + Rc * ((1 - f) * math.sin(a0) + f * math.sin(a1)))
            line(d, poly_rot(p[0], p[1], 78 * S * R / (285 * S), 20 * S * R / (285 * S), math.atan2(math.sin(a1) - math.sin(a0), math.cos(a1) - math.cos(a0))), 255, w)
            cab.append(p)
    players = []; k_ = R / (285 * S)
    for k in range(7):
        a = -math.pi / 2 + k * 2 * math.pi / 7 + rng.uniform(-.1, .1)
        p = (C[0] + 140 * S * k_ * math.cos(a), C[1] + 140 * S * k_ * math.sin(a))
        circ(d, p, 22 * S * k_, 255, w); circ(d, p, 4 * S, 255, 2)
        for rr, sp in ((32 * S * k_, 1.6), (38 * S * k_, .9)):
            st = math.degrees(a) + 90 + rng.uniform(-30, 30)
            d.arc([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], st, st + math.degrees(sp), fill=255, width=w)
        sa = a + math.pi + rng.uniform(-.6, .6)
        d.rectangle([p[0] + 30 * S * k_ * math.cos(sa) - 8 * S, p[1] + 30 * S * k_ * math.sin(sa) - 6 * S,
                     p[0] + 30 * S * k_ * math.cos(sa) + 8 * S, p[1] + 30 * S * k_ * math.sin(sa) + 6 * S], outline=255, width=2)
        players.append(p)
    return players, cab


def panel(d, x, y, k=1.0):
    s = lambda v: v * S * k
    d.rounded_rectangle([x, y, x + s(600), y + s(330)], s(36), outline=255, width=int(s(14)))
    jx, jy = x + s(150), y + s(165)
    d.ellipse([jx - s(85), jy - s(85), jx + s(85), jy + s(85)], outline=255, width=int(s(12)))
    d.ellipse([jx - s(46), jy - s(46), jx + s(46), jy + s(46)], fill=255)
    for i in range(8):
        a = i * math.pi / 4
        d.line([(jx + s(98) * math.cos(a), jy + s(98) * math.sin(a)), (jx + s(116) * math.cos(a), jy + s(116) * math.sin(a))], fill=255, width=int(s(9)))
    for r_ in range(2):
        for c_ in range(3):
            bx, by = x + s(330 + c_ * 92 + r_ * 26), y + s(105 + r_ * 110)
            if (r_, c_) == (0, 1): d.ellipse([bx - s(36), by - s(36), bx + s(36), by + s(36)], outline=255, width=int(s(11)))
            else: d.ellipse([bx - s(36), by - s(36), bx + s(36), by + s(36)], fill=255)


def dpad(d, cx, cy, a_, b_, inner):
    d.rectangle([cx - a_, cy - b_, cx + a_, cy + b_], fill=255); d.rectangle([cx - b_, cy - a_, cx + b_, cy + a_], fill=255)
    d.rectangle([cx - a_ + inner, cy - b_ + inner, cx + a_ - inner, cy + b_ - inner], fill=0)
    d.rectangle([cx - b_ + inner, cy - a_ + inner, cx + b_ - inner, cy + a_ - inner], fill=0)

# ----------------------------------------------------------------- plates
FLIP = (INK, PAPER)          # black on paper, knocked out of the red
SIGNAL = (RED, INK)          # red on paper, black where it crosses the red
GHOST = (RED, None)          # misregistered red pass, only seen on paper


def plate_loop():
    rng = random.Random(SEED + 11); nr = np.random.default_rng(SEED + 11)
    f, fd = M()
    fd.polygon([P(0, 1280), P(0, 900), P(1024, 520), P(1024, 1280)], fill=255)
    fd.ellipse([*P(600, 70), *P(940, 410)], fill=255)
    fd.rectangle([*P(318, 0), *P(380, 600)], fill=255)
    fd.rectangle([*P(0, 1080), *P(1024, 1280)], fill=0)
    fd.rectangle([*P(60, 1120), *P(500, 1250)], fill=255)
    field = torn(f, nr, 10)
    clouds = xerox(nr, 0.68, 0.16)
    t, td = M(); tangle(td, *P(770, 240), 160 * S, rng, 22, 255)
    fc, fcd = M(); q = flowchart(fcd, *P(330, 60), 1.15, rng)
    loop, ld = M()
    line(ld, [P(150, 690), P(150, 760), P(40, 760), P(40, 30), P(330, 30), P(330, 52)], 255, 4)
    line(ld, [P(150, 760), P(150, 1010), P(420, 1010)], 255, 4); arrow(ld, P(400, 1010), P(440, 1010), 255, 4)
    line(ld, [P(410, 200), P(610, 200)], 255, 4); arrow(ld, P(590, 200), P(625, 200), 255, 4)
    ms, msd = M(); mashup(msd, *P(470, 610), 24 * S)
    lv, lvd = M(); level(lvd, *P(80, 1210), 18 * S, 3)
    ds, dsd = M(); datasheet(dsd, rng, 780, 1000, 480, 1000, 20, 6)
    fcb = b(fc)
    compose(field, [(clouds, *FLIP), (b(t), *FLIP), (shift(fcb, 6, 5), *GHOST), (fcb, *FLIP),
                    (b(ds), *FLIP), (b(lv), *FLIP), (b(loop), *SIGNAL), (rough(ms, nr), RED, INK)], nr, '01-the-loop.png')


def plate_zoom():
    rng = random.Random(SEED + 12); nr = np.random.default_rng(SEED + 12)
    C, R = P(640, 360), 300 * S
    f, fd = M()
    fd.pieslice([C[0] - R, C[1] - R, C[0] + R, C[1] + R], 200, 20, fill=255)
    fd.rectangle([*P(0, 760), *P(540, 1280)], fill=255)
    for i in range(9):
        x = 560 + i * 48
        if rng.random() < .6: fd.rectangle([*P(x, 690 - rng.randint(0, 4) * 48), *P(x + 44, 1280)], fill=255)
    field = torn(f, nr, 6)
    tg, tgd = M(); tangle(tgd, *C, R * .95, rng, 30, 255)
    cm = Image.new('L', (W, H), 0); ImageDraw.Draw(cm).ellipse([C[0] - R + 6, C[1] - R + 6, C[0] + R - 6, C[1] + R - 6], fill=255)
    tg = b(tg) & b(cm)
    rim, rd = M(); circ(rd, C, R, 255, 4); circ(rd, C, R - 14 * S, 255, 2)
    lv, lvd = M(); sel = level(lvd, *P(40, 900), 34 * S, 4)
    sl, sld = M(); circ(sld, sel, 30 * S, 255, 5)
    for s_ in (-1, 1):
        a = math.atan2(C[1] - sel[1], C[0] - sel[0]) + s_ * math.pi / 2
        p0 = (sel[0] + 30 * S * math.cos(a), sel[1] + 30 * S * math.sin(a))
        bb = math.atan2(sel[1] - C[1], sel[0] - C[0])
        dashed(sld, p0, (C[0] + R * math.cos(bb - s_ * 1.0), C[1] + R * math.sin(bb - s_ * 1.0)), 255, 3, 7 * S, 5 * S)
    sk, skd = M(); T = 37 * S; base = H - 60 * S
    for i, h in enumerate([3, 3, 5, 5, 2, 2, 2, 7, 7, 4, 4, 4, 6, 1, 1, 3, 3, 8, 8, 2, 5, 5]):
        x = 230 * S + i * T
        if x > W - 20 * S: break
        for j in range(h):
            box = [x, base - (j + 1) * T + 5 * S, x + T - 5 * S, base - j * T]
            if (i * 7 + j * 3) % 11 == 0: skd.rectangle(box, outline=255, width=6 * S)
            else: skd.rectangle(box, fill=255)
    clouds = xerox(nr, 0.18, 0.09, 5)
    mt, mtd = M(); mast(mtd, 960 * S, 1180 * S, 560 * S, 70 * S, 26 * S, 255)
    lvb = b(lv)
    compose(field, [(clouds, *FLIP), (b(mt), *FLIP), (tg, *FLIP), (b(rim), INK, INK), (shift(lvb, -5, 6), *GHOST), (lvb, *FLIP),
                    (b(sl), *SIGNAL), (rough(sk, nr), RED, INK)], nr, '02-the-tile.png')


def plate_arcade():
    rng = random.Random(SEED + 13); nr = np.random.default_rng(SEED + 13)
    C, R = P(500, 400), 330 * S
    f, fd = M()
    hexpts = [(C[0] + (R - 8 * S) * math.cos(math.pi / 3 * k + math.pi / 6 - math.pi / 2 + math.pi / 6 + math.pi / 6), C[1] + (R - 8 * S) * math.sin(math.pi / 3 * k + math.pi / 6 - math.pi / 2 + math.pi / 6 + math.pi / 6)) for k in range(6)]
    fd.polygon(hexpts, fill=255)
    fd.polygon([P(0, 0), P(560, 0), P(380, 1280), P(0, 1280)], fill=0)
    fd.rectangle([*P(0, 900), *P(640, 1280)], fill=255)
    fd.rectangle([*P(420, 820), *P(1024, 1190)], fill=255)
    fd.rectangle([*P(560, 960), *P(980, 1120)], fill=0)
    field = torn(f, nr, 8)
    hx, hxd = M(); players, cab = hexplan(hxd, C, R, rng, 4)
    wi, wid = M()
    for p in players: line(wid, [C, p], 255, 3)
    for p in cab: dashed(wid, C, p, 255, 3, 5 * S, 6 * S)
    wid.ellipse([C[0] - 18 * S, C[1] - 18 * S, C[0] + 18 * S, C[1] + 18 * S], fill=255); circ(wid, C, 30 * S, 255, 4)
    tg, tgd = M(); tangle(tgd, *P(170, 1060), 150 * S, rng, 18, 255)
    pn, pnd = M(); panel(pnd, *P(380, 870), 0.98)
    clouds = xerox(nr, 0.08, 0.07, 5)
    mt, mtd = M(); mast(mtd, 70 * S, 880 * S, 120 * S, 70 * S, 24 * S, 255)
    hxb = b(hx)
    compose(field, [(clouds, *FLIP), (b(mt), *FLIP), (shift(hxb, 6, 6), *GHOST), (hxb, *FLIP), (b(tg), *FLIP),
                    (b(wi), *SIGNAL), (rough(pn, nr), *FLIP)], nr, '03-the-room.png')


def plate_angel():
    rng = random.Random(SEED + 14); nr = np.random.default_rng(SEED + 14)
    f, fd = M()
    fd.rectangle([*P(400, 0), *P(700, 1280)], fill=255)
    fd.polygon([P(80, 360), P(200, 340), P(200, 860), P(80, 830)], fill=255)
    fd.rectangle([*P(700, 1010), *P(1024, 1280)], fill=255)
    fd.rectangle([*P(0, 0), *P(260, 150)], fill=255)
    field = torn(f, nr, 7)
    ds, dsd = M(); datasheet(dsd, rng, 600, 1000, 70, 1220, 46, 12)

    def body(dd):
        dd.polygon([P(420, 450), P(395, 500), P(360, 545), P(385, 556), P(380, 585), P(395, 612), P(425, 650), P(480, 668), P(530, 640), P(540, 470)], fill=95)
        dd.ellipse([*P(420, 380), *P(620, 640)], fill=255)
        dd.polygon([P(470, 640), P(460, 720), P(560, 720), P(560, 620)], fill=120)
        dd.polygon([P(470, 640), P(420, 700), P(360, 1000), P(420, 1260), P(760, 1260), P(740, 860), P(650, 700), P(560, 640)], fill=150)
        dd.polygon([P(420, 760), P(300, 940), P(230, 1010), P(270, 1040), P(360, 980), P(470, 830)], fill=110)
        dd.ellipse([*P(418, 520), *P(438, 534)], fill=255)
    fig = ascii_mask(nr, rng, body)
    wg, wgd = M()
    wing(wgd, P(640, 760), P(700, 360), P(990, 250), 1)
    wing(wgd, P(560, 740), P(470, 300), P(150, 120), -1, 0.8)
    hl, hld = M()
    for o in (0, 9 * S): hld.ellipse([390 * S - o, 330 * S - o / 3, 600 * S + o, 380 * S + o / 3], outline=255, width=4)
    crt, cd = M(); mx = 80 * S
    line(cd, [(mx, 360 * S), (mx + 120 * S, 340 * S), (mx + 140 * S, 340 * S), (mx + 140 * S, 860 * S), (mx + 120 * S, 860 * S), (mx, 830 * S), (mx, 360 * S)], 255, 4)
    cd.rectangle([mx - 30 * S, 860 * S, mx + 180 * S, 890 * S], outline=255, width=4)
    line(cd, [(mx + 40 * S, 890 * S), (mx + 20 * S, 1010 * S), (mx + 160 * S, 1010 * S), (mx + 130 * S, 890 * S)], 255, 4)
    kx, ky = 150 * S, 1030 * S
    line(cd, [(kx, ky), (kx + 260 * S, ky - 20 * S), (kx + 300 * S, ky + 50 * S), (kx + 30 * S, ky + 80 * S), (kx, ky)], 255, 4)
    for r_ in range(4):
        for c_ in range(10):
            x = kx + 20 * S + c_ * 24 * S + r_ * 6 * S; yv = ky + 10 * S + r_ * 15 * S - c_ * 1.8 * S
            cd.rectangle([x, yv, x + 16 * S, yv + 9 * S], outline=255, width=2)
    mz, mzd = M()
    for i in range(9):
        for j in range(30):
            if rng.random() < .45:
                x = mx + 14 * S + i * 10 * S; y = 372 * S + j * 15 * S - i * 1.5 * S
                mzd.rectangle([x, y, x + 8 * S, y + 12 * S], fill=255)
    bm, bmd = M()
    for _ in range(420):
        y = rng.gauss(520, 55) * S; x0 = (mx + 140 * S) + rng.uniform(0, 40) * S
        bmd.line([(x0, y), (rng.uniform(300, 470) * S, y + rng.uniform(-30, 30) * S)], fill=255, width=rng.choice([2, 2, 3, 5]))
    for _ in range(70):
        x = rng.uniform(240, 460) * S; y = rng.gauss(520, 50) * S
        bmd.rectangle([x, y, x + rng.uniform(6, 30) * S, y + rng.uniform(3, 10) * S], fill=255)
    sp, spd = M()
    for nm, x, y, px in [('alien', 30, 40, 9), ('heart', 160, 60, 8), ('T', 820, 1080, 18), ('chest', 900, 1170, 9)]:
        sprite(spd, nm, x * S, y * S, px * S, 255)
    compose(field, [(b(ds), *FLIP), (shift(b(wg), 5, 4), *GHOST), (b(wg), *FLIP), (fig, *FLIP), (b(hl), *SIGNAL), (b(crt), *FLIP),
                    (b(mz), PAPER, PAPER), (b(bm), *SIGNAL), (b(sp), *FLIP)], nr, '04-the-operator.png')


def plate_rig():
    rng = random.Random(SEED + 15); nr = np.random.default_rng(SEED + 15)
    f, fd = M()
    fd.ellipse([*P(250, 300), *P(780, 830)], fill=255)
    fd.polygon([P(0, 1050), P(1024, 1000), P(1024, 1280), P(0, 1280)], fill=255)
    for nm, x, y, px in [('T', 60, 100, 60), ('S', 760, 40, 52), ('L', 600, 860, 46), ('O', 40, 820, 50)]:
        sprite(fd, nm, x * S, y * S, px * S, 255)
    field = torn(f, nr, 5)
    clouds = xerox(nr, 0.55, 0.22)
    m1, m1d = M()
    p1 = mast(m1d, 190 * S, 1120 * S, 300 * S, 120 * S, 40 * S, 255); p2 = mast(m1d, 840 * S, 1160 * S, 210 * S, 150 * S, 50 * S, 255)
    for pts, side in ((p1, -1), (p2, 1)):
        for k in rng.sample(range(2, len(pts) - 1), 5):
            q = pts[k][0] if side < 0 else pts[k][1]
            e = (q[0] + side * rng.uniform(50, 120) * S, q[1] + rng.uniform(-40, 40) * S)
            line(m1d, [q, e, (e[0] + side * 30 * S, e[1])], 255, 2)
    line(m1d, [P(60, 1120), P(980, 1160)], 255, 5)
    for k in range(12):
        x = (260 + k * 45) * S
        line(m1d, [(x, 1123 * S + k * 2 * S), (x + 30 * S, 1080 * S + k * 2 * S), (x + 60 * S, 1126 * S + k * 2 * S)], 255, 3)
    cx, cy = P(512, 560)
    dp, dpd = M(); dpad(dpd, cx, cy, 230 * S, 78 * S, 22 * S)
    inside, ind = M(); ind.rectangle([cx - 200 * S, cy - 50 * S, cx + 200 * S, cy + 50 * S], fill=255); ind.rectangle([cx - 50 * S, cy - 200 * S, cx + 50 * S, cy + 200 * S], fill=255)
    tg, tgd = M(); tangle(tgd, cx, cy, 210 * S, rng, 18, 255)
    tgi = b(tg) & b(inside); clouds_out = clouds & ~b(inside)
    sp, spd = M()
    for nm, (x, y) in [('alien', (cx - 175 * S, cy - 14 * S)), ('coin', (cx + 120 * S, cy - 14 * S)), ('heart', (cx - 14 * S, cy - 165 * S)), ('chest', (cx - 16 * S, cy + 125 * S))]:
        sprite(spd, nm, x, y, 4 * S, 255)
    wg, wgd = M()
    wing(wgd, (cx + 40 * S, cy - 240 * S), P(700, 120), P(1000, 120), 1, 0.7)
    wing(wgd, (cx - 40 * S, cy - 240 * S), P(320, 120), P(20, 120), -1, 0.7)
    bg = np.zeros((H, W), bool)
    m1b = b(m1)
    compose(field, [(clouds_out, *FLIP), (shift(m1b, 6, 5), *GHOST), (m1b, *FLIP), (b(wg), *FLIP),
                    (b(inside), PAPER, PAPER), (tgi, INK, INK), (rough(dp, nr, .35, .05), *FLIP), (b(sp), RED, RED)], nr, '05-the-rig.png')


for fn in (plate_loop, plate_zoom, plate_arcade, plate_angel, plate_rig):
    fn()
