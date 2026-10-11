"""THE AGENTIC BRICOLEUR — Are.na plates, after the channel "Counterculture Cybernetic Capitalism".
Same press as bricoleur3 (two inks, AM screens, SDF edges). Five new motifs from the channel,
each re-cut for the game-mashup bricoleur:

  a1 access-to-tools   Whole Earth: a screened planet, night side red, and a catalogue of game tools
  a2 drop-city         a geodesic dome patched from scavenged panels — screens, pixels, crayon, bare paper
  a3 lib-dream         the two-sided book: a pixel fist on the red, the same fist upside down in wire
  a4 human-use         Wiener's two heads in feedback: one holds the agents, the other the level
  a5 radical-terrain   a hidden-line data landscape, agents on the peaks wired to a hand-drawn internet

Usage: python3 bricoleur4.py OUT [--seeds 1,2,3] [--only a1,a2] [--scale 2] [--sheet]
"""
import argparse, json, math, os, time
import numpy as np
from PIL import Image
from bricoleur3 import (Press, SPR, DW, DH, F, sd_circle, sd_box, sd_below, poisson, bez, line, arrow, ring, disc,
                        dashed, sprite, sprite_wh, hand_blob, agent_graph, level)

SPR['fist'] = [
    "..XXX.XXX.XXX.XX..",
    ".XXXXXXXXXXXXXXXX.",
    ".X...X...X...X..X.",
    ".XXXXXXXXXXXXXXXX.",
    ".XXXXXXXXXXXXXXXX.",
    "XXXXXXXXXXXXXXXXX.",
    "XX.......XXXXXXXX.",
    "XXXXXXXXXXXXXXXXX.",
    ".XXXXXXXXXXXXXXX..",
    "..XXXXXXXXXXXXX...",
    "...XXXXXXXXXXX....",
    "....XXXXXXXXXX....",
    "....XXXXXXXXXX....",
    "....XXXXXXXXXX....",
    "....XXXXXXXXXX....",
]
SPR['cab'] = ["XXXXX", "X...X", "X...X", "XXXXX", "XX.XX", "XXXXX", "X...X"]
SPR['pc'] = ["XXXXXXX", "X.....X", "X.....X", "XXXXXXX", "..XXX..", "XXXXXXX"]

# ------------------------------------------------------------ geometry


def icosphere(n):
    t = (1 + 5 ** .5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    V = [tuple(np.array(v) / np.linalg.norm(v)) for v in V]
    Fc = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
          (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(n):
        cache, nf = {}, []

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = (np.array(V[a]) + np.array(V[b])) / 2; V.append(tuple(m / np.linalg.norm(m))); cache[k] = len(V) - 1
            return cache[k]
        for a, b, c in Fc:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        Fc = nf
    return np.array(V), Fc


def rot(V, rx, ry):
    cx, sx, cy, sy = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    return V @ Ry.T @ Rx.T


def chaikin(pts, n=3, closed=True):
    for _ in range(n):
        out = []; m = len(pts) if closed else len(pts) - 1
        for i in range(m):
            p, q = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            out += [tuple(.75 * p + .25 * q), tuple(.25 * p + .75 * q)]
        pts = out if closed else [pts[0]] + out + [pts[-1]]
    return pts

# ------------------------------------------------------------ plates


def plate_access(P):
    """Whole Earth, re-tooled: the planet is screened, the night side is red, the land is what the red lets through."""
    S = P.S; cx, cy, R = 512, 470, 300
    dx, dy = (P.X - cx) / R, (P.Y - cy) / R; r2 = dx * dx + dy * dy; on = r2 < 1
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    L = np.array([-.55, -.55, .63]); L /= np.linalg.norm(L)
    lam = np.clip(dx * L[0] + dy * L[1] + nz * L[2], 0, 1)
    # land: noise sampled in longitude/latitude, so it wraps the ball instead of sitting on the disc
    lon = np.arctan2(dx, nz + 1e-6) + .4; lat = np.arcsin(np.clip(-dy, -1, 1))
    tex = P.fbm(8, 5); ty = ((lat / np.pi + .5) * (P.H - 1)).astype(np.int32); tx = (((lon / (2 * np.pi)) % 1) * (P.W - 1)).astype(np.int32)
    land = (tex[ty, tx] > .55) & on
    night = np.clip(1.15 - 1.5 * lam, 0, 1)
    P.ink('red', P.screen(night, 75, 5.0) * on)
    P.knock('red', land * (night > .55))
    P.ink('black', P.screen(.55 * (lam > .25), 15, 3.6) * land * (night <= .55))
    rim, rd = P.layer(); ring(rd, P.p(cx, cy), R * S, 4); P.ink('black', P.cov(rim))
    # geodesic frame over the night side only: the structure shows where the light doesn't
    V, Fc = icosphere(2); V = rot(V, .3, .5); g, gd = P.layer()
    for a, b, c in Fc:
        for i, j in ((a, b), (b, c), (c, a)):
            if V[i][2] > 0 and V[j][2] > 0:
                gd.line([P.p(cx + R * V[i][0], cy - R * V[i][1]), P.p(cx + R * V[j][0], cy - R * V[j][1])], fill=255, width=2)
    night_m = (night > .45) & on
    P.knock('red', P.cov(g) * night_m); P.ink('black', P.cov(g) * (~night_m) * (r2 < 1) * (night > .2))
    # orbit: the loop again, around the planet
    o, od = P.layer(); od.ellipse([*P.p(cx - 420, cy - 70), *P.p(cx + 420, cy + 70)], outline=255, width=4 * S // 2)
    P.ink('red', P.cov(o) * ~on * (P.Y < cy)); P.ink('black', P.cov(o) * ((P.Y >= cy) | ~on) * (P.Y >= cy))
    sat, sd_ = P.layer(); sprite(sd_, 'ship', *P.p(cx + 390, cy - 40), 4 * S); P.ink('black', P.cov(sat))
    # the catalogue: a grid of tools, every one from a different game
    tools = ['sword', 'key', 'coin', 'chest', 'heart', 'cab', 'pc', 'alien', 'hero', 'T', 'L', 'ship']
    cat, cd = P.layer(); fills, fd = P.layer(); cols, x0, y0, cw, ch = 6, 56, 900, 152, 170
    for k, nm in enumerate(tools):
        i, j = k % cols, k // cols; x, y = x0 + i * cw, y0 + j * ch
        cd.rectangle([*P.p(x, y), *P.p(x + cw - 14, y + ch - 14)], outline=255, width=3)
        cd.rectangle([*P.p(x + 10, y + ch - 40), *P.p(x + 10 + P.rng.uniform(30, 90), y + ch - 34)], fill=255)
        gw, gh = len(SPR[nm][0]), len(SPR[nm]); px = int(min(90 / gw, 80 / gh) * S); sw, sh = sprite_wh(nm, px)
        tgt = fd if (i + j) % 3 == 0 else cd
        sprite(tgt, nm, P.p(x + (cw - 14) / 2)[0] - sw // 2, P.p(0, y + 60)[1] - sh // 2, px)
        if (i * 5 + j) % 4 == 1: fd.rectangle([*P.p(x + 4, y + 4), *P.p(x + cw - 18, y + ch - 18)], outline=255, width=8 * S)
    P.ink('black', P.cov(cat)); P.ink('red', P.cov(fills))


def plate_dome(P):
    """Drop City: a dome patched from what was lying around. Every panel a different print process."""
    S = P.S; cx, base, R = 512, 1010, 420
    P.ink('red', P.screen(P.edge_tone(sd_below(P, 0, 1030, .0), 18, torn=8), 75, 5.2))
    P.ink('red', P.screen(np.clip(1.2 - np.hypot(P.X - 760, P.Y - 330) / 230, 0, 1) * (sd_circle(P, 760, 330, 230) < 0), 75, 6.0))
    V, Fc = icosphere(3)
    V[:, 1] = np.maximum(V[:, 1], 0)
    W3 = rot(V, -.32, .2)
    faces = []
    for f in Fc:
        if all(V[i][1] <= 1e-6 for i in f): continue
        p3 = W3[list(f)]; n = np.cross(p3[1] - p3[0], p3[2] - p3[0]); c = p3.mean(0)
        if np.dot(n, c) < 0: n = -n
        if n[2] <= 0: continue
        faces.append((c[2], f, n / np.linalg.norm(n)))
    faces.sort(key=lambda t: t[0])
    ys = [R * W3[i][1] for _, f, _ in faces for i in f]
    yoff = min(ys)
    scr = lambda v: P.p(cx + R * v[0], base + 22 - (R * v[1] - yoff))
    L = np.array([-.5, .6, .62]); L /= np.linalg.norm(L)
    styles = ['red', 'redscreen', 'redscreen', 'blackscreen', 'pixel', 'paper', 'paper', 'crayon', 'redpixel', 'lines']
    pats = ['heart', 'alien', 'coin', 'T', 'hero']
    edges, ed = P.layer()
    for z, f, n in faces:
        poly = [scr(W3[i]) for i in f]
        m, md = P.layer(); md.polygon(poly, fill=255); M = P.cov(m)
        P.clear(M); lam = max(0, float(n @ L)); st = P.rng.choice(styles)
        if st == 'red': P.ink('red', M)
        elif st == 'redscreen': P.ink('red', P.screen(np.full_like(M, 1.05 - lam), 75, 4.6) * M)
        elif st == 'blackscreen': P.ink('black', P.screen(np.full_like(M, .75 - .6 * lam), 15, 3.8) * M)
        elif st == 'crayon': P.ink('black', P.crayon(M, .4, .1))
        elif st in ('pixel', 'redpixel'):
            t, td = P.layer(); nm = P.rng.choice(pats); px = 3 * S; sw, sh = sprite_wh(nm, px)
            xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
            for yy in range(int(min(ys)), int(max(ys)), sh + 4 * S):
                for xx in range(int(min(xs)), int(max(xs)), sw + 4 * S): sprite(td, nm, xx, yy, px)
            P.ink('black' if st == 'pixel' else 'red', P.cov(t) * M)
        elif st == 'lines':
            t, td = P.layer(); xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
            for yy in range(int(min(ys)), int(max(ys)), 7 * S): td.line([(min(xs), yy), (max(xs), yy + (max(xs) - min(xs)) * .3)], fill=255, width=2)
            P.ink('black', P.cov(t) * M)
        ed.line(poly + [poly[0]], fill=255, width=int(2.5 * S), joint='curve')
    P.ink('black', P.cov(edges))
    # the door, and the people who built it
    dr, drd = P.layer(); drd.rectangle([*P.p(cx - 40, base - 120), *P.p(cx + 40, base + 4)], fill=255); P.clear(P.cov(dr))
    dl, dld = P.layer(); dld.rectangle([*P.p(cx - 40, base - 120), *P.p(cx + 40, base + 4)], outline=255, width=4); P.ink('black', P.cov(dl))
    fg, fgd = P.layer()
    for k, x in enumerate([150, 230, 790, 880]):
        sprite(fgd, 'hero', *P.p(x, base + 6), 7 * S)
    sprite(fgd, 'cab', *P.p(cx - 18, base - 90), 7 * S)
    F_ = P.cov(fg); red = P.plate['red'] > .5; P.ink('black', F_ * ~red); P.knock('red', F_ * red)


def plate_lib(P):
    """Computer Lib / Dream Machines: one book, two covers. The fist on the red; turned over, the same fist as wire."""
    S = P.S
    P.ink('red', P.screen(P.edge_tone(sd_box(P, 256, 640, 230, 600), 14, torn=6), 75, 5.2))
    px = 24; gw, gh = sprite_wh('fist', px)
    fx, fy = 256 - gw / 2, 560 - gh / 2
    f, fd = P.layer(); sprite(fd, 'fist', *P.p(fx, fy), px * S)
    stick, sd_ = P.layer()
    sd_.rounded_rectangle([*P.p(fx - 30, fy + gh + 10), *P.p(fx + gw + 30, fy + gh + 90)], 16 * S, fill=255)
    for k in range(3): sd_.ellipse([*P.p(fx + gw - 40 - k * 70, fy + gh + 30), *P.p(fx + gw - k * 70, fy + gh + 70)], fill=0)
    body = np.maximum(P.cov(f), P.cov(stick))
    P.ink('black', P.crayon(body, .4, .12))
    # the other cover: rotated a half turn, drawn as wire, red on paper
    w, wd = P.layer(); gx, gy = 768 - gw / 2, 720 - gh / 2
    rows = SPR['fist'][::-1]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row[::-1]):
            if ch == 'X':
                wd.rectangle([*P.p(gx + i * px, gy + j * px), *P.p(gx + (i + 1) * px - 4, gy + (j + 1) * px - 4)], outline=255, width=3)
    wd.rounded_rectangle([*P.p(gx - 30, gy - 90), *P.p(gx + gw + 30, gy - 10)], 16 * S, outline=255, width=3)
    for k in range(3): wd.ellipse([*P.p(gx + 40 + k * 70 - 20, gy - 70), *P.p(gx + 40 + k * 70 + 20, gy - 30)], outline=255, width=3)
    P.ink('red', P.cov(w))
    sh, shd = P.layer()
    for j in range(len(rows)):
        for i, ch in enumerate(rows[j][::-1]):
            if ch == 'X' and (i + j) % 3 == 0: shd.rectangle([*P.p(gx + i * px + 6, gy + j * px + 6), *P.p(gx + (i + 1) * px - 10, gy + (j + 1) * px - 10)], fill=255)
    P.ink('black', P.screen(np.full((P.H, P.W), .5, F), 15, 3.4) * P.cov(sh))
    # the spine between them, and a cable that crosses it: a terminal on one side, a plug on the other
    sp, spd = P.layer(); line(spd, P.pts([(512, 30), (512, 1250)]), 3); dashed(spd, P.p(522, 30), P.p(522, 1250), 2, 6 * S, 6 * S)
    cab, cbd = P.layer()
    pts = chaikin([(120, 1150), (300, 1210), (470, 1120), (560, 1190), (700, 1060), (860, 1180), (930, 1100)], 4, False)
    line(cbd, P.pts(pts), 4); cbd.rectangle([*P.p(70, 1110), *P.p(140, 1170)], outline=255, width=4); cbd.rectangle([*P.p(84, 1122), *P.p(126, 1150)], fill=255)
    disc(cbd, P.p(930, 1100), 12 * S)
    C = np.maximum(P.cov(sp), P.cov(cab)); red = P.plate['red'] > .5
    P.ink('black', C * ~red); P.knock('red', C * red)


def head(cx, cy, k, face=1):
    prof = [(-40, -172), (20, -168), (70, -148), (102, -112), (112, -62), (118, -36), (112, -18), (150, 16), (120, 30), (128, 48), (116, 58),
            (126, 70), (112, 100), (70, 130), (60, 150), (60, 250), (-50, 250), (-55, 150), (-110, 90), (-135, 10), (-128, -80), (-90, -145)]
    return [(cx + face * x * k, cy + y * k) for x, y in chaikin(prof, 3)]


def plate_human(P):
    """The Human Use of Human Beings: two heads in feedback. The player holds the level; the agent holds the graph."""
    S = P.S
    P.ink('red', P.screen(P.edge_tone(sd_box(P, 512, 600, 440, 470), 22, torn=10), 75, 5.2))
    A = head(262, 590, 1.32, 1); B = head(762, 590, 1.32, -1)
    hm, hmd = P.layer(); hmd.polygon(P.pts(A), fill=255); hmd.polygon(P.pts(B), fill=255); P.clear(P.cov(hm))
    ha, had = P.layer(); had.polygon(P.pts(A), fill=255); hb, hbd = P.layer(); hbd.polygon(P.pts(B), fill=255)
    lv, lvd = P.layer(); level(P, lvd, 150, 640, 15, 3); P.ink('black', P.cov(lv) * P.cov(ha))
    P.ink('red', P.screen(np.clip(1 - np.hypot(P.X - 250, P.Y - 520) / 120, 0, 1), 75, 4.4) * P.cov(ha))
    g, gd = P.layer(); agent_graph(P, gd, 790, 540, 135, 16, 3); P.ink('black', P.cov(g) * P.cov(hb))
    out, od = P.layer(); line(od, P.pts(A + [A[0]]), 5); line(od, P.pts(B + [B[0]]), 5); P.ink('black', P.cov(out))
    # the loop between them: one arrow out in red, one back in black
    a1, a1d = P.layer(); arrow(a1d, P.p(445, 470), P.p(578, 470), 10, 34 * S); P.ink('black', P.cov(a1))
    a2, a2d = P.layer(); arrow(a2d, P.p(578, 540), P.p(445, 540), 10, 34 * S); P.clear(P.cov(a2))                     # the way back is bare paper cut out of the red
    # under it, the hardware both of them sit on
    sp, spd = P.layer()
    for k, nm in enumerate(['cab', 'pc', 'cab', 'pc', 'cab']):
        sprite(spd, nm, *P.p(130 + k * 180, 1160), 9 * S)
    line(spd, P.pts([(100, 1240), (930, 1240)]), 4)
    P.ink('black', P.cov(sp))


def plate_terrain(P):
    """Radical Software's data landscape, hidden-line, with agents on the peaks wired to a hand-drawn internet."""
    S = P.S; cx = 512
    hf = P.warp(P.fbm(3, 5), 40)
    N = 74; hor = np.full(P.W, P.H, F); lines_k, lk = P.layer(); lines_r, lr = P.layer()
    peaks = []
    xs = np.arange(0, P.W, 2 * S)
    for r in range(N):
        z = r / (N - 1)
        y0 = (1230 - 560 * z ** .8) * S; s = 1 - .5 * z
        u = (xs / S - cx) / (520 * s)
        hgt = hf[min(P.H - 1, int((z * .85 + .05) * (P.H - 1))), np.clip(((u * .45 + .5) * (P.W - 1)).astype(np.int32), 0, P.W - 1)]
        mount = np.exp(-((u + .15) ** 2 / .08 + (z - .55) ** 2 / .05)) * 1.3
        y = y0 - (np.clip(hgt - .35, 0, 1) * 520 + mount * 330) * S * (1 - .35 * z)
        vis = y < hor[xs]
        tgt = lr if .38 < z < .5 else lk
        seg = []
        for x, yy, v in zip(xs, y, vis):
            if v: seg.append((x, yy))
            elif len(seg) > 1: tgt.line(seg, fill=255, width=int(1.4 * S)); seg = []
            else: seg = []
        if len(seg) > 1: tgt.line(seg, fill=255, width=int(1.4 * S))
        hor[xs] = np.minimum(hor[xs], y)
        if r % 3 == 0:
            pk = (y[1:-1] < y[:-2]) & (y[1:-1] < y[2:]) & vis[1:-1]
            for i in np.nonzero(pk)[0][::6]: peaks.append((xs[i + 1] / S, y[i + 1] / S))
    P.ink('black', P.cov(lines_k)); P.ink('red', P.cov(lines_r))
    # the sky: a screened red under the ridge line, fading up
    ridge = np.broadcast_to(hor[None, :] / S, (P.H, P.W))
    P.ink('red', P.screen(np.clip((P.Y - (ridge - 260)) / 260, 0, 1) * (P.Y < ridge - 4) * .85, 75, 5.6))
    # the internet, as people drew it in 1990: a cloud, some boxes, lines between them
    net, nd = P.layer(); clouds = [(270, 160, 150, 70), (620, 120, 110, 55), (840, 230, 90, 50)]
    for c in clouds: hand_blob(nd, P.rng, P.p(c[0], c[1]), c[2] * S, c[3] * S, 4)
    line(nd, P.pts([(420, 160), (510, 125)]), 3); line(nd, P.pts([(730, 140), (780, 200)]), 3)
    for x, y in [(90, 70), (420, 60), (930, 110), (120, 300)]:
        sprite(nd, 'pc', *P.p(x, y), 5 * S)
    P.ink('black', P.cov(net))
    # the agents stand on the peaks and hang from the cloud
    ag, agd = P.layer(); wires, wd = P.layer()
    chosen = []
    for q in sorted(peaks, key=lambda q: q[1]):
        if 60 < q[0] < 960 and all(abs(q[0] - c[0]) > 150 for c in chosen): chosen.append(q)
        if len(chosen) == 6: break
    for k, (x, y) in enumerate(chosen):
        nm = ['alien', 'hero', 'cab', 'heart', 'ship', 'hero'][k]; px = 5; sw, sh = sprite_wh(nm, px)
        sprite(agd, nm, *P.p(x - sw / 2, y - sh - 6), px * S)
        c = min(clouds, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
        dashed(wd, P.p(x, y - sh - 10), P.p(c[0] + P.rng.uniform(-40, 40), c[1] + c[3]), 3, 9 * S, 6 * S)
    A = P.cov(ag); P.clear(A); P.ink('black', A)
    Wr = P.cov(wires); red = P.plate['red'] > .5; P.ink('red', Wr * ~red); P.knock('red', Wr * red); P.ink('black', Wr * red)


PLATES = {'a1': ('a1-access-to-tools', plate_access), 'a2': ('a2-drop-city', plate_dome), 'a3': ('a3-lib-dream', plate_lib),
          'a4': ('a4-human-use', plate_human), 'a5': ('a5-radical-terrain', plate_terrain)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seeds', default='1'); ap.add_argument('--only', default=','.join(PLATES))
    ap.add_argument('--scale', type=int, default=2); ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    seeds = [int(s) for s in a.seeds.split(',')]; keys = a.only.split(','); thumbs = {}
    for k in keys:
        stem, fn = PLATES[k]
        for sd in seeds:
            t0 = time.time(); P = Press(sd * 1000 + 50 + list(PLATES).index(k), a.scale)
            fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
            name = f'{stem}-s{sd}' if len(seeds) > 1 else stem
            img.save(os.path.join(a.out, name + '.png'))
            meta = {'plate': k, 'seed': sd, 'scale': a.scale, 'source': 'are.na/milan-gress/counterculture-cybernetic-capitalism',
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
