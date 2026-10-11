"""The Agentic Bricoleur — five plates, white/red paper, black ink, no text.
Usage: python3 bricoleur.py OUTDIR [SEED]
"""
import math, random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2
W, H = 1024 * S, 1280 * S
PAPER = (236, 234, 228)
RED = (252, 58, 36)
INK = (24, 22, 20)
LW = 3
SPLIT = int(H * 0.615)

OUT = sys.argv[1]
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- sprites
SPR = {
    'alien': ["...XXXXX...", ".XXXXXXXXX.", "XX..XXX..XX", "XXXXXXXXXXX",
              ".X.XX.XX.X.", "X.........X", ".X.......X."],
    'heart': [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
    'coin':  ["..XXX..", ".X...X.", "X..X..X", "X..X..X", "X..X..X", ".X...X.", "..XXX.."],
    'hero':  ["..XXX..", "..XXX..", "...X...", ".XXXXX.", "X.XXX.X", "..X.X..", ".XX.XX."],
    'key':   [".XXX......", "X...XXXXXX", "X...X..X.X", ".XXX......"],
    'sword': [".......XX", "......XXX", ".....XXX.", "X...XXX..", ".X.XXX...",
              "..XXX....", ".XXX.X...", "XX....X.."],
    'ship':  ["....X....", "...XXX...", "...XXX...", ".X.XXX.X.", "XXXXXXXXX",
              "XX.XXX.XX", "X...X...X"],
    'T': ["XXX", ".X."], 'S': [".XX", "XX."], 'L': ["X..", "XXX"], 'I': ["XXXX"], 'O': ["XX", "XX"],
    'chest': ["XXXXXXXX", "X......X", "XXXXXXXX", "X..XX..X", "X......X", "XXXXXXXX"],
}


def sprite(d, name, x, y, px, fill=INK, outline=False):
    for j, row in enumerate(SPR[name]):
        for i, c in enumerate(row):
            if c == 'X':
                box = [x + i * px, y + j * px, x + (i + 1) * px - 1, y + (j + 1) * px - 1]
                if outline:
                    d.rectangle(box, outline=fill, width=max(2, px // 8))
                else:
                    d.rectangle(box, fill=fill)


def sprite_size(name, px):
    return len(SPR[name][0]) * px, len(SPR[name]) * px

# ---------------------------------------------------------------- linework


def line(d, pts, fill=INK, w=LW):
    d.line(pts, fill=fill, width=w, joint='curve')


def arrow(d, p0, p1, fill=INK, w=LW, head=13 * S // 2):
    line(d, [p0, p1], fill, w)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-1, 1):
        b = a + math.pi - s * 0.42
        line(d, [p1, (p1[0] + head * math.cos(b), p1[1] + head * math.sin(b))], fill, w)


def circ(d, c, r, fill=INK, w=LW):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=fill, width=w)


def rect(d, x, y, w_, h_, fill=INK, w=LW):
    d.rectangle([x, y, x + w_, y + h_], outline=fill, width=w)


def diamond(d, c, rx, ry, fill=INK, w=LW):
    x, y = c
    line(d, [(x, y - ry), (x + rx, y), (x, y + ry), (x - rx, y), (x, y - ry)], fill, w)


def dashed(d, p0, p1, fill=INK, w=2, dash=10, gap=8):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    t = 0
    while t < L:
        e = min(L, t + dash)
        d.line([(p0[0] + ux * t, p0[1] + uy * t), (p0[0] + ux * e, p0[1] + uy * e)], fill=fill, width=w)
        t += dash + gap


def blob(d, cx, cy, rx, ry, rng, fill=INK, w=LW, k=5):
    ph = [rng.uniform(0, 6.3) for _ in range(k)]
    am = [rng.uniform(0.02, 0.09) / (i + 1) ** 0.6 for i in range(k)]
    pts = []
    for t in np.linspace(0, 2 * math.pi, 240):
        r = 1 + sum(am[i] * math.sin((i + 2) * t + ph[i]) for i in range(k))
        pts.append((cx + rx * r * math.cos(t), cy + ry * r * math.sin(t)))
    pts.append(pts[0])
    line(d, pts, fill, w)


def bez(p0, p1, p2, n=40):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]

# ---------------------------------------------------------------- textures


def smooth_noise(rng, w, h, cells):
    a = rng.random((cells[1], cells[0])).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255


def fbm(rng, w, h, base=6, oct=5):
    out = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(oct):
        c = base * 2 ** o
        out += amp * smooth_noise(rng, w, h, (c, max(2, int(c * h / w))))
        tot += amp; amp *= 0.5
    return out / tot


def crayon(img, mask, color, rng, rough=0.55, speck=0.18):
    """Fill a mask the way a wax crayon/overinked press would: chewed edges, open specks."""
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(2.2 * S)), np.float32) / 255
    n = rng.random(m.shape).astype(np.float32)
    coarse = smooth_noise(rng, W, H, (220, 275))
    v = m + (n - 0.5) * rough - (coarse > 1 - speck) * 0.35 * m
    on = v > 0.5
    a = np.asarray(img).copy()
    a[on] = color
    return Image.fromarray(a)


def finish(img, rng, name):
    a = np.asarray(img, np.float32)
    g = rng.normal(0, 7.5, a.shape[:2]).astype(np.float32)[..., None]
    fib = (smooth_noise(rng, W, H, (300, 30)) - 0.5)[..., None] * 6
    a = np.clip(a + g + fib, 0, 255).astype(np.uint8)
    out = Image.fromarray(a).resize((W // S, H // S), Image.LANCZOS)
    out.save(os.path.join(OUT, name), quality=95)
    print('wrote', name)


def red_field(img, y0=SPLIT):
    d = ImageDraw.Draw(img)
    d.rectangle([0, y0, W, H], fill=RED)
    return d

# ---------------------------------------------------------------- 1 · the loop


def plate_loop():
    rng = random.Random(SEED + 1); nr = np.random.default_rng(SEED + 1)
    img = Image.new('RGB', (W, H), PAPER); d = red_field(img)
    cx = 270 * S
    # two process boxes, decision, three agents
    rect(d, cx - 34 * S, 112 * S, 68 * S, 50 * S); rect(d, cx - 34 * S, 198 * S, 68 * S, 50 * S)
    arrow(d, (cx - 8 * S, 162 * S), (cx - 8 * S, 198 * S)); arrow(d, (cx + 8 * S, 198 * S), (cx + 8 * S, 162 * S))
    arrow(d, (cx, 248 * S), (cx, 292 * S))
    diamond(d, (cx, 320 * S), 40 * S, 28 * S)
    line(d, [(cx, 348 * S), (cx, 642 * S)])
    line(d, [(330 * S, 318 * S), (352 * S, 318 * S), (352 * S, 680 * S)])
    names = ['alien', 'heart', 'ship']
    for i, y in enumerate([420, 522, 645]):
        y *= S
        circ(d, (186 * S, y), 42 * S)
        sw, sh = sprite_size(names[i], 5 * S)
        sprite(d, names[i], 186 * S - sw // 2, y - sh // 2, 5 * S)
        rect(d, 240 * S, y - 18 * S, 32 * S, 32 * S)
        arrow(d, (228 * S, y - 2 * S), (240 * S, y - 2 * S))
        line(d, [(272 * S, y - 2 * S), (352 * S, y - 2 * S)])
        arrow(d, (144 * S, y - 10 * S), (86 * S, y - 10 * S)); arrow(d, (86 * S, y + 6 * S), (144 * S, y + 6 * S))
        if i < 2:
            line(d, [(186 * S, y + 42 * S), (186 * S, y + (102 if i == 0 else 81) * S)])
    # the situated world: a hand-drawn blob of game fragments
    blob(d, 60 * S, 520 * S, 44 * S, 190 * S, rng)
    for k, (nm, yy) in enumerate([('coin', 400), ('key', 470), ('T', 548), ('hero', 610)]):
        sprite(d, nm, 42 * S, yy * S, 3 * S)
    # the red feedback loop — what the tinkering feeds back into the spec
    line(d, [(160 * S, 690 * S), (160 * S, 725 * S), (55 * S, 725 * S), (55 * S, 68 * S), (262 * S, 68 * S), (262 * S, 100 * S)], RED, 3 * S // 2 + 1)
    arrow(d, (262 * S, 90 * S), (262 * S, 112 * S), RED, 3 * S // 2 + 1)
    # the loop continues into the red field and lands on the mashup
    line(d, [(160 * S, 725 * S), (160 * S, 1040 * S), (330 * S, 1040 * S)], INK, LW)
    arrow(d, (318 * S, 1040 * S), (356 * S, 1040 * S))
    # the mashup sprite: parts of four games spliced on one grid, seams left open
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    px = 26 * S; ox, oy = 400 * S, 700 * S
    sprite(md, 'alien', ox + 2 * px, oy, px, 255)
    sprite(md, 'heart', ox + 4 * px, oy + 7 * px + 6 * S, px, 255)
    sprite(md, 'sword', ox + 11 * px + 6 * S, oy + 6 * px, px // 2 * 2 - 0, 255)
    sprite(md, 'ship', ox + 1 * px, oy + 13 * px + 12 * S, px, 255)
    sprite(md, 'L', ox - 1 * px - 6 * S, oy + 8 * px, px, 255)
    sprite(md, 'I', ox + 10 * px, oy + 17 * px + 18 * S, px, 255)
    img = crayon(img, mask, INK, nr)
    finish(img, nr, '01-the-loop.png')

# ---------------------------------------------------------------- 2 · the zoom


def tangle(d, cx, cy, R, rng, n=26, fill=INK):
    nodes = []
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); r = R * math.sqrt(rng.uniform(0, 0.8))
        nodes.append((cx + r * math.cos(a), cy + r * math.sin(a), rng.choice([8, 10, 14, 18, 24]) * S))
    for x, y, r in nodes:
        circ(d, (x, y), r, fill, 3)
        if r > 16 * S and rng.random() < 0.6:
            circ(d, (x, y), r * 0.45, fill, 2)
    for _ in range(n * 3):
        a, b = rng.sample(nodes, 2)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        off = rng.uniform(-0.6, 0.6)
        ctrl = (mx - (b[1] - a[1]) * off, my + (b[0] - a[0]) * off)
        pts = bez(a[:2], ctrl, b[:2])
        line(d, pts, fill, rng.choice([2, 2, 3, 6]))
        k = int(len(pts) * 0.55)
        arrow(d, pts[k - 1], pts[k], fill, 2, 7 * S)
    for x, y, r in nodes[:6]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def plate_zoom():
    rng = random.Random(SEED + 2); nr = np.random.default_rng(SEED + 2)
    img = Image.new('RGB', (W, H), PAPER); d = red_field(img)
    # a level, drawn as a plan: ground, platforms, a pipe, a ladder, a hero
    t = 22 * S; gx, gy = 40 * S, 640 * S
    for i in range(14):
        rect(d, gx + i * t, gy, t, t)
    for (i, j, n) in [(2, 5, 3), (7, 9, 4), (1, 13, 2), (6, 15, 3)]:
        for k in range(n):
            rect(d, gx + (i + k) * t, gy - j * t, t, t)
    rect(d, gx + 11 * t, gy - 3 * t, 2 * t, 3 * t); rect(d, gx + 10.7 * t, gy - 3.6 * t, 2.6 * t, 0.6 * t)
    for k in range(8):
        line(d, [(gx + 5 * t, gy - k * t), (gx + 5 * t + t, gy - k * t)], INK, 2)
    line(d, [(gx + 5 * t, gy), (gx + 5 * t, gy - 8 * t)]); line(d, [(gx + 6 * t, gy), (gx + 6 * t, gy - 8 * t)])
    sprite(d, 'hero', gx + 8 * t, gy - 7 * 3 * S, 3 * S)
    sprite(d, 'coin', gx + 2.2 * t, gy - 7 * t, 3 * S); sprite(d, 'coin', gx + 7.6 * t, gy - 11 * t, 3 * S)
    sprite(d, 'alien', gx + 1.2 * t, gy - 15 * t - 22 * S, 2 * S)
    # the tile someone opened up
    sel = (gx + 8.5 * t, gy - 9 * t + t / 2)
    circ(d, sel, 0.95 * t, RED, 3 * S // 2 + 1)
    C, R = (650 * S, 300 * S), 285 * S
    circ(d, C, R)
    # dotted sightlines to the magnifier
    for s in (-1, 1):
        a = math.atan2(C[1] - sel[1], C[0] - sel[0]) + s * math.pi / 2
        p0 = (sel[0] + 0.95 * t * math.cos(a), sel[1] + 0.95 * t * math.sin(a))
        b = math.atan2(sel[1] - C[1], sel[0] - C[0])
        p1 = (C[0] + R * math.cos(b - s * 1.05), C[1] + R * math.sin(b - s * 1.05))
        dashed(d, p0, p1, INK, 2, 7 * S, 5 * S)
    # inside one tile: the agents tangled up in it
    layer = Image.new('RGB', (W, H), PAPER); ld = ImageDraw.Draw(layer)
    tangle(ld, C[0], C[1], R * 0.95, rng)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).ellipse([C[0] - R + 4, C[1] - R + 4, C[0] + R - 4, C[1] + R - 4], fill=255)
    img.paste(layer, (0, 0), m)
    d = ImageDraw.Draw(img); circ(d, C, R)
    # bottom: the level again, at the scale of a body — a skyline of blocks in crayon
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    T = 52 * S; base = H - 70 * S
    heights = [3, 3, 5, 5, 2, 2, 2, 7, 7, 4, 4, 4, 6, 1, 1, 3, 3, 8]
    x0 = 330 * S
    for i, h in enumerate(heights):
        x = x0 + i * T * 0.72
        if x > W - 50 * S: break
        for j in range(h):
            if (i * 7 + j * 3) % 11 == 0:
                md.rectangle([x, base - (j + 1) * T * 0.72 + 6 * S, x + T * 0.72 - 6 * S, base - j * T * 0.72], outline=255, width=7 * S)
            else:
                md.rectangle([x, base - (j + 1) * T * 0.72 + 6 * S, x + T * 0.72 - 6 * S, base - j * T * 0.72], fill=255)
    sprite(md, 'hero', x0 + 4.4 * T * 0.72, base - 5 * T * 0.72 - 7 * 11 * S, 11 * S, 255)
    img = crayon(img, mask, INK, nr)
    finish(img, nr, '02-the-tile.png')

# ---------------------------------------------------------------- 3 · the arcade, in plan


def poly_rot(cx, cy, w, h, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, -h / 2)]]


def plate_arcade():
    rng = random.Random(SEED + 3); nr = np.random.default_rng(SEED + 3)
    img = Image.new('RGB', (W, H), PAPER); d = red_field(img)
    C = (493 * S, 330 * S)
    for R in (285 * S, 270 * S):
        pts = [(C[0] + R * math.cos(math.pi / 6 + k * math.pi / 3 - math.pi / 2 + math.pi / 6), C[1] + R * math.sin(math.pi / 6 + k * math.pi / 3 - math.pi / 2 + math.pi / 6)) for k in range(7)]
        # leave the door open on the lower-left wall
        for k in range(6):
            p, q = pts[k], pts[k + 1]
            if k == 3:
                line(d, [p, (p[0] + (q[0] - p[0]) * 0.35, p[1] + (q[1] - p[1]) * 0.35)])
                line(d, [(p[0] + (q[0] - p[0]) * 0.6, p[1] + (q[1] - p[1]) * 0.6), q])
            else:
                line(d, [p, q])
    # door swing
    # cabinets along the walls
    R = 240 * S
    cab = []
    for k in range(6):
        a0 = math.pi / 6 + k * math.pi / 3 - math.pi / 2 + math.pi / 6
        a1 = a0 + math.pi / 3
        for f in (0.3, 0.7):
            if k == 3 and f == 0.3: continue
            p = (C[0] + R * ((1 - f) * math.cos(a0) + f * math.cos(a1)), C[1] + R * ((1 - f) * math.sin(a0) + f * math.sin(a1)))
            ang = math.atan2(math.sin(a1) - math.sin(a0), math.cos(a1) - math.cos(a0))
            line(d, poly_rot(p[0], p[1], 78 * S, 20 * S, ang))
            cab.append(p)
    # players at their stations: a body seen from above, a reach of arm, a screen
    players = []
    for k in range(7):
        a = -math.pi / 2 + k * 2 * math.pi / 7 + rng.uniform(-0.1, 0.1)
        r = 140 * S
        p = (C[0] + r * math.cos(a), C[1] + r * math.sin(a))
        circ(d, p, 22 * S); circ(d, p, 4 * S, INK, 2)
        for rr, sp in ((32 * S, 1.6), (38 * S, 0.9)):
            st = math.degrees(a) + 90 + rng.uniform(-30, 30)
            d.arc([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], st, st + math.degrees(sp), fill=INK, width=3)
        sa = a + math.pi + rng.uniform(-0.6, 0.6)
        rect(d, p[0] + 30 * S * math.cos(sa) - 8 * S, p[1] + 30 * S * math.sin(sa) - 6 * S, 16 * S, 12 * S, INK, 2)
        players.append(p)
    # the agent in the middle of the room, wired to everyone
    for p in players:
        line(d, [C, p], RED, 2)
    for p in cab:
        dashed(d, C, p, RED, 2, 5 * S, 6 * S)
    d.ellipse([C[0] - 16 * S, C[1] - 16 * S, C[0] + 16 * S, C[1] + 16 * S], fill=RED)
    circ(d, C, 26 * S, RED, 3)
    # bottom: the control panel, the only interface anyone touches, in crayon
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    px0, py0 = 360 * S, 845 * S
    md.rounded_rectangle([px0, py0, px0 + 600 * S, py0 + 330 * S], 36 * S, outline=255, width=14 * S)
    jx, jy = px0 + 150 * S, py0 + 165 * S
    md.ellipse([jx - 85 * S, jy - 85 * S, jx + 85 * S, jy + 85 * S], outline=255, width=12 * S)
    md.ellipse([jx - 46 * S, jy - 46 * S, jx + 46 * S, jy + 46 * S], fill=255)
    for k in range(8):
        a = k * math.pi / 4
        md.line([(jx + 98 * S * math.cos(a), jy + 98 * S * math.sin(a)), (jx + 116 * S * math.cos(a), jy + 116 * S * math.sin(a))], fill=255, width=9 * S)
    for r_ in range(2):
        for c_ in range(3):
            bx, by = px0 + 330 * S + c_ * 92 * S + r_ * 26 * S, py0 + 105 * S + r_ * 110 * S
            if (r_, c_) == (0, 1):
                md.ellipse([bx - 36 * S, by - 36 * S, bx + 36 * S, by + 36 * S], outline=255, width=11 * S)
            else:
                md.ellipse([bx - 36 * S, by - 36 * S, bx + 36 * S, by + 36 * S], fill=255)
    img = crayon(img, mask, INK, nr)
    finish(img, nr, '03-the-room.png')

# ---------------------------------------------------------------- 4 · the angel at the console


def plate_angel():
    rng = random.Random(SEED + 4); nr = np.random.default_rng(SEED + 4)
    img = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(img)
    # schematic margins: leader lines and bars of no-text, like a datasheet with the words removed
    for _ in range(46):
        y = rng.uniform(80, 1200) * S; x0 = rng.uniform(560, 760) * S; x1 = rng.uniform(900, 990) * S
        line(d, [(x0, y), (x1, y)], INK, 2)
        d.ellipse([x0 - 4, y - 4, x0 + 4, y + 4], fill=INK)
    for _ in range(12):
        bx = rng.uniform(820, 960) * S; by = rng.uniform(100, 1150) * S
        for k in range(rng.randint(4, 12)):
            L = rng.uniform(20, 70) * S
            d.rectangle([bx, by + k * 9 * S, bx + L, by + k * 9 * S + 4 * S], fill=INK)
    # the wings: feathers grown from a bone that leaves the shoulder blade
    bone = bez((640 * S, 760 * S), (700 * S, 360 * S), (990 * S, 250 * S), 60)
    for i, (bx, by) in enumerate(bone[4:], 4):
        t = i / len(bone)
        a = -0.35 + t * 1.25
        L = (110 + 230 * t) * S
        p1 = (bx + L * math.cos(a), by + L * math.sin(a))
        line(d, bez((bx, by), (bx + L * 0.5 * math.cos(a - 0.25), by + L * 0.5 * math.sin(a - 0.25)), p1, 20), INK, 2 if i % 2 else 3)
    line(d, bone, INK, 5)
    for row in range(3):
        for i in range(6, len(bone) - 2, 3):
            bx, by = bone[i]; r = (26 - row * 4) * S
            ox, oy = bx + (row + 1) * 26 * S, by + (row + 1) * 22 * S
            d.arc([ox - r, oy - r, ox + r, oy + r], 20, 160, fill=INK, width=3)
    # the halo
    for o in (0, 9 * S):
        d.ellipse([390 * S - o, 330 * S - o / 3, 600 * S + o, 380 * S + o / 3], outline=INK, width=3)
    # the CRT, side view
    mx = 80 * S
    line(d, [(mx, 360 * S), (mx + 120 * S, 340 * S), (mx + 140 * S, 340 * S), (mx + 140 * S, 860 * S), (mx + 120 * S, 860 * S), (mx, 830 * S)])
    for k in range(9):
        y = (380 + k * 52) * S
        line(d, [(mx + 6 * S, y), (mx + 112 * S, y - 4 * S)], INK, 2)
    rect(d, mx - 30 * S, 860 * S, 210 * S, 30 * S)
    line(d, [(mx + 40 * S, 890 * S), (mx + 20 * S, 1010 * S), (mx + 160 * S, 1010 * S), (mx + 130 * S, 890 * S)])
    # on screen: a maze, in red
    for i in range(9):
        for j in range(30):
            if rng.random() < 0.45:
                x = mx + 14 * S + i * 10 * S; y = 372 * S + j * 15 * S - i * 1.5 * S
                d.rectangle([x, y, x + 8 * S, y + 12 * S], fill=RED)
    # the beam: what the screen gives the head
    for _ in range(420):
        y = rng.gauss(520, 55) * S
        x0 = (mx + 140 * S) + rng.uniform(0, 40) * S
        x1 = rng.uniform(300, 430) * S
        d.line([(x0, y), (x1, y + rng.uniform(-30, 30) * S)], fill=RED, width=rng.choice([2, 2, 3, 5]))
    for _ in range(70):
        x = rng.uniform(240, 420) * S; y = rng.gauss(520, 50) * S
        w_ = rng.uniform(6, 30) * S
        d.rectangle([x, y, x + w_, y + rng.uniform(3, 10) * S], fill=RED)
    # the operator, printed in typewriter density marks
    dens = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(dens)
    dd.polygon([(420 * S, 450 * S), (395 * S, 500 * S), (360 * S, 545 * S), (385 * S, 556 * S), (380 * S, 585 * S),
                (395 * S, 612 * S), (425 * S, 650 * S), (480 * S, 668 * S), (530 * S, 640 * S), (540 * S, 470 * S)], fill=95)   # face, in profile
    dd.ellipse([420 * S, 380 * S, 620 * S, 640 * S], fill=255)                       # hair
    dd.polygon([(470 * S, 640 * S), (460 * S, 720 * S), (560 * S, 720 * S), (560 * S, 620 * S)], fill=120)  # neck
    dd.polygon([(470 * S, 640 * S), (420 * S, 700 * S), (360 * S, 1000 * S), (420 * S, 1260 * S),
                (760 * S, 1260 * S), (740 * S, 860 * S), (650 * S, 700 * S), (560 * S, 640 * S)], fill=150)  # back
    dd.polygon([(420 * S, 760 * S), (300 * S, 940 * S), (230 * S, 1010 * S), (270 * S, 1040 * S),
                (360 * S, 980 * S), (470 * S, 830 * S)], fill=110)                   # arm
    dd.ellipse([418 * S, 520 * S, 438 * S, 534 * S], fill=255)                        # eye
    dens = dens.filter(ImageFilter.GaussianBlur(12 * S))
    dn = np.asarray(dens, np.float32) / 255
    shade = fbm(nr, W, H, 5, 4)
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 12 * S)
    ramp = " .,:;-=+*#%@"
    cw, ch = 7.4 * S, 12.5 * S
    y = 0
    while y < H:
        x = 0
        while x < W:
            v = dn[int(min(H - 1, y + ch / 2)), int(min(W - 1, x + cw / 2))]
            if v > 0.04:
                v = min(1, v * (0.75 + 0.6 * shade[int(y), int(x)]))
                c = ramp[min(len(ramp) - 1, int(v * len(ramp)))]
                if c != ' ':
                    col = RED if (abs(y - 520 * S) < 70 * S and x < 470 * S and rng.random() < 0.5) else INK
                    d.text((x, y), c, font=font, fill=col)
            x += cw
        y += ch
    # keyboard under the hands
    kx, ky = 150 * S, 1030 * S
    line(d, [(kx, ky), (kx + 260 * S, ky - 20 * S), (kx + 300 * S, ky + 50 * S), (kx + 30 * S, ky + 80 * S), (kx, ky)])
    for r_ in range(4):
        for c_ in range(10):
            x = kx + 20 * S + c_ * 24 * S + r_ * 6 * S; yv = ky + 10 * S + r_ * 15 * S - c_ * 1.8 * S
            d.rectangle([x, yv, x + 16 * S, yv + 9 * S], outline=INK, width=2)
    finish(img, nr, '04-the-operator.png')

# ---------------------------------------------------------------- 5 · the rig


def mast(d, x, base, top, wb, wt, fill=INK):
    n = 14
    L = [(x - wb / 2, base), (x - wt / 2, top)]; R = [(x + wb / 2, base), (x + wt / 2, top)]
    line(d, L, fill, 4); line(d, R, fill, 4)
    pts = []
    for i in range(n + 1):
        t = i / n
        y = base + (top - base) * t; w_ = wb + (wt - wb) * t
        pts.append(((x - w_ / 2, y), (x + w_ / 2, y)))
        line(d, list(pts[-1]), fill, 3)
    for a, b in zip(pts, pts[1:]):
        line(d, [a[0], b[1]], fill, 2); line(d, [a[1], b[0]], fill, 2)
    rect(d, x - wt / 2 - 18 * S, top - 20 * S, wt + 36 * S, 20 * S, fill, 3)
    return pts


def plate_rig():
    rng = random.Random(SEED + 5); nr = np.random.default_rng(SEED + 5)
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # red sun of the platform, half sunk
    d.ellipse([250 * S, 300 * S, 780 * S, 830 * S], fill=RED)
    # xeroxed cloud bank: an etched noise field cut by contour
    n = fbm(nr, W, H, 4, 6)
    yy = np.linspace(0, 1, H)[:, None]
    region = np.exp(-((yy - 0.55) / 0.22) ** 2) * (0.6 + 0.6 * smooth_noise(nr, W, H, (5, 6)))
    v = n * region
    fine = nr.random((H, W))
    ink = (np.abs(v - 0.33) < 0.012) | (np.abs(v - 0.27) < 0.008) | ((v > 0.40) & (fine < (v - 0.40) * 9)) | ((v > 0.36) & (v < 0.40) & (fine < 0.08))
    a = np.asarray(img).copy(); a[ink] = INK
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    # two drilling masts with leader lines, labels cut away
    p1 = mast(d, 190 * S, 1120 * S, 300 * S, 120 * S, 40 * S)
    p2 = mast(d, 840 * S, 1160 * S, 210 * S, 150 * S, 50 * S)
    for pts, side in ((p1, -1), (p2, 1)):
        for k in rng.sample(range(2, len(pts) - 1), 5):
            q = pts[k][0] if side < 0 else pts[k][1]
            e = (q[0] + side * rng.uniform(50, 120) * S, q[1] + rng.uniform(-40, 40) * S)
            line(d, [q, e], INK, 2)
            line(d, [e, (e[0] + side * 30 * S, e[1])], INK, 2)
    # dimension line under the right mast
    line(d, [(770 * S, 1200 * S), (910 * S, 1200 * S)], INK, 2)
    for xx in (770, 840, 910):
        line(d, [(xx * S, 1185 * S), (xx * S, 1215 * S)], INK, 2)
    # base rig drawn flat along the bottom
    line(d, [(60 * S, 1120 * S), (980 * S, 1160 * S)], INK, 4)
    for k in range(12):
        x = (260 + k * 45) * S
        line(d, [(x, 1123 * S + k * 2 * S), (x + 30 * S, 1080 * S + k * 2 * S), (x + 60 * S, 1126 * S + k * 2 * S)], INK, 2)
    # the bowtie, as a D-pad: a heavy black cross with an open cross inside
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    cx, cy, a_, b_ = 512 * S, 560 * S, 230 * S, 78 * S
    md.rectangle([cx - a_, cy - b_, cx + a_, cy + b_], fill=255)
    md.rectangle([cx - b_, cy - a_, cx + b_, cy + a_], fill=255)
    img = crayon(img, mask, INK, nr, 0.35, 0.05)
    d = ImageDraw.Draw(img)
    i_ = 22 * S
    d.rectangle([cx - a_ + i_, cy - b_ + i_, cx + a_ - i_, cy + b_ - i_], fill=PAPER)
    d.rectangle([cx - b_ + i_, cy - a_ + i_, cx + b_ - i_, cy + a_ - i_], fill=PAPER)
    # inside the pad, the clouds again, and something trapped in each arm
    sub = Image.fromarray(np.where(ink[..., None], np.array(INK, np.uint8), np.array(PAPER, np.uint8)).astype(np.uint8))
    m = Image.new('L', (W, H), 0); mm = ImageDraw.Draw(m)
    mm.rectangle([cx - a_ + i_ + 6, cy - b_ + i_ + 6, cx + a_ - i_ - 6, cy + b_ - i_ - 6], fill=255)
    mm.rectangle([cx - b_ + i_ + 6, cy - a_ + i_ + 6, cx + b_ - i_ - 6, cy + a_ - i_ - 6], fill=255)
    img.paste(sub, (0, 0), m); d = ImageDraw.Draw(img)
    for nm, (x, y) in [('alien', (cx - 175 * S, cy - 14 * S)), ('coin', (cx + 120 * S, cy - 14 * S)),
                       ('heart', (cx - 14 * S, cy - 165 * S)), ('chest', (cx - 16 * S, cy + 125 * S))]:
        sprite(d, nm, x, y, 4 * S, RED)
    # falling pieces, the debris of the mashup
    for nm, x, y, px in [('T', 120, 120, 14), ('S', 900, 90, 12), ('L', 640, 140, 10), ('O', 360, 180, 9), ('I', 70, 760, 10), ('T', 930, 700, 11)]:
        sprite(d, nm, x * S, y * S, px * S, RED)
    # wings at the top of the pad, like the eagle over the logo
    for side in (-1, 1):
        for k in range(16):
            a0 = math.radians(-90 + side * (20 + k * 4.5))
            L = (130 + k * 9) * S
            p0 = (cx + side * 40 * S, cy - a_ - 10 * S)
            p2 = (p0[0] + side * L * abs(math.cos(a0)) * 1.4, p0[1] - L * 0.55 + k * 9 * S)
            line(d, bez(p0, (p0[0] + side * L * 0.4, p0[1] - L * 0.7), p2), INK, 2)
    finish(img, nr, '05-the-rig.png')


for f in [globals()[n] for n in (sys.argv[3].split(',') if len(sys.argv) > 3 else ['plate_loop', 'plate_zoom', 'plate_arcade', 'plate_angel', 'plate_rig'])]:
    f()
