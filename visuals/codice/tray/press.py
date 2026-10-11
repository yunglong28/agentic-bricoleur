"""The press. Drawing makes masks; a plate script adds and subtracts masks into two inks;
this module prints them: a screen for tints, a chewed edge, a mottled drum, misregistration,
and overprint on a sheet of paper that has fibres in it.

Everything is in design units (1024 × 1280) and rendered at K× for the edge,
then brought down to OUT× for the file.
"""
import math
import numpy as np
import skia
from PIL import Image
from scipy import ndimage

DW, DH = 1024, 1280          # design sheet
K = 3                        # render scale
OUTK = 2                     # file scale
W, H = DW * K, DH * K

PAPER = np.array([238, 235, 228], np.float32) / 255
RED = np.array([250, 64, 40], np.float32) / 255          # fluorescent red, as a riso drum gives it
BLACK = np.array([30, 27, 25], np.float32) / 255

# ---------------------------------------------------------------- masks


class Mask:
    """A canvas in design units whose coverage comes back as a float array."""

    def __init__(self):
        self.surf = skia.Surface(W, H)
        self.c = self.surf.getCanvas()
        self.c.clear(skia.ColorTRANSPARENT)
        self.c.scale(K, K)

    def a(self):
        img = self.surf.makeImageSnapshot().toarray()
        return img[..., 3].astype(np.float32) / 255


def union(*ms):
    out = np.zeros((H, W), np.float32)
    for m in ms: out = 1 - (1 - out) * (1 - m)
    return out


# ---------------------------------------------------------------- noise


def _resize(a, shape):
    return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((shape[1], shape[0]), Image.BICUBIC))


def noise(rng, cells_x, cells_y, shape=(H, W)):
    return _resize(rng.random((cells_y, cells_x)), shape)


def fbm(rng, base, octaves=4, shape=(H, W)):
    out = np.zeros(shape, np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = base * 2 ** o
        out += amp * noise(rng, c, max(2, int(c * shape[0] / shape[1])), shape); tot += amp; amp *= 0.5
    return out / tot


_YY, _XX = None, None


def grid():
    global _YY, _XX
    if _YY is None:
        _YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
    return _YY, _XX

# ---------------------------------------------------------------- the press


def screen(t, angle, lpi_cell, rng, grain=0.06):
    """Tint → dots on a rotated screen. cell in design units."""
    yy, xx = grid()
    a = math.radians(angle); cell = lpi_cell * K
    u = (xx * math.cos(a) + yy * math.sin(a)) / cell
    v = (-xx * math.sin(a) + yy * math.cos(a)) / cell
    f = (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v)) / 4 + 0.5
    t = np.clip(t + (rng.random(t.shape, np.float32) - 0.5) * grain * (t > 0.01), 0, 1)
    out = np.clip((f - (1 - t)) / 0.09 + 0.5, 0, 1)
    out[t < 0.01] = 0
    return out


def ink(cov, rng, rough=0.32, mottle=0.16, holes=0.5, starve=0.0):
    """What the drum does to a coverage map: chews the edge, mottles the solid, opens pinholes."""
    fine = ndimage.gaussian_filter(rng.random(cov.shape, np.float32), 1.1)
    fine = (fine - fine.mean()) / (fine.std() + 1e-6)
    c = ndimage.gaussian_filter(cov, 0.9)
    thr = 0.5 + fine * 0.11 * rough / 0.32
    c = np.clip((c - thr) / 0.16 + 0.5, 0, 1)
    dens = 1 - mottle * fbm(rng, 6, 4)
    pin = ndimage.gaussian_filter(rng.random(cov.shape, np.float32), 1.6)
    pin = np.clip((pin - (0.5 + 0.075 * (1.4 - holes))) / 0.02, 0, 1)
    c = c * dens * (1 - 0.85 * pin)
    if starve:
        band = noise(rng, 2, 40)
        c *= 1 - starve * np.clip((band - 0.6) / 0.4, 0, 1)
    return np.clip(c, 0, 1)


def misregister(a, dx, dy):
    return ndimage.shift(a, (dy * K, dx * K), order=1, mode='constant')


def paper(rng):
    fib = (noise(rng, 360, 26) - 0.5) * 0.022 + (noise(rng, 90, 12) - 0.5) * 0.02
    mot = (fbm(rng, 3, 3) - 0.5) * 0.03
    p = PAPER[None, None, :] + (fib + mot)[..., None]
    return p


def press(inks, seed, name, out_dir, dust=True):
    """inks: list of (coverage, colour) in printing order. Overprint is multiply."""
    rng = np.random.default_rng(seed)
    img = paper(rng)
    for cov, col in inks:
        a = np.clip(cov, 0, 1)[..., None]
        img = img * (1 - a * (1 - col[None, None, :]))
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((DW * OUTK, DH * OUTK), Image.LANCZOS)
    o = np.asarray(out, np.float32)
    o += rng.normal(0, 3.2, o.shape[:2])[..., None]
    if dust:
        for _ in range(60):
            x, y = rng.integers(0, o.shape[1] - 4), rng.integers(0, o.shape[0] - 4)
            r = rng.choice([1, 1, 1, 2])
            o[y:y + r, x:x + r] *= rng.uniform(0.55, 0.85)
    Image.fromarray(np.clip(o, 0, 255).astype(np.uint8)).save(f'{out_dir}/{name}', optimize=True)
    print('printed', name)
