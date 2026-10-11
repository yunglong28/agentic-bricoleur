"""THE AGENTIC BRICOLEUR — the night crowds leave the square. Seven grounds, after Bruegel and Bosch, for the
commons, the rent and the bazaar. Same press, same games, same cut-from-the-dark trails as bricoleur12.

  m1 ghiaccio    Bruegel's skaters: a frozen pond from above, crowds turning on the ice, fires on the bank
  m2 cavalcata   Bosch's Garden: the ride round the pool, pods in the meadow, pinnacles on the far water
  m3 spirale     Babel from above: a spiral ramp, the share climbing it toward the well at its heart
  m4 campi       a valley of fields: each its own furrows, its own game; visitors on the roads between
  m5 circuito    the square as a die: traces from everywhere run to one core, packets riding them
  m6 labirinto   a labyrinth on the floor of a nave: walkers ring by ring toward a fire at the centre
  m7 orizzonte   the high horizon: hills in contour, fires on them, smoke for a sky, a net between the fires

Usage: python3 bricoleur13.py OUT [--only m1,m3] [--seed 1] [--palette notte-blu]
"""
import argparse, math, os, time
import numpy as np
import bricoleur3 as b3
import bricoleur11 as e
import bricoleur12 as n
from bricoleur11 import W, H, F, C, scr, play, stack, sigil, mst, Wind, toward, swirl, trails, soft_form, sd_box, dashed, GAMES, persp
from bricoleur12 import cut, glow, fire, PALETTES
from bricoleur3 import line, ring, disc

PALETTES.update({
    'notte-verde': (C(234, 230, 220), C(255, 80, 150), C(14, 42, 34)),
    'notte-viola': (C(236, 232, 222), C(240, 176, 40), C(44, 26, 70)),
    'notte-petrolio': (C(234, 232, 224), C(255, 140, 0), C(8, 34, 44)),
})
DEFAULT = {'m1': 'notte-blu', 'm2': 'notte-verde', 'm3': 'notte', 'm4': 'notte-viola', 'm5': 'notte-petrolio',
           'm6': 'notte-rossa', 'm7': 'notte'}
wd = lambda y: 1.0 + 2.6 * float(np.clip(y / H, 0, 1))


def dark(P, t=.82):
    P.ink('black', scr(P, np.clip(t + (P.fbm(5, 3) - .5) * .3, 0, 1)))


def where(P, n, rmin, ok, tries=8000):
    out = []
    for _ in range(tries):
        x, y = P.rng.uniform(30, W - 30), P.rng.uniform(30, H - 30)
        if ok(x, y) and all((x - a) ** 2 + (y - b) ** 2 > (rmin * persp(y)) ** 2 for a, b in out): out.append((x, y))
        if len(out) == n: break
    return out


def games(P, G, wind, lo=8, hi=18):
    return [play(P, GAMES[int(P.nr.integers(0, len(GAMES)))], c, int(P.nr.integers(lo, hi)), wind=wind) for c in G]


def wanderers(P, n, wind, ok, steps=60):
    pts = where(P, n, 0, ok, n * 20); p0 = np.float32(pts); goal = p0 + P.nr.normal(0, 120, p0.shape).astype(np.float32)
    return e.run(p0, lambda p, v, t: (toward(p, goal) * .6 + wind(p), np.zeros(len(p), bool)), steps, 1.6, inertia=.85, jitter=.4, rng=P.nr)


def knockline(P, pts_list, w=2, k=1.0, ink=None):
    m, d = P.layer()
    for pts in pts_list: line(d, P.pts(pts), w * P.S)
    M = P.cov(m); P.knock('black', M * k)
    if ink: P.ink(ink, M)
    return M

# ------------------------------------------------------------ m1: the frozen pond


def ghiaccio(P):
    rng = P.nr; X, Y = P.X, P.Y; dark(P, .84); cx, cy, rx, ry = 760, 590, 640, 340
    pd = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + (P.fbm(6, 4) - .5) * .35; pond = (pd < 1).astype(F)
    P.knock('black', pond); P.ink('black', scr(P, np.clip(.5 + (P.fbm(4, 3) - .5) * .4, 0, 1)) * pond)
    cracks = P.isolines(P.warp(P.fbm(9, 4), 30), [.35, .5, .65], .4) * pond; P.knock('black', cracks * .8)
    rim = P.isolines(pd.astype(F), [1.0, 1.06, 1.14], .5); P.knock('black', rim * .7)
    # bare trees on the bank, white with snow
    m, d = P.layer()
    def tree(x, y, L, a, k):
        if k == 0 or L < 3: return
        x2, y2 = x + math.cos(a) * L, y + math.sin(a) * L; line(d, P.pts([(x, y), (x2, y2)]), max(1, k * .7 * P.S))
        for s in (-1, 1): tree(x2, y2, L * P.rng.uniform(.62, .78), a + s * P.rng.uniform(.25, .6), k - 1)
    for _ in range(22):
        for _t in range(200):
            x, y = P.rng.uniform(20, W - 20), P.rng.uniform(40, H - 10)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > 1.25: break
        tree(x, y, 26 * persp(y) + 10, -math.pi / 2 + P.rng.uniform(-.2, .2), 7)
    T = P.cov(m); P.knock('black', T)
    inside = lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < .82
    wind = Wind(P, 4, .7); centres = np.float32(where(P, 16, 130, inside))
    ns = 2000; home = rng.integers(0, len(centres), ns); R = rng.uniform(14, 150, ns)[:, None]
    a = rng.uniform(0, 2 * np.pi, ns); p0 = (centres[home] + np.stack([np.cos(a), np.sin(a) * .6], 1) * R).astype(np.float32)
    spin = rng.choice([-1., 1.], ns)[:, None]; O = np.float32([cx, cy])
    def skate(p, v, t):
        c = centres[home]; d = (p - c) * np.float32([1, 1.7]); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        tg = np.stack([-d[:, 1] * .6, d[:, 0]], 1) / r * spin
        out = (((p[:, 0] - cx) / rx) ** 2 + ((p[:, 1] - cy) / ry) ** 2 > .9)[:, None]
        return np.where(out, toward(p, O), tg - d / r * np.clip((r - R) / 30, -1, 1) + wind(p) * .4), np.zeros(len(p), bool)
    ps = e.run(p0, skate, 110, 3.0, inertia=.94, jitter=.12, rng=rng)
    bank = [(x, y) for x, y in where(P, 60, 300, lambda x, y: 1.05 < ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1.4)][:4]
    for x, y in bank: glow(P, x, y, 160, .45)
    G = where(P, 30, 90, lambda x, y: 1.1 < ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 and y > 40)
    cut(P, stack(games(P, G, wind)), wd)
    cut(P, ps, lambda y: .6 * wd(y), red=rng.random(ns) < .05)
    nodes = [tuple(c) for c in centres] + bank
    sigil(P, {'edges': [(nodes[a], nodes[b]) for a, b in mst(nodes)], 'nodes': [(c, 10) for c in nodes]}, 1.4, ink='red', knock=True)
    for i, (x, y) in enumerate(bank): fire(P, x, y, 18 + 6 * persp(y), 20 + i)

# ------------------------------------------------------------ m2: the ride round the pool


def cavalcata(P):
    rng = P.nr; X, Y = P.X, P.Y; dark(P, .84); O = np.float32([768, 640]); ky = .58
    lake = (Y < 210 + 20 * np.sin(X / 160)).astype(F); P.knock('black', lake); P.ink('black', scr(P, .5) * lake)
    P.knock('black', P.isolines(Y.astype(F) + P.fbm(8, 3) * 20, list(range(20, 230, 12)), .4) * lake * .6)
    m, d = P.layer()                                                     # pinnacles on the far water
    for k in range(5):
        x = 140 + k * 310 + P.rng.uniform(-40, 40); b = 215; h = P.rng.uniform(120, 190); w = P.rng.uniform(16, 28)
        d.polygon(P.pts([(x - w, b), (x + w, b), (x + w * .3, b - h * .6), (x + w * .5, b - h * .7), (x, b - h), (x - w * .4, b - h * .55)]), fill=255)
    M = P.cov(m); P.clear(M); P.ink('black', M)
    for k in range(5):
        x = 140 + k * 310; m2, d2 = P.layer(); ring(d2, P.p(x, 120), 22 * P.S, 2 * P.S); ring(d2, P.p(x, 120), 36 * P.S, 1.4 * P.S)
        R2 = P.cov(m2); P.knock('black', R2); P.ink('red', R2 * .999)
    rr = np.hypot(X - O[0], (Y - O[1]) / ky); pool = (rr < 150).astype(F)
    P.knock('black', pool); P.ink('red', P.screen(np.full((P.H, P.W), .35, F), 75, 3) * pool)
    P.knock('black', P.isolines(rr.astype(F), [40, 80, 120, 150], .6) * .9)
    pods = where(P, 12, 160, lambda x, y: y > 280 and np.hypot(x - O[0], (y - O[1]) / ky) > 360)
    for i, (x, y) in enumerate(pods):
        f = soft_form(P, x, y, 26 + 24 * persp(y), 16, 4 + i); P.knock('black', f * .7); P.ink('red', P.screen(f * .25, 75, 2.6))
    wind = Wind(P, 5, .7); nr = 1600; a = rng.uniform(0, 2 * np.pi, nr); R = rng.uniform(190, 300, nr)
    p0 = (O + np.stack([np.cos(a) * R, np.sin(a) * R * ky], 1)).astype(np.float32); Rr = R[:, None]
    def ride(p, v, t):
        d = (p - O) * np.float32([1, 1 / ky]); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        return np.stack([-d[:, 1] * ky, d[:, 0]], 1) / r - d / r * np.clip((r - Rr) / 20, -1, 1) + wind(p) * .2, np.zeros(len(p), bool)
    pr = e.run(p0, ride, 120, 3.4, inertia=.9, jitter=.1, rng=rng)
    orbit = []
    for x, y in pods:
        k = 70; a = rng.uniform(0, 2 * np.pi, k); r0 = (40 + 30 * persp(y)) * rng.uniform(1.1, 2.0, k)
        c = np.float32([x, y]); q0 = (c + np.stack([np.cos(a) * r0, np.sin(a) * r0 * .6], 1)).astype(np.float32); rk = r0[:, None]
        def orb(p, v, t, c=c, rk=rk):
            d = (p - c) * np.float32([1, 1.7]); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
            return np.stack([-d[:, 1] * .6, d[:, 0]], 1) / r - d / r * np.clip((r - rk) / 20, -1, 1) + wind(p) * .5, np.zeros(len(p), bool)
        orbit.append(e.run(q0, orb, 110, 1.8, inertia=.88, rng=rng))
    G = where(P, 30, 110, lambda x, y: y > 260 and np.hypot(x - O[0], (y - O[1]) / ky) > 340)
    cut(P, stack(games(P, G, wind) + orbit + [wanderers(P, 700, wind, lambda x, y: y > 240)]), wd)
    cut(P, pr, lambda y: .5 * wd(y), red=rng.random(nr) < .07)

# ------------------------------------------------------------ m3: the spiral


def spirale(P):
    rng = P.nr; X, Y = P.X, P.Y; dark(P, .86); O = np.float32([768, 560]); ky = .58; r0, pitch = 44, 16.0
    turns = 6; Rmax = r0 + pitch * 2 * np.pi * turns
    dx, dy = X - O[0], (Y - O[1]) / ky; rr = np.hypot(dx, dy); ph = np.mod(np.arctan2(dy, dx), 2 * np.pi)
    k = np.floor((rr - r0 - pitch * ph) / (pitch * 2 * np.pi)); inside = ((rr < Rmax) & (rr > r0)).astype(F)
    tone = .92 - .1 * np.mod(k, 3) - .04 * (k / turns)
    P.knock('black', inside); P.ink('black', scr(P, np.clip(tone, 0, 1).astype(F)) * inside)
    # the plain around: furrows, very dark
    P.knock('black', P.isolines((X * .4 + Y).astype(F), list(range(0, 2200, 14)), .35) * (1 - inside) * .35)
    th = np.linspace(0, 2 * np.pi * turns, 3000); sp = r0 + pitch * th
    pts = list(zip(O[0] + np.cos(th) * sp, O[1] + np.sin(th) * sp * ky))
    knockline(P, [pts], 2.2, 1.0)
    for j in range(0, len(pts) - 30, 26):                                   # arcades on the ramp's wall
        x, y = pts[j]; m, d = P.layer(); disc(d, P.p(x, y), 2.4 * P.S); P.knock('black', P.cov(m))
    well = P.edge_tone(np.hypot(dx, dy) - r0 * .9, 1.2); P.clear(well); P.ink('black', well)
    m, d = P.layer(); d.ellipse([*P.p(O[0] - r0, O[1] - r0 * ky), *P.p(O[0] + r0, O[1] + r0 * ky)], outline=255, width=int(3 * P.S))
    Rm = P.cov(m); P.clear(Rm); P.ink('red', Rm)
    # climbers: enter on the outer turns, walk the ramp inward, toward the well
    nc = 1300; th0 = rng.uniform(1.0, 2 * np.pi * turns, nc); off = rng.uniform(.2, .8, nc) * pitch * 2 * np.pi
    v = rng.uniform(2.6, 4.2, nc); T = 150; path = np.full((T, nc, 2), np.nan, np.float32); t_ = th0.copy()
    for t in range(T):
        r = r0 + pitch * t_ - off * 0 + off - pitch * 2 * np.pi * .5; r = np.maximum(r, r0)
        t_ = t_ - v / np.maximum(r, 30); ok = t_ > 0.3
        path[t, ok, 0] = O[0] + np.cos(t_[ok]) * r[ok]; path[t, ok, 1] = O[1] + np.sin(t_[ok]) * r[ok] * ky
    wind = Wind(P, 5, .7); outside = lambda x, y: np.hypot(x - O[0], (y - O[1]) / ky) > Rmax + 30 and y < H - 20
    G = where(P, 40, 80, outside)
    cut(P, stack(games(P, G, wind) + [wanderers(P, 600, wind, outside)]), wd)
    cut(P, path, lambda y: .55 * wd(y), red=rng.random(nc) < .2)

# ------------------------------------------------------------ m4: the fields


def campi(P):
    rng = P.nr; X, Y = P.X, P.Y; dark(P, .78); ns = 46
    S = np.float32(where(P, ns, 120, lambda x, y: True)); ns = len(S)
    wx, wy = (P.fbm(3, 3) - .5) * 90, (P.fbm(3, 3) - .5) * 90
    d = np.stack([np.hypot(X + wx - x, Y + wy - y) for x, y in S]); o = np.sort(d, 0); idx = np.argmin(d, 0)
    road = ((o[1] - o[0]) < 5).astype(F)
    for i in range(ns):
        cell = (idx == i).astype(F) * (1 - road); a = rng.uniform(0, np.pi); spc = rng.uniform(6, 13)
        fur = ((X * np.cos(a) + Y * np.sin(a)) % spc < 1.4).astype(F); tone = rng.uniform(.62, .95)
        P.knock('black', cell); P.ink('black', scr(P, tone) * cell); P.knock('black', fur * cell * rng.uniform(.3, .7))
    P.knock('black', road); P.ink('red', P.screen(np.full((P.H, P.W), .2, F), 75, 2.4) * road)
    wind = Wind(P, 5, .6); G = [tuple(s) for s in S]
    gp = []
    for c, gm in zip(G, rng.integers(0, len(GAMES), ns)):
        p = play(P, GAMES[gm], c, int(rng.integers(8, 16)), wind=wind); i = int(np.argmin(np.hypot(S[:, 0] - c[0], S[:, 1] - c[1])))
        gp.append(np.clip(p, np.float32(c) - 50, np.float32(c) + 50))
    vis = n.visits(P, G, [S[j] for j in rng.integers(0, ns, ns)], wind, 200, 3)
    cut(P, stack(gp), wd)
    vv = stack(vis); cut(P, vv, lambda y: .45 * wd(y), red=np.ones(vv.shape[1], bool))

# ------------------------------------------------------------ m5: the die


def circuito(P):
    rng = P.nr; X, Y = P.X, P.Y; dark(P, .86); cx, cy, hw, hh = 768, 520, 170, 110
    P.knock('black', P.isolines(X.astype(F), list(range(0, W, 32)), .3) * .2); P.knock('black', P.isolines(Y.astype(F), list(range(0, H, 32)), .3) * .2)
    traces, pins = [], []
    for k in range(70):
        side = k % 4; u = rng.uniform(.08, .92)
        if side == 0: pin = (cx - hw + u * 2 * hw, cy - hh); out = (0, -1)
        elif side == 1: pin = (cx - hw + u * 2 * hw, cy + hh); out = (0, 1)
        elif side == 2: pin = (cx - hw, cy - hh + u * 2 * hh); out = (-1, 0)
        else: pin = (cx + hw, cy - hh + u * 2 * hh); out = (1, 0)
        L1 = rng.uniform(20, 120); p1 = (pin[0] + out[0] * L1, pin[1] + out[1] * L1)
        far = (rng.uniform(40, W - 40), rng.uniform(40, H - 40)) if rng.random() < .7 else (pin[0] + out[0] * 700, pin[1] + out[1] * 700)
        far = (float(np.clip(far[0], 30, W - 30)), float(np.clip(far[1], 30, H - 30)))
        dxx, dyy = far[0] - p1[0], far[1] - p1[1]; c = min(abs(dxx), abs(dyy))
        p2 = (p1[0] + np.sign(dxx) * c, p1[1] + np.sign(dyy) * c) if out[0] == 0 else (p1[0] + np.sign(dxx) * c, p1[1] + np.sign(dyy) * c)
        tr = [far, (far[0] - np.sign(dxx) * 0, p2[1]) if abs(dxx) > abs(dyy) else (p2[0], far[1]), p2, p1, pin]
        traces.append(tr); pins.append(pin)
    knockline(P, traces, 2.0, .95)
    m, d = P.layer()
    for tr in traces: ring(d, P.p(*tr[0]), 6 * P.S, 2 * P.S)
    for _ in range(80): ring(d, P.p(rng.uniform(20, W - 20), rng.uniform(20, H - 20)), 3 * P.S, 1.2 * P.S)
    P.knock('black', P.cov(m))
    die = P.edge_tone(sd_box(P, cx, cy, hw, hh), 1); P.clear(die); P.ink('black', die)
    P.ink('red', P.edge_tone(sd_box(P, cx, cy, hw - 22, hh - 22), 1) * P.screen(np.full((P.H, P.W), .3, F), 75, 2.4))
    m, d = P.layer()
    for pin in pins: disc(d, P.p(*pin), 3.5 * P.S)
    Pm = P.cov(m); P.clear(Pm); P.ink('red', Pm)
    # packets riding each trace into the core
    pk = []
    for tr in traces:
        seg = np.float32(tr); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(seg, axis=0), axis=1))]
        k = int(rng.integers(3, 9)); s0 = rng.uniform(-L[-1], 0, k); T = 160; v = rng.uniform(3, 5)
        out = np.full((T, k, 2), np.nan, np.float32)
        for t in range(T):
            s = s0 + t * v; ok = (s > 0) & (s < L[-1])
            out[t, ok, 0] = np.interp(s[ok], L, seg[:, 0]); out[t, ok, 1] = np.interp(s[ok], L, seg[:, 1])
        pk.append(out)
    wind = Wind(P, 5, .7); G = where(P, 40, 90, lambda x, y: abs(x - cx) > hw + 60 or abs(y - cy) > hh + 60)
    cut(P, stack(games(P, G, wind, 6, 14)), wd)
    pp = stack(pk); cut(P, pp, lambda y: 1.4, red=rng.random(pp.shape[1]) < .5)

# ------------------------------------------------------------ m6: the labyrinth


def labirinto(P):
    rng = P.nr; X, Y = P.X, P.Y; dark(P, .86); O = np.float32([768, 560]); ky = .58; R0, dr, K = 60, 38, 11
    rr = np.hypot(X - O[0], (Y - O[1]) / ky); floor_ = (rr < R0 + dr * K + 30).astype(F)
    P.knock('black', floor_ * .25)
    gaps = [rng.uniform(0, 2 * np.pi, 2) for _ in range(K + 1)]
    walls = []
    for j in range(K + 1):
        r = R0 + dr * j; th = np.linspace(0, 2 * np.pi, 900); keep = np.ones(len(th), bool)
        for g in gaps[j]: keep &= np.abs((th - g + np.pi) % (2 * np.pi) - np.pi) > .09
        seg = []
        for t_, k_ in zip(th, keep):
            if k_: seg.append((O[0] + np.cos(t_) * r, O[1] + np.sin(t_) * r * ky))
            elif len(seg) > 1: walls.append(seg); seg = []
        if len(seg) > 1: walls.append(seg)
    for j in range(1, K):
        for _ in range(3):
            a = rng.uniform(0, 2 * np.pi); r1, r2 = R0 + dr * j, R0 + dr * (j + 1)
            walls.append([(O[0] + np.cos(a) * r1, O[1] + np.sin(a) * r1 * ky), (O[0] + np.cos(a) * r2, O[1] + np.sin(a) * r2 * ky)])
    knockline(P, walls, 2.4, 1.0)
    # rosettes in the corners: the occult margin
    for (x, y) in [(150, 150), (W - 150, 150), (150, H - 150), (W - 150, H - 150)]:
        m, d = P.layer()
        for k in range(6):
            a = k * np.pi / 3; ring(d, P.p(x + np.cos(a) * 40, y + np.sin(a) * 40), 40 * P.S, 1.4 * P.S)
        ring(d, P.p(x, y), 80 * P.S, 1.4 * P.S); M = P.cov(m); P.knock('black', M); P.ink('red', M * .999)
    # walkers: each keeps its ring, turning; at a gap in its inner wall it may step in
    nw = 1100; k = rng.integers(1, K + 1, nw).astype(float); ph = rng.uniform(0, 2 * np.pi, nw); di = rng.choice([-1., 1.], nw)
    v = rng.uniform(1.8, 3.0, nw); T = 260; path = np.full((T, nw, 2), np.nan, np.float32); rcur = R0 + dr * (k - .5)
    for t in range(T):
        ph = ph + di * v / rcur
        for j in range(1, K + 1):
            sel = (k == j)
            if not sel.any(): continue
            near = np.zeros(nw, bool)
            for g in gaps[j - 1]: near |= np.abs((ph - g + np.pi) % (2 * np.pi) - np.pi) < .08
            step = sel & near & (rng.random(nw) < .6); k[step] -= 1
        tgt = R0 + dr * (k - .5); rcur = rcur + (tgt - rcur) * .25; live = k >= 1
        r_ = np.where(live, rcur, R0 * .5)
        path[t, :, 0] = O[0] + np.cos(ph) * r_ + rng.normal(0, .5, nw); path[t, :, 1] = O[1] + np.sin(ph) * r_ * ky
    wind = Wind(P, 5, .7)
    cut(P, path, lambda y: .9 * wd(y), red=rng.random(nw) < .12, glow=.5)
    glow(P, *O, 120, .6); fire(P, *O, 30)

# ------------------------------------------------------------ m7: the horizon


def orizzonte(P):
    rng = P.nr; X, Y = P.X, P.Y; hz = 250 + 30 * np.sin(X / 300); sky = (Y < hz).astype(F)
    P.ink('black', scr(P, np.clip(.86 + (P.fbm(5, 3) - .5) * .25, 0, 1)) * sky)
    land = 1 - sky; terr = P.warp(P.fbm(3, 4), 50)
    P.ink('black', scr(P, np.clip(.8 + (terr - .5) * .3, 0, 1)) * land)
    P.knock('black', P.isolines(terr + (Y / H) * .4, list(np.linspace(.2, 1.3, 34)), .5) * land * .55)
    Fs = where(P, 7, 260, lambda x, y: y > 330 and 80 < x < W - 80)
    n_ = P.fbm(8, 4)
    for x0, y0 in Fs:
        wdt = 14 + (y0 - Y) * .25; dx = X - x0 - (y0 - Y) * .25 - (n_ - .5) * 120
        col = ((np.abs(dx) < wdt) & (Y < y0)).astype(F) * np.clip(1 - (y0 - Y) / 700, 0, 1)
        P.knock('black', col * .55 * np.clip(n_ * 1.4, 0, 1)); glow(P, x0, y0, 150, .5)
    wind = Wind(P, 5, .8); G = where(P, 80, 80, lambda x, y: y > 300)
    Fz = np.float32(Fs); home = [Fz[np.argmin(np.linalg.norm(Fz - np.float32(c), axis=1))] for c in G]
    cut(P, stack(games(P, G, wind) + n.visits(P, G, home, wind) + [wanderers(P, 900, wind, lambda x, y: y > 290)]), wd)
    edges = []
    for j in range(len(Fs)):
        pts = [G[i] for i, h in enumerate(home) if (h == Fz[j]).all()] + [Fs[j]]
        edges += [(pts[a], pts[b]) for a, b in mst(pts)]
    sigil(P, {'edges': edges, 'nodes': [(g, 6) for g in G]}, 1.2, ink='red', knock=True)
    m, d = P.layer()
    for a, b in mst(Fs): dashed(d, P.p(*Fs[a]), P.p(*Fs[b]), 2 * P.S, 10 * P.S, 8 * P.S)
    M = P.cov(m); P.knock('black', M); P.ink('red', M)
    for i, (x, y) in enumerate(Fs): fire(P, x, y, 14 + 6 * persp(y), 30 + i)


PLATES = {'m1': ('m1-ghiaccio', ghiaccio), 'm2': ('m2-cavalcata', cavalcata), 'm3': ('m3-spirale', spirale), 'm4': ('m4-campi', campi),
          'm5': ('m5-circuito', circuito), 'm6': ('m6-labirinto', labirinto), 'm7': ('m7-orizzonte', orizzonte)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1); ap.add_argument('--palette', default=None); ap.add_argument('--suffix', default='')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time(); n.palette(a.palette or DEFAULT[k])
        P = b3.Press(a.seed * 1000 + 90 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + a.suffix + '.png')); print(stem + a.suffix, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
