"""THE AGENTIC BRICOLEUR — Children's Games at night: variations on the commons, the rent and the bazaar.

Same square and same games as bricoleur11; here the ground is dark and the paths are cut out of it, so the
crowd reads as light. The accent ink is the fire, the net, the share that is taken.

  n1 commons          the net round one shared fire (three palettes: notte, notte-blu, notte-rossa)
  n2 fuochi           many small fires, each with its own net, the fires tied to each other: a federation
  n3 vortice          the crowd turning round the fire, slow, Bosch's hell made warm
  n4 rendita          the share of every game drawn into the shaft, at night
  n5 nuvola           the share carried up the shaft and set orbiting in a ring above the square: the cloud
  n6 mercato          the night market: lit stalls in rows down the street, visitors cut between them
  n7 bazar            the day market again, larger stalls, a thicker crowd

Usage: python3 bricoleur12.py OUT [--only n1,n4] [--seed 1] [--palette notte-blu]
"""
import argparse, os, time
import numpy as np
import bricoleur3 as b3
import bricoleur11 as e
from bricoleur11 import (W, H, F, C, VP, scr, square, spots, play, stack, width, folla, sigil, mst, ground_ok,
                         Wind, toward, swirl, trails, soft_form, sd_box, dashed, GAMES, persp)

PALETTES = {                 # paper, accent, key
    'notte': (C(232, 228, 218), C(255, 120, 30), C(20, 18, 24)),
    'notte-blu': (C(234, 230, 220), C(255, 160, 40), C(18, 26, 60)),
    'notte-rossa': (C(236, 232, 224), C(249, 57, 34), C(24, 21, 20)),
    'giorno': (C(240, 236, 228), C(0, 166, 110), C(120, 24, 44)),
}
DEFAULT = {'n1': 'notte', 'n2': 'notte', 'n3': 'notte-rossa', 'n4': 'notte', 'n5': 'notte-blu', 'n6': 'notte', 'n7': 'giorno'}


def palette(name):
    paper, acc, key = PALETTES[name]; b3.PAPER = paper; b3.INK['red'] = acc; b3.INK['black'] = key


def night(P):
    P.ink('black', scr(P, np.clip(.82 + (P.fbm(5, 3) - .5) * .3, 0, 1)))
    return square(P, .98, 0)


def cut(P, path, wfn, red=None, glow=.35):
    """Trails cut out of the dark: the key-ink paths become paper (a little accent screened in), accent ones stay accent."""
    keep = {k: P.plate[k].copy() for k in P.plate}
    for k in P.plate: P.plate[k][:] = 0
    trails(P, path, wfn, red=np.zeros(path.shape[1], bool) if red is None else red)
    c, r = P.plate['black'].copy(), P.plate['red'].copy()
    P.plate['black'] = keep['black'] * (1 - c) * (1 - r)
    P.plate['red'] = np.maximum(keep['red'], np.maximum(P.screen(c * glow, 75, 2.4), r))


def glow(P, x, y, R, k=.6):
    P.knock('black', np.clip(1 - np.hypot(P.X - x, (P.Y - y) * 1.6) / R, 0, 1) ** 1.5 * k)


def fire(P, x, y, r=34, seed=11):
    f = soft_form(P, x, y, r, r * .5, seed); f = P.crayon((f > .4).astype(F), .6, .25); P.clear(f); P.ink('red', f)


def visits(P, G, home, wind, steps=160, k=2):
    """From each group, k walk to their fire and back."""
    rng = P.nr; out = []
    for c, h in zip(G, home):
        q = np.float32(c) + rng.normal(0, 8, (k, 2)).astype(np.float32); p = np.zeros((steps, k, 2), np.float32)
        for t in range(steps):
            q = q + toward(q, h if t < steps // 2 else np.float32(c)) * 3.2 + wind(q) * .5; p[t] = q
        out.append(p)
    return out

# ------------------------------------------------------------ plates


def commons(P):
    e.commons(P)


def fuochi(P):
    rng = P.nr; night(P); wind = Wind(P, 5, .8); G = spots(P, 90, 82)
    F_ = [f for f in spots(P, 40, 300) if 200 < f[0] < W - 260][:6]
    for x, y in F_: glow(P, x, y, 190, .5)
    Fz = np.float32(F_); home = [Fz[np.argmin(np.linalg.norm(Fz - np.float32(c), axis=1))] for c in G]
    paths = [play(P, GAMES[int(rng.integers(0, len(GAMES)))], c, int(rng.integers(8, 18)), wind=wind) for c in G] + [folla(P, 900, wind)]
    paths += visits(P, G, home, wind)
    cut(P, stack(paths), width)
    edges = []
    for j in range(len(F_)):
        idx = [i for i, h in enumerate(home) if (h == Fz[j]).all()]
        pts = [G[i] for i in idx] + [F_[j]]
        edges += [(pts[a], pts[b]) for a, b in e.mst(pts)]
    sigil(P, {'edges': edges, 'nodes': [(g, 7) for g in G]}, 1.3, ink='red', knock=True)
    m, d = P.layer()
    for a, b in e.mst(F_): dashed(d, P.p(*F_[a]), P.p(*F_[b]), 2 * P.S, 10 * P.S, 8 * P.S)
    M = P.cov(m); P.knock('black', M); P.ink('red', M)
    sigil(P, {'edges': [], 'nodes': [(f, 46) for f in F_]}, 1.4, ink='red', knock=True)
    for i, (x, y) in enumerate(F_): fire(P, x, y, 16 + 4 * persp(y), 11 + i)


def vortice(P):
    rng = P.nr; night(P); wind = Wind(P, 5, .7); f0 = np.float32([720, 660]); glow(P, *f0, 320, .7)
    G = [g for g in spots(P, 80, 85) if np.hypot(g[0] - f0[0], (g[1] - f0[1]) * 1.7) > 340]
    paths = [play(P, GAMES[int(rng.integers(0, len(GAMES)))], c, int(rng.integers(8, 18)), wind=wind) for c in G]
    n = 3000; a = rng.uniform(0, 2 * np.pi, n); R = rng.uniform(60, 330, n)
    p0 = (f0 + np.stack([np.cos(a) * R, np.sin(a) * R * .58], 1)).astype(np.float32); ring_r = R[:, None]
    def turn(p, v, t):
        d = (p - f0) * np.float32([1, 1 / .58]); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        tg = np.stack([-d[:, 1] * .58, d[:, 0]], 1) / r
        return tg - d / r * np.clip((r - ring_r * (1 - t / 900)) / 40, -1, 1) + wind(p) * .4, np.zeros(len(p), bool)
    pv = e.run(p0, turn, 110, 2.6, inertia=.86, jitter=.15, rng=rng)
    paths.append(folla(P, 900, wind)); m0 = sum(p.shape[1] for p in paths)
    cut(P, stack(paths), width)
    cut(P, pv, lambda y: .55 * width(y), red=rng.random(n) < .015)
    sigil(P, {'edges': [], 'nodes': [((f0[0], f0[1]), 70)]}, 1.4, ink='red', knock=True)
    fire(P, *f0, 40)


def _share(P, G, wind, mx, base, top, up_then, steps=340):
    rng = P.nr; paths, red = [], []
    for c in G:
        n = int(rng.integers(8, 20)); p = play(P, GAMES[int(rng.integers(0, len(GAMES)))], c, n, wind=wind)
        k = max(1, n // 4); q = p[-1, :k].copy(); q = np.where(np.isnan(q), np.float32(c), q)
        mouth = np.float32([mx, base]); ext = np.full((steps, n, 2), np.nan, np.float32); s = persp(c[1]); st = np.zeros(k, int)
        for t in range(steps):
            st = np.where((st == 0) & (np.linalg.norm(q - mouth, axis=1) < 30), 1, st); st = np.where((st == 1) & (q[:, 1] < top), 2, st)
            w = np.where((st == 0)[:, None], toward(q, mouth) * 2.6 * s + wind(q) * .4, np.float32([[0, -3.0]]) + rng.normal(0, .15, (k, 2)).astype(np.float32))
            if up_then is not None: w = np.where((st == 2)[:, None], up_then(q), w)
            q = q + w; q[:, 0] = np.where(st == 1, mx + (q[:, 0] - mx) * .9, q[:, 0])
            ok = (st < 2) | (up_then is not None); ext[t, :k] = np.where(ok[:, None], q, np.nan)
        paths.append(np.concatenate([p, ext])); red += [True] * k + [False] * (n - k)
    return paths, red


def shaft(P, mx, base, top):
    X, Y = P.X, P.Y
    sh = P.edge_tone(sd_box(P, mx, (base + top) / 2, 26, (base - top) / 2), 1.2); P.clear(sh); P.ink('black', sh)
    rungs = sh * ((Y % 22) < 3).astype(F) * (np.abs(X - mx) < 18); P.knock('black', rungs); P.ink('red', rungs)
    mo = P.edge_tone(sd_box(P, mx, base - 10, 34, 14), 1); P.clear(mo); P.ink('red', mo)


def rendita(P):
    night(P); wind = Wind(P, 5, .8); mx, base, top = 780, 610, 10
    G = [g for g in spots(P, 95, 80) if abs(g[0] - mx) > 70 or g[1] > base + 40]
    paths, red = _share(P, G, wind, mx, base, top, None)
    cut(P, stack(paths + [folla(P, 1000, wind)]), width, red=np.r_[red, np.zeros(1000, bool)])
    shaft(P, mx, base, top)
    sigil(P, {'edges': [((mx - 160, 120), (mx + 160, 120)), ((mx, 40), (mx, 200))], 'nodes': [((mx, 120), 60), ((mx, 120), 100)]}, 1.6, ink='red', knock=True)


def nuvola(P):
    night(P); wind = Wind(P, 5, .8); mx, base, top = 760, 640, 230; O = np.float32([mx, 130])
    def orbit(q):
        d = (q - O) * np.float32([1, 4]); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        return (np.stack([-d[:, 1] / 4, d[:, 0]], 1) / r - d / r * np.clip((r - 420) / 60, -1, 1)) * 3.2
    G = [g for g in spots(P, 95, 80) if abs(g[0] - mx) > 70 or g[1] > base + 40]
    paths, red = _share(P, G, wind, mx, base, top, orbit, 640)
    cut(P, stack(paths + [folla(P, 1000, wind)]), width, red=np.r_[red, np.zeros(1000, bool)])
    shaft(P, mx, base, top)
    m, d = P.layer()
    for R in (380, 460): d.ellipse([*P.p(mx - R, 130 - R / 4), *P.p(mx + R, 130 + R / 4)], outline=255, width=int(2.2 * P.S))
    M = P.cov(m); P.knock('black', M); P.ink('red', M)


def _stalls(P, rows=7, per=11):
    """Market rows running into the street's vanishing point; stalls along them, smaller far away."""
    out = []
    for r in range(rows):
        x_end = -200 + r * (W + 300) / (rows - 1); a = np.float32(VP); b = np.float32([x_end, H + 60])
        for k in range(per):
            t = .18 + .82 * (k / (per - 1)) ** 1.25; x, y = a + (b - a) * t
            if ground_ok(x, y) and P.rng.random() < .85: out.append((float(x), float(y)))
    return out


def mercato(P):
    rng = P.nr; night(P); wind = Wind(P, 5, .8); St = _stalls(P, 9, 13)
    for x, y in St: glow(P, x, y, 70 * persp(y), .55)
    paths = []; m, d = P.layer()
    for i, c in enumerate(St):
        s = persp(c[1]); hw, hh = 52 * s, 30 * s
        d.rectangle([*P.p(c[0] - hw, c[1] - hh), *P.p(c[0] + hw, c[1] + hh)], outline=255, width=max(1, int(1.6 * P.S)))
        n = int(rng.integers(6, 14)); p = play(P, GAMES[i % len(GAMES)], c, n, steps=110, wind=wind)
        paths.append(np.clip(p, np.float32(c) - np.float32([hw, hh]) + 2, np.float32(c) + np.float32([hw, hh]) - 2))
    paths += visits(P, St, [np.float32(St[j]) for j in rng.integers(0, len(St), len(St))], wind, 180, 3)
    paths.append(folla(P, 900, wind))
    cut(P, stack(paths), width, glow=.25)
    M = P.cov(m); P.knock('black', M); P.ink('red', M)
    m2, d2 = P.layer()
    for a, b in e.mst(St):
        if rng.random() < .6: dashed(d2, P.p(*St[a]), P.p(*St[b]), 1.6 * P.S, 6 * P.S, 7 * P.S)
    M2 = P.cov(m2); P.knock('black', M2); P.ink('red', P.screen(M2 * .6, 75, 2.2))


def bazar(P):
    rng = P.nr; square(P, .5); wind = Wind(P, 5, .8); St = _stalls(P, 8, 12)
    trails(P, folla(P, 1100, wind), lambda y: .5 * width(y))
    paths = []; m, d = P.layer()
    for i, c in enumerate(St):
        s = persp(c[1]); hw, hh = 50 * s, 30 * s
        d.rectangle([*P.p(c[0] - hw, c[1] - hh), *P.p(c[0] + hw, c[1] + hh)], outline=255, width=max(1, int(1.6 * P.S)))
        n = int(rng.integers(8, 16)); p = play(P, GAMES[i % len(GAMES)], c, n, steps=110, wind=wind)
        paths.append(np.clip(p, np.float32(c) - np.float32([hw, hh]) + 2, np.float32(c) + np.float32([hw, hh]) - 2))
    M = P.cov(m); P.ink('black', scr(P, .75, 15, 2.4) * M)
    vis = visits(P, St, [np.float32(St[j]) for j in rng.integers(0, len(St), len(St))], wind, 180, 2)
    trails(P, stack(paths), width)
    vv = stack(vis); trails(P, vv, lambda y: .4 * width(y), red=np.ones(vv.shape[1], bool))


PLATES = {'n1': ('n1-commons', commons), 'n2': ('n2-fuochi', fuochi), 'n3': ('n3-vortice', vortice), 'n4': ('n4-rendita', rendita),
          'n5': ('n5-nuvola', nuvola), 'n6': ('n6-mercato', mercato), 'n7': ('n7-bazar', bazar)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1); ap.add_argument('--palette', default=None); ap.add_argument('--suffix', default='')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time(); palette(a.palette or DEFAULT[k])
        P = b3.Press(a.seed * 1000 + 60 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + a.suffix + '.png')); print(stem + a.suffix, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
