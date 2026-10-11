"""Pens. One set of weights for everything, so a gear and a wall belong to the same drawing."""
import math
import numpy as np
import skia

HAIR, FINE, REG, BOLD, HEAVY = 0.8, 1.25, 1.9, 3.0, 5.5


def _paint(w=None, fill=False, dash=None, value=1.0, erase=False, cap=skia.Paint.kRound_Cap):
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(1, 1, 1, value))
    if fill:
        p.setStyle(skia.Paint.kFill_Style)
    else:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
    if erase: p.setBlendMode(skia.BlendMode.kClear)
    return p


class Pen:
    """Draws onto a Mask's canvas. erase=True takes coverage away instead of adding it."""

    def __init__(self, mask, erase=False, value=1.0):
        self.c = mask.c; self.erase = erase; self.value = value

    def p(self, w=None, fill=False, dash=None, cap=skia.Paint.kRound_Cap):
        return _paint(w, fill, dash, self.value, self.erase, cap)

    # -- primitives
    def line(self, pts, w=REG, dash=None, cap=skia.Paint.kRound_Cap):
        path = skia.Path(); path.moveTo(*pts[0])
        for q in pts[1:]: path.lineTo(*q)
        self.c.drawPath(path, self.p(w, dash=dash, cap=cap))

    def poly(self, pts, w=REG, fill=False, dash=None):
        path = skia.Path(); path.moveTo(*pts[0])
        for q in pts[1:]: path.lineTo(*q)
        path.close()
        self.c.drawPath(path, self.p(w, fill, dash))

    def circle(self, c, r, w=REG, dash=None):
        self.c.drawCircle(c[0], c[1], r, self.p(w, dash=dash))

    def disc(self, c, r):
        self.c.drawCircle(c[0], c[1], r, self.p(fill=True))

    def rect(self, x, y, w_, h_, w=REG, fill=False, r=0, dash=None):
        R = skia.Rect.MakeXYWH(x, y, w_, h_)
        if r: self.c.drawRoundRect(R, r, r, self.p(w, fill, dash))
        else: self.c.drawRect(R, self.p(w, fill, dash))

    def oval(self, x, y, w_, h_, w=REG, fill=False):
        self.c.drawOval(skia.Rect.MakeXYWH(x, y, w_, h_), self.p(w, fill))

    def arc(self, c, r, a0, sweep, w=REG):
        path = skia.Path(); path.addArc(skia.Rect.MakeXYWH(c[0] - r, c[1] - r, 2 * r, 2 * r), a0, sweep)
        self.c.drawPath(path, self.p(w, cap=skia.Paint.kButt_Cap))

    def curve(self, p0, p1, p2, w=REG, dash=None, p3=None):
        path = skia.Path(); path.moveTo(*p0)
        if p3 is None: path.quadTo(*p1, *p2)
        else: path.cubicTo(*p1, *p2, *p3)
        self.c.drawPath(path, self.p(w, dash=dash))

    def path(self, path, w=REG, fill=False, dash=None):
        self.c.drawPath(path, self.p(w, fill, dash))

    def arrow(self, p0, p1, w=REG, head=7, filled=True):
        self.line([p0, p1], w)
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        l = (p1[0] - head * math.cos(a - .38), p1[1] - head * math.sin(a - .38))
        r = (p1[0] - head * math.cos(a + .38), p1[1] - head * math.sin(a + .38))
        if filled: self.poly([p1, l, r], w * .6, fill=True)
        else: self.line([l, p1, r], w)

    def hatch(self, x, y, w_, h_, step=4, angle=45, w=HAIR):
        """Diagonal hatching clipped to a rect."""
        self.c.save(); self.c.clipRect(skia.Rect.MakeXYWH(x, y, w_, h_), doAntiAlias=True)
        L = w_ + h_; a = math.radians(angle); cx, cy = x + w_ / 2, y + h_ / 2
        for t in np.arange(-L, L, step):
            ox, oy = cx + t * math.cos(a + math.pi / 2), cy + t * math.sin(a + math.pi / 2)
            self.line([(ox - L * math.cos(a), oy - L * math.sin(a)), (ox + L * math.cos(a), oy + L * math.sin(a))], w, cap=skia.Paint.kButt_Cap)
        self.c.restore()

    # -- transforms
    def at(self, x, y, rot=0, s=1):
        return _At(self.c, x, y, rot, s)

    def clip_circle(self, c, r):
        return _Clip(self.c, lambda cv: cv.clipPath(_circ_path(c, r), doAntiAlias=True))

    def clip_rect(self, x, y, w_, h_):
        return _Clip(self.c, lambda cv: cv.clipRect(skia.Rect.MakeXYWH(x, y, w_, h_), doAntiAlias=True))

    def matrix(self, m):
        return _Clip(self.c, lambda cv: cv.concat(m))


def _circ_path(c, r):
    p = skia.Path(); p.addCircle(c[0], c[1], r); return p


class _At:
    def __init__(self, c, x, y, rot, s): self.c, self.args = c, (x, y, rot, s)

    def __enter__(self):
        x, y, rot, s = self.args
        self.c.save(); self.c.translate(x, y); self.c.rotate(rot); self.c.scale(s, s)

    def __exit__(self, *a): self.c.restore()


class _Clip:
    def __init__(self, c, fn): self.c, self.fn = c, fn

    def __enter__(self): self.c.save(); self.fn(self.c)

    def __exit__(self, *a): self.c.restore()


def wobble(pts, rng, amp=1.2, freq=0.04, step=3.0):
    """Resample a polyline and push it along its normal with smooth noise: a hand on a ruler."""
    out = []
    ph = rng.uniform(0, 100, 3)
    dist = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / step))
        nx, ny = -(y1 - y0) / (L + 1e-9), (x1 - x0) / (L + 1e-9)
        for i in range(n):
            t = i / n; d = dist + L * t
            o = amp * (math.sin(d * freq + ph[0]) * .6 + math.sin(d * freq * 2.3 + ph[1]) * .3 + math.sin(d * freq * 5.1 + ph[2]) * .1)
            out.append((x0 + (x1 - x0) * t + nx * o, y0 + (y1 - y0) * t + ny * o))
        dist += L
    out.append(pts[-1])
    return out


def blob_pts(cx, cy, rx, ry, rng, k=5, n=200):
    ph = [rng.uniform(0, 6.3) for _ in range(k)]
    am = [rng.uniform(0.02, 0.08) / (i + 1) ** 0.6 for i in range(k)]
    pts = []
    for t in np.linspace(0, 2 * math.pi, n):
        r = 1 + sum(am[i] * math.sin((i + 2) * t + ph[i]) for i in range(k))
        pts.append((cx + rx * r * math.cos(t), cy + ry * r * math.sin(t)))
    return pts


def iso_matrix(ox, oy, s=1.0, a=28, b=152):
    """A floor plane seen from above and to the side: x runs down one diagonal, y down the other."""
    a, b = math.radians(a), math.radians(b)
    m = skia.Matrix()
    m.setAll(math.cos(a) * s, math.cos(b) * s, ox, math.sin(a) * s, math.sin(b) * s, oy, 0, 0, 1)
    return m


def iso_pt(m, x, y, z=0):
    p = m.mapXY(x, y)
    return (p.fX, p.fY - z)
