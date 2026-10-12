"""THE AGENTIC BRICOLEUR — panoramas again (after Tübke), with no figures drawn: the crowd is simulated, every
form is soft, there are no lines and no words. Each reads a passage of the essay.

  q1 interregno   left, the workhouse: ranks marching into a dim mass; centre, a soft sphere over the
                  horizon, streams of people rising into it; right, small fires, crowds circling them
  q2 incursioni   three worlds across the width, fading into each other: a tile world, a surveyed land,
                  a ploughed field; the crowd keeps each world's way of moving, and crosses
  q3 fuochi       night: fires all across the land, crowds round each; at the horizon one furnace glows
                  and every fire sends it a thread of people
  q4 sfera        the platform as a sphere: inside it a crowd turns; outside, rings of walkers orbit it
                  and the plain below is full

Usage: python3 bricoleur17.py OUT [--only q1,q3] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
from PIL import Image, ImageFilter
import bricoleur3 as b3
W, H = 3072, 1280
from bricoleur10 import trails, run, toward, swirl
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F

PAL = {
    'carta': ((238, 235, 228), (249, 57, 34), (24, 21, 20)),
    'fluo': ((243, 239, 231), (255, 72, 160), (0, 110, 120)),
    'notte': ((232, 228, 218), (255, 120, 30), (20, 18, 24)),
    'notte-blu': ((234, 230, 220), (255, 160, 40), (18, 26, 60)),
}
DEFAULT = {'q1': 'carta', 'q2': 'fluo', 'q3': 'notte', 'q4': 'notte-blu'}


def palette(k):
    p, a, b = PAL[k]; b3.PAPER = np.float32(p) / 255; b3.INK['red'] = np.float32(a) / 255; b3.INK['black'] = np.float32(b) / 255


class Curl:
    def __init__(self, P, base=6, amp=1.0):
        psi = P.fbm(base, 3)[::P.S, ::P.S]; gy, gx = np.gradient(psi); self.u, self.v = gy * amp * 520, -gx * amp * 520

    def __call__(self, pos):
        xi = np.clip(pos[:, 0].astype(int), 0, W - 1); yi = np.clip(pos[:, 1].astype(int), 0, H - 1)
        return np.stack([self.u[yi, xi], self.v[yi, xi]], 1)


def scr(P, tone, ang=15, cell=3.6):
    return P.screen(np.full((P.H, P.W), tone, F) if np.isscalar(tone) else np.clip(tone, 0, 1).astype(F), ang, cell)


def blob(P, cx, cy, rx, ry, warp=.25, base=5):
    """A soft body: gaussian falloff, edges eaten by noise. No outline anywhere."""
    d = ((P.X - cx) / rx) ** 2 + ((P.Y - cy) / ry) ** 2
    return np.exp(-d * 2.2) * (1 + (P.fbm(base, 3) - .5) * warp * 2)


def ground_y(x, hz):
    return hz + 18 * np.sin(x / 400) + 10 * np.sin(x / 130 + 1)


def persp_w(y, hz):
    return .5 + 2.3 * np.clip((y - hz) / (H - hz), 0, 1)


def land(P, hz, night=False, tone=.07):
    X, Y = P.X, P.Y; g = Y > ground_y(X, hz)
    fog = np.exp(-((Y - hz) / 60) ** 2)
    if night:
        P.ink('black', scr(P, np.clip(.9 - fog * .45 + (P.fbm(6, 3) - .5) * .12, 0, 1)))
    else:
        P.ink('black', scr(P, np.clip(tone + (Y - hz) / H * .14 + (P.fbm(6, 3) - .5) * .06, 0, 1) * g))
        hills = np.exp(-((Y - hz + 30 + P.fbm(3, 3)[0:1, :] * 120) / 50) ** 2) * (Y < hz + 10)
        P.ink('black', scr(P, hills * .35))
    return g, fog


def stream(P, n, x0, x1, y0, y1, drive, steps, speed, hz, rng, inertia=.88, jitter=.2):
    p0 = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)], 1).astype(np.float32)
    return run(p0, drive, steps, speed, inertia=inertia, jitter=jitter, rng=rng)


def soft_trails(P, path, hz, red=None, k=1.0, cutout=False):
    """Trails, then softened: the plate is blurred a little so the paths read as breath, not wire."""
    keep = {c: P.plate[c].copy() for c in P.plate}
    for c in P.plate: P.plate[c][:] = 0
    trails(P, path, lambda y: k * persp_w(y, hz), red=red)
    new = {}
    for c in P.plate:
        im = Image.fromarray((np.clip(P.plate[c], 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6 * P.S))
        new[c] = np.asarray(im, F) / 255
    if cutout:
        P.plate['black'] = keep['black'] * (1 - new['black']) * (1 - new['red'])
        P.plate['red'] = np.maximum(keep['red'], np.maximum(P.screen(new['black'] * .35, 75, 2.6), (new['red'] > .4).astype(F)))
    else:
        P.plate['black'] = np.maximum(keep['black'] * (1 - (new['red'] > .4)), P.screen(new['black'], 15, 2.6))
        P.plate['red'] = np.maximum(keep['red'] * (1 - (new['black'] > .5)), P.screen(new['red'], 75, 2.6))

# ------------------------------------------------------------ q1


def interregno(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 470; wind = Curl(P, 6, .8)
    P.ink('red', scr(P, np.clip((hz - Y) / hz, 0, 1) ** 1.6 * .45 * (Y < hz), 75, 5.0))
    g, fog = land(P, hz); P.knock('red', fog); P.knock('black', fog * .8)
    # the workhouse: a dim mass on the left, rows of pale windows dissolving into it
    wh = blob(P, 470, 470, 430, 230, .3); rows = ((np.abs(((Y - 300) % 46) - 23) < 5) & (np.abs(((X - 120) % 70) - 35) < 14)).astype(F)
    P.ink('black', scr(P, np.clip(wh * 1.1 - rows * wh * .6, 0, .92)))
    door = np.float32([560, 640])
    ranks = stream(P, 1400, 120, 1100, 760, 1250, lambda p, v, t: (toward(p, door) + np.float32([[0, 0]]) + wind(p) * .15, np.linalg.norm(p - door, axis=1) < 30), 260, 2.6, hz, rng, .93, .05)
    # the sphere: a red breath over the horizon; people rise into it
    S0 = np.float32([1536, 300]); sph = blob(P, *S0, 300, 280, .15)
    P.knock('black', sph * .9); P.ink('red', scr(P, sph * .75, 75, 4.2))
    def rise(p, v, t):
        under = np.abs(p[:, 0] - S0[0]) < 60
        w = np.where(under[:, None], np.float32([[0, -1]]) * 1.4 + toward(p, S0) * .3, toward(p, (S0[0], hz + 40)) * 1.0 + wind(p) * .3)
        return w, np.linalg.norm((p - S0) * np.float32([1, 1.1]), axis=1) < 140
    up = stream(P, 2200, 700, 2400, 560, 1250, rise, 380, 2.8, hz, rng, .9, .1)
    inside = np.float32(S0) + rng.normal(0, 1, (700, 2)).astype(np.float32) * np.float32([120, 110])
    sw = run(inside, lambda p, v, t: (swirl(p, S0, 1.0, -.02), np.zeros(len(p), bool)), 120, 3.0, inertia=.9, rng=rng)
    # the commons on the right: soft fires, crowds circling them
    fires = [(rng.uniform(2300, 2980), rng.uniform(600, 1150)) for _ in range(6)]
    for x, y in fires: P.knock('black', blob(P, x, y, 160, 90) * .7); P.ink('red', scr(P, blob(P, x, y, 30, 18, .5) , 75, 3.0))
    circ = []
    for x, y in fires:
        c = np.float32([x, y]); q0 = (c + rng.normal(0, 1, (260, 2)) * np.float32([90, 50])).astype(np.float32)
        circ.append(run(q0, lambda p, v, t, c=c: (swirl(p, c, 1.0, .05) * np.float32([1, .55]) + wind(p) * .5, np.zeros(len(p), bool)), 140, 2.2, inertia=.9, rng=rng))
    wander = stream(P, 2500, 0, W, hz + 30, H, lambda p, v, t: (wind(p), np.zeros(len(p), bool)), 50, 1.6, hz, rng, .85, .5)
    soft_trails(P, wander, hz, k=.5)
    soft_trails(P, ranks, hz, k=.9)
    soft_trails(P, np.concatenate(circ, 1), hz, k=.8, red=rng.random(sum(c.shape[1] for c in circ)) < .08)
    soft_trails(P, up, hz, k=.8, red=rng.random(2200) < .5)
    soft_trails(P, sw, hz, k=.5, red=np.ones(700, bool))

# ------------------------------------------------------------ q2


def incursioni(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 380; wind = Curl(P, 6, .8)
    g, fog = land(P, hz, tone=.05); P.knock('black', fog * .9)
    a = np.clip((1180 - X) / 260 + .5, 0, 1); c = np.clip((X - 1900) / 260 + .5, 0, 1); b = np.clip(1 - a - c, 0, 1)
    depth = np.clip((Y - hz) / (H - hz), 0, 1)
    # a tile world, in perspective, fading toward the horizon
    vx = 600; u = (X - vx) / np.maximum(Y - hz, 1) * 200; v = 9000 / np.maximum(Y - hz, 1)
    grid = (np.abs((u % 60) - 30) > 27.5) | (np.abs((v % 40) - 20) > 18.5)
    soft = lambda m, r: np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r * P.S)), F) / 255
    P.ink('black', scr(P, soft(grid.astype(F), 2.5) * a * g * depth ** .6 * .7))
    # a surveyed land: contours, soft
    terr = P.warp(P.fbm(3, 4), 80); iso = P.isolines(terr + depth * .5, list(np.linspace(.2, 1.3, 40)), .8)
    P.ink('black', scr(P, soft(iso, 1.5) * b * g * .8))
    # a ploughed field: furrows converging, breathing
    fur = (np.abs(((X - 2500) / np.maximum(Y - hz + 40, 1) * 300) % 26 - 13) < 3).astype(F)
    P.ink('black', scr(P, soft(fur, 2.5) * c * g * depth * .65))
    # the crowd: each world's own way of moving, and the ones who cross keep going
    n = 4200; p = np.stack([rng.uniform(0, W, n), rng.uniform(hz + 40, H, n)], 1).astype(np.float32); T = 140
    path = np.zeros((T, n, 2), np.float32); dirs = np.float32([[1, 0], [-1, 0], [0, 1], [0, -1]]); k = rng.integers(0, 4, n)
    C2 = np.float32([1540, 800]); cross = np.zeros(n, bool); start = p[:, 0].copy()
    for t in range(T):
        wa = np.clip((1180 - p[:, 0]) / 260 + .5, 0, 1); wc = np.clip((p[:, 0] - 1900) / 260 + .5, 0, 1); wb = 1 - wa - wc
        k = np.where(rng.random(n) < .06, rng.integers(0, 4, n), k)
        d = (dirs[k] * 2.4) * wa[:, None] + (swirl(p, C2, 1.0, .02) * 2.0) * wb[:, None] + (wind(p) * 1.2 + np.float32([[1.4, 0]])) * wc[:, None]
        p = p + d * persp_w(p[:, 1], hz)[:, None] * .7; path[t] = p
    zone = lambda x: np.digitize(x, [1180, 1900])
    red = zone(start) != zone(path[-1, :, 0])
    soft_trails(P, path, hz, k=.7, red=red)
    for x0 in (1180, 1900):                                      # the seams: breath of accent, no edge
        P.ink('red', scr(P, np.exp(-((X - x0) / 70) ** 2) * g * .25, 75, 4.0))

# ------------------------------------------------------------ q3


def fuochi(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 400; wind = Curl(P, 6, .8)
    g, fog = land(P, hz, night=True)
    F0 = np.float32([1536, hz + 10]); P.knock('black', blob(P, *F0, 700, 160) * .85); P.ink('red', scr(P, blob(P, *F0, 220, 60, .3), 75, 3.6))
    for _ in range(5):                                            # smoke columns, soft
        x = rng.uniform(300, 2800); col = np.exp(-((X - x - (hz - Y) * .2 - (P.fbm(8, 3) - .5) * 160) / 40) ** 2) * (Y < hz + 30) * np.clip((Y) / hz, 0, 1)
        P.knock('black', col * .35)
    fires = [(rng.uniform(150, 2920), rng.uniform(hz + 120, H - 60)) for _ in range(14)]
    for x, y in fires: P.knock('black', blob(P, x, y, 140 * persp_w(y, hz) / 1.5, 70 * persp_w(y, hz) / 1.5) * .7); P.ink('red', scr(P, blob(P, x, y, 22, 14, .6), 75, 3.0))
    circ = []
    for x, y in fires:
        c = np.float32([x, y]); s = persp_w(y, hz) / 1.5; q0 = (c + rng.normal(0, 1, (220, 2)) * np.float32([80, 40]) * s).astype(np.float32)
        circ.append(run(q0, lambda p, v, t, c=c: (swirl(p, c, 1.0, .06) * np.float32([1, .5]) + wind(p) * .4, np.zeros(len(p), bool)), 120, 2.0 * s, inertia=.9, rng=rng))
    threads = []
    for x, y in fires:
        q0 = (np.float32([x, y]) + rng.normal(0, 10, (40, 2))).astype(np.float32)
        threads.append(run(q0, lambda p, v, t: (toward(p, F0) + wind(p) * .3, np.linalg.norm(p - F0, axis=1) < 40), 520, 3.0, inertia=.9, jitter=.08, rng=rng))
    wander = stream(P, 2200, 0, W, hz + 30, H, lambda p, v, t: (wind(p), np.zeros(len(p), bool)), 50, 1.6, hz, rng, .85, .5)
    soft_trails(P, wander, hz, k=.45, cutout=True)
    soft_trails(P, np.concatenate(circ, 1), hz, k=.8, cutout=True)
    soft_trails(P, np.concatenate(threads, 1), hz, k=.6, red=np.ones(sum(t.shape[1] for t in threads), bool), cutout=True)

# ------------------------------------------------------------ q4


def sfera(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 640; wind = Curl(P, 6, .8)
    g, fog = land(P, hz, night=True)
    S0 = np.float32([1536, 430]); R = 330
    rr = np.hypot(X - S0[0], Y - S0[1]); sph = np.exp(-((rr - R * .8) / (R * .45)) ** 2 * 1.2) * (rr < R * 1.25)
    P.knock('black', sph * .6 + np.exp(-(rr / R) ** 2) * .4)
    inside = (S0 + rng.normal(0, 1, (1800, 2)) * np.float32([150, 150])).astype(np.float32)
    def turn(p, v, t):
        d = p - S0; r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        return np.stack([-d[:, 1], d[:, 0]], 1) / r - d / r * np.clip((r - 200) / 80, -1, 1) * .6 + wind(p) * .2, np.zeros(len(p), bool)
    rk = np.float32(rng.uniform(40, 280, (1800, 1)))
    def turn(p, v, t):
        d = p - S0; r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        return np.stack([-d[:, 1], d[:, 0]], 1) / r - d / r * np.clip((r - rk) / 80, -1, 1) * .6 + wind(p) * .3, np.zeros(len(p), bool)
    sw = run(inside, turn, 110, 2.6, inertia=.9, rng=rng)
    orbits = []
    for j, (rx, ry, tilt) in enumerate([(620, 120, .1), (780, 160, -.08), (950, 200, .05)]):
        n = 500; a = rng.uniform(0, 2 * np.pi, n); q0 = np.stack([S0[0] + np.cos(a) * rx, S0[1] + np.sin(a) * ry + np.cos(a) * rx * tilt], 1).astype(np.float32)
        def orb(p, v, t, rx=rx, ry=ry, tilt=tilt):
            d = (p - S0); u = d[:, 0] / rx; w_ = (d[:, 1] - d[:, 0] * tilt) / ry; r = np.sqrt(u * u + w_ * w_) + 1e-6
            tg = np.stack([-w_ / r * rx, (u / r * ry) + (-w_ / r * rx) * tilt], 1); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
            return tg - np.stack([u, w_], 1) / r[:, None] * (r - 1)[:, None] * 2 + wind(p) * .1, np.zeros(len(p), bool)
        orbits.append(run(q0, orb, 90, 4.0, inertia=.9, jitter=.05, rng=rng))
    plain = stream(P, 4000, 0, W, hz + 20, H, lambda p, v, t: (wind(p) + toward(p, (S0[0], hz)) * .25, np.zeros(len(p), bool)), 70, 1.8, hz, rng, .85, .4)
    soft_trails(P, plain, hz, k=.6, cutout=True, red=rng.random(4000) < .03)
    soft_trails(P, np.concatenate(orbits, 1), hz, k=.5, cutout=True)
    soft_trails(P, sw, hz, k=.45, cutout=True, red=rng.random(1800) < .35)


PLATES = {'q1': ('q1-interregno', interregno), 'q2': ('q2-incursioni', incursioni), 'q3': ('q3-fuochi', fuochi), 'q4': ('q4-sfera', sfera)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1); ap.add_argument('--palette', default=None); ap.add_argument('--suffix', default='')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time(); palette(a.palette or DEFAULT[k])
        P = Press(a.seed * 1000 + 190 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + a.suffix + '.png')); print(stem + a.suffix, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
