"""THE AGENTIC BRICOLEUR — Children's Games (Bruegel, 1560), run as a crowd simulation. Six readings of the essay.

The square is seen from above and nobody in it is placed: each group plays a game (a ring, a chain, a tug,
a pile, a chase, hoops, a procession, a scatter), and what is printed is the memory of their paths. No icons,
no marks, no logos: only bodies, the ground they cross and the diagrams laid over them. Each plate swaps the
two inks of the press for its own colourway.

  e1 esempi       examples, not models: one group invents a game and it passes sideways, group to group,
                  changing at each passage. Lineage in the accent ink; nothing returns to an original
  e2 incursione   one world breaks into another: a tile world (moves on the grid) torn into Bruegel's square
                  (moves on the wind); who crosses the seam keeps playing, by the other world's rules
  e3 modello      the engineer's plan as an occult diagram over the square: rings and spokes the crowd is meant
                  to walk; the bricoleurs cut across it, and their desire lines are the accent
  e4 rendita      the workhouse: every game goes on, but a share of each crowd is drawn off into one tall machine
                  in the middle and carried up, out of the square
  e5 commons      night in the square: paths cut from the dark, the groups tied into one network around a fire
                  they share
  e6 bazar        the square as a market of a thousand stalls: every group its own small workshop, situated,
                  each with its own rule, none bigger than its neighbour

Usage: python3 bricoleur11.py OUT [--only e1,e3] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
from PIL import Image, ImageFilter
import bricoleur3 as b3

W, H = 1536, 1024
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F, sd_box, line, disc, ring, bez, dashed
from bricoleur10 import Wind, run, toward, swirl, trails, soft_form

C = lambda *v: np.array(v, np.float32) / 255
COLOURWAYS = {               # paper, accent ink (plays 'red'), key ink (plays 'black')
    'e1': (C(239, 235, 225), C(0, 112, 200), C(26, 24, 22)),          # riso blue / black
    'e2': (C(243, 239, 231), C(255, 72, 160), C(0, 120, 128)),        # fluo pink / teal
    'e3': (C(236, 231, 216), C(232, 152, 20), C(44, 38, 92)),         # gold / indigo
    'e4': (C(238, 234, 224), C(255, 100, 40), C(18, 72, 56)),         # orange / bottle green
    'e5': (C(232, 228, 218), C(255, 120, 30), C(20, 18, 24)),         # fire orange / night
    'e6': (C(240, 236, 228), C(0, 166, 110), C(120, 24, 44)),         # green / burgundy
}


def colourway(k):
    paper, acc, key = COLOURWAYS[k]
    b3.PAPER = paper; b3.INK['red'] = acc; b3.INK['black'] = key


def scr(P, tone, ang=15, cell=3.4):
    return P.screen(np.full((P.H, P.W), tone, F) if np.isscalar(tone) else tone, ang, cell)


def solid(P, ink, M):
    P.clear(M); P.ink(ink, M)


persp = lambda y: .42 + .58 * np.clip(y / H, 0, 1)          # far is small: the square tilts away to the top

# ------------------------------------------------------------ the square (masses only)

VP = (1110, 0)                                               # where the long street goes
HALL = ((0, 360), (980, 70))                                 # the hall's foot, a long diagonal
HOUSES = ((1240, 40), (W, 470))                              # the houses' foot down the right


def foot(a, b, t):
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def facade(P, d, a, b, n, h, rows, arcade, rng):
    """Windows on a receding front: skewed with the foot line, taller toward the viewer."""
    sl = (b[1] - a[1]) / (b[0] - a[0])
    for i in range(n):
        t0, t1 = (i + .25) / n, (i + .75) / n; (x0, y0), (x1, y1) = foot(a, b, t0), foot(a, b, t1)
        k = .55 + .45 * (y0 / H + .3); hh = h * k
        if arcade:
            d.polygon(P.pts([(x0, y0 - 2), (x1, y1 - 2), (x1, y1 - hh * .55), (x0, y0 - hh * .55)]), fill=255)
            d.ellipse([*P.p(x0, y0 - hh * .55 - (x1 - x0) * .5), *P.p(x1, y0 - hh * .55 + (x1 - x0) * .5)], fill=255)
        for r in range(rows):
            if rng.random() < .12: continue
            yb = -hh * (.8 + r * .42); yt = yb - hh * .26
            d.polygon(P.pts([(x0, y0 + yb), (x1, y1 + yb), (x1, y1 + yt), (x0, y0 + yt)]), fill=255)


def square(P, tone=.5, ground=.05):
    """Bruegel's square, reduced: the hall's long front on a diagonal, the street into the top, houses down the right."""
    X, Y = P.X, P.Y; rng = P.rng
    P.ink('black', scr(P, np.clip(ground + (P.fbm(5, 3) - .5) * .07 + Y / H * .03, 0, 1)))
    m, d = P.layer()
    d.polygon(P.pts([(0, 0), (1060, 0), HALL[1], HALL[0]]), fill=255)
    d.polygon(P.pts([(1180, 0), (W, 0), HOUSES[1], HOUSES[0]]), fill=255)
    M = P.cov(m); P.clear(M); P.ink('black', scr(P, tone) * M)
    # the houses are many: each its own tone, a gable line between
    hm, hd = P.layer()
    for k in range(7):
        t = k / 7; (x, y) = foot(*HOUSES, t); hd.line([*P.p(x, y), *P.p(x + 40 + 60 * t, 0)], fill=255, width=int(3 * P.S))
    P.knock('black', P.cov(hm) * M)
    a, ad = P.layer()
    facade(P, ad, *HALL, 26, 120, 4, True, rng)
    facade(P, ad, *HOUSES, 14, 100, 3, False, rng)
    A = P.cov(a) * M; P.knock('black', A); P.ink('black', scr(P, tone * .3) * A)
    # the ground: a faint contour field, as if the square had been surveyed
    P.ink('black', P.isolines(P.warp(P.fbm(3, 3), 60), list(np.linspace(.2, .8, 16)), .5) * scr(P, .5, 75, 2.2) * (1 - M))
    return M


def ground_ok(x, y):
    """Where the children can be: in front of the hall, off the houses."""
    if y > H - 25 or x < 25 or x > W - 25: return False
    if y < 360 - x * .296 + 25: return False
    if x > 1240 + (y - 40) / 1.453 - 25: return False
    return True


def spots(P, n, rmin):
    out = []
    for _ in range(6000):
        x, y = P.rng.uniform(40, W - 40), P.rng.uniform(60, H - 40)
        if ground_ok(x, y) and all((x - a) ** 2 + (y - b) ** 2 > (rmin * persp(y)) ** 2 for a, b in out): out.append((x, y))
        if len(out) == n: break
    return out

# ------------------------------------------------------------ the games (each returns a path: steps × n × 2)

GAMES = ['ring', 'chain', 'tug', 'pile', 'chase', 'hoop', 'procession', 'scatter', 'leapfrog', 'top']


def play(P, game, c, n, steps=120, wind=None):
    rng = P.nr; c = np.asarray(c, np.float32); s = float(persp(c[1])); W0 = (lambda p: wind(p) * .35) if wind else (lambda p: 0)
    if game == 'ring':
        R = 26 * s * rng.uniform(.8, 1.4); a = rng.uniform(0, 2 * np.pi, n)
        p0 = c + np.stack([np.cos(a), np.sin(a) * .55], 1) * R * rng.uniform(1, 2.2, (n, 1))
        def dr(p, v, t):
            d = (p - c) * np.float32([1, 1.8]); r = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
            tg = np.stack([-d[:, 1] * .55, d[:, 0]], 1) / r
            return tg - d / r * np.clip((r - R) / (10 * s), -1, 1) + W0(p), np.zeros(len(p), bool)
        return run(p0.astype(np.float32), dr, steps, 1.6 * s, rng=rng, jitter=.2)
    if game in ('chain', 'procession'):
        a, b = rng.uniform(.02, .05, 2); ph = rng.uniform(0, 6.3); A = (60 if game == 'chain' else 140) * s
        t = np.arange(steps + n * 6, dtype=np.float32)[:, None]
        if game == 'chain': L = c + np.concatenate([np.sin(a * t + ph) * A, np.sin(b * t) * A * .5], 1)
        else:
            u = toward(c[None], VP)[0]; L = c + u * (t - steps / 2) * 1.6 * s + np.concatenate([np.sin(a * t) * 8 * s, np.cos(a * t) * 4 * s], 1)
        lag = 5 if game == 'chain' else 4
        path = np.stack([L[np.clip(np.arange(steps) + n * lag - i * lag, 0, len(L) - 1)] for i in range(n)], 1)
        return (path + rng.normal(0, 1.2 * s, path.shape)).astype(np.float32)
    if game == 'tug':
        ax = rng.uniform(0, np.pi); u = np.float32([np.cos(ax), np.sin(ax) * .6]); side = np.where(np.arange(n) < n // 2, -1, 1)
        k = np.abs(np.arange(n) - n // 2 + .5)
        t = np.arange(min(steps, 40), dtype=np.float32)[:, None, None]
        pull = np.sin(t * .08) * 10 * s
        base = c + (side * (8 + k * 9) * s)[:, None] * u
        return (base[None] + pull * u + rng.normal(0, 1.0, (len(t), n, 2))).astype(np.float32)
    if game == 'pile':
        p0 = c + rng.normal(0, 70 * s, (n, 2)) * np.float32([1, .6])
        return run(p0.astype(np.float32), lambda p, v, t: (toward(p, c) + W0(p) * .5, np.zeros(len(p), bool)), steps, 1.4 * s, rng=rng, jitter=.5)
    if game == 'chase':
        st = {'q': c.copy(), 'v': rng.normal(0, 1, 2).astype(np.float32)}
        p0 = c + rng.normal(0, 50 * s, (n, 2)); p0[0] = c
        def dr(p, v, t):
            if t % 18 == 0: st['v'] = (st['v'] + rng.normal(0, 1.2, 2)).astype(np.float32)
            w = toward(p, p[0]); w[0] = st['v'] + toward(p[:1], c, .4)[0]
            return w + W0(p), np.zeros(len(p), bool)
        return run(p0.astype(np.float32), dr, steps, 2.4 * s, rng=rng, jitter=.3)
    if game == 'hoop':
        t = np.arange(steps, dtype=np.float32)[:, None]; out = []
        for i in range(n):
            d = rng.uniform(0, 2 * np.pi); u = np.float32([np.cos(d), np.sin(d) * .6]); r = 6 * s
            q = c + u * (t - steps / 2) * 1.8 * s + np.concatenate([np.cos(t * .5 + i) * r, np.sin(t * .5 + i) * r * .6], 1)
            out.append(q + rng.normal(0, 10 * s, 2))
        return np.stack(out, 1).astype(np.float32)
    if game == 'scatter':
        p0 = c + rng.normal(0, 6 * s, (n, 2))
        return run(p0.astype(np.float32), lambda p, v, t: ((p - c) / (np.linalg.norm(p - c, axis=1, keepdims=True) + 1) + W0(p), np.zeros(len(p), bool)),
                   steps // 2, 2.0 * s, rng=rng, jitter=.4)
    if game == 'leapfrog':
        u = toward(c[None], c + rng.normal(0, 1, 2))[0] * np.float32([1, .6]); t = np.arange(steps, dtype=np.float32)
        out = []
        for i in range(n):
            x = (t * .9 + i * 14) * s; hop = np.abs(np.sin((t * 1.1 + i * 14) * np.pi / 14)) * 7 * s
            out.append(c + u * x[:, None] - np.float32([0, 1]) * hop[:, None])
        return np.stack(out, 1).astype(np.float32)
    # 'top': spinning tops, tight spirals
    t = np.arange(steps, dtype=np.float32)[:, None]; out = []
    for i in range(n):
        o = c + rng.normal(0, 30 * s, 2); r = (3 + t * .08) * s; ph = rng.uniform(0, 6.3)
        out.append(o + np.concatenate([np.cos(t * .35 + ph) * r, np.sin(t * .35 + ph) * r * .6], 1))
    return np.stack(out, 1).astype(np.float32)


def stack(paths):
    """Join group paths of different lengths into one array (NaN where a group has stopped)."""
    T = max(p.shape[0] for p in paths); out = []
    for p in paths:
        if p.shape[0] < T: p = np.concatenate([p, np.full((T - p.shape[0], *p.shape[1:]), np.nan, np.float32)])
        out.append(p)
    return np.concatenate(out, 1)


def width(y):
    return 1.0 + 2.6 * float(np.clip(y / H, 0, 1))


def folla(P, n, wind, steps=60, clip=None):
    """The crowd between the games: walkers on the wind, short memories, everywhere there is ground."""
    rng = P.nr; pts = []
    while len(pts) < n:
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if ground_ok(x, y): pts.append((x, y))
    p0 = np.float32(pts); goal = p0 + rng.normal(0, 120, p0.shape).astype(np.float32)
    return run(p0, lambda p, v, t: (toward(p, goal) * .6 + wind(p), np.zeros(len(p), bool)), steps, 1.6, inertia=.85, jitter=.4, rng=rng)


def sigil(P, pts, w=1.6, ink='black', knock=False):
    """Tech-occult construction lines: nodes ringed twice, tied by straight chords."""
    m, d = P.layer(); S = P.S
    for a, b in pts['edges']: line(d, P.pts([a, b]), w * S)
    for (x, y), r in pts['nodes']:
        ring(d, P.p(x, y), r * S, w * S); ring(d, P.p(x, y), r * .55 * S, max(1, w * .7 * S)); disc(d, P.p(x, y), 2.4 * S)
    M = P.cov(m)
    if knock: P.knock('black', M)
    P.ink(ink, M)


def mst(pts):
    """Minimum spanning tree over points (Prim): the cheapest net that ties every group to every other."""
    pts = np.asarray(pts, np.float32); n = len(pts); seen = [0]; edges = []
    d = np.linalg.norm(pts[:, None] - pts[None], axis=-1); best = d[0].copy(); frm = np.zeros(n, int)
    best[0] = np.inf
    for _ in range(n - 1):
        j = int(np.argmin(best)); edges.append((frm[j], j)); seen.append(j); best[j] = np.inf
        upd = d[j] < best; upd[seen] = False; best[upd] = d[j][upd]; frm[upd] = j
    return edges

# ------------------------------------------------------------ plates


def esempi(P):
    """Examples circulate sideways. One group invents; the next copies with a variation; and so on."""
    rng = P.nr; square(P); wind = Wind(P, 5, .8)
    trails(P, folla(P, 1400, Wind(P, 5, .8)), lambda y: .5 * width(y))
    G = spots(P, 95, 80); games = [GAMES[i] for i in rng.integers(0, len(GAMES), len(G))]
    # the lineage: a walk from neighbour to neighbour, never back, each step a mutation of the game
    pts = np.float32(G); cur = int(np.argmin(np.abs(pts[:, 0] - 260) + np.abs(pts[:, 1] - 820))); line_ = [cur]; g = 'ring'
    for _ in range(16):
        d = np.linalg.norm(pts - pts[cur], axis=1); d[line_] = np.inf; d[d > 260] = np.inf
        if not np.isfinite(d).any(): break
        cur = int(np.argmin(d + rng.uniform(0, 120, len(d)))); line_.append(cur)
    for k, i in enumerate(line_):
        games[i] = GAMES[(GAMES.index(g) + k // 2) % len(GAMES)]
    paths, red = [], []
    for i, (c, gm) in enumerate(zip(G, games)):
        n = int(rng.integers(10, 28)); p = play(P, gm, c, n, wind=wind); paths.append(p); red += [i in line_] * p.shape[1]
    trails(P, stack(paths), width, red=np.array(red))
    # the passages: arcs from each group to the one that copied it, an open ring at the start, no closure
    m, d = P.layer(); S = P.S
    for a, b in zip(line_[:-1], line_[1:]):
        (x1, y1), (x2, y2) = G[a], G[b]; mx, my = (x1 + x2) / 2, min(y1, y2) - 60 - abs(x2 - x1) * .15
        q = bez((x1, y1 - 14), (mx, my), (x2, y2 - 14), 40);
        for u, v in zip(q[::2], q[1::2]): line(d, P.pts([u, v]), 2 * S)
        disc(d, P.p(x2, y2 - 14), 4 * S)
    ring(d, P.p(G[line_[0]][0], G[line_[0]][1] - 14), 11 * S, 2 * S); ring(d, P.p(G[line_[0]][0], G[line_[0]][1] - 14), 5 * S, 2 * S)
    M = P.cov(m); P.knock('black', M); P.ink('red', M)


def incursione(P):
    """A tile world breaks into the square. The seam is a tear; who crosses it changes how they move."""
    rng = P.nr; X, Y = P.X, P.Y; Mb = square(P, .42)
    seam = lambda x, y: y - (180 + x * .62 + 40 * np.sin(x / 90))           # < 0: the tile world (upper left)
    tw = (seam(X, Y) < 0).astype(F) * (1 - Mb)
    tear = np.abs(seam(X, Y) + (P.fbm(14, 4) - .5) * 40) < 7
    # the tile world: an isometric grid laid flat, screened in the key ink, knocked out under the tear
    gx = ((X + Y * 1.2) % 48 < 2) | ((X - Y * 1.2) % 48 < 2)
    P.knock('black', tw); P.ink('black', scr(P, .14) * tw); P.ink('black', gx.astype(F) * tw)
    blocks = (P.value(30) > .78) & (seam(X, Y) < -40); bl = blocks.astype(F) * (1 - Mb)
    blk = ((((X + Y * 1.2) // 48) + ((X - Y * 1.2) // 48)) % 3 == 0).astype(F) * bl
    P.ink('black', scr(P, .55) * blk)
    wind = Wind(P, 5, .9)
    trails(P, folla(P, 1200, wind), lambda y: .5 * width(y))
    G = spots(P, 95, 80); paths, red = [], []
    for c in G:
        x, y = c; n = int(rng.integers(8, 20)); inside = seam(x, y) < 0
        if inside:                                                           # moves on the grid: four ways, turn at corners
            p = np.zeros((130, n, 2), np.float32); q = np.float32(c) + rng.normal(0, 30, (n, 2)); dirs = np.float32([[1, .83], [-1, -.83], [1, -.83], [-1, .83]])
            k = rng.integers(0, 4, n); s = persp(y)
            for t in range(130):
                turn = rng.random(n) < .08; k = np.where(turn, rng.integers(0, 4, n), k)
                q = q + dirs[k] * 2.2 * s
                cross = seam(q[:, 0], q[:, 1]) > 0                            # through the tear: Bruegel's wind takes over
                q[cross] += wind(q[cross]) * 1.6 + rng.normal(0, .6, (cross.sum(), 2))
                p[t] = q
            paths.append(p); red += list(seam(p[-1, :, 0], p[-1, :, 1]) > 0)
        else:
            gm = GAMES[int(rng.integers(0, len(GAMES)))]
            p = play(P, gm, c, n, wind=wind)
            # those near the tear are pulled through it and start stepping on the grid
            near = abs(seam(x, y)) < 160
            if near:
                q = p[-1].copy(); q = np.where(np.isnan(q), np.float32(c), q); ext = np.zeros((70, n, 2), np.float32)
                for t in range(70):
                    q = q + toward(q, (x - 160, y - 190)) * 2.4 * persp(y)
                    if True:
                        g = seam(q[:, 0], q[:, 1]) < 0
                        q[g] = np.round(q[g] / 12) * 12 + np.float32([[1.0, 0]]) * (t % 2)
                    ext[t] = q
                p = np.concatenate([p, ext]); red += list(seam(ext[-1, :, 0], ext[-1, :, 1]) < 0)
            else: red += [False] * n
            paths.append(p)
    trails(P, stack(paths), width, red=np.array(red))
    T = tear.astype(F) * (1 - Mb); P.clear(T); P.ink('red', P.crayon(T, .5, .2))


def modello(P):
    """The engineer's plan as a sigil: rings and spokes. Conformers walk it; bricoleurs cut across, in gold."""
    rng = P.nr; X, Y = P.X, P.Y; square(P, .5, .04)
    O = np.float32([760, 640]); Rs = [110, 220, 330, 440]; spokes = 12
    # the diagram: ellipses in the square's tilt, spokes, a twelve-pointed star, nodes double-ringed
    m, d = P.layer(); S = P.S; ky = .58
    for R in Rs: d.ellipse([*P.p(O[0] - R, O[1] - R * ky), *P.p(O[0] + R, O[1] + R * ky)], outline=255, width=int(2 * S))
    nodes = []
    for k in range(spokes):
        a = 2 * np.pi * k / spokes
        line(d, P.pts([(O[0] + np.cos(a) * 40, O[1] + np.sin(a) * 40 * ky), (O[0] + np.cos(a) * 470, O[1] + np.sin(a) * 470 * ky)]), 1.5 * S)
        b = 2 * np.pi * ((k * 5) % spokes) / spokes; c2 = 2 * np.pi * (((k + 1) * 5) % spokes) / spokes
        line(d, P.pts([(O[0] + np.cos(b) * Rs[2], O[1] + np.sin(b) * Rs[2] * ky), (O[0] + np.cos(c2) * Rs[2], O[1] + np.sin(c2) * Rs[2] * ky)]), 1.2 * S)
        for R in Rs[1::2]: nodes.append(((O[0] + np.cos(a) * R, O[1] + np.sin(a) * R * ky), 9))
    M = P.cov(m) * (Y > 250); P.knock('black', M); P.ink('black', scr(P, .8) * M)
    sigil(P, {'edges': [], 'nodes': nodes + [((O[0], O[1]), 26)]}, 2)
    # the walkers: each wants another node; conformers go radially then round; bricoleurs go straight
    n = 2600; th = rng.uniform(0, 2 * np.pi, n); r0 = rng.choice(Rs, n) + rng.normal(0, 14, n)
    pos = O + np.stack([np.cos(th) * r0, np.sin(th) * r0 * ky], 1); goal_t = rng.uniform(0, 2 * np.pi, n); goal_r = rng.choice(Rs, n)
    goal = O + np.stack([np.cos(goal_t) * goal_r, np.sin(goal_t) * goal_r * ky], 1); conf = rng.random(n) > .14
    def walk(p, v, t):
        d = (p - O) * np.float32([1, 1 / ky]); r = np.linalg.norm(d, axis=1) + 1e-6; a = np.arctan2(d[:, 1], d[:, 0])
        da = (goal_t - a + np.pi) % (2 * np.pi) - np.pi
        radial = np.abs(r - goal_r) > 8
        snap = np.round(a / (2 * np.pi / spokes)) * (2 * np.pi / spokes)
        rad_dir = np.stack([np.cos(snap), np.sin(snap) * ky], 1) * np.sign(goal_r - r)[:, None]
        tan_dir = np.stack([-np.sin(a), np.cos(a) * ky], 1) * np.sign(da)[:, None]
        want = np.where(radial[:, None], rad_dir + (np.stack([np.cos(snap), np.sin(snap) * ky], 1) * r[:, None] - (p - O)) * .05, tan_dir)
        want = np.where(conf[:, None], want, toward(p, goal) + np.float32(rng.normal(0, .3, (len(p), 2))))
        return want, np.linalg.norm(p - goal, axis=1) < 6
    pw = run(pos.astype(np.float32), walk, 220, 2.2, inertia=.75, jitter=.12, rng=rng)
    trails(P, pw, lambda y: (.45 if True else 0) * width(y), red=np.zeros(n, bool))
    gold = pw[:, ~conf]; trails(P, gold, lambda y: 1.1 * width(y), red=np.ones(gold.shape[1], bool))
    # around the plan, the square goes on with its own games
    wind = Wind(P, 5, .8); trails(P, folla(P, 900, wind), lambda y: .5 * width(y))
    G = [g for g in spots(P, 90, 80) if np.hypot(g[0] - O[0], (g[1] - O[1]) / ky) > 500]
    trails(P, stack([play(P, GAMES[int(rng.integers(0, len(GAMES)))], c, int(rng.integers(8, 18)), wind=wind) for c in G]), width)


def rendita(P):
    """Every game goes on; a share of every crowd is drawn into the machine in the middle and carried up."""
    rng = P.nr; X, Y = P.X, P.Y; square(P, .45)
    mx, base, top = 780, 610, 10
    wind = Wind(P, 5, .8); trails(P, folla(P, 1200, wind), lambda y: .5 * width(y)); G = spots(P, 90, 80)
    G = [g for g in G if abs(g[0] - mx) > 70 or g[1] > base + 40]
    paths, red = [], []
    for c in G:
        n = int(rng.integers(8, 20)); p = play(P, GAMES[int(rng.integers(0, len(GAMES)))], c, n, wind=wind)
        k = max(1, n // 4); q = p[-1, :k].copy(); q = np.where(np.isnan(q), np.float32(c), q)    # the share
        mouth = np.float32([mx, base]); ext = np.full((260, n, 2), np.nan, np.float32); s = persp(c[1])
        alive = np.ones(k, bool)
        for t in range(260):
            up = np.linalg.norm(q - mouth, axis=1) < 30
            w = np.where(up[:, None], np.float32([[0, -1]]) * 3.0 + np.float32(rng.normal(0, .15, (k, 2))), toward(q, mouth) * 2.6 * s + wind(q) * .4)
            q = q + w; q[:, 0] = np.where(up, mx + (q[:, 0] - mx) * .9, q[:, 0]); alive &= q[:, 1] > top
            ext[t, :k] = np.where(alive[:, None], q, np.nan)
        paths.append(np.concatenate([p, ext])); red += [True] * k + [False] * (n - k)
    trails(P, stack(paths), width, red=np.array(red))
    # the machine: a narrow dark shaft, rungs knocked out, a halo of rings over it
    sh = P.edge_tone(sd_box(P, mx, (base + top) / 2, 26, (base - top) / 2), 1.2); P.clear(sh)
    P.ink('black', sh)
    rungs = sh * ((Y % 22) < 3).astype(F) * (np.abs(X - mx) < 18); P.knock('black', rungs); P.ink('red', rungs)
    mo = P.edge_tone(sd_box(P, mx, base - 10, 34, 14), 1); P.clear(mo); P.ink('red', mo)
    sigil(P, {'edges': [((mx - 160, 120), (mx + 160, 120)), ((mx, 40), (mx, 200))], 'nodes': [((mx, 120), 60), ((mx, 120), 100)]}, 1.6)


def commons(P):
    """Night. The paths are cut out of the dark; the groups are tied into one net around a fire they share."""
    rng = P.nr; X, Y = P.X, P.Y
    P.ink('black', scr(P, np.clip(.82 + (P.fbm(5, 3) - .5) * .3, 0, 1)))
    Mb = square(P, .98, 0)
    wind = Wind(P, 5, .8); G = spots(P, 85, 85); fire = np.float32([700, 650])
    paths = [play(P, GAMES[int(rng.integers(0, len(GAMES)))], c, int(rng.integers(8, 18)), wind=wind) for c in G] + [folla(P, 1000, wind)]
    # some from each group walk to the fire and back: the net is made of their visits
    for c in G:
        q = np.float32(c) + rng.normal(0, 8, (2, 2)); out = np.zeros((160, 2, 2), np.float32)
        for t in range(160):
            tgt = fire if t < 80 else np.float32(c)
            q = q + toward(q, tgt) * 3.2 + wind(q) * .5; out[t] = q
        paths.append(out)
    path = stack(paths)
    keep = {k: P.plate[k].copy() for k in P.plate}; P.plate['black'][:] = 0
    trails(P, path, width, red=np.zeros(path.shape[1], bool))
    cut = P.plate['black'].copy(); P.plate['black'] = keep['black'] * (1 - cut); P.plate['red'] = np.maximum(keep['red'], P.screen(cut * .35, 75, 2.4))
    edges = mst(G)
    sigil(P, {'edges': [(G[a], G[b]) for a, b in edges], 'nodes': [(g, 8) for g in G]}, 1.4, ink='red', knock=True)
    f = soft_form(P, fire[0], fire[1], 34, 18, 11); f = P.crayon((f > .4).astype(F), .6, .25); P.clear(f); P.ink('red', f)
    glow = np.clip(1 - np.hypot(X - fire[0], (Y - fire[1]) * 1.6) / 260, 0, 1) ** 1.5
    P.knock('black', glow * .6)


def bazar(P):
    """A market of small workshops: every group fenced in its own plot, each with its own rule, none dominant."""
    rng = P.nr; X, Y = P.X, P.Y; square(P, .5)
    wind = Wind(P, 5, .8); G = spots(P, 110, 78); paths, red = [], []
    m, d = P.layer(); S = P.S
    for i, c in enumerate(G):
        s = persp(c[1]); hw, hh = 44 * s, 26 * s
        d.rectangle([*P.p(c[0] - hw, c[1] - hh), *P.p(c[0] + hw, c[1] + hh)], outline=255, width=max(1, int(1.4 * S)))
        n = int(rng.integers(6, 14)); p = play(P, GAMES[i % len(GAMES)], c, n, steps=110, wind=wind)
        p = np.clip(p, np.float32(c) - np.float32([hw, hh]) + 2, np.float32(c) + np.float32([hw, hh]) - 2)   # nobody leaves the stall
        paths.append(p); red += [False] * n
    M = P.cov(m) * (1 - P.plate['black'] * 0); P.ink('black', scr(P, .7, 15, 2.4) * M)
    trails(P, stack(paths), width, red=np.array(red))
    # the paths between the stalls, worn in the accent: who visits whom
    e = mst(G); m2, d2 = P.layer()
    for a, b in e:
        if rng.random() < .55: dashed(d2, P.p(*G[a]), P.p(*G[b]), 2.4 * S, 7 * S, 6 * S)
    M2 = P.cov(m2); P.knock('black', M2); P.ink('red', M2)


PLATES = {'e1': ('e1-esempi', esempi), 'e2': ('e2-incursione', incursione), 'e3': ('e3-modello', modello),
          'e4': ('e4-rendita', rendita), 'e5': ('e5-commons', commons), 'e6': ('e6-bazar', bazar)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time(); colourway(k)
        P = Press(a.seed * 1000 + 30 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + '.png')); print(stem, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
