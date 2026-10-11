"""THE AGENTIC BRICOLEUR — the crowd as a simulation (after Ian Cheng), in Bruegel's and Bosch's places.

The crowds here are not placed, they are run: a few thousand agents, each with a drive (be swallowed,
flee the fire, orbit a thing, wander), pushed through a curl-noise wind. What is printed is their
memory: the oldest stretch of each path screened light, the middle darker, the last steps solid, the
body itself a soft mark at the head. Symbols are blurred into forms; nothing is drawn crisp but the paths.

  t2 trionfo    high horizon, smoke for a sky; one army streams into the black box, one turns in a slow
                vortex, the people by the fires scatter outward
  w2 trittico   three panels, three regimes: a slow wander round a pond; swarms orbiting soft forms in the
                garden; everything drawn down a drain in the black panel. One red emissary crosses all three.

Usage: python3 bricoleur10.py OUT [--only t2,w2] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
from PIL import Image, ImageFilter
import bricoleur3 as b3

W, H = 1536, 1024
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F, sd_box, line, disc

# ------------------------------------------------------------ the simulation


class Wind:
    """A divergence-free wind: the curl of a smooth noise potential, sampled in design units."""
    def __init__(self, P, base=5, amp=1.0):
        psi = P.fbm(base, 3)[::P.S, ::P.S]
        gy, gx = np.gradient(psi)
        self.u, self.v = gy * amp * 260, -gx * amp * 260

    def __call__(self, pos):
        xi = np.clip(pos[:, 0].astype(int), 0, W - 1); yi = np.clip(pos[:, 1].astype(int), 0, H - 1)
        return np.stack([self.u[yi, xi], self.v[yi, xi]], 1)


def run(pos, drive, steps, speed, inertia=.82, jitter=.25, rng=None):
    """Integrate agents; `drive(pos, vel, t)` returns the desired direction and a 'gone' mask (swallowed)."""
    n = len(pos); vel = np.zeros_like(pos); path = np.full((steps, n, 2), np.nan, np.float32); alive = np.ones(n, bool)
    sp = speed * rng.uniform(.6, 1.4, n)[:, None]
    for t in range(steps):
        want, gone = drive(pos, vel, t)
        nrm = np.linalg.norm(want, axis=1, keepdims=True) + 1e-6
        want = want / nrm + rng.normal(0, jitter, (n, 2))
        vel = inertia * vel + (1 - inertia) * want * sp
        pos = np.where(alive[:, None], pos + vel, pos)
        alive &= ~gone
        path[t][alive] = pos[alive]
    return path


def toward(pos, g, k=1.0):
    d = np.asarray(g, np.float32) - pos; return d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6) * k


def swirl(pos, c, k=1.0, inward=.25):
    d = pos - np.asarray(c, np.float32); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    t = np.stack([-d[:, 1], d[:, 0]], 1) / r
    return (t - d / r * inward) * k


# ------------------------------------------------------------ printing the memory


def trails(P, path, width, clip=None, red=None):
    """Three ages of each path into black (or red) plates; heads as soft smudged marks."""
    S = P.S; steps, n, _ = path.shape; cuts = (0, int(steps * .45), int(steps * .8), steps)
    red = np.zeros(n, bool) if red is None else red
    lay = {(ink, a): P.layer() for ink in ('black', 'red') for a in range(3)}; head = {ink: P.layer() for ink in ('black', 'red')}
    for i in range(n):
        ink = 'red' if red[i] else 'black'; p = path[:, i]
        ok = ~np.isnan(p[:, 0])
        if ok.sum() < 2: continue
        last = p[ok][-1]; w = width(last[1]) * (1.8 if red[i] else 1)
        for a in range(3):
            seg = p[cuts[a]:cuts[a + 1] + 1]; seg = seg[~np.isnan(seg[:, 0])]
            if len(seg) > 1: lay[(ink, a)][1].line([(x * S, y * S) for x, y in seg], fill=255, width=max(1, int(w * (.5 + .25 * a) * S)), joint='curve')
        r = w * 1.7; head[ink][1].ellipse([(last[0] - r) * S, (last[1] - r * 1.3) * S, (last[0] + r) * S, (last[1] + r * .7) * S], fill=255)
    C = np.ones((P.H, P.W), F) if clip is None else clip
    for ink in ('black', 'red'):
        for a, tone in enumerate((.28, .55, 1.0)):
            m = P.cov(lay[(ink, a)][0]) * C
            P.ink(ink, m if tone >= 1 else P.screen(np.full((P.H, P.W), tone, F), 15 if ink == 'black' else 75, 2.6) * m)
        hm = P.cov(head[ink][0].filter(ImageFilter.GaussianBlur(1.2 * S))) * C
        hm = P.crayon(hm, .6, .25); P.clear(hm * (ink == 'red')); P.ink(ink, hm)


def soft_form(P, cx, cy, r, warp=40, seed_base=6):
    """A body without an outline: a warped blob, edge left to the screen."""
    d = np.hypot(P.X - cx, P.Y - cy) - r
    d = d + (P.fbm(seed_base, 4) - .5) * 2 * warp
    return np.clip(-d / 22 + .5, 0, 1)

# ------------------------------------------------------------ plates


def trionfo(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 150 + X * .04
    P.ink('black', P.screen(np.clip(.02 + (P.fbm(6, 4) - .3) * .35, 0, .4), 15, 3.4) * (Y > hz))
    P.ink('black', P.screen(np.full((P.H, P.W), .5, F), 15, 3.4) * (Y <= hz))
    n_ = P.fbm(8, 5); fires = []
    for k in range(9):
        x0 = P.rng.uniform(80, W - 80); y0 = P.rng.uniform(hz.min() + 60, 600); fires.append((x0, y0))
        wdt = 18 + (y0 - Y) * .35; dx = X - x0 - (y0 - Y) * P.rng.uniform(-.4, .4) - (n_ - .5) * 140
        col = ((np.abs(dx) < wdt) & (Y < y0)).astype(F) * np.clip(1 - (y0 - Y) / 900, 0, 1)
        P.knock('red', col); P.ink('black', P.screen(np.clip(.35 + (n_ - .5) * 1.2, .1, .95), 15, 3.4) * col)
        fire = (((X - x0) / 44) ** 2 + ((Y - y0) / 24) ** 2 < 1).astype(F) * (P.value(60) > .35)
        f = P.crayon(fire, .6, .2); P.clear(f); P.ink('red', f)
    wind = Wind(P, 5, 1.0); mouth = np.array([650, 770], np.float32); vort = np.array([1210, 640], np.float32)
    fz = np.array(fires, np.float32)
    # army A: from the lower left, drawn into the box's mouth
    A = np.stack([rng.uniform(-40, 700, 1500), rng.uniform(820, 1100, 1500)], 1).astype(np.float32)
    A = A[(A[:, 1] < 1020) | (A[:, 0] < 600)]
    pa = run(A, lambda p, v, t: (toward(p, mouth, 1.2) + wind(p) * .9, np.linalg.norm(p - mouth, axis=1) < 26), 150, 4.2, rng=rng)
    # army B: massed on the right, turning
    B = np.stack([rng.normal(vort[0], 200, 1500), rng.normal(vort[1], 150, 1500)], 1).astype(np.float32)
    pb = run(B, lambda p, v, t: (swirl(p, vort, 1.0, .12) + wind(p) * .6, np.zeros(len(p), bool)), 120, 3.6, rng=rng)
    # the people by the fires: scatter outward
    near = fz[rng.integers(0, len(fz), 700)]; Cc = (near + rng.normal(0, 30, (700, 2))).astype(np.float32)
    def flee(p, v, t):
        d = p[:, None, :] - fz[None]; r2 = (d ** 2).sum(-1, keepdims=True) + 400
        return (d / r2 * 4000).sum(1) + wind(p) * .5, np.zeros(len(p), bool)
    pc = run(Cc, flee, 70, 3.0, rng=rng)
    persp = lambda y: .6 + max(0, y - 150) * .0035
    for path, rf in ((pb, .05), (pc, .25), (pa, .06)):
        trails(P, path, persp, red=rng.random(path.shape[1]) < rf)
    # the box, drawn last so the streams vanish into it
    bx = P.edge_tone(sd_box(P, 770, 720, 150, 110), 1.5); P.clear(bx); P.ink('black', bx)
    mo = P.edge_tone(sd_box(P, 650, 770, 24, 58), 1); P.clear(mo); P.ink('red', mo)


def trittico(P):
    rng = P.nr; X, Y = P.X, P.Y; g = 18; wl = 340; wc = W - 2 * wl - 4 * g
    xl0, xc0, xr0 = g, 2 * g + wl, W - g - wl
    inner = (Y > g) & (Y < H - g)
    L = ((X > xl0) & (X < xl0 + wl) & inner).astype(F); C = ((X > xc0) & (X < xc0 + wc) & inner).astype(F); R = ((X > xr0) & (X < xr0 + wl) & inner).astype(F)
    frame = 1 - np.maximum.reduce([L, C, R]); P.ink('black', P.screen(np.full((P.H, P.W), .85, F), 15, 3.4) * frame)
    wind = Wind(P, 4, 1.0)
    # left: paradise. pale, a pond, a soft tree; few agents wandering in long slow loops round the water
    P.ink('red', P.screen(np.clip((320 - Y) / 600, 0, .3), 75, 4.5) * L)
    pond = (190, 760)
    pd = np.hypot((X - pond[0]) / 110, (Y - pond[1]) / 36)
    P.ink('black', P.isolines(pd.astype(F), [.3, .55, .8, 1.05], .6) * L)
    tree = soft_form(P, 190, 380, 70, 30, 9) * L; P.ink('black', P.crayon((P.screen(tree * .8, 15, 3) > .5).astype(F), .5, .3) * L)
    p0 = np.stack([rng.uniform(xl0 + 30, xl0 + wl - 30, 160), rng.uniform(560, 960, 160)], 1).astype(np.float32)
    pl = run(p0, lambda p, v, t: (wind(p) * 1.6 + swirl(p, pond, .4, -.05), np.zeros(len(p), bool)), 180, 1.4, inertia=.9, rng=rng)
    trails(P, pl, lambda y: .7, clip=L)
    # centre: the garden. soft forms, red and screened, each one a thing the swarm orbits; some leave for another
    P.ink('black', P.screen(np.full((P.H, P.W), .06, F), 15, 3.2) * C)
    things = [(xc0 + rng.uniform(.12, .88) * wc, rng.uniform(150, 900), rng.uniform(40, 90)) for _ in range(6)]
    for k, (cx, cy, r) in enumerate(things):
        f = soft_form(P, cx, cy, r, 34, 5 + k) * C
        P.ink('red', P.screen(f * .85, 75, 3.0))
        P.ink('black', P.isolines(np.hypot(X - cx, Y - cy).astype(F), [r * .35, r * .6], .5) * (f > .5))
    halo = [(cx + rng.normal(0, 30), cy + rng.normal(0, 30)) for cx, cy, _ in things for _ in range(2)]
    for hx, hy in halo:                                            # faint glass: spheres without a rim
        rr = np.hypot(X - hx, Y - hy); s = ((rr < 40) * np.clip(rr / 40, 0, 1) ** 3 * .35).astype(F)
        P.ink('black', P.screen(s, 15, 2.6) * C)
    n = 2600; home = rng.integers(0, len(things), n); T = np.array([(x, y) for x, y, _ in things], np.float32); Rr = np.array([r for *_, r in things], np.float32)
    ang = rng.uniform(0, 2 * np.pi, n); rad = Rr[home] * rng.uniform(1.2, 2.6, n)
    pos = (T[home] + np.stack([np.cos(ang), np.sin(ang)], 1) * rad[:, None]).astype(np.float32)
    switch = rng.random(n) < .12; tgt = home.copy(); tgt[switch] = rng.integers(0, len(things), switch.sum())
    rf = rng.uniform(1.2, 3.4, n)[:, None]; spin = rng.choice([-1.0, 1.0], n, p=[.3, .7])[:, None]
    def garden(p, v, t):
        h = np.where(t > 70, tgt, home); c = T[h]; d = p - c; r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        ring = Rr[h][:, None] * rf; tang = np.stack([-d[:, 1], d[:, 0]], 1) / r * spin
        pull = np.clip((r - ring) / 120, -.5, 2.0)
        return tang * .9 - d / r * pull + wind(p) * .9, np.zeros(len(p), bool)
    pg = run(pos, garden, 190, 2.2, inertia=.88, jitter=.35, rng=rng)
    trails(P, pg, lambda y: .55, clip=C, red=rng.random(n) < .04)
    # right: the black panel. fires above, everything drawn down a drain
    P.ink('black', P.screen(np.clip(.72 + (P.fbm(6, 3) - .5) * .5, 0, 1), 15, 3.4) * R)
    fires = (P.warp(P.fbm(10, 4), 40) > .6).astype(F) * (Y < 420) * R
    P.knock('black', fires); P.ink('red', P.crayon(fires, .6, .2))
    drain = (xr0 + wl * .5, 700)
    p2 = np.stack([rng.uniform(xr0, xr0 + wl, 1600), rng.uniform(300, 1000, 1600)], 1).astype(np.float32)
    pr = run(p2, lambda p, v, t: (swirl(p, drain, 1.0, .55) + wind(p) * .3, np.linalg.norm(p - drain, axis=1) < 14), 140, 4.0, rng=rng)
    # in the black, the paths are cut out of the ink (paper), the newest ones red
    tmp = {k: P.plate[k].copy() for k in P.plate}; P.plate['black'] = P.plate['black'] * (1 - R)
    trails(P, pr, lambda y: .6, clip=R)
    cut = P.plate['black'] * R; redp = P.plate['red'].copy()
    P.plate['black'] = tmp['black'] * (1 - cut); P.plate['red'] = np.maximum(redp, P.screen(cut * .45, 75, 2.4) * R)
    dm = np.clip(1 - np.hypot(X - drain[0], Y - drain[1]) / 30, 0, 1) * R; P.clear(dm); P.ink('black', (dm > .2).astype(F))
    # the emissary: one red agent, born by the pond, crossing the frames, ending in the drain
    e = np.array([[200.0, 900.0]], np.float32); way = [(300, 700), (560, 520), (760, 300), (980, 620), (1080, 820), drain]
    st = {'k': 0}
    def emissary(p, v, t):
        if np.linalg.norm(p[0] - np.float32(way[st['k']])) < 40 and st['k'] < len(way) - 1: st['k'] += 1
        return toward(p, way[st['k']], 1.0) + wind(p) * 1.0, np.linalg.norm(p - np.float32(drain), axis=1) < 10
    pe = run(e, emissary, 700, 5.0, inertia=.9, jitter=.15, rng=rng)
    em, emd = P.layer(); q = pe[:, 0]; q = q[~np.isnan(q[:, 0])]
    line(emd, [(x * P.S, y * P.S) for x, y in q], 4 * P.S); M = P.cov(em); P.clear(M); P.ink('red', M)
    disc(emd, (q[0][0] * P.S, q[0][1] * P.S), 9 * P.S); P.ink('red', P.cov(em))


PLATES = {'t2': ('t2-trionfo', trionfo), 'w2': ('w2-trittico', trittico)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time(); P = Press(a.seed * 1000 + 10 + list(PLATES).index(k), a.scale)
        P.nr = np.random.default_rng(P.seed); fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + '.png')); print(stem, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
