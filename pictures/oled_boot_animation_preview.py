"""Preview of the OLED boot animation.  python3 oled_boot_animation_preview.py path/to/Adafruit-GFX-Library/glcdfont.c"""
import os, sys, re, numpy as np
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
from PIL import Image, ImageDraw
src = open(sys.argv[1] if len(sys.argv) > 1 else 'glcdfont.c').read()
body = src[src.index('{', src.index('font[]')) + 1: src.rindex('}')]
FONT = [int(v, 16) for v in re.findall(r'0x[0-9A-Fa-f]{2}', body)]
W, H = 128, 64
class O:
    def __init__(s): s.b = np.zeros((H, W), np.uint8)
    def clear(s): s.b[:] = 0
    def px(s, x, y, c):
        if 0 <= x < W and 0 <= y < H: s.b[y, x] = c
    def fillRect(s, x, y, w, h, c):
        for i in range(x, x + w):
            for j in range(y, y + h): s.px(i, j, c)
    def hline(s, x, y, w, c): s.fillRect(x, y, w, 1, c)
    def vline(s, x, y, h, c): s.fillRect(x, y, 1, h, c)
    def fillCircle(s, x0, y0, r, c):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + r: s.px(x0 + dx, y0 + dy, c)
    def fillTri(s, pts, c):
        im = Image.new('1', (W, H), 0); ImageDraw.Draw(im).polygon(pts, fill=1, outline=1)
        a = np.array(im); s.b[a] = c
    def char(s, x, y, ch, size, c=1):
        for i in range(5):
            line = FONT[ord(ch) * 5 + i]
            for j in range(8):
                if line & 1: s.fillRect(x + i * size, y + j * size, size, size, c)
                line >>= 1
    def center(s, t, y, size):
        w = len(t) * 6 * size; x = max(0, (128 - w) // 2)
        for k, ch in enumerate(t): s.char(x + k * 6 * size, y, ch, size)
PROF=[3,4,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,4,4,4,4,3,3,3,3,2,2,2,1,0]
def bullet(o, x, y):
    for i,h in enumerate(PROF): o.vline(x + i, y - h, 2 * h + 1, 1)
def frames():
    o = O(); Y = 25; out = []
    for x in range(-32, 133, 6):
        o.clear(); o.center("BLIPR", 14, 3); o.center("v0.2.2", 44, 1)
        if x < 128: o.fillRect(max(0, x), 0, 128, 64, 0)
        wake = x - 22; w0 = max(0, wake); o.fillRect(w0, 9, x - w0, 31, 0)
        for k in range(3):
            ln = 8 + (((x + 32) // 6 + k * 5) % 3) * 5
            o.hline(x - 3 - ln, Y - 3 + k * 3, ln, 1)
        bullet(o, x, Y); out.append((o.b.copy(), 40))
    o.clear(); o.center("BLIPR", 14, 3); o.center("v0.2.2", 44, 1)
    out.append((o.b.copy(), 30)); out.append((1 - o.b, 70)); out.append((o.b.copy(), 1400))
    return out
def img(b, scale=4):
    rgb = np.zeros((H, W, 3), np.uint8); rgb[b == 1] = (120, 200, 255)
    im = Image.fromarray(rgb).resize((W * scale, H * scale), Image.NEAREST)
    pad = Image.new('RGB', (W * scale + 24, H * scale + 24), (25, 25, 28)); pad.paste(im, (12, 12)); return pad
fr = frames()
ims = [img(b) for b, _ in fr]
ims[0].save(os.path.join(OUTDIR, 'oled_boot_animation.gif'), save_all=True, append_images=ims[1:], duration=[d for _, d in fr], loop=0)
# a still strip of 4 moments
pick = [6, 13, 20, len(fr) - 1]
strip = Image.new('RGB', (ims[0].width * 2 + 10, ims[0].height * 2 + 10), (255, 255, 255))
for i, k in enumerate(pick): strip.paste(ims[k], ((i % 2) * (ims[0].width + 10), (i // 2) * (ims[0].height + 10)))
strip.save(os.path.join(OUTDIR, 'oled_boot_animation_frames.png'))
print(len(fr), 'frames')
