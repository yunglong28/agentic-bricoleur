"""THE AGENTIC BRICOLEUR — flux plates, after the Are.na channel "Fluxus" (Sam Hart).
Same press as bricoleur3. The bricoleur as a Fluxus editor: a kit in a case, an instruction on a card,
a prospectus of editions, a family tree of movements, a sheet of rubber stamps. The pixel symbols are the
RE-INCANTAMENTO set (reincantamento-pixel-lab), read from reinc_icons.json, drawn as they are.

  f1 fluxkit        Maciunas' attaché case, opened: every compartment holds a symbol, a drop, a typed slip
  f2 event-score    an event card, typed: one instruction for an agent, on a red field
  f3 prospectus     a Maciunas order sheet: numbered editions in a tight grid, each with its symbol and price
  f4 flux-diagram   the Maciunas chart: lanes of symbols run in from the left, braid into a red trunk, fan out as agents
  f5 stamp-sheet    a sheet of rubber stamps, each struck once, some underinked, some crooked

Usage: python3 bricoleur6.py OUT [--seeds 1,2,3] [--only f1,f2] [--scale 2] [--sheet]
"""
import argparse, json, math, os, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from bricoleur3 import (Press, SPR, DW, DH, F, MONO, sd_box, bez, line, arrow, ring, disc, dashed, sprite, sprite_wh,
                        agent_graph)

SPR.update(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reinc_icons.json'))))
KIT = ('brand/occhio', 'esoteric/key', 'drops/keyhole', 'acephale/acephale', 'prosopon/prosopon', 'alchemy/ouroboros-cable',
       'archives/index-drawer', 'collective/egregore', 'esoteric/candle', 'esoteric/crystal-ball', 'esoteric/grimoire',
       'esoteric/labyrinth', 'esoteric/black-mirror', 'drops/portal', 'archives/signal-halo', 'alchemy/hermetic-vessel',
       'drops-archive/42-gnomes-in-our-computer', 'drops-archive/21-sabotage', 'alchemy/programma-101-altar', 'drops/star')
DROPS = ('brand/goccia', 'brand/goccia-piena', 'brand/goccia-m', 'brand/goccia-s', 'brand/goccia-xs')


def font(px, bold=False):
    return ImageFont.truetype(MONO, int(px), index=1 if bold else 0)


def typed(P, d, x, y, text, px, lead=1.45, bold=False):
    """Typewriter: each letter struck a little apart, a little darker or lighter, never on the line exactly."""
    f = font(px * P.S, bold); adv = px * .6
    for r, row in enumerate(text.split('\n')):
        for c, ch in enumerate(row):
            if ch == ' ': continue
            jx, jy = P.rng.gauss(0, .5), P.rng.gauss(0, .7)
            d.text(P.p(x + c * adv + jx, y + r * px * lead + jy), ch, fill=int(255 * P.rng.uniform(.75, 1)), font=f)


def stamp(P, kind, w, h, rot):
    """One rubber stamp, cut in its own small block and struck at an angle: returns an L image."""
    S = P.S; m = Image.new('L', (int(w * S), int(h * S)), 0); d = ImageDraw.Draw(m)
    cx, cy = w * S / 2, h * S / 2
    if kind == 'ring':
        ring(d, (cx, cy), min(w, h) * .46 * S, 4 * S); ring(d, (cx, cy), min(w, h) * .34 * S, 2 * S)
        nm = P.rng.choice(KIT); px = int(min(w, h) * .32 * S / max(sprite_wh(nm, 1))); sw, sh = sprite_wh(nm, px)
        sprite(d, nm, cx - sw / 2, cy - sh / 2, px)
    elif kind == 'label':
        d.rectangle([2 * S, 2 * S, w * S - 2 * S, h * S - 2 * S], outline=255, width=3 * S)
        word = P.rng.choice(['AGENT', 'PLAY', 'EVENT', 'SCORE', 'KIT', 'GAME', 'NO.', 'FLUX?'])
        f = font(h * .5 * S, True); tw = d.textlength(word, font=f)
        d.text((cx - tw / 2, cy - h * .34 * S), word, fill=255, font=f)
    elif kind == 'solid':
        nm = P.rng.choice(KIT); px = int(min(w, h) * .7 * S / max(sprite_wh(nm, 1)))
        d.rectangle([0, 0, w * S, h * S], fill=255); sw, sh = sprite_wh(nm, px)
        m2 = Image.new('L', m.size, 0); sprite(ImageDraw.Draw(m2), nm, cx - sw / 2, cy - sh / 2, px)
        m = Image.fromarray(np.where(np.asarray(m2) > 0, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(m)
    else:                                                       # 'grid': a sprite of sprites, very small
        nm = P.rng.choice(KIT); px = int(min(w, h) * .9 * S / max(sprite_wh(nm, 1))); sw, sh = sprite_wh(nm, px)
        sprite(d, nm, cx - sw / 2, cy - sh / 2, px, outline=True)
    return m.rotate(rot, resample=Image.BICUBIC, expand=True)

# ------------------------------------------------------------ plates


def plate_kit(P):
    """The case is open: lid above, tray below, a grid of boxes each holding a borrowed thing."""
    S = P.S; x0, x1 = 110, 914
    # the lid, seen from inside: black, screened lighter toward the hinge, a red paste-on label
    lid = P.edge_tone(sd_box(P, 512, 300, 402, 190), 2.5)
    P.ink('black', P.screen(np.clip(.25 + (380 - P.Y) / 300, .25, .92), 15, 3.8) * lid)
    lab = P.edge_tone(sd_box(P, 512, 270, 170, 46), 2, torn=1.2); P.clear(lab); P.ink('red', lab)
    t, td = P.layer(); f = font(44 * S, True); word = 'AGENTKIT'; tw = td.textlength(word, font=f)
    td.text(((512 * S) - tw / 2, 243 * S), word, fill=255, font=f); P.knock('red', P.cov(t))
    t2, t2d = P.layer(); typed(P, t2d, 362, 330, 'a box of games by many hands', 12); P.ink('black', P.cov(t2) * lab)
    hg, hgd = P.layer()
    for x in (240, 784): hgd.rectangle([*P.p(x - 40, 482), *P.p(x + 40, 500)], fill=255)
    P.ink('black', P.cov(hg))
    # the tray: a recursive cut into compartments
    boxes = []

    def cut(x, y, w, h, n):
        if n == 0 or (w < 150 and h < 150) or (n < 3 and P.rng.random() < .25):
            boxes.append((x, y, w, h)); return
        if (w > h) ^ (P.rng.random() < .2):
            k = P.rng.choice([.33, .5, .5, .62]) * w; cut(x, y, k, h, n - 1); cut(x + k, y, w - k, h, n - 1)
        else:
            k = P.rng.choice([.38, .5, .5, .6]) * h; cut(x, y, w, k, n - 1); cut(x, y + k, w, h - k, n - 1)
    cut(x0, 510, x1 - x0, 650, 5)
    wall, wd = P.layer(); fill, fd = P.layer(); red, rd = P.layer(); tone, tnd = P.layer(); ins, insd = P.layer()
    for i, (x, y, w, h) in enumerate(boxes):
        insd.rectangle([*P.p(x + 8, y + 8), *P.p(x + w - 6, y + h - 6)], fill=255)
        wd.rectangle([*P.p(x, y), *P.p(x + w, y + h)], outline=255, width=5 * S)
        tnd.polygon(P.pts([(x, y), (x + w, y), (x + w - 12, y + 12), (x + 12, y + 12)]), fill=255)   # the inner wall's shade
        tnd.polygon(P.pts([(x, y), (x + 12, y + 12), (x + 12, y + h - 12), (x, y + h)]), fill=255)
        r = P.rng.random(); cx, cy = x + w / 2 + 4, y + h / 2 + 4
        if r < .22:
            rd.rectangle([*P.p(x + 12, y + 12), *P.p(x + w, y + h)], fill=255)
            nm = P.rng.choice(KIT); px = max(2, int(min(w, h) * .5 * S / max(sprite_wh(nm, 1)))); sw, sh = sprite_wh(nm, px)
            sprite(fd, nm, P.p(cx)[0] - sw / 2, P.p(0, cy)[1] - sh / 2, px)
        elif r < .4:                                                     # a deck of event cards, fanned
            for k in range(5):
                a = math.radians(-14 + k * 7); cw, ch = min(w, h) * .3, min(w, h) * .42
                pts = [(-cw, -ch), (cw, -ch), (cw, ch), (-cw, ch)]
                q = [(cx + px_ * math.cos(a) - py_ * math.sin(a), cy + px_ * math.sin(a) + py_ * math.cos(a)) for px_, py_ in pts]
                fd.polygon(P.pts(q), fill=0, outline=255); fd.line(P.pts(q + [q[0]]), fill=255, width=2 * S)
        elif r < .55:                                                    # loose dice / coins, scattered
            px = max(2, int(min(w, h, 160) * .045 * S)); u = 7 * px / S
            for _ in range(min(9, int(w * h / 5000) + 2)):
                nm = P.rng.choice(DROPS[2:])
                sprite(fd, nm, *P.p(P.rng.uniform(x + 18, x + w - 10 - u), P.rng.uniform(y + 18, y + h - 10 - u)), px)
        elif r < .7:                                                     # a stack of tetrominoes
            u = min(w, h, 180) * .12
            for j in range(max(1, int((h - 40) / u / 1.1) - 1)):
                nm = DROPS[(j * 2 + i) % 2]; sprite(rd if j % 2 else fd, nm, *P.p(x + 22 + (j % 3) * u * .6, y + h - 22 - (j + 1) * u * 1.05), max(2, int(u * S / 11)))
        elif r < .85:                                                    # a typed slip
            sl = sd_box(P, cx, cy, w * .34, h * .3); P.clear(P.edge_tone(sl, 1.5))
            tt, ttd = P.layer(); typed(P, ttd, cx - w * .3, cy - h * .2, 'play\nuntil\nlost', max(9, min(w, h) * .09)); P.ink('black', P.cov(tt))
            od, odd = P.layer(); odd.rectangle([*P.p(cx - w * .34, cy - h * .3), *P.p(cx + w * .34, cy + h * .3)], outline=255, width=2 * S); P.ink('black', P.cov(od))
        else:                                                            # something big, outlined
            nm = P.rng.choice(KIT); px = max(2, int(min(w, h) * .65 * S / max(sprite_wh(nm, 1)))); sw, sh = sprite_wh(nm, px)
            sprite(fd, nm, P.p(cx)[0] - sw / 2, P.p(0, cy)[1] - sh / 2, px, outline=True)
    I = P.cov(ins)
    P.ink('red', P.cov(red) * I); P.ink('black', P.screen(np.full((P.H, P.W), .45, F), 15, 3.2) * P.cov(tone))
    fl = P.cov(fill) * I; P.knock('red', fl); P.ink('black', fl * (1 - P.cov(red))); P.ink('black', P.cov(wall))
    # the case's outer edge and handle
    o, od = P.layer(); od.rounded_rectangle([*P.p(x0 - 14, 496), *P.p(x1 + 14, 1174)], 14 * S, outline=255, width=7 * S)
    od.rounded_rectangle([*P.p(452, 1182), *P.p(572, 1222)], 12 * S, outline=255, width=9 * S); P.ink('black', P.cov(o))


SCORES = ["AGENT PIECE\n\nOpen a game.\nPlay it until\nanother game\nbegins.",
          "SOLO FOR TWO ENGINES\n\nLet one agent\nwrite the rules\nand another\nbreak them.\n\nRepeat.",
          "LEVEL\n\nDraw a straight\nline and walk it\nuntil it becomes\na level."]


def plate_score(P):
    """A card on a red field: the field screened to a sunset at the bottom, the card shadowed, the text struck."""
    S = P.S; cx, cy, hw, hh = 512, 560, 360, 290
    P.ink('red', P.screen(np.clip(.55 + .45 * (P.Y / DH), 0, 1), 75, 5.6))
    # a ruled grid ghosted into the field, as on graph paper under the card
    g = (((P.X % 32) < 1.2) | ((P.Y % 32) < 1.2)).astype(F); P.knock('red', g * .9)
    sh = P.edge_tone(sd_box(P, cx + 14, cy + 18, hw, hh), 6)
    P.ink('black', P.screen(np.full((P.H, P.W), .55, F), 15, 3.4) * sh)
    card = P.edge_tone(sd_box(P, cx, cy, hw, hh), 1.6); P.clear(card)
    t, td = P.layer(); txt = SCORES[P.seed // 1000 % len(SCORES)]
    head, body = txt.split('\n\n', 1)
    typed(P, td, cx - hw + 56, cy - hh + 56, head, 30, bold=True)
    typed(P, td, cx - hw + 56, cy - hh + 140, body, 30)
    typed(P, td, cx + hw - 190, cy + hh - 46, 'summer 2026', 13)
    P.ink('black', P.cov(t) * card)
    # rule under the title, a red pixel stamp at the corner (the edition mark)
    r, rd = P.layer(); rd.line([*P.p(cx - hw + 56, cy - hh + 108), *P.p(cx - hw + 300, cy - hh + 108)], fill=255, width=2 * S)
    P.ink('black', P.cov(r))
    m = stamp(P, 'ring', 120, 120, P.rng.uniform(-18, 18)); big = Image.new('L', (P.W, P.H), 0)
    big.paste(m, (int((cx + hw - 110) * S - m.size[0] / 2), int((cy - hh + 100) * S - m.size[1] / 2)))
    P.ink('red', P.cov(big) * (P.value(40) > .32) * card)
    # the box it came from, a small envelope below with its flap
    e, ed = P.layer(); ex, ey = 512, 1080
    ed.rectangle([*P.p(ex - 130, ey - 70), *P.p(ex + 130, ey + 70)], outline=255, width=3 * S)
    line(ed, P.pts([(ex - 130, ey - 70), (ex, ey + 10), (ex + 130, ey - 70)]), 3 * S)
    E = P.edge_tone(sd_box(P, ex, ey, 130, 70), 1.4); P.clear(E); P.ink('black', P.cov(e))
    n, nd = P.layer(); typed(P, nd, ex - 100, ey + 36, 'event card no. %d' % (P.seed // 1000), 11); P.ink('black', P.cov(n))


EDITIONS = ['drop kit', 'eye box', 'labyrinth by mail', 'candle score', 'mirror, black', 'a key for no door',
            'egregore in a jar', 'index of lost hands', 'vessel, sealed', 'portal (flat)', 'grimoire, blank',
            'gnome in the machine', 'sabotage card', 'halo for a signal', 'altar for a calculator', 'the acephale game',
            'face, impersonal', 'ouroboros cable', 'star in a drop', 'crystal, cloudy']


def plate_prospectus(P):
    """An order sheet: a black masthead, numbered editions three to a row, red numbers, prices typed in."""
    S = P.S
    mh = P.edge_tone(sd_box(P, 512, 120, 472, 78), 1.2, torn=.6); P.ink('black', mh)
    t, td = P.layer(); f = font(78 * S, True); word = 'AGENTFLUX'; tw = td.textlength(word, font=f)
    td.text((512 * S - tw / 2, 66 * S), word, fill=255, font=f); P.knock('black', P.cov(t))
    r, rd = P.layer(); rd.rectangle([*P.p(40, 210), *P.p(DW - 40, 238)], fill=255); P.ink('red', P.cov(r))
    t2, t2d = P.layer(); typed(P, t2d, 56, 214, 'EDITIONS  —  ORDER BY MAIL  —  EVERY BOX ASSEMBLED BY A DIFFERENT HAND', 15, bold=True)
    P.knock('red', P.cov(t2))
    order = list(range(len(EDITIONS))); P.rng.shuffle(order)
    cols, rows, gx, gy, cw, ch = 3, 6, 40, 262, (DW - 80) / 3, 152
    G, Gd = P.layer(); R, Rd = P.layer(); K, Kd = P.layer(); inv = P.rng.sample(range(cols * rows), 3)
    for n in range(cols * rows):
        c, r_ = n % cols, n // cols; x, y = gx + c * cw, gy + r_ * ch; e = order[n % len(order)]
        Gd.rectangle([*P.p(x, y), *P.p(x + cw, y + ch)], outline=255, width=2 * S)
        if n in inv: Kd.rectangle([*P.p(x + 4, y + 4), *P.p(x + cw - 4, y + ch - 4)], fill=255)
        Rd.rectangle([*P.p(x + 10, y + 10), *P.p(x + 64, y + 46)], fill=255)
        nm = KIT[e % len(KIT)]; gw, gh = sprite_wh(nm, 1); px = max(2, int(min(110 / gw, 86 / gh) * S)); sw, sh = sprite_wh(nm, px)
        sprite(Gd, nm, P.p(x + cw - 20)[0] - sw, P.p(0, y + ch - 16)[1] - sh, px)
        typed(P, Gd, x + 14, y + 58, EDITIONS[e].replace(', ', ',\n').replace(' by ', '\nby '), 15, lead=1.3)
        typed(P, Gd, x + 14, y + ch - 30, '$ %d' % P.rng.choice([1, 2, 3, 3, 5, 8, 20]), 14, bold=True)
    Gm, Rm, Km = P.cov(G), P.cov(R), P.cov(K)
    num, numd = P.layer()
    for n in range(cols * rows):
        c, r_ = n % cols, n // cols; typed(P, numd, gx + c * cw + 18, gy + r_ * ch + 14, '%02d' % (n + 1), 22, bold=True)
    nums = P.cov(num)
    P.ink('black', P.screen(np.full((P.H, P.W), .82, F), 15, 3.2) * Km)
    P.ink('black', Gm * (1 - Km)); P.knock('black', Gm * Km)
    P.ink('red', Rm); P.knock('red', nums)
    # foot: a typed address and a red rule
    ft, ftd = P.layer(); typed(P, ftd, 40, 1200, 'send cash or a symbol of equal weight to the atelier. no refunds, no returns, no duplicates.', 13)
    P.ink('black', P.cov(ft)); fr, frd = P.layer(); frd.rectangle([*P.p(40, 1236), *P.p(DW - 40, 1242)], fill=255); P.ink('red', P.cov(fr))


def plate_diagram(P):
    """Maciunas' chart: years along the top, movements as lanes, braided into one red trunk, fanning into agents."""
    S = P.S; lanes = 14; y0, y1 = 170, 1180; xL, xM, xR = 40, 520, 760
    ys = np.linspace(y0, y1, lanes); trunk = 640
    tk, tkd = P.layer(); f = font(12 * S)
    for i, yr in enumerate(range(1960, 2030, 10)):
        x = 40 + i * (DW - 80) / 6.6
        tkd.line([*P.p(x, 120), *P.p(x, 140)], fill=255, width=2 * S); tkd.text(P.p(x + 4, 104), str(yr), fill=255, font=f)
    tkd.line([*P.p(40, 140), *P.p(DW - 40, 140)], fill=255, width=2 * S)
    P.ink('black', P.cov(tk))
    # lanes: each starts with an emblem (a game's sprite), runs right, then bends into the trunk
    L, Ld = P.layer(); E, Ed = P.layer(); tr, trd = P.layer()
    for i, y in enumerate(ys):
        nm = KIT[i % len(KIT)]; px = 4 * S; sw, sh = sprite_wh(nm, px)
        sprite(Ed, nm, P.p(xL)[0], P.p(0, y)[1] - sh / 2, px)
        xs = xL + 60 + P.rng.uniform(0, 200)
        Ld.line([*P.p(xL + 54, y), *P.p(xs, y)], fill=255, width=2 * S)
        dashed(Ld, P.p(xs, y), P.p(xs + 70, y), 2 * S, 6 * S, 5 * S)
        ty = trunk + (i - lanes / 2) * 7
        pts = bez(P.p(xs + 70, y), P.p(xM - 40, y), P.p(xM, ty), 60)
        line(Ld, pts, 2 * S)
        trd.line([*P.p(xM, ty), *P.p(xR, ty)], fill=255, width=3 * S)
        if i % 3 == 1:                                              # a cross-link between lanes, as in the chart
            j = min(lanes - 1, i + 2); Ld.line([*P.p(xs + 20, y), *P.p(xs + 40, ys[j])], fill=255, width=S); disc(Ld, P.p(xs + 20, y), 4 * S)
    # the trunk band, red with the lanes knocked through it
    band = P.edge_tone(sd_box(P, (xM + xR) / 2, trunk, (xR - xM) / 2, lanes * 4 + 14), 1.5, torn=1.0)
    P.ink('red', band); P.knock('red', P.cov(tr) * band)
    P.ink('black', P.cov(L)); P.ink('black', P.cov(E))
    lb, lbd = P.layer(); f2 = font(15 * S, True); lbd.text(P.p(xM + 20, trunk - lanes * 4 - 38), 'BRICOLAGE', fill=255, font=f2)
    P.ink('black', P.cov(lb))
    # out of the trunk: an agent graph, fed by every lane at once
    ag, agd = P.layer(); nodes = agent_graph(P, agd, 880, trunk, 140, 16, 2 * S)
    for k in range(lanes):
        ty = trunk + (k - lanes / 2) * 7; nx, ny = nodes[k % len(nodes)]
        line(agd, bez(P.p(xR, ty), P.p(xR + 40, ty), P.p(nx, ny), 30), S)
    P.ink('black', P.cov(ag))
    # a red bracket over the future
    bk, bkd = P.layer(); line(bkd, P.pts([(xR, 152), (xR, 160), (DW - 40, 160), (DW - 40, 152)]), 4 * S)
    P.ink('red', P.cov(bk))


def plate_stamps(P):
    """A stamp sheet returned to the archive: a loose grid, each stamp struck once, the ink never even."""
    S = P.S; red, black = Image.new('L', (P.W, P.H), 0), Image.new('L', (P.W, P.H), 0)
    kinds = ['ring', 'label', 'solid', 'grid']
    cols, rows = 4, 6
    for r in range(rows):
        for c in range(cols):
            if P.rng.random() < .1: continue
            w = P.rng.choice([150, 170, 200]); h = P.rng.choice([110, 150, 170]) if P.rng.random() < .6 else w
            kind = P.rng.choice(kinds)
            if kind == 'label': h = 70
            m = stamp(P, kind, w, h, P.rng.gauss(0, 6))
            x = 130 + c * 255 + P.rng.uniform(-30, 30); y = 120 + r * 200 + P.rng.uniform(-24, 24)
            dst = red if P.rng.random() < .62 else black
            dst.paste(Image.fromarray(np.maximum(np.asarray(dst.crop((int(x * S - m.size[0] / 2), int(y * S - m.size[1] / 2),
                      int(x * S - m.size[0] / 2) + m.size[0], int(y * S - m.size[1] / 2) + m.size[1]))), np.asarray(m))),
                      (int(x * S - m.size[0] / 2), int(y * S - m.size[1] / 2)))
    # uneven inking: each colour has its own pressure field; where it falls off the stamp breaks into specks
    for name, im, k in (('red', red, .30), ('black', black, .26)):
        c = P.cov(im); press = P.fbm(6, 4)
        speck = P.nr.random(c.shape, F) < np.clip((k + .1 - press) * 4, 0, 1)
        P.ink(name, P.crayon(c * (press > k) * (~speck), .35, .12))
    # the sheet's own print: a ruled margin and a typed caption
    t, td = P.layer(); td.line([*P.p(40, 1222), *P.p(DW - 40, 1222)], fill=255, width=2 * S)
    typed(P, td, 40, 1234, 'stamp sheet, returned to the archive  —  %d struck' % (rows * cols), 12); P.ink('black', P.cov(t))


PLATES = {'f1': ('f1-fluxkit', plate_kit), 'f2': ('f2-event-score', plate_score), 'f3': ('f3-prospectus', plate_prospectus),
          'f4': ('f4-flux-diagram', plate_diagram), 'f5': ('f5-stamp-sheet', plate_stamps)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seeds', default='1'); ap.add_argument('--only', default=','.join(PLATES))
    ap.add_argument('--scale', type=int, default=2); ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    seeds = [int(s) for s in a.seeds.split(',')]; keys = a.only.split(','); thumbs = {}
    for k in keys:
        stem, fn = PLATES[k]
        for sd in seeds:
            t0 = time.time(); P = Press(sd * 1000 + 90 + list(PLATES).index(k), a.scale)
            fn(P); img = P.develop((P.rng.uniform(2, 4), P.rng.uniform(-3, -1)))
            name = f'{stem}-s{sd}' if len(seeds) > 1 else stem
            img.save(os.path.join(a.out, name + '.png'))
            meta = {'plate': k, 'seed': sd, 'scale': a.scale, 'source': 'are.na/sam-hart/fluxus-1474596946',
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
