"""THE AGENTIC BRICOLEUR — diagrams of where the value goes. No timeline, no words: only directions.

Width is quantity, chevrons and heads are direction. Red is value that leaves as rent (upstream, to the
model, the compute, the chips, the ground); black is value that stays and circulates (downstream, situated,
the commons).

  v1 flussi      many small sources merge; a thick red band climbs a stack of blocks to the top edge; thin
                 black ribbons fan down to local nodes, each turning its own small loop; dashed returns
  v2 tributo     a ring of nodes, each paying a red line in to one black centre and getting a trickle back;
                 some nodes tied to each other around the rim, their tribute thinner
  v3 recinto     the marketplace: shops in a grid inside an enclosure; every exchange climbs to the rail,
                 pays a red toll, comes back thinner; outside, a few nodes trade directly
  v4 delta       the last mile: one band splits and splits down to many endpoints, each closing a small loop;
                 a hair of red climbs back up the margin from every one of them
  v5 doppio      centripetal and centrifugal at once: red agents spiral into the centre, black ones out

  n1, n2         v1 and v2 cut out of the dark

Usage: python3 bricoleur16.py OUT [--only v1,v2] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
import bricoleur3 as b3
W, H = 1536, 1024
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F, sd_box, line, ring, disc, dashed
from bricoleur10 import run, swirl, toward, trails, Wind


def cubic(p0, p1, p2, p3, n=80):
    t = np.linspace(0, 1, n)[:, None]; p0, p1, p2, p3 = map(np.float32, (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def ribbon(d, P, pts, w0, w1):
    """A band along a centreline, width easing from w0 to w1."""
    pts = np.asarray(pts, np.float32); tg = np.gradient(pts, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1); w = np.linspace(w0, w1, len(pts))[:, None] / 2
    poly = np.concatenate([pts + nrm * w, (pts - nrm * w)[::-1]])
    d.polygon(P.pts([tuple(q) for q in poly]), fill=255)


def chevrons(d, P, pts, w0, w1, every=34, k=.42):
    """Direction marks inside a band: small Vs pointing downstream."""
    pts = np.asarray(pts, np.float32); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); L = np.r_[0, np.cumsum(seg)]
    for s in np.arange(every * .6, L[-1] - every * .3, every):
        i = int(np.searchsorted(L, s)); i = min(max(i, 1), len(pts) - 1); p = pts[i]; t = pts[i] - pts[i - 1]; t /= np.linalg.norm(t) + 1e-6
        n_ = np.float32([-t[1], t[0]]); w = (w0 + (w1 - w0) * s / L[-1]) * k
        if w < 2: continue
        a, b, c = p - t * w * .7 + n_ * w, p + t * w * .3, p - t * w * .7 - n_ * w
        line(d, P.pts([tuple(a), tuple(b), tuple(c)]), max(1, w * .28 * P.S))


def head(d, P, pts, size=12, w=2):
    pts = np.asarray(pts, np.float32); p = pts[-1]; t = pts[-1] - pts[-min(4, len(pts))]; t /= np.linalg.norm(t) + 1e-6; n_ = np.float32([-t[1], t[0]])
    d.polygon(P.pts([tuple(p), tuple(p - t * size + n_ * size * .45), tuple(p - t * size - n_ * size * .45)]), fill=255)


def dashed_path(d, P, pts, w=1.6, on=8, off=7):
    pts = np.asarray(pts, np.float32); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); L = np.r_[0, np.cumsum(seg)]; s = 0.0
    while s < L[-1]:
        e = min(L[-1], s + on); i0, i1 = np.searchsorted(L, s), np.searchsorted(L, e)
        q = pts[max(0, i0 - 1):i1 + 1]
        if len(q) > 1: line(d, P.pts([tuple(x) for x in q]), w * P.S)
        s += on + off


def loop(d, P, c, r, w=2):
    a = np.linspace(.4, 2 * np.pi - .2, 50); pts = np.stack([c[0] + np.cos(a) * r, c[1] + np.sin(a) * r * .8], 1)
    line(d, P.pts([tuple(q) for q in pts]), w * P.S); head(d, P, pts, r * .6)


class Ink:
    """Paper mode draws ink; night mode cuts paper out of the dark."""
    def __init__(self, P, night):
        self.P, self.night = P, night
        if night: P.ink('black', P.screen(np.clip(.84 + (P.fbm(5, 3) - .5) * .2, 0, 1), 15, 3.4))

    def black(self, M):
        (self.P.knock('black', M) if self.night else (self.P.clear(M), self.P.ink('black', M)))

    def red(self, M):
        self.P.clear(M); self.P.ink('red', M)

    def red_knocked(self, M):                             # chevrons inside a red band
        self.P.knock('red', M)
        if self.night: self.P.ink('black', M)

    def black_knocked(self, M):
        (self.P.ink('black', M) if self.night else self.P.knock('black', M))

# ------------------------------------------------------------ plates


def flussi(P, night=False):
    rng = P.rng; I = Ink(P, night); M0 = (640, 540)
    src = [(rng.uniform(70, 300), rng.uniform(110, 940)) for _ in range(44)]
    bl, bd = P.layer(); rd, rdd = P.layer(); kn, knd = P.layer(); rk, rkd = P.layer()
    for s in src:
        pts = cubic(s, (s[0] + 200, s[1]), (M0[0] - 160, M0[1] + (s[1] - M0[1]) * .15), M0); ribbon(bd, P, pts, 3.2, 2.0); ring(bd, P.p(*s), 7 * P.S, 2 * P.S)
    # upstream: one band climbing through a stack, each block smaller, out of the top edge
    stack = [(1060, 430, 70, 38), (1170, 300, 56, 30), (1260, 190, 42, 24), (1330, 95, 30, 18)]
    a = M0; wid = 64
    for j, (x, y, hw, hh) in enumerate(stack):
        pts = cubic(a, (a[0] + 150, a[1]), (x - 140, y), (x - hw, y)); ribbon(rdd, P, pts, wid, wid * .82); chevrons(rkd, P, pts, wid, wid * .82)
        rdd.rectangle([*P.p(x - hw, y - hh), *P.p(x + hw, y + hh)], fill=255); a = (x + hw, y); wid *= .8
    pts = cubic(a, (a[0] + 60, a[1]), (1420, 60), (1430, -20)); ribbon(rdd, P, pts, wid, wid * .9); chevrons(rkd, P, pts, wid, wid * .9)
    # downstream: thin ribbons fanning out to local nodes, each turning its own loop
    loc = [(rng.uniform(860, 1480), rng.uniform(640, 980)) for _ in range(30)]
    for c in loc:
        pts = cubic(M0, (M0[0] + 120, M0[1] + 40), (c[0] - 160, c[1] - 40), c); ribbon(bd, P, pts, 2.6, 1.6)
        loop(bd, P, (c[0] + 14, c[1] - 4), 11, 2)
        if rng.random() < .35:                                 # a hair of red goes back up: the subscription
            q = cubic(c, (c[0] + 40, c[1] - 200), (1400, 500), (1330, 140), 60); dashed_path(rdd, P, q, 1.4, 6, 8)
    for c in rng.sample(loc, 12):                              # the commons: returns to the sources, along the floor
        s = rng.choice(src); q = cubic(c, (c[0] - 200, H - 10), (s[0] + 200, H - 10), (s[0] + 10, s[1] + 10), 120)
        dashed_path(bd, P, q, 1.4); head(bd, P, q, 9)
    md, mdd = P.layer(); disc(mdd, P.p(*M0), 16 * P.S)
    I.black(P.cov(bl)); I.red(P.cov(rd)); I.red_knocked(P.cov(rk)); I.black(P.cov(md))


def tributo(P, night=False):
    rng = P.rng; I = Ink(P, night); C = np.float32([768, 512]); rx, ry = 620, 400
    bl, bd = P.layer(); rd, rdd = P.layer(); rk, rkd = P.layer()
    angs = np.sort(rng_uniform(rng, 0, 2 * np.pi, 64)); nodes = []; commons = set(i for i in range(64) if rng.random() < .3)
    for i, a in enumerate(angs):
        r = rng.uniform(.82, 1.0); p = (C[0] + math.cos(a) * rx * r, C[1] + math.sin(a) * ry * r); nodes.append(p)
        w = 3 if i in commons else 8
        q = cubic(p, (p[0] + (C[0] - p[0]) * .3, p[1] + (C[1] - p[1]) * .1), (C[0] + (p[0] - C[0]) * .35, C[1] + (p[1] - C[1]) * .35), (C[0] + (p[0] - C[0]) * .12, C[1] + (p[1] - C[1]) * .12))
        ribbon(rdd, P, q, w, w * .4); chevrons(rkd, P, q, w * 1.6, w, 40, .5)
        back = cubic(q[-1], (q[-1][0] + 30, q[-1][1] - 30), (p[0] + 20, p[1] + 25), (p[0] + 8, p[1] + 10), 60)
        dashed_path(bd, P, back, 1.2, 5, 9); head(bd, P, back, 7)
        (ring(bd, P.p(*p), 9 * P.S, 2 * P.S) if i in commons else disc(bd, P.p(*p), 6 * P.S))
    for i in commons:                                          # around the rim, the nodes that also feed each other
        j = (i + 1) % 64; k = (i + 2) % 64
        for t in (j, k):
            if t in commons:
                a, b = nodes[i], nodes[t]; m = ((a[0] + b[0]) / 2 + (a[0] - C[0]) * .18, (a[1] + b[1]) / 2 + (a[1] - C[1]) * .18)
                q = cubic(a, m, m, b, 40); line(bd, P.pts([tuple(x) for x in q]), 2 * P.S); head(bd, P, q, 9)
    I.red(P.cov(rd)); I.red_knocked(P.cov(rk)); I.black(P.cov(bl))
    c = P.edge_tone(sd_box(P, C[0], C[1], 54, 54), 1.2); (P.clear(c), P.ink('red' if night else 'black', c))


def rng_uniform(rng, a, b, n):
    return [rng.uniform(a, b) for _ in range(n)]


def recinto(P, night=False):
    rng = P.rng; I = Ink(P, night); x0, y0, x1, y1 = 140, 140, 1080, 900; rail = y0 + 50
    bl, bd = P.layer(); rd, rdd = P.layer()
    bd.rounded_rectangle([*P.p(x0, y0), *P.p(x1, y1)], 30 * P.S, outline=255, width=int(5 * P.S)); bd.line([*P.p(x0 + 20, rail), *P.p(x1 - 20, rail)], fill=255, width=int(4 * P.S))
    shops = [(x0 + 90 + i * 150, y0 + 190 + j * 140) for i in range(6) for j in range(5)]
    for x, y in shops: bd.rectangle([*P.p(x - 26, y - 18), *P.p(x + 26, y + 18)], outline=255, width=int(2.4 * P.S))
    for _ in range(26):
        a, b = rng.sample(shops, 2); w0 = rng.uniform(3, 6); xa, xb = a[0] + rng.uniform(-14, 14), b[0] + rng.uniform(-14, 14)
        lane = rail + 8 + rng.uniform(0, 40); up = [(xa, a[1] - 18), (xa, lane)]; across = [(xa, lane), (xb, lane)]; down = [(xb, lane), (xb, b[1] - 18)]
        line(bd, P.pts(up), w0 * P.S); line(bd, P.pts(across), w0 * .7 * P.S); line(bd, P.pts(down), w0 * .55 * P.S); head(bd, P, np.float32(down), 8)
        rdd.rectangle([*P.p(xa - 7, rail - 12), *P.p(xa + 7, rail + 2)], fill=255)          # the toll at the rail
        q = cubic((xa, rail - 12), (xa, rail - 60), (x1 - 40, y0 - 60), (x1 + 120, y0 - 20), 50); line(rdd, P.pts([tuple(x) for x in q]), 1.4 * P.S)
    # the toll goes off to one place outside the fence
    rdd.rectangle([*P.p(1150, 40), *P.p(1290, 120)], fill=255)
    # outside: a handful of nodes trading directly, one shop slipping out through a gap
    out = [(rng.uniform(1180, 1470), rng.uniform(560, 960)) for _ in range(9)]
    for i, a in enumerate(out):
        ring(bd, P.p(*a), 9 * P.S, 2 * P.S)
        for b in out[i + 1:]:
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 220:
                m = ((a[0] + b[0]) / 2 + rng.uniform(-30, 30), (a[1] + b[1]) / 2 + rng.uniform(-30, 30)); q = cubic(a, m, m, b, 30)
                line(bd, P.pts([tuple(x) for x in q]), 2 * P.S); head(bd, P, q, 8)
    s = shops[-1]; q = cubic(s, (s[0] + 120, s[1] + 40), (x1 - 20, y1 - 60), out[0], 60); dashed_path(bd, P, q, 2); head(bd, P, q, 10)
    I.black(P.cov(bl)); I.red(P.cov(rd))


def delta(P, night=False):
    rng = P.rng; I = Ink(P, night); bl, bd = P.layer(); rd, rdd = P.layer(); kn, knd = P.layer(); ends = []
    def split(p, ang, w, depth):
        L = 60 + depth * 22; q = (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L)
        c = cubic(p, (p[0] + math.cos(ang) * L * .4, p[1] + math.sin(ang) * L * .4), (q[0], q[1] - L * .3), q, 30)
        ribbon(bd, P, c, w, w * .9)
        if w > 6: chevrons(knd, P, c, w, w * .9, 26, .45)
        if depth == 0 or w < 1.6 or q[1] > H - 80: ends.append(q); return
        k = 2 if rng.random() < .7 else 3; parts = np.array([rng.uniform(.5, 1) for _ in range(k)]); parts /= parts.sum()
        for j, f in enumerate(parts):
            split(q, math.pi / 2 + (j - (k - 1) / 2) * rng.uniform(.6, .95) + rng.uniform(-.2, .2), max(1.2, w * f * 1.05), depth - 1)
    split((768, -10), math.pi / 2, 70, 7)
    for e in ends:
        loop(bd, P, (e[0], e[1] + 14), 8, 1.6)
        if rng.random() < .55:
            side = 30 if e[0] < 768 else W - 30
            q = cubic(e, (e[0], e[1] + 40), (side, e[1] + 30), (side, 40), 80); line(rdd, P.pts([tuple(x) for x in q]), 1.2 * P.S)
    rdd.rectangle([*P.p(10, 0), *P.p(60, 40)], fill=255); rdd.rectangle([*P.p(W - 60, 0), *P.p(W - 10, 40)], fill=255)
    I.black(P.cov(bl)); I.black_knocked(P.cov(kn)); I.red(P.cov(rd))


def doppio(P, night=False):
    rng = P.nr; I = Ink(P, night); C = np.float32([768, 512]); wind = Wind(P, 4, .5)
    n = 1800; a = rng.uniform(0, 2 * np.pi, n); r = rng.uniform(260, 620, n)
    pin = (C + np.stack([np.cos(a) * r, np.sin(a) * r * .65], 1)).astype(np.float32)
    def inward(p, v, t): return swirl(p, C, 1.0, .5) + wind(p) * .3, np.linalg.norm((p - C) * np.float32([1, 1.5]), axis=1) < 30
    a2 = rng.uniform(0, 2 * np.pi, n); r2 = rng.uniform(40, 160, n)
    pout = (C + np.stack([np.cos(a2) * r2, np.sin(a2) * r2 * .65], 1)).astype(np.float32)
    def outward(p, v, t):
        d = p - C; rr = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        return np.stack([d[:, 1], -d[:, 0]], 1) / rr * .8 + d / rr * .9 + wind(p) * .3, np.zeros(len(p), bool)
    po = run(pout, outward, 200, 2.2, inertia=.86, jitter=.08, rng=rng)
    pi = run(pin, inward, 200, 3.4, inertia=.86, jitter=.08, rng=rng)
    if night:
        from bricoleur12 import cut
        cut(P, np.concatenate([po, pi], 1), lambda y: 1.2, red=np.r_[np.zeros(n, bool), np.ones(n, bool)])
    else:
        trails(P, np.concatenate([po, pi], 1), lambda y: 1.0, red=np.r_[np.zeros(n, bool), np.ones(n, bool)])
    c = P.edge_tone(np.hypot(P.X - C[0], (P.Y - C[1]) * 1.5) - 26, 1.2); P.clear(c); P.ink('black' if not night else 'red', c)


PLATES = {'v1': ('v1-flussi', flussi), 'v2': ('v2-tributo', tributo), 'v3': ('v3-recinto', recinto), 'v4': ('v4-delta', delta),
          'v5': ('v5-doppio', doppio), 'n1': ('v1-flussi-notte', lambda P: flussi(P, True)), 'n2': ('v2-tributo-notte', lambda P: tributo(P, True))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time()
        if k.startswith('n'):
            b3.PAPER = np.array([232, 228, 218], np.float32) / 255; b3.INK['red'] = np.array([255, 120, 30], np.float32) / 255; b3.INK['black'] = np.array([20, 18, 24], np.float32) / 255
        else:
            b3.PAPER = np.array([238, 235, 228], np.float32) / 255; b3.INK['red'] = np.array([249, 57, 34], np.float32) / 255; b3.INK['black'] = np.array([24, 21, 20], np.float32) / 255
        P = Press(a.seed * 1000 + 170 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + '.png')); print(stem, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
