"""THE AGENTIC BRICOLEUR — panoramas of geometry. The usual press: paper, red, black screened to greys.
Every form is soft (blurred, then screened); no figures, no words, no swirls.

  r1 gradoni   a ziggurat: tiers narrowing upward, the crowd thinning tier by tier, red only at the top
  r2 piega     the engineer's grid laid to the horizon, bent wherever someone is working on it
  r3 stele     monoliths in ranks to the vanishing point; between their feet, shacks and small fires
  r4 dischi    discs everywhere, overlapping into darker commons; one great disc eclipsing the rest in red
  r5 maglia    a mesh: regular triangles on the left (the model), an irregular weave on the right (examples)
  r6 torre     a perfect block on the left; in the middle a leaning tower of mismatched pieces, still standing

Usage: python3 bricoleur18.py OUT [--only r1,r2] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.spatial import Delaunay
import bricoleur3 as b3
W, H = 3072, 1280
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F


def blur(P, M, r):
    return np.asarray(Image.fromarray((np.clip(M, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r * P.S)), F) / 255


def scr(P, tone, ang=15, cell=3.6):
    return P.screen(np.full((P.H, P.W), tone, F) if np.isscalar(tone) else np.clip(tone, 0, 1).astype(F), ang, cell)


def poly(P, pts, soft=6):
    m, d = P.layer(); d.polygon(P.pts(pts), fill=255); return blur(P, P.cov(m), soft)


def ell(P, cx, cy, rx, ry, soft=6):
    m, d = P.layer(); d.ellipse([*P.p(cx - rx, cy - ry), *P.p(cx + rx, cy + ry)], fill=255); return blur(P, P.cov(m), soft)


def sky_ground(P, hz, red=.35, ground=.08):
    X, Y = P.X, P.Y
    P.ink('red', scr(P, np.clip((hz - Y) / hz, 0, 1) ** 1.8 * red * (Y < hz), 75, 5.0))
    P.ink('black', scr(P, np.clip(ground + (Y - hz) / (H - hz) * .18 + (P.fbm(6, 3) - .5) * .05, 0, 1) * (Y > hz)))
    fog = np.exp(-((Y - hz) / 50) ** 2); P.knock('red', fog); P.knock('black', fog * .85)


def stipple(P, pts, r, ink='black', soft=1.4, tone=1.0):
    """The crowd as soft specks, nothing drawn."""
    m, d = P.layer()
    for (x, y), rr in zip(pts, r): d.ellipse([*P.p(x - rr, y - rr * 1.2), *P.p(x + rr, y + rr * .8)], fill=255)
    M = blur(P, P.cov(m), soft); M = (M > .35).astype(F) if tone >= 1 else scr(P, M * tone, 15 if ink == 'black' else 75, 2.6)
    P.clear(M); P.ink(ink, M)

# ------------------------------------------------------------ plates


def gradoni(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 930; sky_ground(P, hz, .3)
    cx, base, tiers, th = 1536, 1010, 8, 92
    for k in range(tiers):
        y1 = base - k * th; y0 = y1 - th; w1 = 980 - k * 112; w0 = w1 - 26
        face = poly(P, [(cx - w1, y1), (cx + w1, y1), (cx + w0, y0), (cx - w0, y0)], 4)
        lit = face * (X < cx - w0 * .15); shade = face * (X >= cx - w0 * .15)
        P.clear(face)
        if k == tiers - 1: P.ink('red', scr(P, face * .9, 75, 4.0))
        else:
            P.ink('black', scr(P, lit * (.22 + k * .02))); P.ink('black', scr(P, shade * (.5 + k * .03)))
            tread = poly(P, [(cx - w0, y0), (cx + w0, y0), (cx + w0 - 10, y0 + 10), (cx - w0 + 10, y0 + 10)], 2); P.knock('black', tread * .8)
        n = int(320 * (1 - k / tiers) ** 2) + 3                 # the crowd, thinning as it climbs
        xs = rng.uniform(cx - w0 + 20, cx + w0 - 20, n); ys = y0 + rng.uniform(4, 18, n)
        stipple(P, zip(xs, ys), np.full(n, 3.2 + k * .1), 'red' if k >= tiers - 2 else 'black')
    stair = poly(P, [(cx - 60, base), (cx + 60, base), (cx + 22, base - th * (tiers - 1)), (cx - 22, base - th * (tiers - 1))], 8)
    P.knock('black', stair * .6)
    climb = [(cx + rng.normal(0, 18), rng.uniform(base - th * (tiers - 1), base)) for _ in range(140)]
    stipple(P, climb, np.full(140, 3.0), 'black')
    for _ in range(26):                                         # the low town around, soft mounds
        x = rng.uniform(0, W); y = rng.uniform(hz + 10, H - 20)
        if abs(x - cx) < 1050 and y < base + 30: continue
        s = 20 + (y - hz) * .25; m = ell(P, x, y, s * rng.uniform(1.5, 3), s * .6, 6); P.ink('black', scr(P, m * .4))
    ground = [(rng.uniform(0, W), rng.uniform(base + 10, H - 10)) for _ in range(1600)]
    stipple(P, ground, rng.uniform(2.4, 4.2, 1600), 'black', tone=.8)


def piega(P):
    rng = P.rng; X, Y = P.X, P.Y; hz = 470; sky_ground(P, hz, .38, .03)
    vx, f, cam = 1536, 600, 1.4
    bumps = [(rng.uniform(-12, 12), rng.uniform(1.3, 9), rng.uniform(.9, 2.6), rng.uniform(-1.5, 1.5)) for _ in range(18)]
    def warp(u, z):
        du, dz = np.zeros_like(u), np.zeros_like(z)
        for bu, bz, s, sh in bumps:
            r2 = ((u - bu) / s) ** 2 + ((z - bz) / (s * 1.4)) ** 2; e = np.exp(-r2)
            du += (u - bu) * e * 1.3 + sh * e * s * 1.2; dz += (z - bz) * e * .9
        return u + du, z + dz
    m, d = P.layer()
    for u0 in np.arange(-26, 26.1, .8):
        z = np.geomspace(1.0, 80, 400); u, zz = warp(np.full_like(z, u0), z)
        pts = [(vx + a * f / b, hz + cam * f / b) for a, b in zip(u, zz)]; d.line(P.pts(pts), fill=255, width=int(3 * P.S))
    for z0 in np.geomspace(1.0, 80, 64):
        u = np.linspace(-60, 60, 600); uu, zz = warp(u, np.full_like(u, z0))
        pts = [(vx + a * f / b, hz + cam * f / b) for a, b in zip(uu, zz)]; d.line(P.pts(pts), fill=255, width=int(3 * P.S))
    G = blur(P, P.cov(m), 1.6) * (Y > hz + 2); P.ink('black', scr(P, G * 1.0, 15, 2.8))
    for bu, bz, s, sh in bumps:                                 # where it bends, the work: a red breath
        x, y = vx + bu * f / bz, hz + cam * f / bz; r = s * f / bz * .7
        if 0 < x < W and y < H: P.ink('red', scr(P, ell(P, x, y, r * 1.4, r * .6, r * .4) * .7, 75, 3.6))


def stele(P):
    rng = P.rng; X, Y = P.X, P.Y; hz = 560; sky_ground(P, hz, .3)
    vx, f = 1536, 520
    for side in (-1, 1):
        for k, z in enumerate(np.geomspace(14, 1.25, 9)):
            x0 = vx + side * 3.2 * f / z; w = 1.4 * f / z; top = hz - 7 * f / z; bot = hz + 1.5 * f / z
            fog = np.clip(1 - z / 16, .15, 1)
            face = poly(P, [(x0, bot), (x0 + side * w, bot), (x0 + side * w, top), (x0, top)], 3 + 20 / z)
            P.clear(face * fog); P.ink('black', scr(P, face * (.35 + .5 * fog)))
            slit = poly(P, [(x0 + side * w * .2, top + 12 * f / z / 10), (x0 + side * w * .8, top + 12 * f / z / 10), (x0 + side * w * .8, top + 20 * f / z / 10), (x0 + side * w * .2, top + 20 * f / z / 10)], 2)
            P.knock('black', slit); P.ink('red', scr(P, slit * .9, 75, 3.0))
    # at their feet: shacks of every shape, small fires, bodies
    for _ in range(110):
        z = rng.uniform(1.4, 12); u = rng.uniform(-3, 3); x, y = vx + u * f / z, hz + 1.5 * f / z; s = 40 / z * 6
        pts = [(x - s, y), (x + s * rng.uniform(.6, 1.2), y), (x + s * rng.uniform(.3, .9), y - s * rng.uniform(.5, 1.1)), (x - s * rng.uniform(.2, .8), y - s * rng.uniform(.6, 1.3))]
        P.ink('black', scr(P, poly(P, pts, 3) * rng.uniform(.3, .7)))
        if rng.random() < .3: P.ink('red', scr(P, ell(P, x + s * 1.6, y - 4, s * .3, s * .2, 3) * .9, 75, 3))
    ppl = [(vx + rng.uniform(-3, 3) * f / z, hz + 1.5 * f / z + rng.uniform(-6, 6)) for z in rng_geom(rng, 1.4, 12, 900)]
    stipple(P, ppl, np.full(900, 2.8), 'black', tone=.85)


def rng_geom(rng, a, b, n):
    return [math.exp(rng.uniform(math.log(a), math.log(b))) for _ in range(n)]


def dischi(P):
    rng = P.rng; X, Y = P.X, P.Y; hz = 760
    P.ink('black', scr(P, np.clip((Y - hz) / (H - hz), 0, 1) * .12 * (Y > hz)))
    acc = np.zeros((P.H, P.W), F)
    for _ in range(70):
        x, y = rng.uniform(-100, W + 100), rng.uniform(150, H - 60); r = rng.uniform(40, 240) * (.5 + y / H)
        acc += ell(P, x, y, r, r * .62, 4 + r * .04) * rng.choice([.12, .18, .25])
    P.ink('black', scr(P, np.clip(acc, 0, .85)))
    big = ell(P, 1900, 420, 480, 480, 14)                       # the one that eclipses
    P.knock('black', big * .7); P.ink('red', scr(P, big * .75, 75, 4.6))
    rim = np.clip(big * 2, 0, 1) - big; P.ink('black', scr(P, rim * .5))
    fog = np.exp(-((Y - hz) / 40) ** 2); P.knock('black', fog * .6); P.knock('red', fog * .6)


def maglia(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 300
    P.ink('red', scr(P, np.clip((hz - Y) / hz, 0, 1) * .3 * (Y < hz), 75, 5.0))
    s = 90; pts = []
    for j in range(-1, int((H - hz) / (s * .866)) + 3):
        for i in range(-1, int(W / s) + 3): pts.append((i * s + (j % 2) * s / 2, hz + j * s * .866))
    reg = np.float32(pts); irr = np.stack([rng.uniform(-50, W + 50, 900), rng.uniform(hz - 20, H + 50, 900)], 1).astype(np.float32)
    t = np.clip((reg[:, 0] - 900) / 1300, 0, 1)[:, None]          # the lattice loosens left to right
    mix = reg + (rng.normal(0, 1, reg.shape) * 46 * t).astype(np.float32)
    allp = np.concatenate([mix[(reg[:, 0] < 2300)], irr[irr[:, 0] > 1500]])
    tri = Delaunay(allp)
    fm, fd = P.layer(); rm, rd = P.layer(); rng2 = P.rng
    for simp in tri.simplices:
        q = allp[simp]; cx_ = q[:, 0].mean()
        if q[:, 1].min() < hz - 10: continue
        c = q.mean(0); qq = c + (q - c) * .86                       # a paper gap between every cell
        tone = .15 + .5 * rng2.random() * (cx_ > 1300) + .25 * (cx_ <= 1300)
        if cx_ > 1600 and rng2.random() < .06: rd.polygon(P.pts([tuple(p) for p in qq]), fill=255)
        else: fd.polygon(P.pts([tuple(p) for p in qq]), fill=int(tone * 255))
    fill, red = P.cov(fm), P.cov(rm)
    fill = blur(P, fill, 2.2); red = blur(P, red, 2.2)
    P.ink('black', scr(P, fill)); P.clear(red); P.ink('red', scr(P, red * .9, 75, 3.2))
    fog = np.exp(-((Y - hz) / 40) ** 2); P.knock('black', fog * .7)


def torre(P):
    rng = P.rng; X, Y = P.X, P.Y; hz = 920; sky_ground(P, hz, .3)
    cube = poly(P, [(260, 990), (900, 990), (900, 330), (260, 330)], 5); side = poly(P, [(900, 990), (1040, 940), (1040, 290), (900, 330)], 5)
    top = poly(P, [(260, 330), (900, 330), (1040, 290), (400, 290)], 5)
    P.clear(cube); P.ink('black', scr(P, cube * .3)); P.clear(side); P.ink('black', scr(P, side * .62)); P.clear(top); P.ink('black', scr(P, top * .12))
    # the tower: every piece a different shape, each set where the last one landed
    x, y = 2000.0, 1000.0; lean = 0.0
    for k in range(13):
        kind = rng.choice(['box', 'slab', 'drum', 'wedge', 'box']); w = rng.uniform(220, 520) * (1 - k * .035); h = rng.uniform(50, 120)
        x += lean + rng.uniform(-30, 30); lean += rng.uniform(-6, 9)
        if kind in ('box', 'slab'):
            hh = h * (.45 if kind == 'slab' else 1); M = poly(P, [(x - w / 2, y), (x + w / 2, y), (x + w / 2 + lean * .3, y - hh), (x - w / 2 + lean * .3, y - hh)], 3)
        elif kind == 'drum': hh = h; M = np.maximum(poly(P, [(x - w / 3, y), (x + w / 3, y), (x + w / 3, y - hh), (x - w / 3, y - hh)], 3), ell(P, x, y - hh, w / 3, w / 10, 3))
        else: hh = h; M = poly(P, [(x - w / 2, y), (x + w / 2, y), (x + rng.uniform(-w / 3, w / 3), y - hh)], 3)
        P.clear(M)
        if rng.random() < .16: P.ink('red', scr(P, M * .85, 75, 3.4))
        else:
            P.ink('black', scr(P, M * rng.uniform(.2, .75), 15, rng.choice([2.6, 3.6, 4.6])))
        y -= hh * (.92 if kind != 'wedge' else .5)
    for _ in range(40):                                          # props: poles and ropes, soft
        a = (rng.uniform(1600, 2200), 1000); b = (1900 + rng.uniform(-200, 300), rng.uniform(300, 900))
        m, d = P.layer(); d.line([P.p(*a), P.p(*b)], fill=255, width=int(2 * P.S)); P.ink('black', scr(P, blur(P, P.cov(m), 1.2) * .7))
    ppl = [(rng.uniform(1400, 2500), rng.uniform(990, H - 20)) for _ in range(700)] + [(rng.uniform(100, 1100), rng.uniform(1000, H - 20)) for _ in range(60)]
    stipple(P, ppl, rng_uniform(rng, 2.4, 4.4, 760), 'black', tone=.85)


def rng_uniform(rng, a, b, n):
    return np.array([rng.uniform(a, b) for _ in range(n)])


PLATES = {'r1': ('r1-gradoni', gradoni), 'r2': ('r2-piega', piega), 'r3': ('r3-stele', stele), 'r4': ('r4-dischi', dischi),
          'r5': ('r5-maglia', maglia), 'r6': ('r6-torre', torre)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time()
        P = Press(a.seed * 1000 + 210 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + '.png')); print(stem, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
