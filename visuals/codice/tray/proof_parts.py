import random, numpy as np
from press import Mask, press, ink, BLACK, RED
from draw import Pen
import parts
m = Mask(); p = Pen(m); rng = random.Random(1)
names = list(parts.PARTS)
for i, n in enumerate(names):
    x = 90 + (i % 6) * 168; y = 110 + (i // 6) * 200
    p.rect(x - 75, y - 75, 150, 150, 0.8)
    parts.draw(p, n, x, y, 62, rng)
nr = np.random.default_rng(3)
press([(ink(m.a(), nr), BLACK)], 3, 'parts.png', 'proofs')
