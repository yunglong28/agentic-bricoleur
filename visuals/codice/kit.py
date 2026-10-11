"""The Agentic Bricoleur, second state: the structures collide, the red is cut and torn,
and every line changes ink when it crosses into the red.
Usage: python3 bricoleur2.py OUTDIR [SEED]
"""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from bricoleur import (W, H, S, PAPER, RED, INK, SPR, sprite, sprite_size, line, arrow, circ, rect,
                       diamond, dashed, blob, bez, smooth_noise, fbm, finish, tangle, mast, poly_rot)

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
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

