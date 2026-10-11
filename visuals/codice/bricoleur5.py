"""THE AGENTIC BRICOLEUR — guild plates, after the Are.na channel "Guild Socialism" (Laura Mas).
Same press as bricoleur3. The bricoleur as a guild craftsman: ornament grown by rule, work clothes cut
from geometry, a continuous grid to live on, a window leaded together from scraps.

  g1 guild-arms      a Socialist League banner: wings, a laurel, the crossed tools of the game guild
  g2 prozodezhda     Stepanova's work clothes for agents: chevrons, stars and tetrominoes cut into cloth
  g3 supersurface    Superstudio's endless grid, people and arcade cabinets camped on it
  g4 the-vine        a Morris panel: a mirrored vine of heart-leaves growing out of a game controller
  g5 rose-window     a glaziers' guild window, every pane from a different print process

Usage: python3 bricoleur5.py OUT [--seeds 1,2,3] [--only g1,g2] [--scale 2] [--sheet]
"""
import argparse, json, math, os, time
import numpy as np
from PIL import Image
from bricoleur3 import (Press, SPR, DW, DH, F, sd_circle, sd_box, sd_below, poisson, bez, line, arrow, ring, disc,
                        dashed, sprite, sprite_wh, wing, agent_graph)
from bricoleur4 import chaikin

# ------------------------------------------------------------ ornament


def leaf(d, P, base, ang, L, w, vein=None):
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca; side = []
    for s in (1, -1):
        for t in (np.linspace(0, 1, 18) if s > 0 else np.linspace(1, 0, 18)):
            b = math.sin(math.pi * t) ** .8 * w * (1 - .35 * t)
            side.append((base[0] + ca * L * t + s * nx * b, base[1] + sa * L * t + s * ny * b))
    d.polygon(P.pts(side), fill=255)
    if vein is not None:
        vein.line(P.pts([base, (base[0] + ca * L * .82, base[1] + sa * L * .82)]), fill=255, width=max(2, int(1.6 * P.S)))


def vine(P, sd, ld, vd, x, y, ang, L, depth, curl, w=6.0, leaf_k=1.0):
    """A Morris stem: a curve that tightens into a spiral, leaves alternating, smaller stems off it."""
    pts = [(x, y)]; a = ang; n = max(8, int(L / 5))
    for i in range(n):
        t = i / n; a += curl * (.15 + 2.2 * t ** 3) * 5 / 60
        x += 5 * math.cos(a); y += 5 * math.sin(a); pts.append((x, y))
    for i in range(len(pts) - 1):
        t = i / len(pts)
        sd.line(P.pts([pts[i], pts[i + 1]]), fill=255, width=max(2, int(w * (1 - .7 * t) * P.S)))
    tang = lambda j: math.atan2(pts[j + 1][1] - pts[j][1], pts[j + 1][0] - pts[j][0])
    for k, j in enumerate(range(4, int(n * .72), max(4, n // 7))):
        s = 1 if k % 2 else -1
        leaf(ld, P, pts[j], tang(j) + s * .95, L * .2 * leaf_k * (1 - j / n * .4), L * .075 * leaf_k, vd)
    if depth > 0:
        for f, s in ((.3, 1), (.55, -1)):
            j = int(n * f); vine(P, sd, ld, vd, *pts[j], tang(j) + s * .85, L * .5, depth - 1, -curl * 1.1, w * .7, leaf_k)
    return pts


def mirror(c):
    return np.maximum(c, c[:, ::-1])


def star(cx, cy, r, k=.45, n=5, rot=-math.pi / 2):
    return [(cx + (r if i % 2 == 0 else r * k) * math.cos(rot + i * math.pi / n), cy + (r if i % 2 == 0 else r * k) * math.sin(rot + i * math.pi / n)) for i in range(2 * n)]

# ------------------------------------------------------------ plates


def plate_arms(P):
    """The banner of a guild that makes games: wings, laurel, crossed sword and key, a blank ribbon."""
    S = P.S; cx, cy = 512, 560
    P.ink('red', P.screen(P.edge_tone(sd_box(P, 512, 560, 440, 330), 16, torn=7), 75, 5.2))
    fr, frd = P.layer()
    for o, w in ((0, 6), (16, 2)):
        frd.rectangle([*P.p(72 + o, 230 + o), *P.p(952 - o, 890 - o)], outline=255, width=int(w * S / 2 * 2))
    # a border of small hearts, the guild's running ornament
    for x in range(110, 920, 34):
        for y in (250, 856): sprite(frd, 'heart', *P.p(x, y), 2 * S)
    F_ = P.cov(fr); P.knock('red', F_)
    # cartouche: a paper oval carved out of the red, edged twice
    ov = ((P.X - cx) / 180) ** 2 + ((P.Y - cy) / 230) ** 2 < 1
    P.clear(ov.astype(F))
    oe, oed = P.layer(); oed.ellipse([*P.p(cx - 180, cy - 230), *P.p(cx + 180, cy + 230)], outline=255, width=6 * S // 2)
    oed.ellipse([*P.p(cx - 194, cy - 244), *P.p(cx + 194, cy + 244)], outline=255, width=2)
    P.ink('black', P.cov(oe))
    # crossed tools, the arms of the guild: a sword and its mirror, a key across them
    t, td = P.layer(); px = 16; sw, sh = sprite_wh('sword', px * S)
    sprite(td, 'sword', P.p(cx)[0] - sw // 2, P.p(0, cy - 20)[1] - sh // 2, px * S)
    T = P.cov(t); T = np.maximum(T, T[:, ::-1])
    k_, kd = P.layer(); kw, kh = sprite_wh('key', 9 * S); sprite(kd, 'key', P.p(cx)[0] - kw // 2, P.p(0, cy + 120)[1], 9 * S)
    P.ink('black', P.crayon(np.maximum(T, P.cov(k_)), .35, .06))
    # laurel: two mirrored stems of leaves hugging the oval
    sd, sdd = P.layer(); ld, ldd = P.layer(); vd, vdd = P.layer()
    pts = [(cx - 120 * math.sin(a), cy + 190 * math.cos(a)) for a in np.linspace(.15, 2.4, 40)]
    sdd.line(P.pts(pts), fill=255, width=4 * S // 2)
    for k, i in enumerate(range(2, 38, 3)):
        a = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
        leaf(ldd, P, pts[i], a + (.7 if k % 2 else -.7), 46, 14, vdd)
    stem = mirror(P.cov(sd)); leaves = mirror(P.cov(ld)); veins = mirror(P.cov(vd))
    P.ink('black', stem); P.ink('red', leaves); P.knock('red', veins)
    # wings out of the cartouche, the angel of the old banner
    wg, wgd = P.layer(); wing(P, wgd, (cx + 186, cy - 40), (760, 380), (880, 360), 1, .36)
    W_ = mirror(P.cov(wg)); red = P.plate['red'] > .5; P.ink('black', W_ * ~red); P.knock('red', W_ * red)
    # ribbon: a blank scroll under the banner — nothing is written on it
    rb, rbd = P.layer()
    top = chaikin([(150, 990), (330, 960), (512, 985), (694, 960), (874, 990)], 3, False); bot = [(x, y + 62) for x, y in top]
    rbd.polygon(P.pts(top + bot[::-1]), outline=255, width=4 * S // 2)
    for x, d_ in ((150, -1), (874, 1)):
        rbd.polygon(P.pts([(x, 1000), (x + d_ * 70, 1000), (x + d_ * 40, 1032), (x + d_ * 70, 1070), (x, 1062)]), outline=255, width=4 * S // 2)
    P.ink('black', P.cov(rb))
    tail, tld = P.layer()
    for x, d_ in ((150, -1), (874, 1)): tld.polygon(P.pts([(x, 1000), (x + d_ * 70, 1000), (x + d_ * 40, 1032), (x + d_ * 70, 1070), (x, 1062)]), fill=255)
    P.ink('red', P.screen(np.full((P.H, P.W), .55, F), 75, 4.4) * P.cov(tail))


def garment(kind, cx, cy, k=1.0):
    shapes = {
        'tunic': [(-60, -200), (60, -200), (150, -150), (200, -20), (150, 0), (110, -80), (110, 200), (-110, 200), (-110, -80), (-150, 0), (-200, -20), (-150, -150)],
        'trousers': [(-110, -200), (110, -200), (135, 200), (30, 200), (0, -30), (-30, 200), (-135, 200)],
        'dress': [(-50, -200), (50, -200), (110, -140), (165, -40), (125, -20), (90, -90), (175, 200), (-175, 200), (-90, -90), (-125, -20), (-165, -40), (-110, -140)],
        'overall': [(-70, -200), (70, -200), (140, -150), (180, -40), (140, -25), (105, -80), (120, 200), (20, 200), (0, 40), (-20, 200), (-120, 200), (-105, -80), (-140, -25), (-180, -40), (-140, -150)],
    }
    return [(cx + x * k, cy + y * k) for x, y in shapes[kind]]


def plate_prozodezhda(P):
    """Work clothes for the agents' guild, cut like Stepanova's: flat, geometric, two inks."""
    S = P.S
    slots = [('tunic', 270, 330), ('trousers', 754, 330), ('dress', 270, 900), ('overall', 754, 900)]
    for n, (kind, cx, cy) in enumerate(slots):
        g, gd = P.layer(); poly = garment(kind, cx, cy, 1.12); gd.polygon(P.pts(poly), fill=255); G = P.cov(g)
        X, Y = P.X - cx, P.Y - cy
        if n == 0:                                    # chevrons down the body, a red star on the chest
            chev = ((np.abs(X) * .9 + Y) % 70 < 32).astype(F) * (Y > -40)
            P.ink('black', chev * G)
            s, sd_ = P.layer(); sd_.polygon(P.pts(star(cx, cy - 120, 62)), fill=255); P.ink('red', P.cov(s) * G)
            P.ink('red', (Y < -150).astype(F) * G)
        elif n == 1:                                  # split legs: one solid red, one striped black
            P.ink('red', ((X < 0) & (Y > -150)).astype(F) * G)
            P.ink('black', (((Y % 46) < 20) & (X >= 0) & (Y > -150)).astype(F) * G)
            P.ink('black', (Y <= -150).astype(F) * G)
            sp, spd = P.layer(); sprite(spd, 'alien', *P.p(cx - 90, cy - 10), 7 * S); P.knock('red', P.cov(sp) * G)
        elif n == 2:                                  # the skirt is stacked tetrominoes, the bodice a target
            tt, ttd = P.layer(); u = 26
            for r_ in range(9):
                for c_ in range(-8, 8):
                    nm = 'TSLOI'[(r_ * 3 + c_) % 5]
                    if (r_ + c_) % 2 == 0: sprite(ttd, nm, *P.p(cx + c_ * u * 1.7, cy - 30 + r_ * u * 1.05), u * S // 2)
            P.ink('red', P.cov(tt) * G * (Y > -60))
            P.ink('black', ((np.hypot(X, Y + 130) % 34) < 12).astype(F) * G * (Y <= -60))
        else:                                         # diagonal split, the hammer replaced by a joystick
            P.ink('black', ((X + Y * .6) < 0).astype(F) * G)
            P.ink('red', P.screen(np.clip(.25 + (X + Y * .6) / 260, 0, 1), 75, 4.6) * ((X + Y * .6) >= 0) * G)
            j, jd = P.layer(); jd.ellipse([*P.p(cx + 30, cy - 160), *P.p(cx + 90, cy - 100)], fill=255)
            jd.rectangle([*P.p(cx + 52, cy - 104), *P.p(cx + 68, cy - 30)], fill=255); jd.rounded_rectangle([*P.p(cx + 10, cy - 34), *P.p(cx + 112, cy - 4)], 8 * S, fill=255)
            J = P.cov(j) * G; P.clear(J); P.ink('black', J * ((X + Y * .6) >= 0))          # black on the red half, bare paper on the black
        o, od = P.layer(); line(od, P.pts(poly + [poly[0]]), 4); P.ink('black', P.cov(o))
    # the cutting table: pattern pieces' notches and grain lines, as a tailor marks them
    m, md = P.layer()
    for kind, cx, cy in slots:
        dashed(md, P.p(cx, cy - 250), P.p(cx, cy + 250), 2, 8 * S, 6 * S)
        arrow(md, P.p(cx, cy + 236), P.p(cx, cy + 250), 2, 8 * S)
    line(md, P.pts([(40, 615), (984, 615)]), 2)
    P.ink('black', P.cov(m) * (1 - (P.plate['red'] > .5)) * (1 - (P.plate['black'] > .5)))


def plate_supersurface(P):
    """Superstudio's continuous grid, now the platform: people and machines camped on it, a red sky over."""
    S = P.S; vx, hy, f, cam = 512, 520, 520, 1.6
    P.ink('red', P.screen(np.clip(1 - (hy - P.Y) / 420, 0, 1) * (P.Y < hy), 75, 5.4))
    hills = P.fbm(5, 5)[int(P.H * .3)]                       # one row of noise as a skyline
    hy_px = hy * S; prof = hy_px - (np.clip(hills - .35, 0, 1) * 160 + 6) * S
    mtn = (P.Y * S >= prof[None, :]) & (P.Y < hy)
    P.knock('red', mtn.astype(F)); P.ink('black', P.screen(np.clip((P.Y * S - prof[None, :]) / (80 * S), .15, .8), 15, 3.6) * mtn)
    g, gd = P.layer()
    for xw in range(-30, 31):
        z0, z1 = .9, 60
        gd.line([P.p(vx + xw * f / z0, hy + cam * f / z0), P.p(vx + xw * f / z1, hy + cam * f / z1)], fill=255, width=3)
    z = 1.0
    while z < 60:
        y = hy + cam * f / z
        if y < DH + 5: gd.line([P.p(-50, y), P.p(DW + 50, y)], fill=255, width=3)
        z *= 1.16
    P.ink('black', P.cov(g) * (P.Y > hy))
    # what is camped on the grid, far to near
    things = []
    for _ in range(22):
        xw = P.rng.uniform(-5, 5); zz = P.rng.uniform(1.6, 11); things.append((zz, xw, P.rng.choice(['hero', 'hero', 'hero', 'cab', 'tree', 'tree', 'alien'])))
    things.sort(key=lambda t: -t[0])
    for zz, xw, kind in things:
        sx, sy = vx + xw * f / zz, hy + cam * f / zz; u = 260 / zz          # u: a person's height at this depth
        if not (20 < sx < DW - 20) or u < 6: continue
        sh, shd = P.layer(); shd.ellipse([*P.p(sx - .45 * u, sy - .09 * u), *P.p(sx + .9 * u, sy + .1 * u)], fill=255)
        P.clear(P.cov(sh)); P.ink('red', P.screen(np.full((P.H, P.W), .6, F), 75, 3.8) * P.cov(sh))
        o, od = P.layer()
        if kind == 'tree':
            for _ in range(6):
                r = P.rng.uniform(.3, .55) * u; ox = P.rng.uniform(-.4, .4) * u; oy = P.rng.uniform(-1.2, -.5) * u
                od.ellipse([*P.p(sx + ox - r, sy + oy - r), *P.p(sx + ox + r, sy + oy + r)], fill=255)
            od.rectangle([*P.p(sx - .05 * u, sy - .6 * u), *P.p(sx + .05 * u, sy)], fill=255)
            M = P.cov(o); P.clear(M); P.ink('black', P.crayon(M, .5, .2))
        else:
            px = max(1, int(u * (1.3 if kind == 'cab' else 1.0) / 7 * S)); sw, shh = sprite_wh(kind, px)
            sprite(od, kind, P.p(sx)[0] - sw // 2, P.p(0, sy)[1] - shh, px)
            M = P.cov(o); P.clear(M); P.ink('black', M)

def plate_vine(P):
    """A Morris panel. The vine is mirrored, its leaves are hearts, its pot is a game controller."""
    S = P.S
    fr, frd = P.layer()
    frd.rounded_rectangle([*P.p(70, 60), *P.p(954, 1220)], 60 * S, outline=255, width=6 * S // 2)
    frd.rounded_rectangle([*P.p(90, 80), *P.p(934, 1200)], 46 * S, outline=255, width=2)
    P.ink('black', P.cov(fr))
    bg, bgd = P.layer(); bgd.rounded_rectangle([*P.p(90, 80), *P.p(934, 1200)], 46 * S, fill=255)
    P.ink('red', P.screen(np.full((P.H, P.W), .16, F), 75, 6.0) * P.cov(bg))
    sd, sdd = P.layer(); ld, ldd = P.layer(); vd, vdd = P.layer()
    sdd.line(P.pts([(512, 1000), (512, 300)]), fill=255, width=7 * S)
    vine(P, sdd, ldd, vdd, 512, 960, -math.pi / 2 - .35, 520, 2, -1.15, 7, 1.2)
    vine(P, sdd, ldd, vdd, 512, 760, -math.pi / 2 - .9, 380, 2, -1.3, 5.5, 1.1)
    vine(P, sdd, ldd, vdd, 512, 520, -math.pi / 2 - .5, 300, 1, -1.4, 5, 1.0)
    st, lv, vn = mirror(P.cov(sd)), mirror(P.cov(ld)), mirror(P.cov(vd))
    P.clear(lv); P.ink('red', lv); P.knock('red', vn); P.ink('black', st)
    fl, fld = P.layer()
    for (x, y, px) in [(512, 230, 11), (330, 420, 7), (260, 690, 6), (360, 860, 5)]:
        sw, sh = sprite_wh('heart', px * S); sprite(fld, 'heart', P.p(x)[0] - sw // 2, P.p(0, y)[1] - sh // 2, px * S)
    FL = mirror(P.cov(fl)); P.clear(FL); P.ink('black', P.crayon(FL, .35, .08))
    pot, pd = P.layer()
    pd.rounded_rectangle([*P.p(300, 1000), *P.p(724, 1150)], 70 * S, fill=255)
    pm = P.cov(pot); P.clear(pm); P.ink('black', P.crayon(pm, .35, .05))
    k_, kd = P.layer(); cx, cy = 400, 1075
    kd.rectangle([*P.p(cx - 42, cy - 13), *P.p(cx + 42, cy + 13)], fill=255); kd.rectangle([*P.p(cx - 13, cy - 42), *P.p(cx + 13, cy + 42)], fill=255)
    for bx, by in ((610, 1050), (650, 1095), (570, 1100)): kd.ellipse([*P.p(bx - 18, by - 18), *P.p(bx + 18, by + 18)], fill=255)
    P.clear(P.cov(k_)); P.ink('red', P.cov(k_))


def plate_rose(P):
    """A glaziers' guild window: lead cames of circles and spokes, each pane from a different process."""
    S = P.S; cx, cy, R = 512, 560, 400
    dx, dy = P.X - cx, P.Y - cy; r = np.hypot(dx, dy); th = (np.arctan2(dy, dx) + 2 * np.pi) % (2 * np.pi)
    inside = r < R
    ring_i = np.digitize(r, [R * .16, R * .38, R * .64, R * .86])
    sect = (th / (2 * np.pi / 12)).astype(np.int32)
    petal = np.zeros_like(r, dtype=np.int32)
    for k in range(12):
        a = (k + .5) * 2 * np.pi / 12; px, py = cx + R * .51 * math.cos(a), cy + R * .51 * math.sin(a)
        petal += ((np.hypot(P.X - px, P.Y - py) < R * .2) * (k + 1)).astype(np.int32)
    ids = np.where(ring_i == 0, 0, ring_i * 1000 + sect * 10 + (petal > 0)) + petal * 100000
    ids = np.where(inside, ids, -1)
    pats = {}
    for nm in ('heart', 'alien', 'coin', 'T'):
        t, td = P.layer(); sw, sh = sprite_wh(nm, 3 * S)
        for yy in range(0, P.H, sh + 5 * S):
            for xx in range(0, P.W, sw + 5 * S): sprite(td, nm, xx + (yy // (sh + 5 * S)) % 2 * (sw // 2), yy, 3 * S)
        pats[nm] = P.cov(t)
    hatch = (((P.X + P.Y) % 9) < 2.2).astype(F)
    for u in np.unique(ids):
        if u < 0: continue
        M = (ids == u).astype(F); st = P.rng.choice(['red', 'red', 'rs', 'bs', 'pix', 'rpix', 'paper', 'hatch', 'paper'])
        if u == 0: st = 'center'
        if st == 'red': P.ink('red', M)
        elif st == 'rs': P.ink('red', P.screen(np.clip(r / R * 1.1, .2, 1), 75, 4.6) * M)
        elif st == 'bs': P.ink('black', P.screen(np.full_like(M, .35), 15, 3.6) * M)
        elif st == 'pix': P.ink('black', pats[P.rng.choice(list(pats))] * M)
        elif st == 'rpix': P.ink('red', pats[P.rng.choice(list(pats))] * M)
        elif st == 'hatch': P.ink('black', hatch * M)
    lead, ldd = P.layer(); W_ = 7 * S
    for rr in (R * .16, R * .38, R * .64, R * .86, R): ring(ldd, P.p(cx, cy), rr * S, W_)
    for k in range(12):
        a = k * 2 * np.pi / 12; ldd.line([P.p(cx + R * .16 * math.cos(a), cy + R * .16 * math.sin(a)), P.p(cx + R * math.cos(a), cy + R * math.sin(a))], fill=255, width=W_)
        a2 = (k + .5) * 2 * np.pi / 12; ring(ldd, P.p(cx + R * .51 * math.cos(a2), cy + R * .51 * math.sin(a2)), R * .2 * S, W_)
    ring(ldd, P.p(cx, cy), (R + 22) * S, 3 * S // 2 + 1)
    L = P.cov(lead); P.clear(L); P.ink('black', L)
    # the centre: the guild's sign, an agent graph in the glass
    g, gd = P.layer(); agent_graph(P, gd, cx, cy, R * .15, 7, 3); P.ink('black', P.cov(g) * (r < R * .15))
    # the wall it is set in, and Morris spandrels in the four corners
    sd, sdd = P.layer(); ld, ldd2 = P.layer(); vd, vdd = P.layer()
    vine(P, sdd, ldd2, vdd, 60, 120, .25, 260, 1, 1.3, 5, .9)
    vine(P, sdd, ldd2, vdd, 60, 1180, -.25, 260, 1, -1.3, 5, .9)
    out = (r > R + 30).astype(F)
    st, lv, vn = mirror(P.cov(sd)) * out, mirror(P.cov(ld)) * out, mirror(P.cov(vd)) * out
    P.ink('red', lv); P.knock('red', vn); P.ink('black', st)


PLATES = {'g1': ('g1-guild-arms', plate_arms), 'g2': ('g2-prozodezhda', plate_prozodezhda), 'g3': ('g3-supersurface', plate_supersurface),
          'g4': ('g4-the-vine', plate_vine), 'g5': ('g5-rose-window', plate_rose)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seeds', default='1'); ap.add_argument('--only', default=','.join(PLATES))
    ap.add_argument('--scale', type=int, default=2); ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    seeds = [int(s) for s in a.seeds.split(',')]; keys = a.only.split(','); thumbs = {}
    for k in keys:
        stem, fn = PLATES[k]
        for sd in seeds:
            t0 = time.time(); P = Press(sd * 1000 + 70 + list(PLATES).index(k), a.scale)
            fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
            name = f'{stem}-s{sd}' if len(seeds) > 1 else stem
            img.save(os.path.join(a.out, name + '.png'))
            meta = {'plate': k, 'seed': sd, 'scale': a.scale, 'source': 'are.na/laura-mas/guild-socialism',
                    'coverage': P.stats(), 'seconds': round(time.time() - t0, 1)}
            json.dump(meta, open(os.path.join(a.out, name + '.json'), 'w'), indent=1)
            print(name, json.dumps(meta['coverage']), f"{meta['seconds']}s", flush=True)
            thumbs[(k, sd)] = img.resize((256, 320), Image.LANCZOS)
    if a.sheet:
        g = 12; sheet = Image.new('RGB', (len(seeds) * (256 + g) + g, len(keys) * (320 + g) + g), (40, 38, 36))
        for r, k in enumerate(keys):
            for c, sd in enumerate(seeds): sheet.paste(thumbs[(k, sd)], (g + c * (256 + g), g + r * (320 + g)))
        sheet.save(os.path.join(a.out, 'contact-sheet.png')); print('contact-sheet.png')


if __name__ == '__main__':
    main()
