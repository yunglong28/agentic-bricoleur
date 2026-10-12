"""THE AGENTIC BRICOLEUR — the diagram on its own: a Maciunas chart of the essay's lineage.

Each lane starts at its year with a bare node (no emblem) and a typed name, runs toward the present, and is
tied to the lanes it fed. All of them braid into the red BRICOLAGE trunk at 2026. Out of the trunk the
chart splits, as the essay does: a few thick lines climb into one black block (upstream: models, compute,
rent); many thin ones spill down into small rings (downstream: situated software, the commons).

  d1 diagramma        paper, red and black
  d2 diagramma-notte  the same chart cut out of the dark

Usage: python3 bricoleur15.py OUT [--only d1,d2] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
from PIL import ImageFont
import bricoleur3 as b3
W, H = 1536, 1024
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F, MONO, sd_box, bez, line, ring, disc, dashed, agent_graph

LANES = [  # year, name, the lanes it feeds (by name)
    (1962, 'bricolage — Lévi-Strauss', ['models & examples']),
    (1962, 'Fluxus', ['incursions']),
    (1965, 'Drop City', ['cyberdecks']),
    (1967, 'Logo', ['epistemological pluralism']),
    (1968, 'Whole Earth Catalog', ['cyberdecks', 'free software']),
    (1972, 'Supersurface', ['Liangzhu']),
    (1977, 'home computers', ['demoscene']),
    (1983, 'free software', ['open weights']),
    (1986, 'demoscene', ['modding']),
    (1990, 'epistemological pluralism', ['agentic coding']),
    (1996, 'modding', ['decompilation', 'incursions']),
    (2004, 'situated software', ['Liangzhu']),
    (2009, 'Taobao villages', ['Liangzhu']),
    (2012, 'cheap boards', ['cyberdecks']),
    (2019, 'models & examples', []),
    (2021, 'cyberdecks', []),
    (2023, 'open weights', []),
    (2024, 'decompilation', ['incursions']),
    (2025, 'agentic coding', ['incursions', 'Liangzhu']),
    (2026, 'incursions', []),
    (2026, 'Liangzhu', []),
]
Y0, Y1 = 1955, 2026
XL, XP = 90, 930                                            # 1955 and the present
xy = lambda yr: XL + (yr - Y0) / (Y1 - Y0) * (XP - XL)


def font(px, bold=False):
    return ImageFont.truetype(MONO, int(px), index=1 if bold else 0)


def node(d, P, x, y, kind, S):
    if kind == 0: ring(d, P.p(x, y), 8 * S, 2 * S); disc(d, P.p(x, y), 3 * S)
    elif kind == 1: disc(d, P.p(x, y), 7 * S)
    elif kind == 2: d.rectangle([*P.p(x - 7, y - 7), *P.p(x + 7, y + 7)], outline=255, width=int(2 * S))
    else: ring(d, P.p(x, y), 9 * S, 2 * S); ring(d, P.p(x, y), 4 * S, 2 * S)


def chart(P, night=False):
    S = P.S; X, Y = P.X, P.Y; rng = P.rng
    if night: P.ink('black', P.screen(np.clip(.84 + (P.fbm(5, 3) - .5) * .2, 0, 1), 15, 3.4))
    ink = (lambda M: P.knock('black', M)) if night else (lambda M: P.ink('black', M))
    # the ledger: a faint column per decade, the timeline on top, a red bracket over what has not happened
    g, gd = P.layer(); fo = font(12 * S)
    for yr in range(1960, 2030, 10):
        x = xy(yr); gd.line([*P.p(x, 62), *P.p(x, 80)], fill=255, width=2 * S); gd.text(P.p(x + 4, 44), str(yr), fill=255, font=fo)
        dashed(gd, P.p(x, 90), P.p(x, H - 40), 1 * S, 3 * S, 9 * S)
    gd.line([*P.p(XL, 80), *P.p(W - 40, 80)], fill=255, width=2 * S); ink(P.cov(g))
    bk, bkd = P.layer(); line(bkd, P.pts([(XP + 10, 92), (XP + 10, 100), (W - 40, 100), (W - 40, 92)]), 4 * S)
    P.knock('black', P.cov(bk)); P.ink('red', P.cov(bk))
    n = len(LANES); ys = np.linspace(140, H - 70, n); trunk = 560; tw = n * 5 + 10; xT0, xT1 = XP + 70, XP + 210
    pos = {name: (xy(yr), y) for (yr, name, _), y in zip(LANES, ys)}
    L, Ld = P.layer(); Tx, Txd = P.layer(); tr, trd = P.layer(); lf = font(12 * S); bf = font(12 * S, True)
    for i, ((yr, name, feeds), y) in enumerate(zip(LANES, ys)):
        x0 = xy(yr); node(Ld, P, x0, y, i % 4, S)
        if yr >= 2019:
            tw_ = (bf if yr >= 2024 else lf).getlength(name) / S; Txd.text(P.p(x0 - 52 - tw_, y - 8), name, fill=255, font=bf if yr >= 2024 else lf)
        else: Txd.text(P.p(x0 + 14, y - 22), name, fill=255, font=lf)
        Txd.text(P.p(x0 - 44, y - 6), str(yr), fill=255, font=font(10 * S))
        xb = max(x0 + 20, XP - 140 + rng.uniform(-60, 40)); ty = trunk + (i - n / 2) * 5
        Ld.line([*P.p(x0 + 10, y), *P.p(xb, y)], fill=255, width=2 * S)
        # a gap where the lineage went quiet
        if yr < 2000 and rng.random() < .5:
            g0 = rng.uniform(x0 + 60, max(x0 + 70, xb - 80)); dashed(Ld, P.p(g0, y), P.p(g0 + 50, y), 2 * S, 5 * S, 5 * S)
        line(Ld, bez(P.p(xb, y), P.p(xT0 - 30, y), P.p(xT0, ty), 60), 2 * S)
        trd.line([*P.p(xT0, ty), *P.p(xT1, ty)], fill=255, width=3 * S)
        for f in feeds:                                       # who fed whom: a drop line, a dot where it lands
            fx, fy = pos[f]; x = fx if fx > x0 + 12 else x0 + 24
            Ld.line([*P.p(x, y), *P.p(x, fy - 9)], fill=255, width=S); disc(Ld, P.p(x, y), 3 * S)
    M = P.cov(L); ink(M); T = P.cov(Tx); ink(T)
    band = P.edge_tone(sd_box(P, (xT0 + xT1) / 2, trunk, (xT1 - xT0) / 2, tw / 2 + 8), 1.5, torn=1.0)
    P.clear(band); P.ink('red', band); P.knock('red', P.cov(tr) * band)
    lb, lbd = P.layer(); lbd.text(P.p(xT0 + 4, trunk - tw / 2 - 30), 'BRICOLAGE', fill=255, font=font(16 * S, True))
    P.knock('black', P.cov(lb)); P.ink('red' if night else 'black', P.cov(lb))
    # after the trunk: upstream, a few thick lines into one block; downstream, many thin ones into small rings
    up, upd = P.layer(); bx, by = 1340, 250
    for k in range(5):
        ty = trunk - tw / 2 + 6 + k * 3; line(upd, bez(P.p(xT1, ty), P.p(xT1 + 120, ty), P.p(bx - 60 + k * 30, by + 70), 50), (5 - k * .5) * S)
    upd.text(P.p(bx - 70, by - 108), 'UPSTREAM', fill=255, font=font(11 * S, True))
    dn, dnd = P.layer(); rings = []
    for _ in range(46):
        rx, ry = rng.uniform(1250, W - 50), rng.uniform(620, H - 70); rings.append((rx, ry))
        ty = trunk + rng.uniform(0, tw / 2); line(dnd, bez(P.p(xT1, ty), P.p(xT1 + rng.uniform(40, 140), ty + rng.uniform(0, 60)), P.p(rx, ry), 40), S)
        ring(dnd, P.p(rx, ry), rng.choice([4, 5, 7, 9]) * S, max(1, int(1.5 * S)))
    for _ in range(26):
        a, b = rng.sample(rings, 2)
        if math.hypot(a[0] - b[0], a[1] - b[1]) < 130: dashed(dnd, P.p(*a), P.p(*b), max(1, S), 4 * S, 4 * S)
    dnd.text(P.p(1260, H - 40), 'DOWNSTREAM', fill=255, font=font(11 * S, True))
    ink(P.cov(up)); ink(P.cov(dn))
    blk = P.edge_tone(sd_box(P, bx, by, 90, 60), 1.2)
    if night: P.clear(blk); P.ink('red', blk)
    else: P.clear(blk); P.ink('black', blk)
    if not night:
        for rx, ry in rng.sample(rings, 12):
            m, d = P.layer(); disc(d, P.p(rx, ry), 4 * S); M = P.cov(m); P.clear(M); P.ink('red', M)


def d1(P): chart(P, False)
def d2(P): chart(P, True)


PLATES = {'d1': ('d1-diagramma', d1), 'd2': ('d2-diagramma-notte', d2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time()
        if k == 'd2': b3.PAPER = np.array([232, 228, 218], np.float32) / 255; b3.INK['red'] = np.array([255, 120, 30], np.float32) / 255; b3.INK['black'] = np.array([20, 18, 24], np.float32) / 255
        P = Press(a.seed * 1000 + 150 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + '.png')); print(stem, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
