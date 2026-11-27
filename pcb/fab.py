"""From design.py + the routed SES: ground pour, DRC, connectivity check, Gerbers, drill files, pictures, BOM."""
import os, sys, math, json, zipfile, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import design as D
import route as RT

OUT = "out"
VERSION = "v1.2"            # v1.2 (Nov 2026): the two 5 V filters on the board; v1.1 is frozen in v1.1/
POUR_CLR = 0.35          # pour to other-net copper
EDGE_CLR = 0.5           # copper to board edge
SPOKE_W = 0.5
SPOKE_MIN_CLR = 0.3       # thermal spokes keep at least this from other nets
ANTENNA_KEEPOUT = D.ANTENNA_KEEPOUT          # no pour under the ESP32-C3's chip antenna (x0, y0, x1, y1)

# ------------------------------------------------------------------ collect copper
def load():
    r = json.load(open(os.path.join(OUT, "routes.json")))
    pn = D.pin_net()
    pads = []
    for (ref, nm, x, y, sh, w, h, dr, ro) in D.pads_world():
        pads.append({"ref": ref, "pin": nm, "x": x, "y": y, "sh": sh, "w": w, "h": h, "dr": dr, "rot": ro, "net": pn.get(ref + "-" + nm)})
    wires = [{"net": n, "layer": L, "w": w, "pts": [tuple(p) for p in pts]} for (n, L, w, pts) in r["wires"]]
    vias = [{"net": n, "x": x, "y": y, "d": 0.6, "dr": 0.3} for (n, x, y) in r["vias"]]
    return pads, wires, vias

# ------------------------------------------------------------------ geometry
def seg_seg(a, b, c, d):
    """min distance between segments ab and cd"""
    def pt_seg(p, a, b):
        ax, ay = a; bx, by = b; px, py = p
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
        return math.hypot(px - ax - t * dx, py - ay - t * dy)
    def inter(a, b, c, d):
        def cr(o, p, q): return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
        d1, d2, d3, d4 = cr(c, d, a), cr(c, d, b), cr(a, b, c), cr(a, b, d)
        return (d1 * d2 < 0) and (d3 * d4 < 0)
    if inter(a, b, c, d):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))

def rect_edges(cx, cy, w, h):
    a, b, c, d = (cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)
    return [(a, b), (b, c), (c, d), (d, a)]

def in_rect(pt, cx, cy, w, h):
    return abs(pt[0] - cx) <= w / 2 and abs(pt[1] - cy) <= h / 2

def item_dist(A, B):
    """items: ("cap", a, b, r) capsule  or  ("rect", cx, cy, w, h)"""
    if A[0] == "cap" and B[0] == "cap":
        return seg_seg(A[1], A[2], B[1], B[2]) - A[3] - B[3]
    if A[0] == "rect" and B[0] == "cap":
        A, B = B, A
    if A[0] == "cap" and B[0] == "rect":
        _, cx, cy, w, h = B
        if in_rect(A[1], cx, cy, w, h) or in_rect(A[2], cx, cy, w, h):
            return -A[3]
        return min(seg_seg(A[1], A[2], e0, e1) for e0, e1 in rect_edges(cx, cy, w, h)) - A[3]
    _, ax, ay, aw, ah = A; _, bx, by, bw, bh = B
    dx = max(0, abs(ax - bx) - (aw + bw) / 2); dy = max(0, abs(ay - by) - (ah + bh) / 2)
    return math.hypot(dx, dy)

def geom(p):
    if p["sh"] == "rect":
        return ("rect", p["x"], p["y"], p["w"], p["h"])
    return ("cap", (p["x"], p["y"]), (p["x"], p["y"]), max(p["w"], p["h"]) / 2)

def items(pads, wires, vias, layer):
    out = []
    for p in pads:
        out.append(("pad %s-%s" % (p["ref"], p["pin"]), p["net"], geom(p), p["ref"]))
    for w in wires:
        if w["layer"] != layer:
            continue
        for k in range(len(w["pts"]) - 1):
            out.append(("wire", w["net"], ("cap", w["pts"][k], w["pts"][k + 1], w["w"] / 2), None))
    for v in vias:
        out.append(("via", v["net"], ("cap", (v["x"], v["y"]), (v["x"], v["y"]), v["d"] / 2), None))
    return out

def bbox(g):
    if g[0] == "rect":
        return (g[1] - g[3] / 2, g[2] - g[4] / 2, g[1] + g[3] / 2, g[2] + g[4] / 2)
    (ax, ay), (bx, by), r = g[1], g[2], g[3]
    return (min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r)

def drc(pads, wires, vias):
    probs = []
    for layer in ("F.Cu", "B.Cu"):
        its = items(pads, wires, vias, layer)
        bb = [bbox(it[2]) for it in its]
        for i in range(len(its)):
            for j in range(i + 1, len(its)):
                A, B = its[i], its[j]
                if A[1] is not None and A[1] == B[1]:
                    continue
                a, b = bb[i], bb[j]
                if a[0] > b[2] + 0.3 or b[0] > a[2] + 0.3 or a[1] > b[3] + 0.3 or b[1] > a[3] + 0.3:
                    continue
                d = item_dist(A[2], B[2])
                # pads of one part were placed by the footprint (e.g. 2 mm capacitor leads): allow 0.3 mm there
                lim = 0.3 if (A[3] and A[3] == B[3]) else D.CLEARANCE - 0.01
                if d < lim:
                    probs.append("%s %s(%s) to %s(%s): %.3f mm" % (layer, A[0], A[1], B[0], B[1], d))
        for it in its:
            if it[0] in ("wire", "via"):
                g = it[2]
                for (x, y) in (g[1], g[2]):
                    r = g[3]
                    if x - r < EDGE_CLR - 0.2 or y - r < EDGE_CLR - 0.2 or x + r > D.BOARD_W - EDGE_CLR + 0.2 or y + r > D.BOARD_H - EDGE_CLR + 0.2:
                        probs.append("%s %s near edge at (%.1f, %.1f)" % (layer, it[0], x, y))
                    for hx, hy in D.HOLES:
                        if math.hypot(x - hx, y - hy) < D.HOLE_KEEPOUT + r - 0.05:
                            probs.append("%s %s in hole keepout at (%.1f, %.1f)" % (layer, it[0], x, y))
    return probs

def connectivity(pads, wires, vias):
    """union-find over touching copper of the same net; every net's pads must end up in one group."""
    nodes = []
    for p in pads:
        if p["net"]:
            nodes.append((p["net"], "both", (p["x"], p["y"]), (p["x"], p["y"]), min(p["w"], p["h"]) / 2))
    for w in wires:
        for k in range(len(w["pts"]) - 1):
            nodes.append((w["net"], w["layer"], w["pts"][k], w["pts"][k + 1], w["w"] / 2))
    for v in vias:
        nodes.append((v["net"], "both", (v["x"], v["y"]), (v["x"], v["y"]), v["d"] / 2))
    par = list(range(len(nodes)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            A, B = nodes[i], nodes[j]
            if A[0] != B[0]:
                continue
            if A[1] != "both" and B[1] != "both" and A[1] != B[1]:
                continue
            if seg_seg(A[2], A[3], B[2], B[3]) <= A[4] + B[4] - 0.01:
                par[f(i)] = f(j)
    bad = []
    for n in D.NETS:
        groups = {f(i) for i, nd in enumerate(nodes) if nd[0] == n and nd[1] == "both" and i < sum(1 for p in pads if p["net"])}
        if len(groups) > 1:
            bad.append("%s: %d separate pieces" % (n, len(groups)))
    return bad

# ------------------------------------------------------------------ Gerber writer
class Gerber:
    def __init__(self, name, func):
        self.name, self.func = name, func
        self.ap = {}
        self.body = []
        self.cur = None
    def aperture(self, kind, *dims):
        key = (kind,) + tuple(round(d, 4) for d in dims)
        if key not in self.ap:
            self.ap[key] = 10 + len(self.ap)
        return self.ap[key]
    @staticmethod
    def c(v):
        return "%d" % int(round(v * 1e6))
    def use(self, code):
        if self.cur != code:
            self.body.append("D%d*" % code); self.cur = code
    def polarity(self, dark):
        self.body.append("%%LP%s*%%" % ("D" if dark else "C"))
    def flash(self, x, y, code):
        self.use(code); self.body.append("X%sY%sD03*" % (self.c(x), self.c(y)))
    def circle(self, x, y, d):
        self.flash(x, y, self.aperture("C", d))
    def rect(self, x, y, w, h):
        self.flash(x, y, self.aperture("R", w, h))
    def oval(self, x, y, w, h):
        self.flash(x, y, self.aperture("O", w, h))
    def track(self, pts, w):
        self.use(self.aperture("C", w))
        self.body.append("X%sY%sD02*" % (self.c(pts[0][0]), self.c(pts[0][1])))
        for x, y in pts[1:]:
            self.body.append("X%sY%sD01*" % (self.c(x), self.c(y)))
    def region(self, pts):
        self.body.append("G36*")
        self.body.append("X%sY%sD02*" % (self.c(pts[0][0]), self.c(pts[0][1])))
        for x, y in pts[1:] + [pts[0]]:
            self.body.append("X%sY%sD01*" % (self.c(x), self.c(y)))
        self.body.append("G37*")
    def write(self, path):
        h = ["G04 RB BLIPR main board %s*" % VERSION, "%%TF.FileFunction,%s*%%" % self.func, "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%", "G01*"]
        for key, code in sorted(self.ap.items(), key=lambda kv: kv[1]):
            if key[0] == "C":
                h.append("%%ADD%dC,%.4f*%%" % (code, key[1]))
            elif key[0] == "R":
                h.append("%%ADD%dR,%.4fX%.4f*%%" % (code, key[1], key[2]))
            else:
                h.append("%%ADD%dO,%.4fX%.4f*%%" % (code, key[1], key[2]))
        open(path, "w").write("\n".join(h + self.body + ["M02*"]) + "\n")

def pad_flash(g, p, grow=0.0):
    w, h = p["w"] + 2 * grow, p["h"] + 2 * grow
    if p["sh"] == "rect":
        g.rect(p["x"], p["y"], w, h)
    elif p["sh"] == "oval" and abs(w - h) > 1e-6:
        if p["rot"] % 180 == 90:
            w, h = h, w
        g.oval(p["x"], p["y"], w, h)
    else:
        g.circle(p["x"], p["y"], max(w, h))

# ------------------------------------------------------------------ ground pour (bottom), with islands removed
def pour(pads, wires, vias, res=0.05):
    W, H = D.BOARD_W, D.BOARD_H
    nx, ny = int(W / res) + 1, int(H / res) + 1
    X, Y = np.meshgrid(np.arange(nx) * res, np.arange(ny) * res)
    m = np.zeros((ny, nx), bool)
    m[(X >= EDGE_CLR) & (X <= W - EDGE_CLR) & (Y >= EDGE_CLR) & (Y <= H - EDGE_CLR)] = True
    def clear_disc(x, y, r):
        i0, i1 = max(0, int((y - r) / res) - 1), min(ny, int((y + r) / res) + 2)
        j0, j1 = max(0, int((x - r) / res) - 1), min(nx, int((x + r) / res) + 2)
        sub = (X[i0:i1, j0:j1] - x) ** 2 + (Y[i0:i1, j0:j1] - y) ** 2 <= r * r
        m[i0:i1, j0:j1] &= ~sub
    def clear_seg(a, b, r):
        x0, x1 = min(a[0], b[0]) - r, max(a[0], b[0]) + r
        y0, y1 = min(a[1], b[1]) - r, max(a[1], b[1]) + r
        i0, i1 = max(0, int(y0 / res) - 1), min(ny, int(y1 / res) + 2)
        j0, j1 = max(0, int(x0 / res) - 1), min(nx, int(x1 / res) + 2)
        px, py = X[i0:i1, j0:j1], Y[i0:i1, j0:j1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = np.zeros_like(px) if L == 0 else np.clip(((px - a[0]) * dx + (py - a[1]) * dy) / L, 0, 1)
        sub = (px - a[0] - t * dx) ** 2 + (py - a[1] - t * dy) ** 2 <= r * r
        m[i0:i1, j0:j1] &= ~sub
    for hx, hy in D.HOLES:
        clear_disc(hx, hy, D.HOLE_KEEPOUT)
    ax0, ay0, ax1, ay1 = ANTENNA_KEEPOUT
    m[(X >= ax0) & (X <= ax1) & (Y >= ay0) & (Y <= ay1)] = False
    for p in pads:
        r = math.hypot(p["w"], p["h"]) / 2 if p["sh"] == "rect" else max(p["w"], p["h"]) / 2
        clear_disc(p["x"], p["y"], r + POUR_CLR)
    for w in wires:
        if w["layer"] == "B.Cu" and w["net"] != "GND":
            for k in range(len(w["pts"]) - 1):
                clear_seg(w["pts"][k], w["pts"][k + 1], w["w"] / 2 + POUR_CLR)
    for v in vias:
        if v["net"] != "GND":
            clear_disc(v["x"], v["y"], v["d"] / 2 + POUR_CLR)
    # thermal spokes for GND pads, GND wires and vias are part of the pour
    spokes = []
    for p in pads:
        if p["net"] == "GND":
            r = (math.hypot(p["w"], p["h"]) / 2 if p["sh"] == "rect" else max(p["w"], p["h"]) / 2) + POUR_CLR + 0.25
            for ang in (0, 90, 180, 270):
                b = (p["x"] + r * math.cos(math.radians(ang)), p["y"] + r * math.sin(math.radians(ang)))
                spokes.append(((p["x"], p["y"]), b))
    # find which pour pieces reach a GND spoke/wire/via; the rest are islands
    from scipy import ndimage
    lab, n = ndimage.label(m)
    keep = set()
    def touch(x, y):
        i, j = int(round(y / res)), int(round(x / res))
        if 0 <= i < ny and 0 <= j < nx and lab[i, j]:
            keep.add(lab[i, j])
    for a, b in spokes:
        touch(*b)
    for w in wires:
        if w["net"] == "GND" and w["layer"] == "B.Cu":
            for pt in w["pts"]:
                touch(*pt)
    for v in vias:
        if v["net"] == "GND":
            touch(v["x"], v["y"])
    # spokes only count where they actually land in pour; drop spokes ending in a cleared area
    good_spokes = []
    for a, b in spokes:
        i, j = int(round(b[1] / res)), int(round(b[0] / res))
        if 0 <= i < ny and 0 <= j < nx and m[i, j]:
            good_spokes.append((a, b))
    # drop spokes that would pass closer than SPOKE_MIN_CLR to other-net copper on the bottom layer
    def sd(pt, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L))
        return math.hypot(pt[0] - a[0] - t * dx, pt[1] - a[1] - t * dy)
    def clr(a, b):
        best = 9.0
        for q in pads:
            if q["net"] != "GND":
                rq = math.hypot(q["w"], q["h"]) / 2 if q["sh"] == "rect" else max(q["w"], q["h"]) / 2
                best = min(best, sd((q["x"], q["y"]), a, b) - rq)
        for w in wires:
            if w["layer"] == "B.Cu" and w["net"] != "GND":
                for k in range(len(w["pts"]) - 1):
                    c, d = w["pts"][k], w["pts"][k + 1]
                    best = min(best, min(sd(a, c, d), sd(b, c, d), sd(c, a, b), sd(d, a, b)) - w["w"] / 2)
        for v in vias:
            if v["net"] != "GND":
                best = min(best, sd((v["x"], v["y"]), a, b) - v["d"] / 2)
        return best - SPOKE_W / 2
    good_spokes = [(a, b) for a, b in good_spokes if clr(a, b) >= SPOKE_MIN_CLR]
    islands = (lab > 0) & ~np.isin(lab, list(keep))
    return m, islands, good_spokes, res

def contours_of(mask, res, grow=0.08):
    from skimage import measure
    from scipy import ndimage
    if not mask.any():
        return []
    mm = ndimage.binary_dilation(mask, iterations=max(1, int(grow / res)))
    cs = measure.find_contours(np.pad(mm, 1).astype(float), 0.5)
    out = []
    for c in cs:
        pts = [((col - 1) * res, (row - 1) * res) for row, col in c[::2]]
        if len(pts) >= 3:
            out.append(pts)
    return out

# ------------------------------------------------------------------ silkscreen text as filled regions
FONT = FontProperties(family="DejaVu Sans", weight="bold")
def text_regions(s, x, y, size=1.0, ha="center", rot=0):
    """-> list of (dark, polygon) : outer contours dark, holes clear"""
    tp = TextPath((0, 0), s, size=size * 1.37, prop=FONT)
    ext = tp.get_extents()
    ox = {"center": -(ext.x0 + ext.x1) / 2, "left": -ext.x0, "right": -ext.x1}[ha]
    oy = -(ext.y0 + ext.y1) / 2
    polys = tp.to_polygons()
    out = []
    for poly in polys:
        pts = []
        for px, py in poly:
            qx, qy = D.rot(px + ox, py + oy, rot)
            pts.append((x + qx, y + qy))
        area = 0.5 * sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))
        out.append((area < 0, pts))   # matplotlib: outer contours clockwise in this sense
    # make sure the biggest polygon of each glyph is dark (orientation conventions vary)
    return out

def silk_text(g, s, x, y, size=1.0, ha="center", rot=0):
    regs = text_regions(s, x, y, size, ha, rot)
    darks = [p for d, p in regs if d]
    clears = [p for d, p in regs if not d]
    # if orientation came out reversed (no darks, or clears larger), swap
    def area(p): return abs(0.5 * sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p))))
    if sum(area(p) for p in clears) > sum(area(p) for p in darks):
        darks, clears = clears, darks
    for p in darks:
        g.region(p)
    if clears:
        g.polarity(False)
        for p in clears:
            g.region(p)
        g.polarity(True)
    return darks, clears

# ------------------------------------------------------------------ outlines for silk + pictures
def outline_paths(ref, p):
    """list of polylines (world coords) for the part's silkscreen outline"""
    fp = p["fp"]; b = fp["body"]; x, y, r = p["x"], p["y"], p["rot"]
    T = lambda pts: [(x + D.rot(a, c, r)[0], y + D.rot(a, c, r)[1]) for a, c in pts]
    out = []
    if b[0] == "rect":
        w, h = b[1] / 2, b[2] / 2
        out.append(T([(-w, -h), (w, -h), (w, h), (-w, h), (-w, -h)]))
        if fp.get("band"):
            out.append(T([(w - 1.0, -h), (w - 1.0, h)]))
            out.append(T([(w - 1.4, -h), (w - 1.4, h)]))
    elif b[0] == "circle":
        rr = b[1] / 2
        out.append(T([(rr * math.cos(t), rr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 37)]))
        if fp.get("plus"):
            px = fp["pads"][0][1] - 0.2
            out.append(T([(px - 0.5, 1.9), (px + 0.5, 1.9)])); out.append(T([(px, 1.4), (px, 2.4)]))
    elif b[0] == "to92":
        arc = [(2.9 * math.cos(t), 1.0 + 2.9 * math.sin(t)) for t in np.linspace(0, math.pi, 25)]
        out.append(T(arc))
        out.append(T([(-1.7, -1.3), (1.7, -1.3)]))
    elif b[0] == "dip":
        w, h = b[1] / 2, b[2] / 2
        out.append(T([(-w, -h), (w, -h), (w, h), (0.8, h)] + [(0.8 * math.cos(t), h - 0.8 * math.sin(t)) for t in np.linspace(0, math.pi, 13)] + [(-w, h), (-w, -h)]))
        # pin 1 at the notch end on the left: make sure the notch is at the pin-1 end
    elif b[0] == "module":
        n, sep, pitch = b[1], b[2], b[3]
        if n == 24:
            pts = [(1.27, -9.0), (1.27 - 61.0, -9.0), (1.27 - 61.0, 9.0), (1.27, 9.0), (1.27, -9.0)]
        else:
            pts = [(2.4, -9.0), (2.4 - 22.5, -9.0), (2.4 - 22.5, 9.0), (2.4, 9.0), (2.4, -9.0)]
        out.append(T(pts))
    return out

# per-part label positions (ref text) relative to the part: put it beside the body
LABEL_AT = {"L1": (0, 2.3), "L2": (0, 2.3), "C27": (0.6, 2.3), "C29": (0.6, 2.3), "R23": (0, -2.15), "R24": (0, -1.73)}

def label_pos(ref, p):
    if ref in LABEL_AT:   # v1.2: inside the big round parts; under the standing resistors
        return (p["x"] + LABEL_AT[ref][0], p["y"] + LABEL_AT[ref][1], 0)
    b = p["fp"]["body"]
    if ref in ("U4", "U5") or ref.startswith("J"):
        return None
    if b[0] == "rect" and p["rot"] % 180 == 90:
        return (p["x"], p["y"], 90)
    if b[0] == "rect":
        return (p["x"], p["y"], 0)
    if b[0] == "circle":
        r = b[1] / 2
        below = {"C4"}
        return (p["x"], p["y"] - r - 0.9 if ref in below else p["y"] + r + 0.9, 0)
    if ref.startswith("J"):
        return None
    if b[0] == "to92":
        return (p["x"], p["y"] + 3.4, 0)
    if b[0] == "dip":
        return (p["x"], p["y"], 0)
    return (p["x"], p["y"], 0)

HEADER_PINS = {
    "J1": ["+5V", "GND", "BAT"], "J2": ["Q", "VCC", "I", "GND"], "J3": ["GND", "VCC", "SCL", "SDA"],
    "J4": ["GND", "3V3", "SDA", "SCL"], "J5": ["TIP", "RNG", "SLV"]}

def build_silk(pads):
    g = Gerber("F.Silk", "Legend,Top")
    lw = 0.15
    for ref, p in D.P.items():
        for path in outline_paths(ref, p):
            g.track(path, lw)
    # pad lookup
    P = {(q["ref"], q["pin"]): q for q in pads}
    # reference designators
    for ref, p in D.P.items():
        lp = label_pos(ref, p)
        if lp is None:
            continue
        size = 1.0
        silk_text(g, ref, lp[0], lp[1], size, "center", lp[2])
    # header pin names: J1 beside its pins; J2, J3, J5 below (staggered so they fit); J4 above
    for ref, names in HEADER_PINS.items():
        p = D.P[ref]
        for i, nm in enumerate(names):
            q = P[(ref, str(i + 1))]
            if ref == "J1":
                silk_text(g, nm, q["x"] - 1.3, q["y"], 0.9, "right", 0)
            elif p["rot"] == 90:
                silk_text(g, nm, q["x"] + 1.4, q["y"], 0.9, "left", 0)
            else:
                off = 1.75 if i % 2 == 0 else 3.05
                silk_text(g, nm, q["x"], q["y"] + (off if ref == "J4" else -off), 0.9, "center", 0)
        lab = {"J1": "POWER", "J2": "RADAR", "J3": "OLED", "J4": "SENSORS", "J5": "AMMO"}[ref]
        if ref == "J1":
            silk_text(g, ref + " " + lab, p["x"] - 0.2, p["y"] + 5.4, 0.9, "center", 0)
        elif p["rot"] == 90:
            silk_text(g, ref + " " + lab, 1.05, p["y"], 0.8, "center", 90)
        elif ref == "J2":
            silk_text(g, ref + " " + lab, p["x"], p["y"] + 1.95, 0.9, "center", 0)
        elif ref == "J4":
            silk_text(g, ref + " " + lab, p["x"], p["y"] - 2.3, 0.9, "center", 0)
        else:
            silk_text(g, ref + " " + lab, p["x"], p["y"] - 4.4, 0.9, "center", 0)
    # module pin names
    for ref, names_pair, rowmap in (("U5", (D.T_FRONT, D.T_REAR), None), ("U4", (D.E_RIGHT, D.E_LEFT), None)):
        p = D.P[ref]
        for row, names in zip("AB", names_pair):
            for i, nm in enumerate(names):
                q = P[(ref, "%s%d" % (row, i))]
                if ref == "U5":
                    if nm not in ("VIN", "GND", "34", "35", "14", "15", "3.3V") and i not in (0,):
                        continue
                    stag = 1.3 if (row == "A" and i in (1,)) else 0.0
                    dy = (1.75 if row == "B" else -1.75 - stag)
                    silk_text(g, nm, q["x"], q["y"] + dy, 0.9, "center", 0)
                else:
                    dx = 1.4 if row == "B" else -1.4
                    silk_text(g, nm, q["x"] + dx, q["y"], 0.9, "left" if row == "B" else "right", 0)
    silk_text(g, "TEENSY 4.1  (USB this end >)", 38.0, 75.0, 1.2, "center", 0)
    silk_text(g, "CUT VIN-VUSB PADS UNDER TEENSY", 38.0, 72.6, 0.85, "center", 0)
    ux, uy = D.P["U4"]["x"], D.P["U4"]["y"]
    silk_text(g, "ESP32-C3", ux, uy - 6.6, 0.8, "center", 0)
    silk_text(g, "SUPERMINI", ux, uy - 8.1, 0.7, "center", 0)
    silk_text(g, "CHIP SIDE", ux, uy - 10.0, 0.7, "center", 0)
    silk_text(g, "UP", ux, uy - 11.3, 0.7, "center", 0)
    silk_text(g, "USB ^", ux, uy - 3.6, 0.9, "center", 0)
    silk_text(g, "ANTENNA", ux, uy - 16.2, 0.8, "center", 0)
    silk_text(g, "RB BLIPR " + VERSION, 35.0, 88.2, 1.2, "center", 0)
    silk_text(g, "I CHANNEL", 28.0, 36.5, 0.8, "center", 0)
    silk_text(g, "Q CHANNEL", 46.0, 63.6, 0.8, "center", 0)
    # DIP pin-1 dots and TO-92 pin numbers
    for ref in ("U1", "U2"):
        pp = D.P[ref]
        dx, dy = D.rot(-3.81, 3.81 + 1.7, pp["rot"])
        g.circle(pp["x"] + dx, pp["y"] + dy, 0.6)
    q = P[("U3", "1")]
    silk_text(g, "GND IN OUT", D.P["U3"]["x"], D.P["U3"]["y"] - 2.5, 0.9, "center", 0)
    return g

# ------------------------------------------------------------------ write everything
def silk_check(pads):
    """outline lines must stay 0.15 mm clear of every pad (the line is 0.15 wide)."""
    bad = []
    for ref, p in D.P.items():
        for path in outline_paths(ref, p):
            for k in range(len(path) - 1):
                for q in pads:
                    if item_dist(("cap", path[k], path[k + 1], 0.075), geom(q)) < 0.1:
                        bad.append("%s outline over pad %s-%s" % (ref, q["ref"], q["pin"]))
    return sorted(set(bad))

def write_all(pads, wires, vias):
    os.makedirs(os.path.join(OUT, "gerber"), exist_ok=True)
    pre = os.path.join(OUT, "gerber", "rbblipr-")
    # copper top
    gt = Gerber("F.Cu", "Copper,L1,Top")
    for w in wires:
        if w["layer"] == "F.Cu":
            gt.track(w["pts"], w["w"])
    for p in pads:
        pad_flash(gt, p)
    for v in vias:
        gt.circle(v["x"], v["y"], v["d"])
    gt.write(pre + "F_Cu.gtl")
    # copper bottom with GND pour
    m, islands, spokes, res = pour(pads, wires, vias)
    gb = Gerber("B.Cu", "Copper,L2,Bot")
    gb.region([(EDGE_CLR, EDGE_CLR), (D.BOARD_W - EDGE_CLR, EDGE_CLR), (D.BOARD_W - EDGE_CLR, D.BOARD_H - EDGE_CLR), (EDGE_CLR, D.BOARD_H - EDGE_CLR)])
    gb.polarity(False)
    for hx, hy in D.HOLES:
        gb.circle(hx, hy, 2 * D.HOLE_KEEPOUT)
    ax0, ay0, ax1, ay1 = ANTENNA_KEEPOUT
    gb.region([(ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1)])
    for p in pads:
        r = math.hypot(p["w"], p["h"]) / 2 if p["sh"] == "rect" else max(p["w"], p["h"]) / 2
        gb.circle(p["x"], p["y"], 2 * (r + POUR_CLR))
    for w in wires:
        if w["layer"] == "B.Cu" and w["net"] != "GND":
            gb.track(w["pts"], w["w"] + 2 * POUR_CLR)
    for v in vias:
        if v["net"] != "GND":
            gb.circle(v["x"], v["y"], v["d"] + 2 * POUR_CLR)
    for poly in contours_of(islands, res, grow=0.12):   # v1.2: a little wider, so no slivers are left at their edges
        gb.region(poly)
    gb.polarity(True)
    for a, b in spokes:
        gb.track([a, b], SPOKE_W)
    for w in wires:
        if w["layer"] == "B.Cu":
            gb.track(w["pts"], w["w"])
    for p in pads:
        pad_flash(gb, p)
    for v in vias:
        gb.circle(v["x"], v["y"], v["d"])
    gb.write(pre + "B_Cu.gbl")
    # masks (vias tented)
    for side, fn, func in (("F", "F_Mask.gts", "Soldermask,Top"), ("B", "B_Mask.gbs", "Soldermask,Bot")):
        g = Gerber(side, func)
        for p in pads:
            pad_flash(g, p, 0.05)
        for hx, hy in D.HOLES:
            g.circle(hx, hy, D.HOLE_D + 0.2)
        g.write(pre + fn)
    # silk
    build_silk(pads).write(pre + "F_Silk.gto")
    # outline
    ge = Gerber("Edge", "Profile,NP")
    ge.track([(0, 0), (D.BOARD_W, 0), (D.BOARD_W, D.BOARD_H), (0, D.BOARD_H), (0, 0)], 0.1)
    ge.write(pre + "Edge_Cuts.gm1")
    # drills
    def excellon(path, holes, plated):
        tools = sorted({round(d, 2) for _, _, d in holes})
        L = ["M48", "; RB BLIPR main board %s, %s" % (VERSION, "plated" if plated else "non-plated"), "FMAT,2", "METRIC,TZ",
             "; #@! TF.FileFunction,%s,1,2,%s" % ("Plated" if plated else "NonPlated", "PTH" if plated else "NPTH")]
        for i, d in enumerate(tools):
            L.append("T%dC%.3f" % (i + 1, d))
        L.append("%")
        L.append("G90"); L.append("G05")
        for i, d in enumerate(tools):
            L.append("T%d" % (i + 1))
            for x, y, dd in holes:
                if round(dd, 2) == d:
                    L.append("X%.3fY%.3f" % (x, y))
        L.append("M30")
        open(path, "w").write("\n".join(L) + "\n")
    pth = [(p["x"], p["y"], p["dr"]) for p in pads] + [(v["x"], v["y"], v["dr"]) for v in vias]
    excellon(pre + "PTH.drl", pth, True)
    excellon(pre + "NPTH.drl", [(x, y, D.HOLE_D) for x, y in D.HOLES], False)
    return m, islands, spokes, res

def bom(path):
    rows = {}
    for ref, p in D.P.items():
        if ref == "J4":
            key = ("Header, 1x4 FEMALE (the sensor cable ends in male pins; or solder its wires straight in)", "")
        elif ref in ("J2", "J3"):
            key = ("No header: solder the wires straight in (radar J2, screen J3)", "")
        elif ref.startswith("J"):
            key = ("Header, 1x%d male (or solder wires straight in)" % len(p["fp"]["pads"]), "")
        elif ref in ("U4",):
            key = ("Female header 1x8 (socket for the ESP32-C3 SuperMini)", "2 per board")
        elif ref == "U5":
            key = ("Female header 1x24 (socket for the Teensy 4.1)", "2 per board")
        elif ref in ("U1", "U2"):
            key = ("MCP6022-E/P op-amp + DIP-8 socket", "")
        else:
            kind = {"R": "Resistor 1/4 W", "C": "Capacitor", "D": "Schottky diode", "U": "Regulator",
                    "L": "Inductor, radial drum, 1 A or more, up to 8.4 mm across, leads 5 mm or 3.2 mm apart (three holes)"}[ref[0]]
            if ref[0] == "C" and p["fp"]["body"][0] == "circle" and p["fp"]["body"][1] >= 8:
                kind = "Electrolytic capacitor, 10 V or more, 8 mm across, 3.5 mm lead spacing"
            elif ref[0] == "C" and p["fp"]["body"][0] == "circle":
                kind = "Electrolytic capacitor, 10 V or more"
            elif ref[0] == "C":
                kind = "Ceramic capacitor, 5 mm lead spacing"
            key = ("%s %s" % (kind, p["value"]), "stands on end" if p["fp"].get("hairpin") else "")
        rows.setdefault(key, []).append(ref)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Qty", "Part", "References", "Note"])
        for (part, note), refs in sorted(rows.items(), key=lambda kv: kv[1][0]):
            q = len(refs) * (2 if "per board" in note else 1)
            w.writerow([q, part, " ".join(sorted(refs, key=lambda r: (r[0], int(''.join(c for c in r if c.isdigit()) or 0)))), note])
        # Off the board: one resistor on the battery holder. (v1.2 has the two 5 V filters on the board; v1.1 had them in the wiring.)
        w.writerow([1, "Resistor 1/4 W 10k", "R25", "off-board: soldered on the battery holder's + tab (battery gauge)"])

# ------------------------------------------------------------------ pictures
def picture(pads, wires, vias, path, side="top", pour_mask=None, res=0.05, assembly=False):
    fig, ax = plt.subplots(figsize=(8.2, 10.2), dpi=220)
    bg = "#1f5e3a" if side == "top" else "#173f2a"
    ax.add_patch(plt.Rectangle((0, 0), D.BOARD_W, D.BOARD_H, color=bg, zorder=0))
    if pour_mask is not None and not assembly:
        img = np.zeros(pour_mask.shape + (4,))
        img[pour_mask] = (0.85, 0.6, 0.25, 0.35 if side == "top" else 0.75)
        ax.imshow(img, origin="lower", extent=(0, pour_mask.shape[1] * res, 0, pour_mask.shape[0] * res), interpolation="nearest", zorder=0.5)
    order = ["B.Cu", "F.Cu"] if side == "top" else ["F.Cu", "B.Cu"]
    for L in order:
        col = "#e8a33a" if L == "F.Cu" else "#4aa3df"
        alpha = 0.95 if (L == "F.Cu") == (side == "top") else 0.35
        if assembly:
            alpha *= 0.25
        for w in wires:
            if w["layer"] == L:
                xs, ys = zip(*w["pts"])
                ax.plot(xs, ys, color=col, lw=w["w"] * 72 / 25.4 * 150 / 150 * 1.35, solid_capstyle="round", alpha=alpha)
    for v in vias:
        ax.add_patch(plt.Circle((v["x"], v["y"]), v["d"] / 2, color="#ccc"))
        ax.add_patch(plt.Circle((v["x"], v["y"]), v["dr"] / 2, color="k"))
    for p in pads:
        if p["sh"] == "rect":
            ax.add_patch(plt.Rectangle((p["x"] - p["w"] / 2, p["y"] - p["h"] / 2), p["w"], p["h"], color="#d9d9d9"))
        else:
            ax.add_patch(plt.Circle((p["x"], p["y"]), max(p["w"], p["h"]) / 2, color="#d9d9d9"))
        ax.add_patch(plt.Circle((p["x"], p["y"]), p["dr"] / 2, color="#111"))
    for hx, hy in D.HOLES:
        ax.add_patch(plt.Circle((hx, hy), D.HOLE_D / 2, color="white"))
    if side == "top":
        for ref, pp in D.P.items():
            for path_ in outline_paths(ref, pp):
                xs, ys = zip(*path_)
                ax.plot(xs, ys, color="white", lw=0.7)
            lp = label_pos(ref, pp)
            if assembly and ref in ("U1", "U2", "U3"):
                lp = None
            if lp:
                txt = ref + ((" " if ref in ("R23", "R24") else "\n") + pp["value"] if assembly and ref[0] in "RCDL" else "")
                ax.text(lp[0], lp[1], txt, color="white" if not assembly else "#ffe680", fontsize=4.6 if not assembly else 4.4,
                        ha="center", va="center", rotation=lp[2], fontweight="bold", linespacing=0.95)
        if assembly:
            for ref in ("U1", "U2", "U3", "U4", "U5", "J1", "J2", "J3", "J4", "J5"):
                pp = D.P[ref]
                if ref in ("U4", "U5"):
                    ax.text(pp["x"] - (30 if ref == "U5" else -8.0) * (1 if ref == "U5" else 0), pp["y"] - (0 if ref == "U5" else 0),
                            "", fontsize=1)
            ax.text(38, 75, "U5  Teensy 4.1\non 2 x 24 female headers\nUSB to the right edge", color="#ffe680", ha="center", va="center", fontsize=6.5, fontweight="bold")
            ux, uy = D.P["U4"]["x"], D.P["U4"]["y"]
            ax.text(ux, uy - 8.0, "U4\nESP32-C3\nSuperMini\nchip side\nup, USB\nto the back", color="#ffe680", ha="center", va="center", fontsize=4.6, fontweight="bold")
            ax.text(ux, uy - 17.2, "antenna end", color="#ffe680", ha="center", va="center", fontsize=4.2, fontstyle="italic")
            for row, names in (("A", D.E_RIGHT), ("B", D.E_LEFT)):
                for i, nm in enumerate(names):
                    q = [pp_ for pp_ in pads if pp_["ref"] == "U4" and pp_["pin"] == "%s%d" % (row, i)][0]
                    ax.text(q["x"] + (-1.25 if row == "A" else 1.25), q["y"], nm, color="#ffe680", fontsize=4.0, ha="right" if row == "A" else "left", va="center", fontweight="bold")
            for jr in ("J3", "J4", "J5"):
                for i, nm in enumerate(HEADER_PINS[jr]):
                    q = [pp_ for pp_ in pads if pp_["ref"] == jr and pp_["pin"] == str(i + 1)][0]
                    ax.text(q["x"] + 1.3, q["y"], nm, color="#ffe680", fontsize=3.8, ha="left", va="center", fontweight="bold")
            for ref, nm in (("J1", "J1 POWER\n+5V GND BAT\n(pin 1 = square)"), ("J2", "J2 RADAR  Q VCC I GND"), ("J3", "J3 OLED"), ("J4", "J4 SENSORS"), ("J5", "J5 AMMO")):
                pp = D.P[ref]
                if ref in ("J3", "J4", "J5"):
                    n = len(HEADER_PINS[ref])
                    ax.text(1.0, pp["y"] + (n - 1) * 1.27 + 1.6, nm, color="#ffe680", fontsize=4.6, ha="left", va="bottom", fontweight="bold")
                elif ref == "J1":   # v1.2: L1 is right of J1, so the label goes on its left
                    ax.text(pp["x"] - 0.2, pp["y"] + 4.3, "J1 POWER", color="#ffe680", fontsize=4.4, ha="center", va="center", fontweight="bold")
                    for i, pin in enumerate(HEADER_PINS["J1"]):
                        q = [pp_ for pp_ in pads if pp_["ref"] == "J1" and pp_["pin"] == str(i + 1)][0]
                        ax.text(q["x"] - 1.2, q["y"], pin, color="#ffe680", fontsize=3.7, ha="right", va="center", fontweight="bold")
                else:
                    ax.text(pp["x"], pp["y"] - 2.6, nm, color="#ffe680", fontsize=4.8, ha="center", va="top", fontweight="bold")
            ax.text(42, 15.8, "U3", color="#ffe680", ha="center", fontsize=5, fontweight="bold")
            ax.text(36, 43, "U1\nMCP6022", color="#ffe680", ha="center", va="center", fontsize=5.0, fontweight="bold")
            ax.text(56, 43, "U2\nMCP6022", color="#ffe680", ha="center", va="center", fontsize=5.0, fontweight="bold")
    ax.set_xlim(-1, D.BOARD_W + 1)
    if side == "bottom":
        ax.set_xlim(D.BOARD_W + 1, -1)
    if True: ax.set_ylim(-1, D.BOARD_H + 1); ax.set_aspect("equal"); ax.axis("off")
    t = {"top": "Top (component side)", "bottom": "Bottom (seen from below: left and right are swapped)"}[side]
    if assembly:
        t = "Where each part goes (top view, front edge at the bottom)"
    ax.set_title(t, fontsize=10)
    plt.savefig(path, bbox_inches="tight", facecolor="white"); plt.close(fig)

def render_gerbers(path):
    """Draw the Gerber files themselves (a check that what PCBWay gets looks right): parse flashes/tracks/regions simply."""
    pass

if __name__ == "__main__":
    pads, wires, vias = load()
    probs = drc(pads, wires, vias)
    con = connectivity(pads, wires, vias)
    print("DRC problems:", len(probs))
    for p in probs[:40]:
        print("  ", p)
    print("Unconnected nets:", con or "none")
    sc = silk_check(pads)
    print("Silk outline over pads:", sc or "none")
    m, islands, spokes, res = write_all(pads, wires, vias)
    print("islands removed (cells):", int(islands.sum()), " spokes:", len(spokes))
    bom(os.path.join(OUT, "RBBLIPR_BOM.csv"))
    pour_final = m & ~islands
    picture(pads, wires, vias, os.path.join(OUT, "pcb_top.png"), "top", pour_final, res)
    picture(pads, wires, vias, os.path.join(OUT, "pcb_bottom.png"), "bottom", pour_final, res)
    picture(pads, wires, vias, os.path.join(OUT, "pcb_assembly.png"), "top", None, res, assembly=True)
    z = zipfile.ZipFile(os.path.join(OUT, "RBBLIPR_PCB_%s_gerbers.zip" % VERSION), "w", zipfile.ZIP_DEFLATED)
    for fn in sorted(os.listdir(os.path.join(OUT, "gerber"))):
        z.write(os.path.join(OUT, "gerber", fn), fn)
    z.close()
    print("written")
