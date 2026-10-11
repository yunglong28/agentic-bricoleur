"""THE AGENTIC BRICOLEUR — one abstract panel after Maciunas' charts (Are.na "Fluxus", Sam Hart).
No words, no numbers. What is left of a Maciunas diagram once the names are gone: a time ruler with
uneven columns, lanes that run, stop, double and hand over to each other, brackets that gather
them, blocks of solid and screened ink, one red trunk that everything braids into.

Usage: python3 bricoleur7.py OUT [--seeds 1,2,3] [--scale 2] [--sheet]
"""
import argparse, json, math, os, time
import numpy as np
from PIL import Image
from bricoleur3 import Press, DW, DH, F, sd_box, bez, line, arrow, ring, disc, dashed


def bracket(d, P, x, y0, y1, w, s=1):
    """A square brace, open to the right (s=1) or left (s=-1), with a nib at its middle."""
    m = (y0 + y1) / 2
    line(d, P.pts([(x + s * w, y0), (x, y0), (x, y1), (x + s * w, y1)]), 3 * P.S)
    line(d, P.pts([(x, m), (x - s * w * .8, m)]), 3 * P.S)


def panel(P):
    S = P.S; rng = P.rng
    L, R, T, B = 60, 964, 150, 1200
    # the ruler: uneven columns, ticks without numerals, a heavier rule every so often
    cols = [L]
    while cols[-1] < R - 30: cols.append(cols[-1] + rng.choice([28, 36, 36, 48, 64, 90]))
    cols[-1] = R
    ru, rud = P.layer(); gr, grd = P.layer()
    rud.rectangle([*P.p(L, 96), *P.p(R, 104)], fill=255)
    for i, x in enumerate(cols):
        h = 30 if i % 4 == 0 else 16
        rud.rectangle([*P.p(x - 1.5, 104), *P.p(x + 1.5, 104 + h)], fill=255)
        dashed(grd, P.p(x, T - 10), P.p(x, B), S, 3 * S, 7 * S)
    P.ink('black', P.cov(ru)); P.ink('black', P.cov(gr) * .0 + P.cov(gr) * (P.value(9) > .35))
    # a red era band behind a stretch of the ruler, screened
    ex0 = cols[rng.randint(2, 6)]; ex1 = cols[rng.randint(len(cols) // 2, len(cols) - 3)]
    P.ink('red', P.screen(np.full((P.H, P.W), .5, F), 75, 4.4) * ((P.X > ex0) & (P.X < ex1) & (P.Y > 60) & (P.Y < 92)))

    # lanes
    n = rng.choice([22, 26, 30]); ys = np.linspace(T + 20, B - 30, n)
    trunk_y = ys[n // 2] + rng.uniform(-60, 60); tx0 = cols[int(len(cols) * .58)]; tx1 = cols[int(len(cols) * .82)]
    blk, blkd = P.layer(); scr, scrd = P.layer(); red, redd = P.layer(); ln, lnd = P.layer(); hat, hatd = P.layer()
    groups = []; g0 = 0
    while g0 < n:
        g1 = min(n, g0 + rng.choice([2, 3, 4, 5])); groups.append((g0, g1)); g0 = g1
    starts = {}
    for i, y in enumerate(ys):
        x = rng.choice(cols[:len(cols) // 3]); starts[i] = x
        end = rng.choice(cols[len(cols) // 3: int(len(cols) * .55)])
        disc(lnd, P.p(x, y), 4 * S)
        # run along the lane in segments: line, dashed, solid bar, screened bar, red bar, hatched bar
        cx = x
        while cx < end:
            nx = min(end, cx + rng.choice([36, 48, 64, 90, 130])); k = rng.random()
            if k < .35: lnd.line([*P.p(cx, y), *P.p(nx, y)], fill=255, width=2 * S)
            elif k < .5: dashed(lnd, P.p(cx, y), P.p(nx, y), 2 * S, 6 * S, 5 * S)
            elif k < .66: blkd.rectangle([*P.p(cx, y - 7), *P.p(nx, y + 7)], fill=255)
            elif k < .8: scrd.rectangle([*P.p(cx, y - 9), *P.p(nx, y + 9)], fill=255)
            elif k < .9: redd.rectangle([*P.p(cx, y - 8), *P.p(nx, y + 8)], fill=255)
            else:
                hatd.rectangle([*P.p(cx, y - 9), *P.p(nx, y + 9)], fill=255)
            cx = nx
        # hand-over: a vertical step to another lane, a dot at each end
        if rng.random() < .3:
            j = int(np.clip(i + rng.choice([-2, -1, 1, 2]), 0, n - 1)); hx = rng.choice([c for c in cols if x < c < end] or [end])
            lnd.line([*P.p(hx, y), *P.p(hx, ys[j])], fill=255, width=2 * S); disc(lnd, P.p(hx, ys[j]), 4 * S)
        # into the trunk: orthogonal staircase down/up to the trunk band
        ty = trunk_y + (i - n / 2) * 3.2
        mx = end + rng.uniform(20, 60)
        line(lnd, [P.p(end, y), P.p(mx, y), P.p(mx, ty), P.p(tx0, ty)], 2 * S)
    # brackets gathering groups on the left
    br, brd = P.layer()
    for g0, g1 in groups:
        if g1 - g0 < 2: continue
        xs = min(starts[i] for i in range(g0, g1)) - 14
        bracket(brd, P, xs, ys[g0] - 6, ys[g1 - 1] + 6, 8)
    # the trunk: a red band with the lanes knocked through it as hairlines
    band = P.edge_tone(sd_box(P, (tx0 + tx1) / 2, trunk_y, (tx1 - tx0) / 2, n * 1.6 + 10), 1.4, torn=.8)
    hl, hld = P.layer()
    for i in range(n):
        ty = trunk_y + (i - n / 2) * 3.2; hld.line([*P.p(tx0, ty), *P.p(tx1, ty)], fill=255, width=max(1, S))
    # out of the trunk: a fan of lanes to the right edge, ending in rings, discs and arrows
    fan, fand = P.layer(); m = rng.choice([7, 9, 11])
    for k in range(m):
        fy = T + 60 + k * (B - T - 120) / (m - 1); oy = trunk_y + (k - m / 2) * 6
        mx = tx1 + rng.uniform(20, 60)
        line(fand, [P.p(tx1, oy), P.p(mx, oy), P.p(mx, fy), P.p(R - 34, fy)], 3 * S if k % 3 else 5 * S)
        r = rng.random()
        if r < .4: ring(fand, P.p(R - 20, fy), 14 * S, 3 * S)
        elif r < .7: disc(fand, P.p(R - 20, fy), 12 * S)
        else: arrow(fand, P.p(R - 50, fy), P.p(R - 6, fy), 3 * S, 12 * S)
    # a few cross-lane rules, as in the charts' heavy separators
    sep, sepd = P.layer()
    for g0, g1 in groups[1:]:
        if rng.random() < .35:
            y = (ys[g0 - 1] + ys[g0]) / 2; sepd.line([*P.p(L, y), *P.p(cols[len(cols) // 2], y)], fill=255, width=S)

    P.ink('black', P.cov(ln)); P.ink('black', P.cov(blk)); P.ink('black', P.cov(br)); P.ink('black', P.cov(sep))
    P.ink('black', P.screen(np.full((P.H, P.W), .45, F), 15, 3.0) * P.cov(scr))
    hz = (((P.X + P.Y) % 7) < 2.2).astype(F); P.ink('black', hz * P.cov(hat))
    P.ink('red', P.cov(red)); P.clear(band * .0)
    P.ink('red', band); P.knock('red', P.cov(hl) * band); P.knock('black', band)
    P.ink('black', P.cov(fan))
    # foot: a closing double rule
    ft, ftd = P.layer(); ftd.rectangle([*P.p(L, 1226), *P.p(R, 1232)], fill=255); ftd.rectangle([*P.p(L, 1238), *P.p(R, 1240)], fill=255)
    P.ink('black', P.cov(ft))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seeds', default='1'); ap.add_argument('--scale', type=int, default=2)
    ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    seeds = [int(s) for s in a.seeds.split(',')]; thumbs = []
    for sd in seeds:
        t0 = time.time(); P = Press(sd * 1000 + 97, a.scale)
        panel(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        name = f'f-maciunas-panel-s{sd}'
        img.save(os.path.join(a.out, name + '.png'))
        meta = {'plate': 'f-panel', 'seed': sd, 'scale': a.scale, 'source': 'are.na/sam-hart/fluxus-1474596946',
                'coverage': P.stats(), 'seconds': round(time.time() - t0, 1)}
        json.dump(meta, open(os.path.join(a.out, name + '.json'), 'w'), indent=1)
        print(name, json.dumps(meta['coverage']), f"{meta['seconds']}s", flush=True)
        thumbs.append(img.resize((384, 480), Image.LANCZOS))
    if a.sheet:
        g = 12; sheet = Image.new('RGB', (len(thumbs) * (384 + g) + g, 480 + 2 * g), (40, 38, 36))
        for c, t in enumerate(thumbs): sheet.paste(t, (g + c * (384 + g), g))
        sheet.save(os.path.join(a.out, 'contact-sheet.png')); print('contact-sheet.png')


if __name__ == '__main__':
    main()
