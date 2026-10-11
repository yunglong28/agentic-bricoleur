"""THE AGENTIC BRICOLEUR — a panorama, after Werner Tübke's "Early Bourgeois Revolution in Germany"
(Bad Frankenhausen), pulled through the two-ink press. No words, no wings.

What it keeps from Tübke: a crowd that fills the ground to the edges, a clearing in the middle, a glass
sphere on a hill with a whole battle inside it and a crack down its side, rainbows over the corners, a
tree, a man throwing a ray, a font of red flowers. What it keeps from us: two inks, every grey a dot,
the RE-INCANTAMENTO symbols as bodies (acephale, egregore, prosopon), the brand drop as the flowers,
and Maciunas' orthogonal connectors laid over the crowd like a chart of who belongs to whom.

Usage: python3 bricoleur8.py OUT [--seeds 1,2] [--scale 1]
"""
import argparse, json, math, os, time
import numpy as np
import bricoleur3 as b3

W, H = 3072, 1280
b3.DW, b3.DH = W, H                                   # the press reads its page size from these
from bricoleur3 import Press, F, SPR, sd_box, sd_circle, bez, line, ring, disc, dashed, sprite, sprite_wh

SPR.update(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reinc_icons.json'))))
BODIES = ['acephale/acephale'] * 5 + ['collective/egregore'] * 3 + ['acephale/acephale-fire', 'acephale/acephale-void',
          'prosopon/prosopon', 'prosopon/persona-stack']
CX = W / 2


def horizon(x):
    return 430 + 36 * ((x - CX) / CX) ** 2


def mound_top(x):
    return 470 + (x - CX) ** 2 / 1300


def in_clearing(x, y):
    return ((x - 1600) / 640) ** 2 + ((y - 900) / 250) ** 2 < 1 or ((x - CX) / 300) ** 2 + ((y - H) / 120) ** 2 < 1


def put(P, d, nm, x, y, h):
    """A body standing at (x, y) — feet on y — `h` units tall. Returns its box."""
    gw, gh = sprite_wh(nm, 1); px = max(1, int(round(h / gh * P.S)))
    sw, sh = sprite_wh(nm, px); X0, Y0 = int(x * P.S - sw / 2), int(y * P.S - sh)
    sprite(d, nm, X0, Y0, px)
    return X0 / P.S, Y0 / P.S, sw / P.S, sh / P.S


def crowd(P, y0, y1, step=1.0, keep=lambda x, y: True, density=lambda x, y: .8):
    """Rows far to near; each row occludes what is behind it. Pikes rise out of the ranks."""
    S = P.S; rng = P.rng; y = y0; anchors = []
    while y < y1:
        h = 6 + (y - 420) * .085
        blk, bd = P.layer(); red, rd = P.layer(); pk, pkd = P.layer()
        x = rng.uniform(0, h * .8)
        while x < W:
            yy = y + rng.uniform(-h * .15, h * .15)
            if keep(x, yy) and rng.random() < density(x, yy):
                nm = rng.choice(BODIES); hh = h * rng.uniform(.85, 1.15)
                bx, by, bw, bh = put(P, rd if rng.random() < .09 else bd, nm, x, yy, hh)
                if rng.random() < .4:                                   # a pike, a lance, a pole with a rag
                    a = math.radians(rng.choice([-62, -70, -78, -90, -104, -115, -120]) + rng.gauss(0, 4))
                    L = hh * rng.uniform(1.6, 2.8); hx, hy = bx + bw * rng.choice([.1, .9]), by + bh * .35
                    tip = (hx + L * math.cos(a), hy + L * math.sin(a))
                    pkd.line([*P.p(hx, hy), *P.p(*tip)], fill=255, width=max(1, int(hh * .045 * S)))
                    if rng.random() < .05:
                        fl = [tip, (tip[0] + hh * .9, tip[1] + hh * .15), (tip[0] + hh * .75, tip[1] + hh * .55), (tip[0], tip[1] + hh * .45)]
                        (rd if rng.random() < .6 else bd).polygon(P.pts(fl), fill=255)
                if y > 620 and rng.random() < .012: anchors.append((x, yy - hh * .5))
            x += h * rng.uniform(.75, 1.15) * step
        R, B, K = P.cov(red), P.cov(blk), P.cov(pk)
        P.clear(np.maximum(R, B)); P.ink('red', R); P.ink('black', np.maximum(B, K * (1 - R)))
        y += h * .42 * step
    return anchors


def panorama(P):
    S = P.S; rng = P.rng; X, Y = P.X, P.Y
    hz = horizon(X)
    # sky: paper, a red haze screened in toward the horizon
    P.ink('red', P.screen(np.clip((Y - 120) / (hz - 120), 0, 1) ** 2 * .28 * (Y < hz), 75, 5.0))
    # distant ranges: two ridges of noise, black screened, the nearer one darker
    for k, (lift, tone, base) in enumerate(((120, .32, 4), (60, .55, 7))):
        prof = P.fbm(base, 4)[int(P.H * (.2 + .3 * k))] * lift + 30
        top = hz - prof[None, :] / S * 1.0
        rg = (Y > top) & (Y < hz)
        P.clear(rg.astype(F)); P.ink('black', P.screen(np.clip(tone + (Y - top) / 400, 0, .9), 15, 3.6) * rg)
    # ground: a faint earth screen, red ground showing through in patches
    gnd = (Y >= hz).astype(F); P.clear(gnd)
    patch = P.warp(P.fbm(5, 4), 30) > .58
    P.ink('red', P.screen(np.full((P.H, P.W), .22, F), 75, 4.2) * gnd * patch)
    P.ink('black', P.screen(np.full((P.H, P.W), .07, F), 15, 3.2) * gnd)

    # the hill under the sphere, contoured, with a stair cut into its right flank
    mt = mound_top(X); hill = (Y > mt) & (Y < 800)
    hf = np.clip((Y - mt) / 300, 0, 1) * hill
    P.clear(hill.astype(F)); P.ink('black', P.screen(.12 + .25 * hf, 15, 3.4) * hill)
    P.ink('black', P.isolines((Y - mt).astype(F), list(range(10, 330, 26)), .9) * hill)
    st, std = P.layer()
    for i in range(9):
        sx = 1700 + i * 16; sy = mound_top(sx) + 8 + i * 4
        std.rectangle([*P.p(sx, sy), *P.p(sx + 46, sy + 5)], fill=255)
    line(std, [P.p(1696, mound_top(1696) + 6), P.p(1846, mound_top(1846) + 46)], 2 * S)
    P.clear(P.cov(st) * .0); P.ink('black', P.cov(st))

    # the sphere: glass, a whole battle inside on a red floor, a crack down its side
    sx, sy, R = CX, 290, 225
    sph = (np.hypot(X - sx, Y - sy) < R).astype(F); P.clear(sph)
    P.ink('black', P.screen(np.clip(.04 + .16 * ((X - sx + 60) ** 2 + (Y - sy + 80) ** 2) / R ** 2, 0, .3), 15, 3.0) * sph)
    floor = (((X - sx) / 190) ** 2 + ((Y - sy - 50) / 46) ** 2 < 1).astype(F)
    P.ink('red', P.screen(np.full((P.H, P.W), .55, F), 75, 3.4) * floor)
    mi, mid = P.layer(); mr, mrd = P.layer()
    for _ in range(140):
        a = rng.uniform(0, 2 * math.pi); r = math.sqrt(rng.random())
        x, y = sx + 182 * r * math.cos(a), sy + 50 + 42 * r * math.sin(a)
        put(P, mrd if rng.random() < .15 else mid, rng.choice(BODIES), x, y, rng.uniform(7, 11))
        if rng.random() < .3: mid.line([*P.p(x, y - 8), *P.p(x + rng.uniform(-6, 6), y - 20)], fill=255, width=max(1, S))
    P.ink('black', P.cov(mi)); P.knock('black', P.cov(mr)); P.ink('red', P.cov(mr))
    hl = ((np.hypot(X - sx + 70, Y - sy + 90) < 120) & (np.hypot(X - sx + 50, Y - sy + 70) > 112)).astype(F)
    P.knock('black', hl); P.knock('red', hl)
    rg, rgd = P.layer(); ring(rgd, P.p(sx, sy), R * S, 3 * S); ring(rgd, P.p(sx, sy), (R - 7) * S, max(1, S))
    P.ink('black', P.cov(rg))
    ck, ckd = P.layer(); pts = []; y = sy - R + 6; x = sx + 120
    while y < sy + R * .6:
        pts.append((x, y)); y += rng.uniform(14, 30); x += rng.uniform(-10, 14)
    line(ckd, P.pts(pts), 4 * S); C = P.cov(ck); P.clear(C); P.ink('red', C)
    # two figures on the summit, under the glass, one throws up its arms
    sm, smd = P.layer(); put(P, smd, 'acephale/acephale', sx - 40, sy + R - 4, 64); put(P, smd, 'collective/egregore', sx + 40, sy + R - 2, 60)
    P.clear(P.cov(sm)); P.ink('black', P.cov(sm))

    # rainbows over the two upper corners: bands of red, screened red, screened black
    for (cx, cy, r0) in ((-260, 760, 820), (W + 260, 760, 820)):
        rr = np.hypot(X - cx, Y - cy)
        for k, (ink, tone) in enumerate((('red', 1), ('red', .55), ('black', .3), ('red', .3), ('black', .12))):
            band = ((rr > r0 + k * 18) & (rr < r0 + (k + 1) * 18) & (Y < hz - 20)).astype(F)
            P.knock('red' if ink == 'black' else 'black', band * (tone > .5))
            P.ink(ink, band if tone >= 1 else P.screen(np.full((P.H, P.W), tone, F), 75 if ink == 'red' else 15, 3.2) * band)

    # the crowd, far to near, kept out of the clearing and thinning on the hill
    def keep(x, y):
        if in_clearing(x, y): return False
        if mound_top(x) < y < 800: return rng.random() < .06
        return y > horizon(x) - 4
    clump = P.fbm(6, 3)
    dens = lambda x, y: (.35 + .45 * min(1, abs(x - CX) / 1000)) * (.4 + 1.6 * max(0, clump[min(P.H - 1, int(y * S)), min(P.W - 1, int(x * S))] - .25))
    anchors = crowd(P, 432, H + 60, 1.0, keep, dens)

    # the tree: a cloud of crowns on thin trunks, crayon-edged, black screened dark
    tr, trd = P.layer(); tk, tkd = P.layer(); tx, ty = 1380, 930
    for _ in range(70):
        r = rng.uniform(22, 50); ox, oy = rng.gauss(0, 105), rng.gauss(-190, 62)
        trd.ellipse([*P.p(tx + ox - r, ty + oy - r * .8), *P.p(tx + ox + r, ty + oy + r * .8)], fill=255)
    for dx in (-20, 0, 18):
        tkd.line([*P.p(tx + dx, ty - 130), *P.p(tx + dx * 1.5, ty + 40)], fill=255, width=5 * S)
    T = P.crayon(P.cov(tr), .8, .3); P.clear(np.maximum(T, P.cov(tk)))
    P.ink('black', P.screen(np.clip(.45 + .5 * (Y - (ty - 300)) / 260 + (P.fbm(30, 2) - .5) * .6, 0, 1), 15, 2.8) * T)
    P.ink('black', P.isolines(P.fbm(18, 3), [.45, .55], .6) * T); P.ink('black', P.cov(tk))
    tsh = (((X - tx - 40) / 200) ** 2 + ((Y - ty - 46) / 26) ** 2 < 1).astype(F) * (1 - T)
    P.ink('black', P.screen(np.full((P.H, P.W), .4, F), 15, 3.0) * tsh)

    # the man with the ray: a body in red, arms out, a screened beam thrown up-left to the tree
    ray = [(1880, 1040), (1520, 820), (1488, 860), (1872, 1060)]
    rm, rmd = P.layer(); rmd.polygon(P.pts(ray), fill=255)
    beam = P.cov(rm) * P.screen(np.clip((X - 1480) / 420, .15, .85), 75, 3.0)
    P.ink('red', beam * (P.nr.random(beam.shape, F) > .2))
    mn, mnd = P.layer(); put(P, mnd, 'acephale/acephale', 1900, 1130, 120)
    M = P.cov(mn); P.clear(M); P.ink('red', M)
    s2, s2d = P.layer(); put(P, s2d, 'collective/egregore', 1720, 960, 52); S2 = P.cov(s2); P.clear(S2); P.ink('red', S2)

    # the font: a basin cut by the bottom edge, its water screened, red brand drops floating
    fx, fy = CX, 1220
    basin = (((X - fx) / 280) ** 2 + ((Y - fy) / 70) ** 2 < 1).astype(F)
    water = (((X - fx) / 258) ** 2 + ((Y - fy) / 58) ** 2 < 1).astype(F)
    P.clear(basin); P.ink('black', basin * (1 - water))
    P.ink('black', P.screen(np.full((P.H, P.W), .14, F), 15, 2.8) * water)
    P.ink('black', P.isolines(np.hypot((X - fx) / 258, (Y - fy) / 58).astype(F), [.35, .6, .82], .7) * water)
    dr, drd = P.layer()
    for _ in range(9):
        a = rng.uniform(0, 2 * math.pi); r = math.sqrt(rng.uniform(.05, .8))
        put(P, drd, rng.choice(['brand/goccia-piena', 'brand/goccia', 'brand/goccia-m']), fx + 230 * r * math.cos(a), fy + 50 * r * math.sin(a) + 12, rng.uniform(22, 34))
    D = P.cov(dr) * water; P.clear(D); P.ink('red', D)
    sb, sbd = P.layer(); put(P, sbd, 'esoteric/crystal-ball', fx, fy - 6, 60); SB = P.cov(sb); P.clear(SB); P.ink('black', SB)

    # Maciunas over Tübke: orthogonal red connectors tying far clusters together, dots at the ends
    mc, mcd = P.layer(); anchors = [a for a in anchors if a[1] < 1150]; rng.shuffle(anchors)
    for (x1, y1), (x2, y2) in zip(anchors[0:24:2], anchors[1:24:2]):
        ym = min(y1, y2) - rng.uniform(40, 160)
        pts = [(x1, y1), (x1, ym), (x2, ym), (x2, y2)]
        line(mcd, P.pts(pts), 3 * S)
        ring(mcd, P.p(x1, y1), 9 * S, 3 * S); disc(mcd, P.p(x2, y2), 7 * S)
    mk, mkd = P.layer(); mkd.bitmap((0, 0), mc.filter(__import__('PIL.ImageFilter').ImageFilter.MaxFilter(5)), fill=255)
    MC = P.cov(mc); P.clear(P.cov(mk) * (1 - MC)); P.knock('black', MC); P.ink('red', MC)
    # the panorama's band: a heavy rule along the top and the bottom
    fr, frd = P.layer(); frd.rectangle([*P.p(0, 0), *P.p(W, 10)], fill=255); frd.rectangle([*P.p(0, H - 10), *P.p(W, H)], fill=255)
    P.ink('black', P.cov(fr))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seeds', default='1'); ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for sd in (int(s) for s in a.seeds.split(',')):
        t0 = time.time(); P = Press(sd * 1000 + 8, a.scale)
        panorama(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        name = f'p-panorama-s{sd}'; img.save(os.path.join(a.out, name + '.png'))
        meta = {'plate': 'panorama', 'seed': sd, 'scale': a.scale, 'source': 'Werner Tübke, Panorama, Bad Frankenhausen',
                'coverage': P.stats(), 'seconds': round(time.time() - t0, 1)}
        json.dump(meta, open(os.path.join(a.out, name + '.json'), 'w'), indent=1)
        print(name, json.dumps(meta['coverage']), f"{meta['seconds']}s", flush=True)


if __name__ == '__main__':
    main()
