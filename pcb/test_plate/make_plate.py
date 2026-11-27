"""3D-printable hole-check plate for the RB BLIPR PCB v1.2: the board outline and every component hole, nothing else.
Holes print a little bigger than drilled, because FDM printers make small holes undersize.
A triangle cut through the plate points at the FRONT (radar) edge and sits the right way up when you look at the TOP."""
import os, sys, re, math
import numpy as np
from scipy.spatial import Delaunay
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "case"))
import csg

HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "gerber", "rbblipr-")
W, H, T = 70.0, 90.0, 1.6     # same as the real board (1.6 mm)
GROW = 0.30                   # printed hole = drill + this
SKIP_BELOW = 0.5              # vias (0.3 mm) carry no part: left out

def read_drl(path):
    tools, cur, out = {}, None, []
    for ln in open(path):
        ln = ln.strip()
        m = re.match(r"T(\d+)C([\d.]+)", ln)
        if m: tools[m.group(1)] = float(m.group(2)); continue
        m = re.match(r"T(\d+)$", ln)
        if m: cur = tools[m.group(1)]; continue
        m = re.match(r"X([-\d.]+)Y([-\d.]+)", ln)
        if m: out.append((float(m.group(1)), float(m.group(2)), cur))
    return out

holes = [h for h in read_drl(G + "PTH.drl") + read_drl(G + "NPTH.drl") if h[2] >= SKIP_BELOW]

def densify(loop, step):
    out = []
    for i in range(len(loop)):
        (x0, y0), (x1, y1) = loop[i], loop[(i + 1) % len(loop)]
        n = max(1, int(math.ceil(math.hypot(x1 - x0, y1 - y0) / step)))
        out += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    return out

def inside(pt, loop):
    x, y = pt; c = False
    for i in range(len(loop)):
        (x0, y0), (x1, y1) = loop[i], loop[(i + 1) % len(loop)]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c

def main():
    # arrow spot: clear of every hole, near the middle
    def free(cx, cy, r): return all(math.hypot(x - cx, y - cy) > r + d / 2 + 1.0 for x, y, d in holes)
    spots = [(x, y) for y in range(10, 82) for x in range(8, 63) if free(x, y, 4.5)]
    ax, ay = min(spots, key=lambda p: abs(p[0] - 35) + abs(p[1] - 45))
    outer = densify([(0, 0), (W, 0), (W, H), (0, H)], 0.5)                     # CCW
    hole_loops = []
    for x, y, d in holes:
        r = (d + GROW) / 2; seg = 48 if d > 2 else 16
        hole_loops.append([(x + r * math.cos(2 * math.pi * k / seg), y + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)])
    hole_loops.append(densify([(ax, ay - 3.5), (ax + 3.0, ay + 2.5), (ax - 3.0, ay + 2.5)], 0.25))   # points toward y=0 (front)
    loops = [outer] + hole_loops
    pts2 = [p for L in loops for p in L]
    idx, k = [], 0
    for L in loops:
        idx.append(list(range(k, k + len(L)))); k += len(L)
    tri = Delaunay(np.array(pts2))
    keep = []
    for a, b, c in tri.simplices:
        cx = (pts2[a][0] + pts2[b][0] + pts2[c][0]) / 3; cy = (pts2[a][1] + pts2[b][1] + pts2[c][1]) / 3
        if any(inside((cx, cy), L) for L in hole_loops): continue
        if (pts2[b][0] - pts2[a][0]) * (pts2[c][1] - pts2[a][1]) - (pts2[b][1] - pts2[a][1]) * (pts2[c][0] - pts2[a][0]) < 0:
            b, c = c, b
        keep.append((a, b, c))
    n = len(pts2)
    pts = [(x, y, 0.0) for x, y in pts2] + [(x, y, T) for x, y in pts2]
    faces = [[a + n, b + n, c + n] for a, b, c in keep] + [[a, c, b] for a, b, c in keep]
    # walls: outer loop CCW faces out; hole loops (CCW) face inward to the hole
    for li, L in enumerate(idx):
        m = len(L)
        for i in range(m):
            p, q = L[i], L[(i + 1) % m]
            faces.append([p, q, q + n, p + n] if li == 0 else [q, p, p + n, q + n])
    planes = []
    for f in faces:
        P = [np.array(pts[i]) for i in f[:3]]
        nn = np.cross(P[1] - P[0], P[2] - P[0]); nn /= np.linalg.norm(nn)
        planes.append((tuple(nn), float(nn @ P[0])))
    bad, total = csg.edge_report(faces)
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    name = "RBBLIPR_PCB_v1.2_hole_check"
    nt = csg.write_stl(os.path.join(out, name + ".stl"), pts, faces, planes, name)
    if bad == 0:
        csg.write_step(os.path.join(out, name + ".step"), pts, faces, planes, name)
    print("holes %d (sizes %s), arrow at (%d, %d), triangles %d, unpaired edges %d/%d"
          % (len(holes), sorted({h[2] for h in holes}), ax, ay, nt, bad, total))
    return bad

if __name__ == "__main__":
    sys.exit(1 if csg.run_big_stack(main) else 0)
