"""THE AGENTIC BRICOLEUR — a two-ink press for five plates.

Model
  Two ink plates (red, black) are coverage maps in [0,1]. Shapes are drawn as line masks
  (PIL, supersampled) or as signed distance fields (numpy). Tone is never a flat alpha:
  it goes through an AM halftone screen — red at 75°, black at 15° — so every grey is a
  dot. Knockouts remove ink from a plate. At the end the plates are developed onto paper
  with multiplicative overprint, the red plate slightly out of register, ink density
  breathing, paper grain on top.

Usage
  python3 bricoleur3.py OUT [--seeds 1,2,3] [--only loop,tile] [--scale 2] [--sheet]
"""
import argparse, json, math, os, random, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DW, DH = 1024, 1280                                     # design units (= output px)
PAPER = np.array([238, 235, 228], np.float32) / 255
INK = {'red': np.array([249, 57, 34], np.float32) / 255,
       'black': np.array([24, 21, 20], np.float32) / 255}
MONO = '/System/Library/Fonts/Menlo.ttc'
F = np.float32

SPR = {
    'alien': ["...XXXXX...", ".XXXXXXXXX.", "XX..XXX..XX", "XXXXXXXXXXX", ".X.XX.XX.X.", "X.........X", ".X.......X."],
    'heart': [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
    'coin': ["..XXX..", ".X...X.", "X..X..X", "X..X..X", "X..X..X", ".X...X.", "..XXX.."],
    'hero': ["..XXX..", "..XXX..", "...X...", ".XXXXX.", "X.XXX.X", "..X.X..", ".XX.XX."],
    'key': [".XXX......", "X...XXXXXX", "X...X..X.X", ".XXX......"],
    'sword': [".......XX", "......XXX", ".....XXX.", "X...XXX..", ".X.XXX...", "..XXX....", ".XXX.X...", "XX....X.."],
    'ship': ["....X....", "...XXX...", "...XXX...", ".X.XXX.X.", "XXXXXXXXX", "XX.XXX.XX", "X...X...X"],
    'chest': ["XXXXXXXX", "X......X", "XXXXXXXX", "X..XX..X", "X......X", "XXXXXXXX"],
    'T': ["XXX", ".X."], 'S': [".XX", "XX."], 'L': ["X..", "XXX"], 'I': ["XXXX"], 'O': ["XX", "XX"],
}

# =============================================================== the press


class Press:
    def __init__(self, seed, scale):
        self.seed, self.S = seed, scale
        self.W, self.H = DW * scale, DH * scale
        self.rng = random.Random(seed)
        self.nr = np.random.default_rng(seed)
        self.plate = {k: np.zeros((self.H, self.W), F) for k in INK}
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(F)
        self.X, self.Y = xx / scale, yy / scale               # design-unit coordinates
        self.params = {}

    # --- coordinates & masks
    def p(self, *v):
        return tuple(x * self.S for x in v)

    def pts(self, seq):
        return [(x * self.S, y * self.S) for x, y in seq]

    def layer(self):
        m = Image.new('L', (self.W, self.H), 0)
        return m, ImageDraw.Draw(m)

    @staticmethod
    def cov(m):
        return np.asarray(m, F) / 255

    # --- ink
    def ink(self, name, c):
        self.plate[name] = np.maximum(self.plate[name], c)

    def knock(self, name, c):
        self.plate[name] *= 1 - np.clip(c, 0, 1)

    def clear(self, c):
        for k in self.plate: self.knock(k, c)

    # --- noise
    def value(self, cells_x, cells_y=None):
        cy = cells_y or max(2, int(cells_x * DH / DW))
        a = self.nr.random((cy, cells_x)).astype(F)
        return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((self.W, self.H), Image.BICUBIC), F) / 255

    def fbm(self, base=4, octaves=5):
        out, amp, tot = np.zeros((self.H, self.W), F), 1.0, 0.0
        for o in range(octaves):
            out += amp * self.value(base * 2 ** o); tot += amp; amp *= 0.5
        return out / tot

    def warp(self, field, amount, base=3):
        """Domain warp: resample a field along a smooth displacement (design units)."""
        wx = (self.value(base) - .5) * 2 * amount * self.S
        wy = (self.value(base) - .5) * 2 * amount * self.S
        yi = np.clip((self.Y * self.S + wy).astype(np.int32), 0, self.H - 1)
        xi = np.clip((self.X * self.S + wx).astype(np.int32), 0, self.W - 1)
        return field[yi, xi]

    # --- screening
    def screen(self, gray, angle, cell):
        """AM halftone with a euclidean spot: 0 → paper, 1 → solid, dots in between."""
        a = math.radians(angle)
        u = (self.X * math.cos(a) + self.Y * math.sin(a)) / cell
        v = (-self.X * math.sin(a) + self.Y * math.cos(a)) / cell
        spot = (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v)) * 0.5
        return (spot > 1 - 2 * np.clip(gray, 0, 1)).astype(F)

    def edge_tone(self, sd, soft, torn=0.0, base=10):
        """Signed distance → tone, solid inside, screened across a band of `soft` units at the edge."""
        if torn:
            sd = sd + (self.fbm(base, 4) - .5) * 2 * torn
        return np.clip(-sd / soft + 0.5, 0, 1)

    def isolines(self, field, levels, width):
        gy, gx = np.gradient(field)
        g = np.hypot(gx, gy) * self.S + 1e-6
        out = np.zeros_like(field)
        for L in levels:
            out = np.maximum(out, (np.abs(field - L) / g < width).astype(F))
        return out

    def crayon(self, c, rough=0.5, speck=0.15):
        """Wax/overinked fill: chewed edge, open specks — same hand as the reference lettering."""
        b = np.asarray(Image.fromarray((c * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2 * self.S)), F) / 255
        v = b + (self.nr.random(b.shape, F) - .5) * rough - (self.value(220) > 1 - speck) * .35 * b
        return (v > .5).astype(F)

    # --- development
    def develop(self, misreg=(3.0, -2.0)):
        out = np.broadcast_to(PAPER, (self.H, self.W, 3)).copy()
        for name, off in (('red', misreg), ('black', (0, 0))):
            c = self.plate[name]
            if off != (0, 0):
                c = np.roll(c, (int(off[1] * self.S), int(off[0] * self.S)), (0, 1))
            density = 0.86 + 0.14 * self.value(7)                       # the roller is never even
            pin = self.nr.random(c.shape, F) < 0.015                    # pinholes in the solids
            k = c * density * (~pin)
            out *= 1 - k[..., None] * (1 - INK[name])
        fib = (self.value(300, 30) - .5) * 0.025
        grain = self.nr.normal(0, 0.028, (self.H, self.W)).astype(F)
        out = np.clip(out + (fib + grain)[..., None], 0, 1)
        img = Image.fromarray((out * 255).astype(np.uint8))
        return img.resize((DW, DH), Image.LANCZOS) if self.S != 1 else img

    def stats(self):
        r, b = self.plate['red'] > .5, self.plate['black'] > .5
        return {'red_only': float((r & ~b).mean()), 'black': float(b.mean()), 'paper': float((~r & ~b).mean())}

# =============================================================== geometry


def sd_circle(P, cx, cy, r):
    return np.hypot(P.X - cx, P.Y - cy) - r


def sd_box(P, cx, cy, hw, hh):
    dx, dy = np.abs(P.X - cx) - hw, np.abs(P.Y - cy) - hh
    return np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0)


def sd_below(P, x0, y0, slope):
    """Negative below the line through (x0,y0) with given slope."""
    return ((y0 + slope * (P.X - x0)) - P.Y) / math.sqrt(1 + slope * slope)


def poisson(rng, n, bounds, rmin, inside=lambda x, y: True, tries=4000):
    x0, y0, x1, y1 = bounds; out = []
    for _ in range(tries):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if inside(x, y) and all((x - a) ** 2 + (y - b) ** 2 > rmin * rmin for a, b in out):
            out.append((x, y))
            if len(out) == n: break
    return out


def bez(p0, p1, p2, n=48):
    t = np.linspace(0, 1, n)[:, None]
    a, b, c = map(np.array, (p0, p1, p2))
    return [tuple(q) for q in ((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c)]

# =============================================================== drawing (onto masks, canvas px)


def line(d, pts, w=3):
    d.line(pts, fill=255, width=int(w), joint='curve')


def arrow(d, p0, p1, w=3, head=14):
    line(d, [p0, p1], w)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-1, 1):
        b = a + math.pi - s * .42
        line(d, [p1, (p1[0] + head * math.cos(b), p1[1] + head * math.sin(b))], w)


def ring(d, c, r, w=3):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=255, width=int(w))


def disc(d, c, r):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)


def dashed(d, p0, p1, w=2, dash=14, gap=10):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    t = 0.0
    while t < L:
        e = min(L, t + dash); d.line([(p0[0] + ux * t, p0[1] + uy * t), (p0[0] + ux * e, p0[1] + uy * e)], fill=255, width=int(w)); t += dash + gap


def sprite(d, name, x, y, px, outline=False):
    for j, row in enumerate(SPR[name]):
        for i, ch in enumerate(row):
            if ch == 'X':
                box = [x + i * px, y + j * px, x + (i + 1) * px - 1, y + (j + 1) * px - 1]
                d.rectangle(box, outline=255, width=max(2, int(px / 7))) if outline else d.rectangle(box, fill=255)


def sprite_wh(name, px):
    return len(SPR[name][0]) * px, len(SPR[name]) * px


def hand_blob(d, rng, c, rx, ry, w=3):
    ph = [rng.uniform(0, 6.3) for _ in range(5)]; am = [rng.uniform(.02, .08) / (i + 1) ** .6 for i in range(5)]
    pts = []
    for t in np.linspace(0, 2 * math.pi, 260):
        r = 1 + sum(am[i] * math.sin((i + 2) * t + ph[i]) for i in range(5))
        pts.append((c[0] + rx * r * math.cos(t), c[1] + ry * r * math.sin(t)))
    line(d, pts + [pts[0]], w)

# =============================================================== the vocabulary


def agent_graph(P, d, cx, cy, R, n=26, w=3):
    """Agents as a proximity graph: each tied to its nearest neighbours, a few long reaches across."""
    S = P.S
    nodes = poisson(P.rng, n, (cx - R, cy - R, cx + R, cy + R), R * 0.22, lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 < (R * .86) ** 2)
    sizes = [P.rng.choice([7, 9, 12, 16, 22]) for _ in nodes]
    edges = set()
    for i, (x, y) in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: (nodes[j][0] - x) ** 2 + (nodes[j][1] - y) ** 2)[1:3]
        for j in near: edges.add(tuple(sorted((i, j))))
    for _ in range(n // 3):
        edges.add(tuple(sorted(P.rng.sample(range(len(nodes)), 2))))
    for i, j in edges:
        a, b = nodes[i], nodes[j]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2; off = P.rng.uniform(-.45, .45)
        pts = bez(P.p(*a), P.p(mx - (b[1] - a[1]) * off, my + (b[0] - a[0]) * off), P.p(*b))
        line(d, pts, P.rng.choice([w * .7, w * .7, w, w * 2]))
        k = int(len(pts) * .55); arrow(d, pts[k - 1], pts[k], max(2, w * .7), 8 * S)
    for (x, y), s in zip(nodes, sizes):
        c = P.p(x, y)
        if s >= 16 and P.rng.random() < .35: disc(d, c, s * S)
        else:
            ring(d, c, s * S, w)
            if s >= 12: ring(d, c, s * .45 * S, max(2, w * .7))
    return nodes


def flowchart(P, d, ox, oy, k, names=('alien', 'heart', 'ship')):
    S = P.S; q = lambda x, y: P.p(ox + x * k, oy + y * k); w = max(3, 2.2 * k * S / 2)
    for y0 in (0, 86): d.rectangle([*q(-34, y0), *q(34, y0 + 50)], outline=255, width=int(w))
    arrow(d, q(-8, 50), q(-8, 86), w, 10 * k * S); arrow(d, q(8, 86), q(8, 50), w, 10 * k * S); arrow(d, q(0, 136), q(0, 180), w, 10 * k * S)
    line(d, [q(0, 180), q(40, 208), q(0, 236), q(-40, 208), q(0, 180)], w)
    line(d, [q(0, 236), q(0, 530)], w); line(d, [q(60, 206), q(82, 206), q(82, 568)], w)
    nodes = []
    for i, y in enumerate([308, 410, 533]):
        c = q(-84, y); ring(d, c, 42 * k * S, w)
        px = int(4.6 * k * S); sw, sh = sprite_wh(names[i], px); sprite(d, names[i], c[0] - sw // 2, c[1] - sh // 2, px)
        d.rectangle([*q(-30, y - 18), *q(2, y + 14)], outline=255, width=int(w))
        arrow(d, q(-42, y - 2), q(-30, y - 2), w, 8 * k * S); line(d, [q(2, y - 2), q(82, y - 2)], w)
        arrow(d, q(-126, y - 10), q(-184, y - 10), w, 10 * k * S); arrow(d, q(-184, y + 6), q(-126, y + 6), w, 10 * k * S)
        if i < 2: line(d, [q(-84, y + 42), q(-84, y + (60 if i == 0 else 81))], w)
        nodes.append(c)
    hand_blob(d, P.rng, q(-215, 410), 44 * k * S, 190 * k * S, w)
    for nm, yy in [('coin', 290), ('key', 360), ('T', 438), ('hero', 500)]:
        sprite(d, nm, *q(-232, yy), int(3 * k * S))
    return q


def sprite_of_sprites(P, d, name, ox, oy, cell, parts=('heart', 'coin', 'ship', 'hero', 'chest', 'key')):
    """The mashup: one game's body, every pixel of it another game's thing."""
    S = P.S; k = 0
    for j, row in enumerate(SPR[name]):
        for i, ch in enumerate(row):
            if ch != 'X': continue
            x, y = P.p(ox + i * cell, oy + j * cell)
            d.rectangle([x, y, x + cell * S - 3 * S, y + cell * S - 3 * S], outline=255, width=max(2, int(1.6 * S)))
            if (i + 2 * j) % 5 == 0:
                d.rectangle([x, y, x + cell * S - 3 * S, y + cell * S - 3 * S], fill=255)
            else:
                nm = parts[k % len(parts)]; k += 1
                gw, gh = len(SPR[nm][0]), len(SPR[nm])
                px = max(2, int((cell - 4) * S / max(gw, gh)))
                sw, sh = sprite_wh(nm, px)
                sprite(d, nm, x + (cell * S - sw) // 2, y + (cell * S - sh) // 2, px)


def level(P, d, gx, gy, t, w=3):
    S = P.S; T = t * S; X0, Y0 = P.p(gx, gy)
    for i in range(14): d.rectangle([X0 + i * T, Y0, X0 + (i + 1) * T, Y0 + T], outline=255, width=int(w))
    for (i, j, n) in [(2, 5, 3), (7, 9, 4), (1, 13, 2), (6, 15, 3)]:
        for k in range(n): d.rectangle([X0 + (i + k) * T, Y0 - j * T, X0 + (i + k + 1) * T, Y0 - j * T + T], outline=255, width=int(w))
    d.rectangle([X0 + 11 * T, Y0 - 3 * T, X0 + 13 * T, Y0], outline=255, width=int(w)); d.rectangle([X0 + 10.7 * T, Y0 - 3.6 * T, X0 + 13.3 * T, Y0 - 3 * T], outline=255, width=int(w))
    for k in range(8): line(d, [(X0 + 5 * T, Y0 - k * T), (X0 + 6 * T, Y0 - k * T)], max(2, w * .7))
    line(d, [(X0 + 5 * T, Y0), (X0 + 5 * T, Y0 - 8 * T)], w); line(d, [(X0 + 6 * T, Y0), (X0 + 6 * T, Y0 - 8 * T)], w)
    px = max(2, int(T / 7)); sprite(d, 'hero', X0 + 8 * T, Y0 - 7 * px, px)
    sprite(d, 'coin', X0 + 2.2 * T, Y0 - 7 * T, px); sprite(d, 'coin', X0 + 7.6 * T, Y0 - 11 * T, px)
    sprite(d, 'alien', X0 + 1.2 * T, Y0 - 15 * T - 8 * px, px)
    return ((X0 + 8.5 * T) / S, (Y0 - 8.5 * T) / S)


def hexplan(P, d, cx, cy, R, w=3):
    S = P.S; ang = [math.pi / 3 * k for k in range(7)]
    for RR in (R, R - 15):
        pts = [P.p(cx + RR * math.cos(a), cy + RR * math.sin(a)) for a in ang]
        for k in range(6):
            p, q = pts[k], pts[k + 1]
            if k == 1:
                line(d, [p, (p[0] + (q[0] - p[0]) * .35, p[1] + (q[1] - p[1]) * .35)], w); line(d, [(p[0] + (q[0] - p[0]) * .6, p[1] + (q[1] - p[1]) * .6), q], w)
            else: line(d, [p, q], w)
    cab, players = [], []
    for k in range(6):
        a0, a1 = ang[k], ang[k + 1]
        for f in (.3, .7):
            if k == 1 and f == .3: continue
            x = cx + (R - 45) * ((1 - f) * math.cos(a0) + f * math.cos(a1)); y = cy + (R - 45) * ((1 - f) * math.sin(a0) + f * math.sin(a1))
            th = math.atan2(math.sin(a1) - math.sin(a0), math.cos(a1) - math.cos(a0)); c_, s_ = math.cos(th), math.sin(th)
            hw, hh = 40 * R / 300, 10 * R / 300
            box = [(x + u * c_ - v * s_, y + u * s_ + v * c_) for u, v in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh), (-hw, -hh)]]
            line(d, P.pts(box), w); cab.append((x, y))
    k_ = R / 285
    for k in range(7):
        a = -math.pi / 2 + k * 2 * math.pi / 7 + P.rng.uniform(-.1, .1)
        x, y = cx + 140 * k_ * math.cos(a), cy + 140 * k_ * math.sin(a); c = P.p(x, y)
        ring(d, c, 22 * k_ * S, w); ring(d, c, 4 * S, 2)
        for rr, sp in ((32 * k_ * S, 1.6), (38 * k_ * S, .9)):
            st = math.degrees(a) + 90 + P.rng.uniform(-30, 30); d.arc([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], st, st + math.degrees(sp), fill=255, width=int(w))
        sa = a + math.pi + P.rng.uniform(-.6, .6); sx, sy = c[0] + 30 * k_ * S * math.cos(sa), c[1] + 30 * k_ * S * math.sin(sa)
        d.rectangle([sx - 8 * S, sy - 6 * S, sx + 8 * S, sy + 6 * S], outline=255, width=2)
        players.append((x, y))
    return players, cab


def control_panel(P, d, x, y, k=1.0):
    s = lambda v: v * P.S * k; X0, Y0 = P.p(x, y)
    d.rounded_rectangle([X0, Y0, X0 + s(600), Y0 + s(330)], s(36), outline=255, width=int(s(14)))
    jx, jy = X0 + s(150), Y0 + s(165)
    d.ellipse([jx - s(85), jy - s(85), jx + s(85), jy + s(85)], outline=255, width=int(s(12))); d.ellipse([jx - s(46), jy - s(46), jx + s(46), jy + s(46)], fill=255)
    for i in range(8):
        a = i * math.pi / 4; d.line([(jx + s(98) * math.cos(a), jy + s(98) * math.sin(a)), (jx + s(116) * math.cos(a), jy + s(116) * math.sin(a))], fill=255, width=int(s(9)))
    for r_ in range(2):
        for c_ in range(3):
            bx, by = X0 + s(330 + c_ * 92 + r_ * 26), Y0 + s(105 + r_ * 110); bb = [bx - s(36), by - s(36), bx + s(36), by + s(36)]
            d.ellipse(bb, outline=255, width=int(s(11))) if (r_, c_) == (0, 1) else d.ellipse(bb, fill=255)


def lattice_mast(P, d, x, base, top, wb, wt, w=3, leaders=0, side=1):
    n = 14; rows = []
    for i in range(n + 1):
        t = i / n; y = base + (top - base) * t; ww = wb + (wt - wb) * t; rows.append((P.p(x - ww / 2, y), P.p(x + ww / 2, y)))
        line(d, list(rows[-1]), w * .8)
    line(d, [rows[0][0], rows[-1][0]], w * 1.3); line(d, [rows[0][1], rows[-1][1]], w * 1.3)
    for a, b in zip(rows, rows[1:]): line(d, [a[0], b[1]], max(2, w * .6)); line(d, [a[1], b[0]], max(2, w * .6))
    d.rectangle([*P.p(x - wt / 2 - 18, top - 20), *P.p(x + wt / 2 + 18, top)], outline=255, width=int(w))
    for k in P.rng.sample(range(2, n), leaders):
        q = rows[k][1] if side > 0 else rows[k][0]; e = (q[0] + side * P.rng.uniform(60, 130) * P.S, q[1] + P.rng.uniform(-40, 40) * P.S)
        line(d, [q, e, (e[0] + side * 34 * P.S, e[1])], 2); disc(d, (e[0] + side * 34 * P.S, e[1]), 3 * P.S)


def wing(P, d, root, ctrl, tip, flip=1, scale=1.0, w=3):
    S = P.S; bone = bez(P.p(*root), P.p(*ctrl), P.p(*tip), 60)
    for i, (bx, by) in enumerate(bone[4:], 4):
        t = i / len(bone); a = (-.35 + t * 1.25) if flip > 0 else (math.pi + .35 - t * 1.25); L = (110 + 230 * t) * S * scale
        p1 = (bx + L * math.cos(a), by + L * math.sin(a))
        line(d, bez((bx, by), (bx + L * .5 * math.cos(a - .25 * flip), by + L * .5 * math.sin(a - .25 * flip)), p1, 20), 2 if i % 2 else w)
    line(d, bone, w * 1.6)
    for row in range(3):
        for i in range(6, len(bone) - 2, 3):
            bx, by = bone[i]; r = (26 - row * 4) * S * scale; ox, oy = bx + flip * (row + 1) * 26 * S * scale, by + (row + 1) * 22 * S * scale
            d.arc([ox - r, oy - r, ox + r, oy + r], 20, 160, fill=255, width=int(w))


def datasheet(P, d, x0, x1, y0, y1, leads=24, blocks=7):
    S = P.S
    for _ in range(leads):
        y = P.rng.uniform(y0, y1); a = P.rng.uniform(x0, x0 + (x1 - x0) * .4); e = P.rng.uniform(x0 + (x1 - x0) * .6, x1)
        line(d, [P.p(a, y), P.p(e, y)], 2); disc(d, P.p(a, y), 3 * S)
    for _ in range(blocks):
        bx = P.rng.uniform(x0 + (x1 - x0) * .5, x1 - 60); by = P.rng.uniform(y0, y1 - 100)
        for k in range(P.rng.randint(4, 12)):
            d.rectangle([*P.p(bx, by + k * 9), *P.p(bx + P.rng.uniform(20, 70), by + k * 9 + 4)], fill=255)


def cloud_bank(P, yc, sig, thresh=.42):
    """Xerox clouds: domain-warped fbm, screened at 15°, contoured at constant width."""
    n = P.warp(P.fbm(3, 6), 60, 3)
    band = np.exp(-((P.Y / DH - yc) / sig) ** 2)
    v = n * band
    tone = .8 * np.clip((v - thresh) / .24, 0, 1) ** 1.7
    return P.screen(tone, 15, 4.2), P.isolines(v, [thresh - .03, thresh - .09], 1.6)


def ascii_figure(P, shapes, cell=15):
    """A body in density marks, contours in oriented strokes. No letters, only marks."""
    S = P.S
    m, d = P.layer(); shapes(d)
    soft = np.asarray(m.filter(ImageFilter.GaussianBlur(4 * S)), F) / 255
    wide = np.asarray(m.filter(ImageFilter.GaussianBlur(9 * S)), F) / 255
    gy, gx = np.gradient(wide)
    shade = P.fbm(5, 3)
    font = ImageFont.truetype(MONO, int(cell * S), index=1)
    ramp = " .,:;-=+*#%@"
    out, od = P.layer(); cw, ch = cell * .61 * S, cell * 1.05 * S
    y = 0.0
    while y < P.H - ch:
        x = 0.0
        while x < P.W - cw:
            iy, ix = int(y + ch / 2), int(x + cw / 2)
            v, g = soft[iy, ix], math.hypot(gx[iy, ix], gy[iy, ix]) * 9 * S
            if g > .28:
                ang = math.degrees(math.atan2(gx[iy, ix], -gy[iy, ix])) % 180   # edge direction in screen space
                c = '-' if ang < 22.5 or ang >= 157.5 else '\\' if ang < 67.5 else '|' if ang < 112.5 else '/'
            elif v > .05:
                vv = min(1, .25 + v * (.75 + .6 * shade[iy, ix])); c = ramp[min(len(ramp) - 1, int(vv * len(ramp)))]
            else: c = ' '
            if c != ' ': od.text((x, y), c, font=font, fill=255)
            x += cw
        y += ch
    return P.cov(out)

# =============================================================== plates


def plate_loop(P):
    """Hero: the agentic flowchart. The red feedback loop runs the length of the sheet."""
    S, rng = P.S, P.rng
    sd = np.minimum(sd_below(P, 512, 790, -.16), sd_circle(P, 800, 250, 150))
    field = P.edge_tone(sd, 26, torn=14)
    P.ink('red', P.screen(field, 75, 5.2))
    topo = P.isolines(P.warp(P.fbm(3, 5), 40), [.38, .44, .5, .56, .62], 1.3) * (field > .98)
    P.knock('red', topo)                                               # the ground under the red, as contours
    g, gd = P.layer(); agent_graph(P, gd, 800, 250, 140, 18, 3); P.knock('red', P.cov(g) * (sd_circle(P, 800, 250, 150) < 0)); P.ink('black', P.cov(g) * (sd_circle(P, 800, 250, 150) >= 0))
    f, fd = P.layer(); flowchart(P, fd, 360, 70, 1.42); P.ink('black', P.cov(f))
    lp, ld = P.layer()
    line(ld, P.pts([(150, 870), (150, 910), (52, 910), (52, 30), (360, 30), (360, 60)]), 5)
    arrow(ld, P.p(360, 46), P.p(360, 68), 5, 16 * S)
    line(ld, P.pts([(150, 910), (150, 1180), (520, 1180)]), 5); arrow(ld, P.p(500, 1180), P.p(548, 1180), 5, 16 * S)
    line(ld, P.pts([(480, 200), (636, 200)]), 5); arrow(ld, P.p(620, 200), P.p(648, 200), 5, 16 * S)
    L = P.cov(lp); P.ink('red', L * (field < .5)); P.knock('red', L * (field >= .5))
    ms, md = P.layer(); sprite_of_sprites(P, md, 'alien', 500, 815, 46); P.ink('black', P.crayon(P.cov(ms), .35, .08))
    lv, lvd = P.layer(); level(P, lvd, 70, 1230, 14, 2); P.knock('red', P.cov(lv))


def plate_tile(P):
    """Hero: the magnifier. One tile of a level opened, a tangle of agents inside."""
    S = P.S; C, R = (632, 380), 300
    inside = sd_circle(P, *C, R) < 0
    t = (P.Y - (C[1] - R)) / (2 * R)
    P.ink('red', P.screen(np.clip(1.25 - 1.45 * t, 0, 1), 75, 6.5) * inside)
    cl, lines = cloud_bank(P, .14, .07); P.ink('black', np.maximum(cl, lines) * ~inside)
    g, gd = P.layer(); agent_graph(P, gd, *C, R, 30, 3); P.ink('black', P.cov(g) * inside)
    r, rd = P.layer(); ring(rd, P.p(*C), R * S, 5); ring(rd, P.p(*C), (R - 14) * S, 2); P.ink('black', P.cov(r))
    lv, lvd = P.layer(); sel = level(P, lvd, 40, 960, 34, 4); P.ink('black', P.cov(lv))
    sl, sld = P.layer(); ring(sld, P.p(*sel), 30 * S, 6); P.ink('red', P.cov(sl))
    dl, dld = P.layer()
    for s_ in (-1, 1):
        a = math.atan2(C[1] - sel[1], C[0] - sel[0]) + s_ * math.pi / 2; bb = math.atan2(sel[1] - C[1], sel[0] - C[0])
        dashed(dld, P.p(sel[0] + 30 * math.cos(a), sel[1] + 30 * math.sin(a)), P.p(C[0] + R * math.cos(bb - s_ * 1.0), C[1] + R * math.sin(bb - s_ * 1.0)), 3, 9 * S, 7 * S)
    P.ink('black', P.cov(dl))
    # the level again, at body scale: two passes that never quite agree
    fill, fdd = P.layer(); edge, ed = P.layer(); T = 52; base = 1250
    hs = [2, 2, 4, 4, 1, 1, 6, 6, 3, 3, 3, 5, 1, 2, 2, 7, 7]
    for i, h in enumerate(hs):
        x = 470 + i * T
        if x > DW - 40: break
        for j in range(h):
            box = [*P.p(x, base - (j + 1) * T + 5), *P.p(x + T - 5, base - j * T)]
            fdd.rectangle(box, fill=255) if (i * 7 + j * 3) % 5 else None
            ed.rectangle([box[0] + 7 * S, box[1] - 5 * S, box[2] + 7 * S, box[3] - 5 * S], outline=255, width=3 * S)
    P.ink('red', P.cov(fill)); P.ink('black', P.crayon(P.cov(edge), .45, .05))


def plate_room(P):
    """Hero: the arcade in plan. The agent's reach is a red screen that thins with distance."""
    S = P.S; cx, cy, R = 512, 430, 340
    hx, hxd = P.layer(); hxd.polygon(P.pts([(cx + (R - 8) * math.cos(math.pi / 3 * k), cy + (R - 8) * math.sin(math.pi / 3 * k)) for k in range(6)]), fill=255)
    hexin = P.cov(hx)
    dist = np.hypot(P.X - cx, P.Y - cy)
    P.ink('red', P.screen(np.clip(1.05 - dist / 330, 0, 1) ** .9, 75, 9.0) * hexin)
    h, hd = P.layer(); players, cab = hexplan(P, hd, cx, cy, R, 4); P.ink('black', P.cov(h))
    wi, wd = P.layer()
    for x, y in players: dashed(wd, P.p(cx, cy), P.p(x, y), 3, 8 * S, 6 * S)
    for x, y in cab: line(wd, [P.p(cx, cy), P.p(x, y)], 2)
    P.ink('black', P.cov(wi))
    hub, hbd = P.layer(); disc(hbd, P.p(cx, cy), 34 * S); P.clear(P.cov(hub))
    hr, hrd = P.layer(); disc(hrd, P.p(cx, cy), 15 * S); ring(hrd, P.p(cx, cy), 27 * S, 5); P.ink('red', P.cov(hr))
    band = P.edge_tone(sd_below(P, 0, 920, .06), 30, torn=16)
    P.ink('red', P.screen(band, 75, 5.2))
    g, gd = P.layer(); agent_graph(P, gd, 150, 1110, 120, 14, 3); P.knock('red', P.cov(g))
    pn, pnd = P.layer(); control_panel(P, pnd, 360, 900, .98); P.ink('black', P.crayon(P.cov(pn)))
    m, mdd = P.layer(); lattice_mast(P, mdd, 70, 880, 110, 70, 24, 3, 4, 1); P.ink('black', P.cov(m) * (1 - (band > .5)))


def plate_operator(P):
    """Hero: the operator at the console, printed in marks, crossed by the red column."""
    S = P.S
    col = P.edge_tone(sd_box(P, 600, 640, 120, 700), 24, torn=12)
    P.ink('red', P.screen(col, 75, 5.2))

    def body(dd):
        dd.polygon(P.pts([(420, 450), (395, 500), (360, 545), (385, 556), (380, 585), (395, 612), (425, 650), (480, 668), (530, 640), (540, 470)]), fill=110)
        dd.ellipse([*P.p(425, 380), *P.p(625, 640)], fill=255)
        dd.polygon(P.pts([(470, 640), (460, 720), (560, 720), (560, 620)]), fill=130)
        dd.polygon(P.pts([(470, 680), (420, 720), (360, 1000), (420, 1270), (790, 1270), (760, 860), (660, 700), (560, 660)]), fill=165)
        dd.polygon(P.pts([(425, 760), (300, 940), (232, 1010), (272, 1042), (362, 982), (475, 830)]), fill=120)
        dd.ellipse([*P.p(415, 518), *P.p(437, 534)], fill=255)
    fig = ascii_figure(P, body)
    incol = col > .5
    P.knock('red', fig * incol); P.ink('black', fig * ~incol)
    ds, dsd = P.layer(); datasheet(P, dsd, 740, 1000, 70, 1220, 34, 9); P.ink('black', P.cov(ds) * ~incol)
    wg, wgd = P.layer(); wing(P, wgd, (660, 760), (720, 360), (1000, 250), 1, 1.0); P.ink('black', P.cov(wg))
    hl, hld = P.layer()
    for o in (0, 10): hld.ellipse([*P.p(395 - o, 330 - o / 3), *P.p(605 + o, 380 + o / 3)], outline=255, width=5)
    P.knock('red', P.cov(hl) * incol); P.ink('red', P.cov(hl) * ~incol)
    cr, crd = P.layer(); mx = 80
    line(crd, P.pts([(mx, 360), (mx + 120, 340), (mx + 140, 340), (mx + 140, 860), (mx + 120, 860), (mx, 830), (mx, 360)]), 4)
    crd.rectangle([*P.p(mx - 30, 860), *P.p(mx + 180, 890)], outline=255, width=4)
    line(crd, P.pts([(mx + 40, 890), (mx + 20, 1010), (mx + 160, 1010), (mx + 130, 890)]), 4)
    kx, ky = 150, 1030
    line(crd, P.pts([(kx, ky), (kx + 260, ky - 20), (kx + 300, ky + 50), (kx + 30, ky + 80), (kx, ky)]), 4)
    for r_ in range(4):
        for c_ in range(10):
            x = kx + 20 + c_ * 24 + r_ * 6; y = ky + 10 + r_ * 15 - c_ * 1.8; crd.rectangle([*P.p(x, y), *P.p(x + 16, y + 9)], outline=255, width=2)
    P.ink('black', P.cov(cr))
    sc, scd = P.layer(); scd.polygon(P.pts([(mx + 4, 364), (mx + 118, 346), (mx + 118, 852), (mx + 4, 826)]), fill=255); P.ink('red', P.cov(sc))
    mz, mzd = P.layer()
    for i in range(9):
        for j in range(30):
            if P.rng.random() < .45:
                x = mx + 14 + i * 10; y = 372 + j * 15 - i * 1.5; mzd.rectangle([*P.p(x, y), *P.p(x + 8, y + 12)], fill=255)
    P.knock('red', P.cov(mz))
    bm, bmd = P.layer()
    for _ in range(380):
        y = P.rng.gauss(520, 50); x0 = mx + 140 + P.rng.uniform(0, 30)
        bmd.line([P.p(x0, y), P.p(P.rng.uniform(300, 445), y + P.rng.uniform(-28, 28))], fill=255, width=P.rng.choice([2, 2, 3, 5]))
    for _ in range(60):
        x = P.rng.uniform(240, 440); y = P.rng.gauss(520, 46); bmd.rectangle([*P.p(x, y), *P.p(x + P.rng.uniform(6, 30), y + P.rng.uniform(3, 10))], fill=255)
    B = P.cov(bm); P.ink('red', B * ~incol); P.ink('black', B * incol)


def plate_rig(P):
    """Hero: the D-pad as an emblem on a drilling platform, under a screened red sun."""
    S = P.S; cx, cy = 512, 560
    sun = sd_circle(P, cx, cy, 290) < 0
    t = (P.Y - (cy - 290)) / 580
    P.ink('red', P.screen(np.clip(1.6 - 1.7 * t, 0, 1), 75, 6.0) * sun)
    P.ink('red', P.screen(P.edge_tone(sd_below(P, 0, 1110, -.04), 22, torn=10), 75, 5.2))
    cl, lines = cloud_bank(P, .6, .2, .4)
    dp, dpd = P.layer(); a_, b_, inner = 236, 80, 24
    dpd.rectangle([*P.p(cx - a_, cy - b_), *P.p(cx + a_, cy + b_)], fill=255); dpd.rectangle([*P.p(cx - b_, cy - a_), *P.p(cx + b_, cy + a_)], fill=255)
    padall = P.cov(dp)
    inn, ind = P.layer(); ind.rectangle([*P.p(cx - a_ + inner, cy - b_ + inner), *P.p(cx + a_ - inner, cy + b_ - inner)], fill=255); ind.rectangle([*P.p(cx - b_ + inner, cy - a_ + inner), *P.p(cx + b_ - inner, cy + a_ - inner)], fill=255)
    padin = P.cov(inn)
    P.ink('black', np.maximum(cl, lines) * (1 - padall))
    m, mdd = P.layer()
    lattice_mast(P, mdd, 170, 1130, 300, 120, 40, 3, 5, -1); lattice_mast(P, mdd, 855, 1170, 210, 150, 50, 3, 5, 1)
    line(mdd, P.pts([(60, 1130), (980, 1170)]), 5)
    for k in range(12):
        x = 260 + k * 45; line(mdd, P.pts([(x, 1133 + k * 2), (x + 30, 1090 + k * 2), (x + 60, 1136 + k * 2)]), 3)
    M_ = P.cov(m); ground = P.plate['red'] > .5
    P.ink('black', M_ * ~ground); P.knock('red', M_ * ground)
    P.clear(padall)
    P.ink('black', P.crayon(padall * (1 - padin), .35, .05))
    g, gd = P.layer(); agent_graph(P, gd, cx, cy, 215, 20, 3); P.ink('black', P.cov(g) * padin)
    sp, spd = P.layer()
    for nm, (x, y) in [('alien', (cx - 190, cy - 14)), ('coin', (cx + 150, cy - 14)), ('heart', (cx - 14, cy - 190)), ('chest', (cx - 16, cy + 165))]:
        sprite(spd, nm, *P.p(x, y), 4 * S)
    P.ink('red', P.cov(sp))
    wg, wgd = P.layer(); wing(P, wgd, (cx + 50, cy - a_ - 6), (720, 140), (1000, 130), 1, .66); wing(P, wgd, (cx - 50, cy - a_ - 6), (304, 140), (24, 130), -1, .66)
    P.ink('black', P.cov(wg))
    tt, ttd = P.layer()
    for (x, y), nm in zip(poisson(P.rng, 7, (40, 40, 980, 300), 120, lambda x, y: abs(x - cx) > 160), ['T', 'S', 'L', 'O', 'I', 'T', 'S']):
        sprite(ttd, nm, *P.p(x, y), P.rng.choice([10, 12, 16]) * S)
    P.ink('red', P.cov(tt))


PLATES = {'loop': ('01-the-loop', plate_loop), 'tile': ('02-the-tile', plate_tile), 'room': ('03-the-room', plate_room),
          'operator': ('04-the-operator', plate_operator), 'rig': ('05-the-rig', plate_rig)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seeds', default='1'); ap.add_argument('--only', default=','.join(PLATES))
    ap.add_argument('--scale', type=int, default=2); ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    seeds = [int(s) for s in a.seeds.split(',')]; keys = a.only.split(',')
    thumbs = {}
    for k in keys:
        stem, fn = PLATES[k]
        for sd in seeds:
            t0 = time.time(); P = Press(sd * 1000 + list(PLATES).index(k), a.scale)
            fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
            name = f'{stem}-s{sd}' if len(seeds) > 1 else stem
            img.save(os.path.join(a.out, name + '.png'))
            meta = {'plate': k, 'seed': sd, 'scale': a.scale, 'coverage': P.stats(), 'seconds': round(time.time() - t0, 1)}
            json.dump(meta, open(os.path.join(a.out, name + '.json'), 'w'), indent=1)
            print(name, json.dumps(meta['coverage']), f"{meta['seconds']}s", flush=True)
            thumbs[(k, sd)] = img.resize((256, 320), Image.LANCZOS)
    if a.sheet:
        g = 12; sheet = Image.new('RGB', (len(seeds) * (256 + g) + g, len(keys) * (320 + g) + g), (40, 38, 36))
        for r, k in enumerate(keys):
            for c, sd in enumerate(seeds): sheet.paste(thumbs[(k, sd)], (g + c * (256 + g), g + r * (320 + g)))
        sheet.save(os.path.join(a.out, 'contact-sheet.png')); print('contact-sheet.png')


if __name__ == '__main__':
    main()
