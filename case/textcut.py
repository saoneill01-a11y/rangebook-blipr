"""Text outlines from a real font, as solids to cut into a part (for small lettering like rangebook.org).
Ear-clipping triangulation, so no extra packages are needed beyond matplotlib."""
import math
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from csg import V, Poly, Solid, union_all


def _area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def _clean(p, eps=1e-4):
    out = []
    for q in p:
        if not out or abs(q[0] - out[-1][0]) > eps or abs(q[1] - out[-1][1]) > eps:
            out.append(q)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    k = 0   # drop points on a straight line
    while k < len(out) and len(out) > 3:
        a, b, c = out[k - 1], out[k], out[(k + 1) % len(out)]
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 1e-7:
            out.pop(k)
        else:
            k += 1
    return out


def _inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _ears(p):
    """Triangulate a simple CCW polygon (list of (x,y)) by ear clipping."""
    idx = list(range(len(p)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 100000:
        guard += 1
        n = len(idx)
        for k in range(n):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % n]
            a, b, c = p[i0], p[i1], p[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12:
                continue   # reflex
            tri = (a, b, c)
            if any(_inside(p[j], tri) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def _extrude(p, z0, z1):
    """Closed solid from a simple CCW polygon."""
    polys = []
    for i0, i1, i2 in _ears(p):
        polys.append(Poly([V(*p[i0], z1), V(*p[i1], z1), V(*p[i2], z1)]))
        polys.append(Poly([V(*p[i2], z0), V(*p[i1], z0), V(*p[i0], z0)]))
    n = len(p)
    for i in range(n):
        j = (i + 1) % n
        polys.append(Poly([V(*p[i], z0), V(*p[j], z0), V(*p[j], z1), V(*p[i], z1)]))
    return Solid(polys)


def text_outline(text, font_file, size):
    """Contours of the text in mm, baseline at v = 0, starting at u = 0. Returns (contours, (u0, v0, u1, v1))."""
    tp = TextPath((0, 0), text, size=size, prop=FontProperties(fname=font_file))
    cs = [_clean([tuple(q) for q in c]) for c in tp.to_polygons(closed_only=True)]
    cs = [c for c in cs if len(c) >= 3 and abs(_area(c)) > 1e-4]
    us = [q[0] for c in cs for q in c]
    vs = [q[1] for c in cs for q in c]
    return cs, (min(us), min(vs), max(us), max(vs))


def text_solid(contours, place, z0, z1):
    """Solids for the letters. place(u, v) -> (x, y) maps text coordinates onto the part (may turn or mirror it).
    A contour inside an odd number of others is a hole (the inside of an o, the counter of an a)."""
    mapped = []
    for c in contours:
        m = [place(u, v) for u, v in c]
        if _area(m) < 0:
            m.reverse()
        mapped.append(m)
    outers, holes = [], []
    for i, c in enumerate(mapped):
        depth = sum(1 for j, d in enumerate(mapped) if j != i and _inside(c[0], d))
        (holes if depth % 2 else outers).append(c)
    letters = []
    for o in outers:
        s = _extrude(o, z0, z1)
        hs = [h for h in holes if _inside(h[0], o)]
        if hs:
            s = s.subtract(union_all([_extrude(h, z0 - 1, z1 + 1) for h in hs]))
        letters.append(s)
    return letters
