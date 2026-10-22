"""Parse Adafruit GFX custom font headers and draw text like the library does."""
import re
import os
FD = os.environ.get('GFX_FONTS', 'Adafruit-GFX-Library/Fonts/')   # the library's Fonts folder
_cache = {}
def load(name):
    if name in _cache: return _cache[name]
    s = open(FD + name + '.h').read()
    bm = s[s.index('Bitmaps[]'):]; bm = bm[bm.index('{') + 1: bm.index('};')]
    bits = [int(v, 16) for v in re.findall(r'0x[0-9A-Fa-f]+', bm)]
    gl = s[s.index('Glyphs[]'):]; gl = gl[gl.index('{') + 1: gl.index('};')]
    glyphs = [tuple(int(x) for x in g) for g in re.findall(r'\{\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\}', gl)]
    m = re.search(r'GFXfont\s+\w+\s+PROGMEM\s*=\s*\{[^,]+,[^,]+,\s*(0x[0-9A-Fa-f]+|\d+),\s*(0x[0-9A-Fa-f]+|\d+),\s*(\d+)', s)
    first, last, yadv = int(m.group(1), 0), int(m.group(2), 0), int(m.group(3))
    f = dict(bits=bits, glyphs=glyphs, first=first, last=last, yadv=yadv)
    _cache[name] = f; return f
def bounds(name, text):
    """like getTextBounds at cursor (0,0): returns x0, y0, w, h relative to the baseline start"""
    f = load(name); x = 0; minx = miny = 10**9; maxx = maxy = -10**9
    for ch in text:
        g = f['glyphs'][ord(ch) - f['first']]
        off, w, h, xa, xo, yo = g
        if w and h:
            minx = min(minx, x + xo); maxx = max(maxx, x + xo + w - 1); miny = min(miny, yo); maxy = max(maxy, yo + h - 1)
        x += xa
    return minx, miny, maxx - minx + 1, maxy - miny + 1
def draw(o, name, text, x, y, c=1):
    f = load(name)
    for ch in text:
        off, w, h, xa, xo, yo = f['glyphs'][ord(ch) - f['first']]
        bit = 0
        for yy in range(h):
            for xx in range(w):
                b = f['bits'][off + (bit >> 3)] & (0x80 >> (bit & 7)); bit += 1
                if b: o.px(x + xo + xx, y + yo + yy, c)
        x += xa
