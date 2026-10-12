"""THE AGENTIC BRICOLEUR — the supersurface carrying the flux diagram, and the operator taken apart.

No sprites, no emblems: the lanes of the diagram start from bare nodes, the grid holds only trees and shadows.
The operator loses the halo and the wing; what is left is a body made of what was at hand.

  s1 supersurface-flux   Superstudio's grid under a red sky; the Maciunas lanes run in along the grid's rows,
                         braid into the red BRICOLAGE trunk on the horizon, fan out as agents into the sky
  o1 cyberdeck           the operator cut into strips and taped back together, wired to a deck built in a
                         compact case and to a bare board; screws and parts on the table
  o2 innesto             the body from two processes at once: typed marks on one side, contour lines on the
                         other, the halves out of register; the screen holds another world's grid
  o3 sciame              the operator is many: a swarm leaves the screen and settles into the shape of a body
  o4 banco               the bench from above: the stock spread out, two arms reaching in, the chosen pieces
                         tied to the red field where the thing is being made

Usage: python3 bricoleur14.py OUT [--only s1,o1] [--seed 1] [--scale 1]
"""
import argparse, math, os, time
import numpy as np
from PIL import Image, ImageFilter, ImageFont
import bricoleur3 as b3
from bricoleur10 import trails, run, toward
b3.DW, b3.DH = 1024, 1280                                   # bricoleur10 sets a landscape page on import; back to portrait
from bricoleur3 import Press, F, MONO, sd_box, bez, line, ring, disc, dashed, ascii_figure, datasheet, agent_graph
DW, DH = 1024, 1280


def font(px, bold=False):
    return ImageFont.truetype(MONO, int(px), index=1 if bold else 0)


def scr(P, tone, ang=15, cell=3.4):
    return P.screen(np.full((P.H, P.W), tone, F) if np.isscalar(tone) else tone, ang, cell)


def solid(P, ink, M):
    P.clear(M); P.ink(ink, M)


class Curl:
    """A divergence-free wind for the portrait page."""
    def __init__(self, P, base=5, amp=1.0):
        psi = P.fbm(base, 3)[::P.S, ::P.S]; gy, gx = np.gradient(psi); self.u, self.v = gy * amp * 260, -gx * amp * 260

    def __call__(self, pos):
        xi = np.clip(pos[:, 0].astype(int), 0, DW - 1); yi = np.clip(pos[:, 1].astype(int), 0, DH - 1)
        return np.stack([self.u[yi, xi], self.v[yi, xi]], 1)

# ------------------------------------------------------------ s1: the supersurface carrying the diagram


def supersurface_flux(P):
    S = P.S; X, Y = P.X, P.Y; vx, hy, f, cam = 512, 610, 520, 1.6
    P.ink('red', P.screen(np.clip(1 - (hy - Y) / 470, 0, 1) * (Y < hy), 75, 5.4))
    hills = P.fbm(5, 5)[int(P.H * .3)]; prof = hy * S - (np.clip(hills - .35, 0, 1) * 150 + 6) * S
    mtn = (Y * S >= prof[None, :]) & (Y < hy)
    P.knock('red', mtn.astype(F)); P.ink('black', P.screen(np.clip((Y * S - prof[None, :]) / (80 * S), .15, .8), 15, 3.6) * mtn)
    g, gd = P.layer(); rows = []
    for xw in range(-30, 31):
        gd.line([P.p(vx + xw * f / .9, hy + cam * f / .9), P.p(vx + xw * f / 60, hy + cam * f / 60)], fill=255, width=3)
    z = 1.0
    while z < 60:
        y = hy + cam * f / z
        if y < DH + 5: gd.line([P.p(-50, y), P.p(DW + 50, y)], fill=255, width=3); rows.append(y)
        z *= 1.16
    P.ink('black', P.cov(g) * (Y > hy))
    # trees only, far to near, each with its red shadow
    for _ in range(9):
        xw = P.rng.uniform(-5, 5); zz = P.rng.uniform(2.2, 10); sx, sy = vx + xw * f / zz, hy + cam * f / zz; u = 260 / zz
        if not (40 < sx < DW - 40) or abs(sx - 520) < 160: continue
        sh, shd = P.layer(); shd.ellipse([*P.p(sx - .45 * u, sy - .09 * u), *P.p(sx + .9 * u, sy + .1 * u)], fill=255)
        M = P.cov(sh); P.clear(M); P.ink('red', scr(P, .6, 75, 3.8) * M)
        o, od = P.layer()
        for _k in range(6):
            r = P.rng.uniform(.3, .55) * u; ox = P.rng.uniform(-.4, .4) * u; oy = P.rng.uniform(-1.2, -.5) * u
            od.ellipse([*P.p(sx + ox - r, sy + oy - r), *P.p(sx + ox + r, sy + oy + r)], fill=255)
        od.rectangle([*P.p(sx - .05 * u, sy - .6 * u), *P.p(sx + .05 * u, sy)], fill=255)
        M = P.cov(o); P.clear(M); P.ink('black', P.crayon(M, .5, .2))
    # the timeline over the sky
    tk, tkd = P.layer(); fo = font(12 * S)
    for i, yr in enumerate(range(1960, 2030, 10)):
        x = 40 + i * (DW - 80) / 6.6; tkd.line([*P.p(x, 120), *P.p(x, 140)], fill=255, width=2 * S); tkd.text(P.p(x + 4, 104), str(yr), fill=255, font=fo)
    tkd.line([*P.p(40, 140), *P.p(DW - 40, 140)], fill=255, width=2 * S); P.ink('black', P.cov(tk))
    bk, bkd = P.layer(); line(bkd, P.pts([(640, 152), (640, 160), (DW - 40, 160), (DW - 40, 152)]), 4 * S); P.ink('red', P.cov(bk))
    # the lanes: bare nodes at the left, each running in along a row of the grid, then up into the trunk
    lanes = 14; ry = [y for y in rows if 660 < y < DH - 20]; ry = [ry[int(i)] for i in np.linspace(0, len(ry) - 1, lanes)] if len(ry) >= lanes else list(np.linspace(680, 1240, lanes))
    xM, xR = 400, 624; trunk = hy - 6
    L, Ld = P.layer(); tr, trd = P.layer()
    for i, y in enumerate(sorted(ry, reverse=True)):
        ring(Ld, P.p(40, y), 9 * S, 2 * S); disc(Ld, P.p(40, y), 3 * S)
        xs = 70 + P.rng.uniform(0, 160)
        Ld.line([*P.p(52, y), *P.p(xs, y)], fill=255, width=2 * S); dashed(Ld, P.p(xs, y), P.p(xs + 60, y), 2 * S, 6 * S, 5 * S)
        ty = trunk + (i - lanes / 2) * 5
        line(Ld, bez(P.p(xs + 60, y), P.p(xM - 30, y), P.p(xM, ty), 60), 2 * S)
        trd.line([*P.p(xM, ty), *P.p(xR, ty)], fill=255, width=3 * S)
        if i % 3 == 1:
            j = min(lanes - 1, i + 2); yj = sorted(ry, reverse=True)[j]
            Ld.line([*P.p(xs + 20, y), *P.p(xs + 40, yj)], fill=255, width=S); disc(Ld, P.p(xs + 20, y), 4 * S)
    Lm = P.cov(L); P.knock('red', Lm); P.ink('black', Lm)
    band = P.edge_tone(sd_box(P, (xM + xR) / 2, trunk, (xR - xM) / 2, lanes * 3 + 12), 1.5, torn=1.0)
    P.clear(band); P.ink('red', band); P.knock('red', P.cov(tr) * band)
    lb, lbd = P.layer(); lbd.text(P.p(xM + 16, trunk - lanes * 3 - 36), 'BRICOLAGE', fill=255, font=font(15 * S, True)); P.ink('black', P.cov(lb))
    # out of the trunk, into the sky: the agents
    cx, cy = 800, hy - 190; halo = P.edge_tone(np.hypot(X - cx, Y - cy) - 175, 30); P.knock('red', halo * .85)
    ag, agd = P.layer(); nodes = agent_graph(P, agd, cx, cy, 150, 16, 2 * S)
    for k in range(lanes):
        ty = trunk + (k - lanes / 2) * 5; nx, ny = nodes[k % len(nodes)]
        line(agd, bez(P.p(xR, ty), P.p(xR + 60, ty), P.p(nx, ny), 30), S)
    P.ink('black', P.cov(ag))

# ------------------------------------------------------------ the operator, taken apart


def body(P, ox=0, oy=0, k=1.0):
    """The operator's silhouette (head, neck, torso, arm), grey levels as in plate_operator, movable and scalable."""
    q = lambda pts: P.pts([(ox + 512 + (x - 512) * k, oy + y * k) for x, y in pts])
    def draw(dd):
        dd.polygon(q([(420, 450), (395, 500), (360, 545), (385, 556), (380, 585), (395, 612), (425, 650), (480, 668), (530, 640), (540, 470)]), fill=110)
        a, b = q([(425, 380), (625, 640)]); dd.ellipse([*a, *b], fill=255)
        dd.polygon(q([(470, 640), (460, 720), (560, 720), (560, 620)]), fill=130)
        dd.polygon(q([(470, 680), (420, 720), (360, 1000), (420, 1270), (790, 1270), (760, 860), (660, 700), (560, 660)]), fill=165)
        dd.polygon(q([(425, 760), (300, 940), (232, 1010), (272, 1042), (362, 982), (475, 830)]), fill=120)
    return draw


def mask_of(P, draw):
    m, d = P.layer(); draw(d); return P.cov(m)


def tape(P, x, y, w, h, a, tone=.35):
    c, s = math.cos(a), math.sin(a); dx, dy = P.X - x, P.Y - y
    u, v = dx * c + dy * s, -dx * s + dy * c
    edge = (P.fbm(30, 2) - .5) * 6
    M = ((np.abs(u) < w / 2 + edge) & (np.abs(v) < h / 2)).astype(F)
    P.ink('red', P.screen(M * tone, 75, 3.0)); return M


def cables(P, d, a, b, n, spread=40, w=3):
    for _ in range(n):
        m = ((a[0] + b[0]) / 2 + P.rng.uniform(-spread, spread), max(a[1], b[1]) + P.rng.uniform(20, 160))
        line(d, bez(P.p(*a), P.p(*m), P.p(b[0] + P.rng.uniform(-8, 8), b[1] + P.rng.uniform(-8, 8)), 50), w * P.S)


def board(P, d, x, y, w, h, pins=True):
    d.rectangle([*P.p(x, y), *P.p(x + w, y + h)], outline=255, width=int(3 * P.S))
    if pins:
        for i in range(int(w / 12) - 1): d.rectangle([*P.p(x + 8 + i * 12, y + 6), *P.p(x + 13 + i * 12, y + 11)], fill=255)
    for _ in range(4):
        cw, ch = P.rng.uniform(.15, .35) * w, P.rng.uniform(.2, .4) * h; cx_, cy_ = x + P.rng.uniform(.1, .9 - cw / w) * w, y + P.rng.uniform(.3, .9 - ch / h) * h
        d.rectangle([*P.p(cx_, cy_), *P.p(cx_ + cw, cy_ + ch)], fill=255)


def screw(P, d, x, y, r=7):
    ring(d, P.p(x, y), r * P.S, 2 * P.S); a = P.rng.uniform(0, math.pi)
    line(d, [P.p(x - math.cos(a) * r * .7, y - math.sin(a) * r * .7), P.p(x + math.cos(a) * r * .7, y + math.sin(a) * r * .7)], 2 * P.S)


def cyberdeck(P):
    S = P.S; X, Y = P.X, P.Y
    fig = ascii_figure(P, body(P, 60, -20))
    # cut into strips, each pushed sideways and inked alternately: taped back together, not quite matching
    cuts = sorted(P.rng.sample(range(380, 1240), 6)); edges = [0] + cuts + [DH]; out_b = np.zeros_like(fig); out_r = np.zeros_like(fig)
    for i, (a, b) in enumerate(zip(edges, edges[1:])):
        band = ((Y >= a) & (Y < b)).astype(F); sh = int(P.rng.uniform(-46, 46) * S)
        piece = np.roll(fig, sh, 1) * band
        (out_r if i % 3 == 1 else out_b)[:] += piece
    P.ink('black', np.clip(out_b, 0, 1)); P.ink('red', np.clip(out_r, 0, 1))
    for y in cuts: tape(P, P.rng.uniform(560, 760), y, P.rng.uniform(150, 260), 34, P.rng.uniform(-.12, .12))
    # the deck: a compact case opened, mirror lid turned screen, a keyboard where the powder was
    m, d = P.layer(); lx, ly = 70, 520
    d.rounded_rectangle([*P.p(lx, ly), *P.p(lx + 260, ly + 210)], 26 * S, outline=255, width=int(4 * S))
    d.rounded_rectangle([*P.p(lx, ly + 222), *P.p(lx + 260, ly + 380)], 26 * S, outline=255, width=int(4 * S))
    d.ellipse([*P.p(lx + 110, ly + 205), *P.p(lx + 150, ly + 235)], outline=255, width=int(3 * S))
    for r_ in range(5):
        for c_ in range(11): d.rectangle([*P.p(lx + 22 + c_ * 20, ly + 250 + r_ * 18), *P.p(lx + 36 + c_ * 20, ly + 262 + r_ * 18)], outline=255, width=int(2 * S))
    board(P, d, 90, 1000, 210, 120); board(P, d, 760, 70, 170, 96)
    cables(P, d, (lx + 250, ly + 300), (520, 470), 6, 60, 3)
    cables(P, d, (lx + 130, ly + 380), (195, 1000), 4, 40, 3)
    cables(P, d, (845, 166), (600, 430), 3, 40, 2)
    for _ in range(14): screw(P, d, P.rng.uniform(60, 980), P.rng.uniform(1140, 1250), P.rng.uniform(5, 9))
    M = P.cov(m); P.knock('red', M); P.ink('black', M)
    sc = P.edge_tone(sd_box(P, lx + 130, ly + 105, 110, 85), 1.2); P.clear(sc)
    P.ink('red', sc * P.screen(np.clip(P.value(40) * .9, 0, 1), 75, 3.2))
    P.knock('red', sc * (((X - lx) // 8 + (Y - ly) // 8) % 5 == 0))
    ds, dsd = P.layer(); datasheet(P, dsd, 760, 1000, 220, 900, 22, 6); P.ink('black', P.cov(ds))


def innesto(P):
    S = P.S; X, Y = P.X, P.Y; seam = 520 + (P.fbm(20, 3) - .5) * 40
    left = (X < seam).astype(F)
    fig = ascii_figure(P, body(P)); P.ink('black', fig * left)
    bm = mask_of(P, body(P, 0, -26)); soft = np.asarray(Image.fromarray((bm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10 * S)), F) / 255
    iso = P.isolines(soft + (P.fbm(6, 3) - .5) * .12, list(np.linspace(.08, .95, 16)), .7) * (1 - left)
    P.ink('red', iso); P.ink('red', P.screen(soft * .35, 75, 4.0) * (1 - left))
    tear = (np.abs(X - seam) < 3).astype(F) * (Y > 300); P.clear(tear)
    # the console: the old screen, but showing another world's floor; the keyboard kept
    cr, crd = P.layer(); mx = 80
    line(crd, P.pts([(mx, 360), (mx + 120, 340), (mx + 140, 340), (mx + 140, 860), (mx + 120, 860), (mx, 830), (mx, 360)]), 4 * S)
    crd.rectangle([*P.p(mx - 30, 860), *P.p(mx + 180, 890)], outline=255, width=4 * S)
    line(crd, P.pts([(mx + 40, 890), (mx + 20, 1010), (mx + 160, 1010), (mx + 130, 890)]), 4 * S)
    kx, ky = 150, 1030
    line(crd, P.pts([(kx, ky), (kx + 260, ky - 20), (kx + 300, ky + 50), (kx + 30, ky + 80), (kx, ky)]), 4 * S)
    P.ink('black', P.cov(cr))
    scr_m = np.zeros((P.H, P.W), F); sm, smd = P.layer(); smd.polygon(P.pts([(mx + 4, 364), (mx + 118, 346), (mx + 118, 852), (mx + 4, 826)]), fill=255); scr_m = P.cov(sm)
    gx = ((((X - mx) * 1.0 + (Y - 600) * .0) % 18) < 2) | (((Y - 600) * (1 + (Y - 360) / 600)) % 22 < 2)
    P.ink('black', scr(P, .15) * scr_m); P.ink('black', gx.astype(F) * scr_m)
    # grafting threads: stitches across the seam, like a wound sewn shut
    st, std = P.layer()
    for y in range(420, 1240, 26):
        xx = float(seam[int(y * S), int(512 * S)]) if seam.ndim else 520
        line(std, P.pts([(xx - 14, y), (xx + 14, y + 10)]), 2 * S)
    P.ink('black', P.cov(st))
    ds, dsd = P.layer(); datasheet(P, dsd, 760, 1000, 70, 380, 14, 4); P.ink('black', P.cov(ds))


def sciame(P):
    S = P.S; X, Y = P.X, P.Y; rng = P.nr
    bm = mask_of(P, body(P, 40, 0))[::S, ::S]
    ys, xs = np.nonzero(bm > .3); k = 2600; pick = rng.integers(0, len(xs), k)
    tgt = np.stack([xs[pick], ys[pick]], 1).astype(np.float32) + rng.normal(0, 2, (k, 2)).astype(np.float32)
    mx = 80; src = np.stack([rng.uniform(mx + 10, mx + 120, k), rng.uniform(370, 840, k)], 1).astype(np.float32)
    wind = Curl(P, 4, 1.2)
    def go(p, v, t):
        d = np.linalg.norm(tgt - p, axis=1, keepdims=True)
        w = toward(p, tgt) * np.clip(d / 30, .05, 1) * min(1.0, .3 + t / 50) + wind(p) * max(0, .8 - t / 70)
        return w, np.zeros(len(p), bool)
    path = run(src, go, 260, 4.6, inertia=.8, jitter=.12, rng=rng)
    trails(P, path, lambda y: .9, red=rng.random(k) < .12)
    cr, crd = P.layer()
    line(crd, P.pts([(mx, 360), (mx + 120, 340), (mx + 140, 340), (mx + 140, 860), (mx + 120, 860), (mx, 830), (mx, 360)]), 4 * S)
    crd.rectangle([*P.p(mx - 30, 860), *P.p(mx + 180, 890)], outline=255, width=4 * S)
    line(crd, P.pts([(mx + 40, 890), (mx + 20, 1010), (mx + 160, 1010), (mx + 130, 890)]), 4 * S)
    P.ink('black', P.cov(cr))
    col = P.edge_tone(sd_box(P, 150, 600, 56, 250), 30, torn=10); P.ink('red', P.screen(col * .5, 75, 5.2))


def banco(P):
    S = P.S; X, Y = P.X, P.Y; rng = P.rng
    P.ink('black', scr(P, .08)); P.ink('black', P.isolines((X * .02 + Y * .3 + P.fbm(4, 3) * 30).astype(F), list(range(0, 420, 9)), .4) * scr(P, .4, 75, 2))
    # the field where the thing is being made: red, with a few chosen pieces already laid in it
    fx, fy, fw, fh = 330, 420, 360, 300
    fld = P.edge_tone(sd_box(P, fx + fw / 2, fy + fh / 2, fw / 2, fh / 2), 1.5, torn=2); P.clear(fld); P.ink('red', P.screen(fld * .55, 75, 3.6))
    m, d = P.layer(); placed = []
    for _ in range(46):
        for _t in range(60):
            x, y = rng.uniform(40, DW - 140), rng.uniform(60, DH - 360)
            if not (fx - 120 < x < fx + fw + 20 and fy - 100 < y < fy + fh + 20) and all(abs(x - a) > 90 or abs(y - b) > 70 for a, b, _ in placed): break
        kind = rng.choice(['board', 'case', 'coil', 'screen', 'screw', 'screw', 'lens', 'strip'])
        if kind == 'board': board(P, d, x, y, rng.uniform(60, 120), rng.uniform(40, 70))
        elif kind == 'case': d.rounded_rectangle([*P.p(x, y), *P.p(x + 90, y + 60)], 14 * S, outline=255, width=int(3 * S)); d.ellipse([*P.p(x + 30, y + 15), *P.p(x + 60, y + 45)], outline=255, width=int(2 * S))
        elif kind == 'coil':
            t = np.linspace(0, 6 * math.pi, 200); line(d, [P.p(x + 40 + math.cos(a) * (8 + a * 2.5), y + 30 + math.sin(a) * (6 + a * 2)) for a in t], 2 * S)
        elif kind == 'screen': d.rectangle([*P.p(x, y), *P.p(x + 80, y + 56)], fill=255)
        elif kind == 'screw':
            for _k in range(rng.randint(3, 8)): screw(P, d, x + rng.uniform(0, 60), y + rng.uniform(0, 40), rng.uniform(4, 8))
        elif kind == 'lens': ring(d, P.p(x + 30, y + 30), 28 * S, 3 * S); ring(d, P.p(x + 30, y + 30), 14 * S, 2 * S)
        else:
            for i in range(6): d.rectangle([*P.p(x, y + i * 9), *P.p(x + rng.uniform(30, 90), y + i * 9 + 4)], fill=255)
        placed.append((x, y, kind))
    chosen = rng.sample(placed, 7)
    for i, (x, y, kind) in enumerate(chosen):
        tx, ty = fx + 40 + (i % 3) * 110, fy + 40 + (i // 3) * 90
        board(P, d, tx, ty, 70, 44, False) if kind in ('board', 'screen') else d.rounded_rectangle([*P.p(tx, ty), *P.p(tx + 70, ty + 44)], 10 * S, outline=255, width=int(3 * S))
    M = P.cov(m); P.clear(M * (1 - fld)); P.ink('black', M)
    ln, lnd = P.layer()
    for i, (x, y, kind) in enumerate(chosen):
        tx, ty = fx + 75 + (i % 3) * 110, fy + 62 + (i // 3) * 90; ym = min(y, ty) - rng.uniform(30, 80)
        line(lnd, P.pts([(x + 30, y), (x + 30, ym), (tx, ym), (tx, ty)]), 2 * S); ring(lnd, P.p(x + 30, y), 7 * S, 2 * S); disc(lnd, P.p(tx, ty), 5 * S)
    L = P.cov(ln); P.knock('black', L); P.ink('red', L)
    # two arms in from the bottom, in typed marks, the hands over the field
    def arms(dd):
        dd.polygon(P.pts([(160, DH + 20), (300, DH + 20), (470, 760), (410, 720)]), fill=170); dd.ellipse([*P.p(380, 680), *P.p(480, 780)], fill=230)
        dd.polygon(P.pts([(700, DH + 20), (860, DH + 20), (640, 760), (590, 730)]), fill=150); dd.ellipse([*P.p(560, 690), *P.p(660, 790)], fill=210)
    fig = ascii_figure(P, arms, 14); P.knock('red', fig * fld); P.ink('black', fig)


def innesto_operator(P):
    """The first operator's vibe (red column, mosaic screen, scribbled beam, datasheet) with the graft's two processes.
    No halo, no wing: behind the head, where the wing was, a bundle of cables and a second sheet of leads."""
    S = P.S; X, Y = P.X, P.Y
    col = P.edge_tone(sd_box(P, 600, 640, 120, 700), 24, torn=12); P.ink('red', P.screen(col, 75, 5.2)); incol = col > .5
    seam = 505 + (P.fbm(20, 3) - .5) * 30; left = X < seam
    fig = ascii_figure(P, body(P))
    P.knock('red', fig * incol * left); P.ink('black', fig * ~incol * left)
    bm = mask_of(P, body(P, 6, -22)); blur = lambda r: np.asarray(Image.fromarray((bm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r * S)), F) / 255
    deep = blur(34) * (blur(3) > .5)
    iso = P.isolines(deep + (P.fbm(6, 3) - .5) * .06, list(np.linspace(.04, .98, 26)), .6) * ~left
    P.knock('red', iso * incol); P.ink('red', iso * ~incol)
    P.ink('black', P.screen(deep * .45, 15, 3.0) * ~left * ~incol)
    st, std = P.layer()
    for y in range(400, 1260, 24):
        xx = float(seam[int(y * S), int(505 * S)]); line(std, P.pts([(xx - 12, y), (xx + 12, y + 9)]), 2 * S)
    St_ = P.cov(st); P.knock('red', St_); P.ink('black', St_)
    # where the wing was: cables out of the back of the head, into a sheet of leads
    cb, cbd = P.layer()
    for _ in range(16):
        a = (P.rng.uniform(600, 640), P.rng.uniform(440, 560)); b_ = (P.rng.uniform(800, 990), P.rng.uniform(250, 720))
        m = (P.rng.uniform(680, 900), P.rng.uniform(300, 700)); line(cbd, bez(P.p(*a), P.p(*m), P.p(*b_), 60), P.rng.choice([2, 2, 3, 5]) * S)
        disc(cbd, P.p(*b_), 4 * S)
    datasheet(P, cbd, 760, 1000, 70, 1220, 30, 8)
    CB = P.cov(cb); P.knock('red', CB * incol); P.ink('black', CB)
    # the console as it was: screen in red with its mosaic knocked out, keyboard, the beam to the head
    cr, crd = P.layer(); mx = 80
    line(crd, P.pts([(mx, 360), (mx + 120, 340), (mx + 140, 340), (mx + 140, 860), (mx + 120, 860), (mx, 830), (mx, 360)]), 4 * S)
    crd.rectangle([*P.p(mx - 30, 860), *P.p(mx + 180, 890)], outline=255, width=4 * S)
    line(crd, P.pts([(mx + 40, 890), (mx + 20, 1010), (mx + 160, 1010), (mx + 130, 890)]), 4 * S)
    kx, ky = 150, 1030
    line(crd, P.pts([(kx, ky), (kx + 260, ky - 20), (kx + 300, ky + 50), (kx + 30, ky + 80), (kx, ky)]), 4 * S)
    for r_ in range(4):
        for c_ in range(10):
            x = kx + 20 + c_ * 24 + r_ * 6; y = ky + 10 + r_ * 15 - c_ * 1.8; crd.rectangle([*P.p(x, y), *P.p(x + 16, y + 9)], outline=255, width=2 * S)
    P.ink('black', P.cov(cr))
    sc, scd = P.layer(); scd.polygon(P.pts([(mx + 4, 364), (mx + 118, 346), (mx + 118, 852), (mx + 4, 826)]), fill=255); P.ink('red', P.cov(sc))
    mz, mzd = P.layer()
    for i in range(9):
        for j in range(30):
            if P.rng.random() < .45:
                x = mx + 14 + i * 10; y = 372 + j * 15 - i * 1.5; mzd.rectangle([*P.p(x, y), *P.p(x + 8, y + 12)], fill=255)
    P.knock('red', P.cov(mz))
    bmm, bmd = P.layer()
    for _ in range(380):
        y = P.rng.gauss(520, 50); x0 = mx + 140 + P.rng.uniform(0, 30)
        bmd.line([P.p(x0, y), P.p(P.rng.uniform(300, 445), y + P.rng.uniform(-28, 28))], fill=255, width=P.rng.choice([2, 2, 3, 5]) * S)
    for _ in range(60):
        x = P.rng.uniform(240, 440); y = P.rng.gauss(520, 46); bmd.rectangle([*P.p(x, y), *P.p(x + P.rng.uniform(6, 30), y + P.rng.uniform(3, 10))], fill=255)
    B = P.cov(bmm); P.ink('red', B * ~incol); P.ink('black', B * incol)


PLATES = {'s1': ('s1-supersurface-flux', supersurface_flux), 'o1': ('o1-cyberdeck', cyberdeck), 'o2': ('o2-innesto', innesto),
          'o3': ('o3-sciame', sciame), 'o4': ('o4-banco', banco), 'o5': ('o5-operator-innesto', innesto_operator)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--only', default=','.join(PLATES)); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--scale', type=int, default=1); ap.add_argument('--suffix', default='')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for k in a.only.split(','):
        stem, fn = PLATES[k]; t0 = time.time()
        P = Press(a.seed * 1000 + 120 + list(PLATES).index(k), a.scale); P.nr = np.random.default_rng(P.seed)
        fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
        img.save(os.path.join(a.out, stem + a.suffix + '.png')); print(stem + a.suffix, f'{time.time() - t0:.1f}s', flush=True)


if __name__ == '__main__':
    main()
