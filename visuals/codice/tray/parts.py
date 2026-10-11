"""The repertoire: odds and ends kept because they might come in handy.
Every part is drawn about the origin inside radius r, with the house pens, and nothing written on it.
"""
import math
import numpy as np
import skia
from draw import HAIR, FINE, REG, BOLD, HEAVY

TAU = 2 * math.pi


def _pc(r, a): return (r * math.cos(a), r * math.sin(a))


def gear(p, r, rng):
    n = rng.choice([10, 12, 14, 16]); ro, ri = r * .95, r * .78
    pts = []
    for k in range(n):
        a = k * TAU / n; d = TAU / n
        for (rr, aa) in ((ri, a), (ro, a + d * .18), (ro, a + d * .5), (ri, a + d * .68)):
            pts.append(_pc(rr, aa))
    p.poly(pts, REG)
    p.circle((0, 0), r * .52, FINE); p.circle((0, 0), r * .2, REG)
    for k in range(4):
        a = k * TAU / 4 + .4; p.circle(_pc(r * .37, a), r * .07, FINE)


def spring(p, r, rng):
    n = 9; w = r * .45
    for k in range(n):
        y = -r * .8 + k * (1.6 * r / n)
        p.oval(-w, y, 2 * w, 1.6 * r / n * 1.4, FINE)
    p.line([(-w, -r * .8), (-w, -r * .95), (0, -r * .95)], REG)
    p.line([(w, r * .85), (w, r * .95), (0, r * .95)], REG)


def key(p, r, rng):
    p.circle((-r * .55, 0), r * .36, REG); p.circle((-r * .55, 0), r * .14, FINE)
    p.line([(-r * .19, -r * .06), (r * .9, -r * .06)], REG); p.line([(-r * .19, r * .06), (r * .9, r * .06)], REG)
    p.line([(r * .9, -r * .06), (r * .9, r * .06)], REG)
    for x, h in ((.45, .28), (.6, .18), (.75, .3)):
        p.rect(r * x, r * .06, r * .1, r * h, FINE)


def bolt(p, r, rng):
    hx = [_pc(r * .42, k * TAU / 6) for k in range(6)]
    p.c.save(); p.c.translate(0, -r * .55)
    p.poly([(x, y * .4) for x, y in hx], REG)
    p.line([(-r * .42, 0), (-r * .42, r * .16)], REG); p.line([(r * .42, 0), (r * .42, r * .16)], REG)
    p.line([(-r * .42, r * .16), (r * .42, r * .16)], REG)
    p.c.restore()
    p.rect(-r * .2, -r * .39, r * .4, r * 1.3, REG)
    for k in range(9):
        y = -r * .32 + k * r * .13; p.line([(-r * .2, y), (r * .2, y + r * .07)], HAIR)


def lens(p, r, rng):
    path = skia.Path(); path.moveTo(0, -r * .9)
    path.quadTo(r * .55, 0, 0, r * .9); path.quadTo(-r * .55, 0, 0, -r * .9); path.close()
    p.path(path, REG)
    for k in (1, 2, 3):
        f = k / 4
        q = skia.Path(); q.moveTo(0, -r * .9 * (1 - f * .2)); q.quadTo(r * .55 * (1 - f), 0, 0, r * .9 * (1 - f * .2))
        p.path(q, HAIR)
    for k in range(-3, 4):
        y = k * r * .2; p.line([(-r * .95, y * 1.6), (-r * .3, y)], HAIR); p.line([(r * .3, y * .4), (r * .95, -y * .3)], HAIR)


def coil(p, r, rng):
    path = skia.Path(); first = True
    for t in np.linspace(0, TAU * 5.5, 300):
        rr = r * (.12 + .78 * t / (TAU * 5.5)); x, y = rr * math.cos(t), rr * math.sin(t)
        if first: path.moveTo(x, y); first = False
        else: path.lineTo(x, y)
    p.path(path, FINE)
    p.curve((r * .9, 0), (r * 1.1, r * .5), (r * .7, r * .95), REG)


def dial(p, r, rng):
    p.circle((0, 0), r * .9, REG); p.circle((0, 0), r * .72, HAIR)
    for k in range(24):
        a = math.radians(135 + k * 270 / 23); l = .62 if k % 4 == 0 else .67
        p.line([_pc(r * l, a), _pc(r * .72, a)], FINE if k % 4 == 0 else HAIR)
    a = math.radians(rng.uniform(150, 390)); p.line([(0, 0), _pc(r * .6, a)], BOLD); p.disc((0, 0), r * .1)


def valve(p, r, rng):
    p.circle((0, 0), r * .85, BOLD); p.circle((0, 0), r * .72, HAIR); p.circle((0, 0), r * .16, REG)
    for k in range(5):
        a = k * TAU / 5 - math.pi / 2
        p.line([_pc(r * .16, a), _pc(r * .74, a)], REG); p.disc(_pc(r * .85, a), r * .09)


def mast(p, r, rng):
    n = 7; wb, wt = r * .7, r * .22
    L = [(-wb / 2, r * .95), (-wt / 2, -r * .8)]; R = [(wb / 2, r * .95), (wt / 2, -r * .8)]
    p.line(L, REG); p.line(R, REG)
    rows = []
    for i in range(n + 1):
        t = i / n; y = r * .95 + (-r * 1.75) * t; w = wb + (wt - wb) * t
        rows.append(((-w / 2, y), (w / 2, y))); p.line(list(rows[-1]), FINE)
    for a, b in zip(rows, rows[1:]): p.line([a[0], b[1]], HAIR); p.line([a[1], b[0]], HAIR)
    p.rect(-wt / 2 - r * .12, -r * .95, wt + r * .24, r * .15, FINE)


def feather(p, r, rng):
    p.curve((0, r * .95), (r * .12, 0), (-r * .05, -r * .95), REG)
    for k in range(18):
        t = .12 + k * .048
        y = r * .95 - t * r * 1.9; x = r * .12 * 4 * t * (1 - t) * .5
        l = r * .5 * math.sin(math.pi * min(1, t * 1.1))
        p.curve((x, y), (x - l * .5, y - r * .02), (x - l, y - r * .18), HAIR)
        p.curve((x, y), (x + l * .5, y - r * .02), (x + l, y - r * .16), HAIR)


SPR = {
    'alien': ["...XXXXX...", ".XXXXXXXXX.", "XX..XXX..XX", "XXXXXXXXXXX", ".X.XX.XX.X.", "X.........X", ".X.......X."],
    'heart': [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
    'ship': ["....X....", "...XXX...", "...XXX...", ".X.XXX.X.", "XXXXXXXXX", "XX.XXX.XX", "X...X...X"],
    'hero': ["..XXX..", "..XXX..", "...X...", ".XXXXX.", "X.XXX.X", "..X.X..", ".XX.XX."],
    'coin': ["..XXX..", ".X...X.", "X..X..X", "X..X..X", "X..X..X", ".X...X.", "..XXX.."],
    'chest': ["XXXXXXXX", "X......X", "XXXXXXXX", "X..XX..X", "X......X", "XXXXXXXX"],
}


def sprite(p, r, rng, name=None):
    name = name or rng.choice(list(SPR))
    rows = SPR[name]; n = max(len(rows[0]), len(rows)); px = 1.5 * r / n
    ox, oy = -len(rows[0]) * px / 2, -len(rows) * px / 2
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == 'X': p.rect(ox + i * px + .2, oy + j * px + .2, px - .4, px - .4, fill=True)


def nodes(p, r, rng):
    pts = [_pc(r * rng.uniform(.2, .8), rng.uniform(0, TAU)) for _ in range(7)]
    for _ in range(11):
        a, b = rng.sample(pts, 2); m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); o = rng.uniform(-.5, .5)
        p.curve(a, (m[0] - (b[1] - a[1]) * o, m[1] + (b[0] - a[0]) * o), b, HAIR)
    for i, q in enumerate(pts):
        rr = r * rng.choice([.06, .09, .13, .17])
        if i < 2: p.disc(q, rr)
        else: p.circle(q, rr, FINE)


def flow(p, r, rng):
    s = r / 1.0
    p.rect(-s * .3, -s * .9, s * .6, s * .32, FINE); p.arrow((0, -s * .58), (0, -s * .3), FINE, 4)
    p.poly([(0, -s * .3), (s * .3, -s * .05), (0, s * .2), (-s * .3, -s * .05)], FINE)
    p.line([(0, s * .2), (0, s * .45)], FINE)
    for x in (-.55, 0, .55):
        p.circle((s * x, s * .65), s * .2, FINE)
    p.line([(-s * .55, s * .45), (s * .55, s * .45)], FINE)
    for x in (-.55, .55): p.line([(s * x, s * .45), (s * x, s * .45)], FINE)


def hexroom(p, r, rng):
    hx = [_pc(r * .92, k * TAU / 6 + math.pi / 6) for k in range(6)]
    p.poly(hx, REG); p.poly([_pc(r * .82, k * TAU / 6 + math.pi / 6) for k in range(6)], HAIR)
    for k in range(6):
        a = k * TAU / 6 + math.pi / 6 + math.pi / 6
        c = _pc(r * .62, a)
        with p.at(c[0], c[1], math.degrees(a) + 90): p.rect(-r * .17, -r * .04, r * .34, r * .08, HAIR)
        q = _pc(r * .32, a + .3); p.circle(q, r * .08, FINE); p.arc(q, r * .13, math.degrees(a) + 120, 100, HAIR)
    p.disc((0, 0), r * .05)


def pulley(p, r, rng):
    a, b = (-r * .45, -r * .35), (r * .5, r * .4); ra, rb = r * .38, r * .22
    p.circle(a, ra, REG); p.circle(a, ra * .3, FINE); p.circle(b, rb, REG); p.circle(b, rb * .35, FINE)
    d = math.atan2(b[1] - a[1], b[0] - a[0]); L = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.acos((ra - rb) / L)
    for s in (-1, 1):
        t = d + s * ang
        p.line([(a[0] + ra * math.cos(t), a[1] + ra * math.sin(t)), (b[0] + rb * math.cos(t), b[1] + rb * math.sin(t))], FINE)


def chain(p, r, rng):
    for k in range(4):
        x = -r * .75 + k * r * .5
        with p.at(x, 0, 0 if k % 2 == 0 else 0):
            if k % 2 == 0: p.rect(-r * .32, -r * .2, r * .64, r * .4, REG, r=r * .2); p.rect(-r * .2, -r * .07, r * .4, r * .14, HAIR, r=r * .07)
            else: p.line([(-r * .32, 0), (r * .32, 0)], BOLD)


def hinge(p, r, rng):
    p.rect(-r * .85, -r * .7, r * .78, r * 1.4, REG); p.rect(r * .07, -r * .7, r * .78, r * 1.4, REG)
    for k in range(5):
        y = -r * .7 + k * r * .28; p.rect(-r * .1, y, r * .2, r * .26, FINE, fill=(k % 2 == 0))
    for x in (-.5, .5):
        for y in (-.4, .4): p.circle((r * x, r * y), r * .07, FINE)


def magnet(p, r, rng):
    path = skia.Path(); path.moveTo(-r * .6, -r * .1); path.lineTo(-r * .6, r * .2)
    path.arcTo(skia.Rect.MakeXYWH(-r * .6, -r * .4, r * 1.2, r * 1.2), 180, -180, False); path.lineTo(r * .6, -r * .1)
    p.path(path, BOLD * 1.6)
    p.rect(-r * .75, -r * .7, r * .3, r * .5, fill=True); p.rect(r * .45, -r * .7, r * .3, r * .5, BOLD)
    for k in range(3):
        p.arc((0, -r * .45), r * (.4 + k * .16), 220, 100, HAIR)


def halo(p, r, rng):
    p.oval(-r * .9, -r * .28, r * 1.8, r * .56, REG); p.oval(-r * .82, -r * .2, r * 1.64, r * .4, HAIR)
    p.circle((0, r * .55), r * .22, FINE); p.disc((0, r * .55), r * .07)


def dish(p, r, rng):
    path = skia.Path(); path.moveTo(-r * .8, -r * .6); path.quadTo(0, r * .7, r * .8, -r * .6)
    p.path(path, BOLD); p.line([(-r * .8, -r * .6), (r * .8, -r * .6)], HAIR)
    p.line([(0, r * .05), (0, -r * .6)], FINE); p.disc((0, -r * .62), r * .06)
    p.line([(0, r * .07), (-r * .3, r * .9)], REG); p.line([(0, r * .07), (r * .3, r * .9)], REG)
    for k in range(3): p.arc((0, -r * .62), r * (.16 + k * .12), 200, 140, HAIR)


def plug(p, r, rng):
    p.rect(-r * .35, -r * .5, r * .7, r * .55, REG, r=r * .08)
    p.rect(-r * .22, -r * .85, r * .1, r * .35, FINE, fill=True); p.rect(r * .12, -r * .85, r * .1, r * .35, FINE, fill=True)
    p.rect(-r * .18, r * .05, r * .36, r * .15, FINE)
    p.curve((0, r * .2), (r * .1, r * .7), (r * .8, r * .55), REG, p3=(r * .9, r * .95))


def ladder(p, r, rng):
    for x in (-.3, .3): p.line([(r * x, -r * .95), (r * x * 1.15, r * .95)], REG)
    for k in range(8):
        y = -r * .85 + k * r * .24; p.line([(-r * .3, y), (r * .3, y)], FINE)


def elbow(p, r, rng):
    for rr, w in ((r * .35, REG), (r * .75, REG)):
        p.arc((-r * .75, r * .75), rr + r * .0, 270, 90, w)
    p.line([(-r * .75, r * .4 - r * .0), (-r * .95, r * .4)], REG)
    for (x, y, w_, h_) in ((-r * .95, -r * .08, r * .2, r * .56), (r * .32, r * .75 - r * .02, r * .48, r * .2)):
        pass
    p.rect(-r * .82, r * -.05, r * .14, r * .5, FINE)
    p.rect(-r * .45, r * .55, r * .52, r * .14, FINE)


def toggle(p, r, rng):
    p.rect(-r * .55, -r * .35, r * 1.1, r * .7, REG, r=r * .1)
    p.circle((0, 0), r * .2, FINE); p.line([(0, 0), (r * .38, -r * .7)], BOLD * 1.3); p.disc((r * .38, -r * .7), r * .1)
    for x in (-.4, .4): p.circle((r * x, r * .22), r * .05, HAIR)


def die(p, r, rng):
    s = r * .55
    top = [(0, -s * 1.1), (s, -s * .55), (0, 0), (-s, -s * .55)]
    p.poly(top, REG); p.poly([(-s, -s * .55), (0, 0), (0, s * 1.1), (-s, s * .55)], REG); p.poly([(s, -s * .55), (0, 0), (0, s * 1.1), (s, s * .55)], REG)
    p.disc((0, -s * .55), s * .1)
    for q in ((-s * .7, -s * .1), (-s * .3, s * .55)): p.disc(q, s * .09)
    for q in ((s * .3, -s * .1), (s * .5, s * .25), (s * .7, s * .6)): p.disc(q, s * .09)


def propeller(p, r, rng):
    for k in range(3):
        a = k * 120
        with p.at(0, 0, a):
            path = skia.Path(); path.moveTo(0, 0); path.cubicTo(r * .2, -r * .2, r * .9, -r * .25, r * .92, 0)
            path.cubicTo(r * .9, r * .12, r * .3, r * .1, 0, 0); p.path(path, REG)
    p.circle((0, 0), r * .14, REG); p.disc((0, 0), r * .05)


def screw(p, r, rng):
    p.circle((0, 0), r * .8, BOLD); p.circle((0, 0), r * .62, HAIR)
    a = rng.uniform(0, 180)
    with p.at(0, 0, a): p.rect(-r * .62, -r * .09, r * 1.24, r * .18, fill=True)


def prism(p, r, rng):
    tri = [(0, -r * .7), (r * .65, r * .45), (-r * .65, r * .45)]
    p.poly(tri, REG)
    p.line([(-r * .98, -r * .1), (-r * .3, -r * .08)], FINE)
    for k in range(5):
        p.line([(r * .3, -r * .02 + k * r * .04), (r * .98, -r * .25 + k * r * .14)], HAIR if k % 2 else FINE)


def cell(p, r, rng):
    p.rect(-r * .3, -r * .75, r * .6, r * 1.55, REG, r=r * .06); p.rect(-r * .12, -r * .9, r * .24, r * .15, FINE, fill=True)
    p.hatch(-r * .3, r * .2, r * .6, r * .6, r * .1, 45, HAIR)
    p.line([(-r * .3, r * .2), (r * .3, r * .2)], FINE)


def rings(p, r, rng):
    for k in range(4): p.circle((0, 0), r * (.25 + k * .22), FINE if k % 2 else REG)
    p.disc((0, 0), r * .1)


def tile(p, r, rng):
    s = r * .42
    for (i, j) in ((-1, 0), (0, 0), (1, 0), (0, -1)):
        p.rect(i * s - s / 2, j * s - s / 2 + s * .3, s, s, REG)
    p.rect(-s * .2, -s * 1.2 + s * .3 - s * .45, s * .4, s * .4, FINE, fill=True)


def blob(p, r, rng):
    from draw import blob_pts
    p.poly(blob_pts(0, 0, r * .45, r * .92, rng), FINE)
    for k, nm in enumerate(('coin', 'heart', 'hero')):
        with p.at(0, -r * .5 + k * r * .5): sprite(p, r * .2, rng, nm)


PARTS = {f.__name__: f for f in (gear, spring, key, bolt, lens, coil, dial, valve, mast, feather, sprite, nodes, flow,
                                 hexroom, pulley, chain, hinge, magnet, halo, dish, plug, ladder, elbow, toggle, die,
                                 propeller, screw, prism, cell, rings, tile, blob)}
SMALL = ['screw', 'sprite', 'die', 'rings', 'key', 'bolt', 'toggle', 'plug', 'halo', 'magnet', 'chain', 'cell']
LARGE = ['gear', 'spring', 'lens', 'coil', 'dial', 'valve', 'mast', 'feather', 'nodes', 'flow', 'hexroom', 'pulley',
         'hinge', 'dish', 'ladder', 'propeller', 'prism', 'tile', 'blob']
TALL = ['mast', 'feather', 'ladder', 'spring', 'cell', 'blob', 'lens']


def draw(p, name, x, y, r, rng, rot=0, **kw):
    with p.at(x, y, rot):
        PARTS[name](p, r, rng, **kw) if kw else PARTS[name](p, r, rng)
