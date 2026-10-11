"""THE AGENTIC BRICOLEUR — sketches after Bosch and Bruegel, in the two-ink press. Masses and composition only.

  b1 giochi     Children's Games: a square seen from above, no sky, groups each at its own rite, tied by Maciunas lines
  b2 torre      Tower of Babel: a spiral tower off to the left, every tier a different print process, a harbour right
  b3 trionfo    Triumph of Death: a high horizon, smoke columns for a sky, two armies on the diagonal, a box that swallows
  b4 trittico   Garden of Earthly Delights: three panels, pale, crowded with pods, black and burning
  b5 occhio     Table of the Seven Sins: the eye as a table, seven wedges, four roundels
  b6 icaro      Landscape with the Fall of Icarus: a tilted calm, ploughed land, one small red drop in the sea

Usage: python3 bricoleur9.py OUT [--only b1,b3] [--seed 1] [--scale 1]
"""
import argparse, json, math, os, time
import numpy as np
from PIL import Image
import bricoleur3 as b3

W, H = 1536, 1024
b3.DW, b3.DH = W, H
from bricoleur3 import Press, F, SPR, sd_box, bez, line, ring, disc, dashed, sprite, sprite_wh

SPR.update(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reinc_icons.json'))))
BODIES = ['acephale/acephale'] * 4 + ['collective/egregore'] * 3 + ['prosopon/prosopon', 'acephale/acephale-void']


def put(P, d, nm, x, y, h):
    gw, gh = sprite_wh(nm, 1); px = max(1, int(round(h / gh * P.S))); sw, sh = sprite_wh(nm, px)
    sprite(d, nm, int(x * P.S - sw / 2), int(y * P.S - sh), px)


def scr(P, tone, ang=15, cell=3.4):
    return P.screen(np.full((P.H, P.W), tone, F) if np.isscalar(tone) else tone, ang, cell)


def solid(P, ink, M):
    P.clear(M); P.ink(ink, M)


def maciunas(P, pts, w=3):
    mc, d = P.layer(); rng = P.rng
    for (x1, y1), (x2, y2) in pts:
        ym = min(y1, y2) - rng.uniform(20, 70)
        line(d, P.pts([(x1, y1), (x1, ym), (x2, ym), (x2, y2)]), w * P.S)
        ring(d, P.p(x1, y1), 7 * P.S, 2 * P.S); disc(d, P.p(x2, y2), 5 * P.S)
    M = P.cov(mc); P.knock('black', M); P.ink('red', M)

# ------------------------------------------------------------ sketches


def giochi(P):
    rng = P.rng; X, Y = P.X, P.Y
    P.ink('black', scr(P, .06))
    # the street: two rows of houses running off diagonally, top left and right edge
    hs, hd = P.layer()
    for k in range(9):
        t = k / 9; x, y = 40 + t * 520, 0 + t * 260; s = 60 + t * 50
        hd.polygon(P.pts([(x, y), (x + s, y - s * .3), (x + s, y + s * .7), (x, y + s)]), fill=255)
    for k in range(7):
        y = 120 + k * 130; hd.rectangle([*P.p(W - 150 - k * 6, y), *P.p(W, y + 110)], fill=255)
    solid(P, 'black', scr(P, .5) * P.cov(hs))
    P.ink('black', P.isolines((X * .5 + Y).astype(F), list(range(300, 2400, 60)), .5) * (Y > 300) * scr(P, .4, 75, 2))
    forms = ['ring', 'line', 'chain', 'pile', 'pair', 'spiral']; groups = []
    for _ in range(70):
        gx, gy = rng.uniform(80, W - 200), rng.uniform(200, H - 40)
        if gx < 560 and gy < 260 + gx * .5 - 40: continue
        groups.append((gx, gy, rng.choice(forms)))
    b, bd = P.layer(); r, rd = P.layer(); h0 = lambda y: 10 + y * .022
    for gx, gy, f in sorted(groups, key=lambda g: g[1]):
        h = h0(gy); d = rd if rng.random() < .12 else bd; n = rng.randint(4, 9)
        for i in range(n):
            if f == 'ring': a = 2 * math.pi * i / n; x, y = gx + math.cos(a) * h * 1.6, gy + math.sin(a) * h * .8
            elif f == 'line': x, y = gx + i * h * .8, gy
            elif f == 'chain': x, y = gx + i * h * .7, gy + math.sin(i) * h * .3
            elif f == 'pile': x, y = gx + rng.gauss(0, h * .5), gy - i * h * .3
            elif f == 'pair': x, y = gx + (i % 2) * h * .9, gy + (i // 2) * h * .2
            else: a = i * .9; x, y = gx + math.cos(a) * i * h * .25, gy + math.sin(a) * i * h * .12
            put(P, d, rng.choice(BODIES), x, y, h)
    solid(P, 'black', P.cov(b)); solid(P, 'red', P.cov(r))
    same = {}
    for g in groups: same.setdefault(g[2], []).append(g)
    pairs = []
    for f, gs in same.items():
        for a, c in zip(gs[:4], gs[1:5]):
            if rng.random() < .5: pairs.append(((a[0], a[1] - 30), (c[0], c[1] - 30)))
    maciunas(P, pairs[:14], 2)


def torre(P):
    rng = P.rng; X, Y = P.X, P.Y
    cl = P.warp(P.fbm(4, 5), 60); P.ink('red', scr(P, np.clip((cl - .45) * 1.6, 0, .5) * (Y < 700), 75, 4.4))
    P.ink('black', P.crayon(((cl > .66) & (Y < 600)).astype(F), .6, .3) * scr(P, .35))
    # sea and harbour to the right
    sea = ((Y > 640) & (X > 760)).astype(F); P.clear(sea)
    P.ink('black', P.isolines(Y.astype(F) + P.fbm(9, 3) * 30, list(range(650, 1024, 14)), .6) * sea)
    bt, btd = P.layer()
    for _ in range(14):
        x, y = rng.uniform(820, 1500), rng.uniform(680, 980); s = 6 + (y - 640) * .05
        btd.polygon(P.pts([(x - s, y), (x + s, y), (x + s * .6, y + s * .4), (x - s * .6, y + s * .4)]), fill=255)
        btd.line([*P.p(x, y), *P.p(x, y - s * 2.4)], fill=255, width=2 * P.S); btd.polygon(P.pts([(x + 2, y - s * 2.3), (x + s * 1.3, y - s * .6), (x + 2, y - s * .6)]), fill=255)
    solid(P, 'black', P.cov(bt))
    # the tower: tiers narrowing upward, each a different process, arcades knocked out
    cx, base, top = 520, 980, 70; tiers = 9; procs = ['solid', 'screen', 'iso', 'crayon', 'hatch', 'red']
    for k in range(tiers):
        y1 = base - k * (base - top) / tiers; y0 = y1 - (base - top) / tiers
        w1 = 470 - k * 42; w0 = w1 - 30
        jag = k == tiers - 1
        tm, td = P.layer(); poly = [(cx - w1, y1), (cx + w1, y1), (cx + w0, y0), (cx - w0, y0)]
        if jag: poly = [(cx - w1, y1), (cx + w1, y1)] + [(cx + w0 - i * (2 * w0) / 8, y0 + rng.uniform(0, 50)) for i in range(9)]
        td.polygon(P.pts(poly), fill=255); M = P.cov(tm); P.clear(M)
        p = procs[k % len(procs)]
        if p == 'solid': P.ink('black', M)
        elif p == 'screen': P.ink('black', scr(P, .45) * M)
        elif p == 'iso': P.ink('black', P.isolines(X.astype(F), list(range(0, 1100, 12)), .5) * M)
        elif p == 'crayon': P.ink('black', P.crayon(M * (P.value(30) > .4), .7, .3))
        elif p == 'hatch': P.ink('black', (((X - Y) % 9) < 2.5).astype(F) * M)
        else: P.ink('red', M)
        ar, ad = P.layer(); n = int(w0 / 22)
        for i in range(n):
            x = cx - w0 + 14 + i * (2 * w0 - 28) / n; h = (y1 - y0) * .5
            ad.rectangle([*P.p(x, y1 - h - 4), *P.p(x + 9, y1 - 4)], fill=255); ad.ellipse([*P.p(x, y1 - h - 9), *P.p(x + 9, y1 - h + 1)], fill=255)
        A = P.cov(ar) * M; P.clear(A); P.ink('black', scr(P, .7) * A * (p != 'solid'))
        sc, sd = P.layer()
        if rng.random() < .6:
            x = cx + rng.choice([-1, 1]) * (w0 - 20)
            for j in range(5): sd.line([*P.p(x + j * 8, y0 - 30), *P.p(x + j * 8, y1)], fill=255, width=P.S)
            for j in range(4): sd.line([*P.p(x, y0 - 30 + j * 14), *P.p(x + 32, y0 - 30 + j * 14)], fill=255, width=P.S)
        P.ink('black', P.cov(sc))
    # a crane on the summit, a swarm at the foot
    cr, crd = P.layer(); line(crd, P.pts([(560, 130), (560, 30), (700, 50), (700, 110)]), 3 * P.S); P.ink('black', P.cov(cr))
    sw, swd = P.layer()
    for _ in range(260): put(P, swd, rng.choice(BODIES), rng.gauss(cx, 300), rng.uniform(985, 1020), rng.uniform(9, 13))
    solid(P, 'black', P.cov(sw))


def trionfo(P):
    rng = P.rng; X, Y = P.X, P.Y; hz = 150 + X * .04
    P.ink('black', scr(P, np.clip(.2 + P.fbm(6, 4) * .4, 0, .7)) * (Y > hz))
    P.ink('black', scr(P, .55) * (Y <= hz))
    n = P.fbm(8, 5)
    for k in range(9):                                            # smoke columns: the sky is made of them
        x0 = rng.uniform(80, W - 80); y0 = rng.uniform(hz.min() + 60, 640)
        wdt = 18 + (y0 - Y) * .35; dx = X - x0 - (y0 - Y) * rng.uniform(-.4, .4) - (n - .5) * 140
        col = ((np.abs(dx) < wdt) & (Y < y0)).astype(F) * np.clip(1 - (y0 - Y) / 900, 0, 1)
        P.clear(col * .0); P.knock('red', col); P.ink('black', scr(P, np.clip(.35 + (n - .5) * 1.2, .1, .95)) * col)
        fire = (((X - x0) / 40) ** 2 + ((Y - y0) / 22) ** 2 < 1).astype(F) * (P.value(60) > .35)
        solid(P, 'red', P.crayon(fire, .6, .2))
    # two armies on the diagonal, the left one charging down, the right one massed
    a, ad = P.layer(); r, rd = P.layer()
    for _ in range(900):
        t = rng.random(); x = 40 + t * 900 + rng.gauss(0, 60); y = 980 - t * 520 + rng.gauss(0, 40)
        put(P, rd if rng.random() < .05 else ad, 'collective/egregore', x, y, 10 + y * .025)
    for _ in range(700):
        x = rng.uniform(1000, W); y = rng.uniform(420, 1020)
        put(P, ad, rng.choice(BODIES), x, y, 10 + y * .025)
    pk, pkd = P.layer()
    for _ in range(300):
        x = rng.uniform(1000, W); y = rng.uniform(400, 1000); pkd.line([*P.p(x, y), *P.p(x - 20, y - 70)], fill=255, width=P.S)
    solid(P, 'black', P.cov(a)); P.ink('black', P.cov(pk)); solid(P, 'red', P.cov(r))
    # the box: a great black trap, mouth open, a line of bodies walking in
    bx = P.edge_tone(sd_box(P, 760, 720, 150, 110), 1.5); solid(P, 'black', bx)
    mo = P.edge_tone(sd_box(P, 640, 760, 26, 60), 1); solid(P, 'red', mo)
    q, qd = P.layer()
    for i in range(18): put(P, qd, 'acephale/acephale', 620 - i * 22, 830 + i * 9, 18 + i * .4)
    solid(P, 'black', P.cov(q))


def trittico(P):
    rng = P.rng; X, Y = P.X, P.Y; g = 18; wl = 340; wc = W - 2 * wl - 4 * g
    L = (X > g) & (X < g + wl); C = (X > 2 * g + wl) & (X < 2 * g + wl + wc); R = (X > W - g - wl) & (X < W - g)
    inner = ((Y > g) & (Y < H - g)); L, C, R = [(m & inner).astype(F) for m in (L, C, R)]
    frame = 1 - np.maximum.reduce([L, C, R]); P.ink('black', scr(P, .85) * frame)
    # left: paradise, nearly empty, a pond, one tree
    P.ink('red', scr(P, np.clip((300 - Y) / 600, 0, .3), 75, 4.5) * L)
    pond = (((X - 190) / 110) ** 2 + ((Y - 760) / 36) ** 2 < 1).astype(F) * L
    P.ink('black', P.isolines(np.hypot((X - 190) / 110, (Y - 760) / 36).astype(F), [.3, .55, .8], .6) * pond)
    t, td = P.layer()
    for _ in range(18):
        r = rng.uniform(14, 28); ox, oy = 190 + rng.gauss(0, 34), 380 + rng.gauss(0, 30); td.ellipse([*P.p(ox - r, oy - r), *P.p(ox + r, oy + r)], fill=255)
    td.line([*P.p(190, 400), *P.p(190, 600)], fill=255, width=6 * P.S); solid(P, 'black', P.crayon(P.cov(t), .6, .2) * L)
    f, fd = P.layer(); put(P, fd, 'acephale/acephale', 140, 900, 40); put(P, fd, 'collective/egregore', 240, 905, 38); solid(P, 'black', P.cov(f) * L)
    # centre: the garden of pods, drops as fruit and shelters, small spheres scattered, pools
    x0 = 2 * g + wl
    P.ink('black', scr(P, .08) * C)
    pools = np.zeros_like(X)
    for _ in range(4):
        cx, cy = rng.uniform(x0 + 80, x0 + wc - 80), rng.uniform(300, 900)
        pools = np.maximum(pools, (((X - cx) / 120) ** 2 + ((Y - cy) / 34) ** 2 < 1).astype(F))
    P.ink('red', scr(P, .45, 75, 3) * pools * C)
    pods, pd = P.layer(); inside, ins = P.layer(); sph, sd = P.layer()
    for _ in range(16):
        cx, cy = rng.uniform(x0 + 60, x0 + wc - 60), rng.uniform(160, 960); h = rng.uniform(70, 170)
        put(P, pd, 'brand/goccia', cx, cy, h)
        for _ in range(3): put(P, ins, rng.choice(BODIES), cx + rng.gauss(0, h * .12), cy - h * .18, h * .16)
    for _ in range(22):
        cx, cy, r = rng.uniform(x0 + 30, x0 + wc - 30), rng.uniform(80, 980), rng.uniform(12, 40)
        ring(sd, P.p(cx, cy), r * P.S, 2 * P.S)
    cr, crd = P.layer()
    for _ in range(500): put(P, crd, rng.choice(BODIES), rng.uniform(x0 + 10, x0 + wc - 10), rng.uniform(100, 1000), rng.uniform(9, 14))
    solid(P, 'black', P.cov(cr) * C)
    PD = P.cov(pods) * C; solid(P, 'red', PD); P.ink('black', P.cov(inside) * C); P.ink('black', P.cov(sph) * C)
    # right: hell, black, burning, machines made of rings and spikes
    P.ink('black', scr(P, np.clip(.75 + (P.fbm(6, 3) - .5) * .5, 0, 1)) * R)
    fires = (P.warp(P.fbm(10, 4), 40) > .6).astype(F) * (Y < 500)
    P.knock('black', fires * R); P.ink('red', P.crayon(fires * R, .6, .2))
    m, md = P.layer(); x1 = W - g - wl
    for k in range(3):
        cx, cy, r = x1 + rng.uniform(80, 260), rng.uniform(560, 900), rng.uniform(40, 80)
        ring(md, P.p(cx, cy), r * P.S, 6 * P.S)
        for i in range(12):
            a = i * math.pi / 6; md.line([*P.p(cx + math.cos(a) * r, cy + math.sin(a) * r), *P.p(cx + math.cos(a) * r * 1.4, cy + math.sin(a) * r * 1.4)], fill=255, width=4 * P.S)
    M = P.cov(m) * R; P.knock('black', M); P.ink('red', M)


def occhio(P):
    rng = P.rng; X, Y = P.X, P.Y; cx, cy, R = W / 2, H / 2, 440
    P.ink('black', scr(P, .1))
    rr = np.hypot(X - cx, Y - cy); ang = (np.arctan2(Y - cy, X - cx) + 2 * np.pi) % (2 * np.pi)
    disk = (rr < R).astype(F); P.clear(disk)
    wedge = (ang / (2 * np.pi / 7)).astype(np.int32)
    procs = [scr(P, .3), P.isolines(rr.astype(F), list(range(0, 500, 10)), .5), ((X + Y) % 10 < 3).astype(F),
             P.crayon((P.value(40) > .5).astype(F), .5, .2), scr(P, .15, 75, 3), (((X - Y) % 12) < 3).astype(F), scr(P, .55)]
    for k in range(7):
        m = disk * (wedge == k) * (rr > 150)
        P.ink('red' if k in (1, 4) else 'black', procs[k] * m)
        a = (k + .5) * 2 * np.pi / 7; fx, fy = cx + math.cos(a) * 300, cy + math.sin(a) * 300
        f, fd = P.layer()
        for i in range(7): put(P, fd, rng.choice(BODIES), fx + rng.gauss(0, 40), fy + rng.gauss(0, 30), 26)
        F_ = P.cov(f); P.clear(F_); P.ink('black', F_)
    sp, spd = P.layer()
    for k in range(7):
        a = k * 2 * np.pi / 7; spd.line([*P.p(cx + math.cos(a) * 150, cy + math.sin(a) * 150), *P.p(cx + math.cos(a) * R, cy + math.sin(a) * R)], fill=255, width=4 * P.S)
    ring(spd, P.p(cx, cy), R * P.S, 8 * P.S); ring(spd, P.p(cx, cy), 150 * P.S, 5 * P.S); P.clear(P.cov(sp)); P.ink('black', P.cov(sp))
    pu = (rr < 145).astype(F); P.clear(pu); P.ink('red', scr(P, np.clip(rr / 160, 0, .8), 75, 3.4) * pu)
    e, ed = P.layer(); put(P, ed, 'brand/occhio', cx, cy + 50, 100); solid(P, 'black', P.cov(e))
    rd_, rdd = P.layer()
    for (x, y) in ((150, 150), (W - 150, 150), (150, H - 150), (W - 150, H - 150)):
        ring(rdd, P.p(x, y), 105 * P.S, 5 * P.S)
    P.ink('black', P.cov(rd_))
    for (x, y), nm in zip(((150, 150), (W - 150, 150), (150, H - 150), (W - 150, H - 150)), ('esoteric/candle', 'esoteric/black-mirror', 'dissipation/bonfire', 'drops/portal')):
        disk2 = (np.hypot(X - x, Y - y) < 98).astype(F); P.clear(disk2); P.ink('red', scr(P, .25, 75, 3) * disk2)
        i, idd = P.layer(); put(P, idd, nm, x, y + 55, 110); solid(P, 'black', P.cov(i))


def icaro(P):
    rng = P.rng; X, Y = P.X, P.Y; hz = 260 + X * .16
    strata = P.warp(Y.astype(F) + P.fbm(5, 4) * 120, 40)
    cl = ((strata % 70) < 26) & (Y < hz)
    P.ink('black', P.crayon(cl.astype(F) * (P.value(12) > .45), .7, .35) * scr(P, .3))
    P.ink('red', scr(P, .12, 75, 5) * (Y < hz))
    sea = (Y > hz).astype(F); P.clear(sea)
    P.ink('black', P.isolines((Y - hz).astype(F) + P.fbm(14, 3) * 12, list(range(8, 900, 18)), .5) * sea)
    # the land: a diagonal wedge from the left, ploughed furrows, a rock spur
    land = ((Y - 1024) > -(1100 - X) * .75).astype(F); P.clear(land)
    P.ink('black', scr(P, .14) * land)
    fur = P.isolines((X * .4 + Y).astype(F), list(range(500, 2500, 16)), .6) * land * (X < 800) * (Y > 640)
    P.ink('black', fur)
    rk = P.edge_tone(sd_box(P, 120, 560, 120, 200), 4, torn=40); solid(P, 'black', scr(P, .6) * rk)
    pl, pld = P.layer(); put(P, pld, 'acephale/acephale', 520, 860, 90)
    pld.line([*P.p(560, 820), *P.p(660, 880)], fill=255, width=5 * P.S); solid(P, 'black', P.cov(pl))
    sh, shd = P.layer()
    for k in range(9):
        cx, cy = rng.uniform(300, 700), rng.uniform(700, 780)
        for _ in range(26):
            ox, oy = cx + rng.gauss(0, 7), cy + rng.gauss(0, 4); shd.ellipse([*P.p(ox - 4, oy - 3), *P.p(ox + 4, oy + 3)], fill=255)
    solid(P, 'black', P.cov(sh) * scr(P, .7))
    bt, btd = P.layer(); x, y = 1050, 560
    btd.polygon(P.pts([(x - 60, y), (x + 70, y), (x + 50, y + 22), (x - 45, y + 22)]), fill=255)
    btd.line([*P.p(x, y), *P.p(x, y - 140)], fill=255, width=3 * P.S); btd.polygon(P.pts([(x + 4, y - 136), (x + 80, y - 40), (x + 4, y - 30)]), fill=255)
    solid(P, 'black', P.cov(bt))
    # the event: a red drop just entering the water, two rings, low in the right corner
    dx, dy = 1400, 900
    ev, evd = P.layer(); put(P, evd, 'brand/goccia-piena', dx, dy, 34); solid(P, 'red', P.cov(ev))
    rg, rgd = P.layer(); rgd.ellipse([*P.p(dx - 30, dy - 6), *P.p(dx + 30, dy + 8)], outline=255, width=2 * P.S)
    rgd.ellipse([*P.p(dx - 54, dy - 10), *P.p(dx + 54, dy + 14)], outline=255, width=2 * P.S); P.clear(P.cov(rg)); P.ink('red', P.cov(rg))


SKETCHES = {'b1': ('b1-giochi', giochi), 'b2': ('b2-torre', torre), 'b3': ('b3-trionfo', trionfo),
            'b4': ('b4-trittico', trittico), 'b5': ('b5-occhio', occhio), 'b6': ('b6-icaro', icaro)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(SKETCHES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); thumbs = []
    for k in a.only.split(','):
        stem, fn = SKETCHES[k]; t0 = time.time(); P = Press(a.seed * 1000 + 50 + list(SKETCHES).index(k), a.scale)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + '.png')); print(stem, f'{time.time() - t0:.1f}s', flush=True)
        thumbs.append(img.resize((576, 384), Image.LANCZOS))
    g = 14; cols = 2; rows = (len(thumbs) + 1) // 2
    sheet = Image.new('RGB', (cols * (576 + g) + g, rows * (384 + g) + g), (40, 38, 36))
    for i, t in enumerate(thumbs): sheet.paste(t, (g + (i % cols) * (576 + g), g + (i // cols) * (384 + g)))
    sheet.save(os.path.join(a.out, 'contact-sheet.png'))


if __name__ == '__main__':
    main()
