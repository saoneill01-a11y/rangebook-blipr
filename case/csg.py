"""
Minimal constructive solid geometry (CSG) on polygons using BSP trees.
Port of Evan Wallace's csg.js (MIT license) to plain Python, plus helpers to
build primitives, repair T-junctions, and export STL and STEP (B-rep, planar faces).
No third-party packages are needed.
"""
import math, sys, threading

EPS = 1e-5


class V:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def __add__(s, o): return V(s.x + o.x, s.y + o.y, s.z + o.z)
    def __sub__(s, o): return V(s.x - o.x, s.y - o.y, s.z - o.z)
    def __mul__(s, k): return V(s.x * k, s.y * k, s.z * k)
    def neg(s): return V(-s.x, -s.y, -s.z)
    def dot(s, o): return s.x * o.x + s.y * o.y + s.z * o.z
    def cross(s, o): return V(s.y * o.z - s.z * o.y, s.z * o.x - s.x * o.z, s.x * o.y - s.y * o.x)
    def length(s): return math.sqrt(s.dot(s))
    def unit(s):
        l = s.length()
        return V(s.x / l, s.y / l, s.z / l)
    def lerp(s, o, t): return s + (o - s) * t


class Plane:
    __slots__ = ("n", "w")

    def __init__(self, n, w):
        self.n, self.w = n, w

    @staticmethod
    def from_points(a, b, c):
        n = (b - a).cross(c - a).unit()
        return Plane(n, n.dot(a))

    def flip(self):
        self.n = self.n.neg()
        self.w = -self.w

    def split(self, poly, cofront, coback, front, back):
        COP, FR, BK, SP = 0, 1, 2, 3
        ptype = 0
        types = []
        n, w = self.n, self.w
        for v in poly.verts:
            t = n.dot(v) - w
            ty = BK if t < -EPS else (FR if t > EPS else COP)
            ptype |= ty
            types.append(ty)
        if ptype == COP:
            (cofront if n.dot(poly.plane.n) > 0 else coback).append(poly)
        elif ptype == FR:
            front.append(poly)
        elif ptype == BK:
            back.append(poly)
        else:
            f, b = [], []
            vs = poly.verts
            m = len(vs)
            for i in range(m):
                j = (i + 1) % m
                ti, tj = types[i], types[j]
                vi, vj = vs[i], vs[j]
                if ti != BK:
                    f.append(vi)
                if ti != FR:
                    b.append(vi)
                if (ti | tj) == SP:
                    t = (w - n.dot(vi)) / n.dot(vj - vi)
                    v = vi.lerp(vj, t)
                    f.append(v)
                    b.append(v)
            if len(f) >= 3:
                front.append(Poly(f, poly.plane))
            if len(b) >= 3:
                back.append(Poly(b, poly.plane))


class Poly:
    __slots__ = ("verts", "plane")

    def __init__(self, verts, plane=None):
        self.verts = verts
        self.plane = plane if plane is not None else Plane.from_points(verts[0], verts[1], verts[2])

    def flipped(self):
        return Poly(list(reversed(self.verts)), Plane(self.plane.n.neg(), -self.plane.w))


class Node:
    __slots__ = ("plane", "front", "back", "polys")

    def __init__(self, polys=None):
        self.plane = None
        self.front = None
        self.back = None
        self.polys = []
        if polys:
            self.build(polys)

    def invert(self):
        stack = [self]
        while stack:
            nd = stack.pop()
            nd.polys = [p.flipped() for p in nd.polys]
            if nd.plane:
                nd.plane = Plane(nd.plane.n.neg(), -nd.plane.w)
            nd.front, nd.back = nd.back, nd.front
            if nd.front: stack.append(nd.front)
            if nd.back: stack.append(nd.back)

    def clip_polys(self, polys):
        if self.plane is None:
            return list(polys)
        front, back = [], []
        for p in polys:
            self.plane.split(p, front, back, front, back)
        if self.front:
            front = self.front.clip_polys(front)
        if self.back:
            back = self.back.clip_polys(back)
        else:
            back = []
        return front + back

    def clip_to(self, bsp):
        stack = [self]
        while stack:
            nd = stack.pop()
            nd.polys = bsp.clip_polys(nd.polys)
            if nd.front: stack.append(nd.front)
            if nd.back: stack.append(nd.back)

    def all_polys(self):
        out = []
        stack = [self]
        while stack:
            nd = stack.pop()
            out.extend(nd.polys)
            if nd.front: stack.append(nd.front)
            if nd.back: stack.append(nd.back)
        return out

    def build(self, polys):
        work = [(self, polys)]
        while work:
            nd, ps = work.pop()
            if not ps:
                continue
            if nd.plane is None:
                p0 = ps[0].plane
                nd.plane = Plane(p0.n, p0.w)
            front, back = [], []
            for p in ps:
                nd.plane.split(p, nd.polys, nd.polys, front, back)
            if front:
                if nd.front is None: nd.front = Node()
                work.append((nd.front, front))
            if back:
                if nd.back is None: nd.back = Node()
                work.append((nd.back, back))


class Solid:
    def __init__(self, polys):
        self.polys = polys

    def union(self, o):
        a, b = Node(list(self.polys)), Node(list(o.polys))
        a.clip_to(b); b.clip_to(a); b.invert(); b.clip_to(a); b.invert()
        a.build(b.all_polys())
        return Solid(a.all_polys())

    def subtract(self, o):
        a, b = Node(list(self.polys)), Node(list(o.polys))
        a.invert(); a.clip_to(b); b.clip_to(a); b.invert(); b.clip_to(a); b.invert()
        a.build(b.all_polys()); a.invert()
        return Solid(a.all_polys())

    def intersect(self, o):
        a, b = Node(list(self.polys)), Node(list(o.polys))
        a.invert(); b.clip_to(a); b.invert(); a.clip_to(b); b.clip_to(a)
        a.build(b.all_polys()); a.invert()
        return Solid(a.all_polys())

    def __add__(self, o): return self.union(o)
    def __sub__(self, o): return self.subtract(o)

    def bbox(self):
        xs = [v.x for p in self.polys for v in p.verts]
        ys = [v.y for p in self.polys for v in p.verts]
        zs = [v.z for p in self.polys for v in p.verts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


# ---------------- primitives ----------------

def prism(pts2d, z0, z1):
    """Extrude a convex or concave-free CCW 2D outline (list of (x,y)) from z0 to z1."""
    n = len(pts2d)
    bot = [V(x, y, z0) for x, y in pts2d]
    top = [V(x, y, z1) for x, y in pts2d]
    polys = [Poly(list(reversed(bot))), Poly(top)]
    for i in range(n):
        j = (i + 1) % n
        polys.append(Poly([bot[i], bot[j], top[j], top[i]]))
    return Solid(polys)


def box(x0, y0, z0, x1, y1, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def rrect_pts(x0, y0, x1, y1, r, seg=8):
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    if r == 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
    for cx, cy, a0 in corners:
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rbox(x0, y0, z0, x1, y1, z1, r, seg=8):
    return prism(rrect_pts(x0, y0, x1, y1, r, seg), z0, z1)


def circle_pts(cx, cy, r, seg=40):
    return [(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]


def cyl_z(cx, cy, r, z0, z1, seg=40):
    return prism(circle_pts(cx, cy, r, seg), z0, z1)


def cyl_y(cx, cz, r, y0, y1, seg=40):
    """Cylinder along Y axis (centre x=cx, z=cz)."""
    s = cyl_z(0, 0, r, y0, y1, seg)
    # map (x, y, z) -> (cx + x, z, cz + y): rotation keeps handedness
    out = []
    for p in s.polys:
        vs = [V(cx + v.x, v.z, cz + v.y) for v in p.verts]
        out.append(Poly(list(reversed(vs))))
    return Solid(out)


def union_all(solids):
    solids = list(solids)
    while len(solids) > 1:
        nxt = []
        for i in range(0, len(solids), 2):
            if i + 1 < len(solids):
                nxt.append(solids[i].union(solids[i + 1]))
            else:
                nxt.append(solids[i])
        solids = nxt
    return solids[0]


def run_big_stack(fn):
    """Run fn with a large recursion limit / thread stack (BSP clipping recurses)."""
    sys.setrecursionlimit(1000000)
    threading.stack_size(1024 * 1024 * 1024)
    res = {}
    def target():
        try:
            res["v"] = fn()
        except BaseException as e:
            res["e"] = e
    t = threading.Thread(target=target)
    t.start(); t.join()
    if "e" in res:
        raise res["e"]
    return res["v"]


# ---------------- mesh clean-up ----------------

def clean_mesh(solid, q=1e-4):
    """Weld vertices, insert T-junction vertices, drop degenerate polygons.
    Returns (points[list of (x,y,z)], faces[list of index lists], planes[list of (n,w)])."""
    key_to_idx = {}
    pts = []

    def idx(v):
        k = (round(v.x / q), round(v.y / q), round(v.z / q))
        i = key_to_idx.get(k)
        if i is None:
            i = len(pts)
            key_to_idx[k] = i
            pts.append((v.x, v.y, v.z))
        return i

    faces, planes = [], []
    for p in solid.polys:
        f = []
        for v in p.verts:
            i = idx(v)
            if not f or f[-1] != i:
                f.append(i)
        while len(f) > 1 and f[0] == f[-1]:
            f.pop()
        if len(f) >= 3:
            faces.append(f)
            planes.append(((p.plane.n.x, p.plane.n.y, p.plane.n.z), p.plane.w))

    # spatial hash of points for T-junction search
    cell = 2.0
    grid = {}
    for i, (x, y, z) in enumerate(pts):
        grid.setdefault((int(math.floor(x / cell)), int(math.floor(y / cell)), int(math.floor(z / cell))), []).append(i)

    def points_on_segment(a, b):
        ax, ay, az = pts[a]; bx, by, bz = pts[b]
        dx, dy, dz = bx - ax, by - ay, bz - az
        L2 = dx * dx + dy * dy + dz * dz
        if L2 < 1e-12:
            return []
        mnx, mny, mnz = min(ax, bx), min(ay, by), min(az, bz)
        mxx, mxy, mxz = max(ax, bx), max(ay, by), max(az, bz)
        out = []
        for gx in range(int(math.floor(mnx / cell)) , int(math.floor(mxx / cell)) + 1):
            for gy in range(int(math.floor(mny / cell)), int(math.floor(mxy / cell)) + 1):
                for gz in range(int(math.floor(mnz / cell)), int(math.floor(mxz / cell)) + 1):
                    for i in grid.get((gx, gy, gz), ()):
                        if i == a or i == b:
                            continue
                        px, py, pz = pts[i]
                        t = ((px - ax) * dx + (py - ay) * dy + (pz - az) * dz) / L2
                        if t <= 1e-7 or t >= 1 - 1e-7:
                            continue
                        cx, cy, cz = ax + dx * t - px, ay + dy * t - py, az + dz * t - pz
                        if cx * cx + cy * cy + cz * cz < (5 * q) ** 2:
                            out.append((t, i))
        out.sort()
        return [i for _, i in out]

    seg_cache = {}
    new_faces = []
    for f in faces:
        nf = []
        m = len(f)
        for k in range(m):
            a, b = f[k], f[(k + 1) % m]
            nf.append(a)
            key = (a, b)
            if key not in seg_cache:
                rk = (b, a)
                if rk in seg_cache:
                    seg_cache[key] = list(reversed(seg_cache[rk]))
                else:
                    seg_cache[key] = points_on_segment(a, b)
            nf.extend(seg_cache[key])
        new_faces.append(nf)
    return pts, new_faces, planes


def edge_report(faces):
    from collections import Counter
    c = Counter()
    for f in faces:
        m = len(f)
        for k in range(m):
            c[(f[k], f[(k + 1) % m])] += 1
    bad = 0
    for (a, b), n in c.items():
        if n != 1 or c.get((b, a), 0) != 1:
            bad += 1
    return bad, len(c)


# ---------------- export ----------------

def tri_fan(face):
    return [(face[0], face[k], face[k + 1]) for k in range(1, len(face) - 1)]


def write_stl(path, pts, faces, planes, name="part"):
    import struct
    tris = []
    for f, (n, w) in zip(faces, planes):
        for t in tri_fan(f):
            tris.append((n, t))
    with open(path, "wb") as fh:
        fh.write(name.encode()[:80].ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        for n, (a, b, c) in tris:
            fh.write(struct.pack("<3f", *n))
            for i in (a, b, c):
                fh.write(struct.pack("<3f", *pts[i]))
            fh.write(b"\x00\x00")
    return len(tris)


def merge_coplanar(pts, faces, planes):
    """Merge edge-connected coplanar faces into single faces (outer loop + hole loops).
    Returns list of (loops, plane) where loops[0] is the outer loop."""
    from collections import defaultdict
    key = lambda pl: (round(pl[0][0], 4), round(pl[0][1], 4), round(pl[0][2], 4), round(pl[1], 3))
    edge_owner = {}
    for fi, f in enumerate(faces):
        for k in range(len(f)):
            edge_owner[(f[k], f[(k + 1) % len(f)])] = fi
    # union-find over faces sharing an edge and a plane
    parent = list(range(len(faces)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for (a, b), fi in edge_owner.items():
        fj = edge_owner.get((b, a))
        if fj is not None and key(planes[fi]) == key(planes[fj]):
            ra, rb = find(fi), find(fj)
            if ra != rb:
                parent[ra] = rb
    groups = defaultdict(list)
    for fi in range(len(faces)):
        groups[find(fi)].append(fi)
    out = []
    for g, members in groups.items():
        pl = planes[members[0]]
        if len(members) == 1:
            out.append(([faces[members[0]]], pl))
            continue
        es = set()
        for fi in members:
            f = faces[fi]
            for k in range(len(f)):
                es.add((f[k], f[(k + 1) % len(f)]))
        bnd = [(a, b) for (a, b) in es if (b, a) not in es]
        nxt = defaultdict(list)
        for a, b in bnd:
            nxt[a].append(b)
        if any(len(v) != 1 for v in nxt.values()):
            out.extend(([faces[fi]], pl) for fi in members)   # pinch point: keep unmerged
            continue
        loops, seen = [], set()
        for a, _ in bnd:
            if a in seen:
                continue
            loop, cur = [], a
            while cur not in seen:
                seen.add(cur); loop.append(cur); cur = nxt[cur][0]
            loops.append(loop)
        # outer loop = largest projected area with positive orientation along the normal
        n = pl[0]
        def area(loop):
            sx = sy = sz = 0.0
            for k in range(len(loop)):
                p, q = pts[loop[k]], pts[loop[(k + 1) % len(loop)]]
                sx += p[1] * q[2] - p[2] * q[1]; sy += p[2] * q[0] - p[0] * q[2]; sz += p[0] * q[1] - p[1] * q[0]
            return (sx * n[0] + sy * n[1] + sz * n[2]) / 2
        loops.sort(key=lambda l: -area(l))
        if area(loops[0]) <= 0 or any(area(l) >= 0 for l in loops[1:]):
            out.extend(([faces[fi]], pl) for fi in members)
            continue
        out.append((loops, pl))
    return out


def write_step(path, pts, faces, planes, name="part"):
    """Write a closed B-rep (MANIFOLD_SOLID_BREP) with planar faces, AP214.
    Requires every directed edge to have exactly one opposite (checked by caller)."""
    lines = []
    nid = [0]

    def ent(s):
        nid[0] += 1
        lines.append("#%d=%s;" % (nid[0], s))
        return nid[0]

    def f(x):
        s = repr(float(round(x, 6)))
        if "e" in s or "E" in s:
            s = "%.6f" % x
        if "." not in s:
            s += "."
        return s

    app = ent("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
    ent("APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#%d)" % app)
    pc = ent("PRODUCT_CONTEXT('',#%d,'mechanical')" % app)
    prod = ent("PRODUCT('%s','%s','',(#%d))" % (name, name, pc))
    pdf = ent("PRODUCT_DEFINITION_FORMATION('','',#%d)" % prod)
    pdc = ent("PRODUCT_DEFINITION_CONTEXT('part definition',#%d,'design')" % app)
    pd = ent("PRODUCT_DEFINITION('design','',#%d,#%d)" % (pdf, pdc))
    pds = ent("PRODUCT_DEFINITION_SHAPE('','',#%d)" % pd)
    ent("PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#%d))" % prod)
    lu = ent("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
    au = ent("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
    su = ent("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
    unc = ent("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-05),#%d,'distance_accuracy_value','confusion accuracy')" % lu)
    ctx = ent("(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#%d))GLOBAL_UNIT_ASSIGNED_CONTEXT((#%d,#%d,#%d))REPRESENTATION_CONTEXT('Context3D','3D Context with UNIT and UNCERTAINTY'))" % (unc, lu, au, su))
    o = ent("CARTESIAN_POINT('',(0.,0.,0.))")
    dz = ent("DIRECTION('',(0.,0.,1.))")
    dx = ent("DIRECTION('',(1.,0.,0.))")
    origin = ent("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)" % (o, dz, dx))

    vp = {}
    def vertex(i):
        if i not in vp:
            cp = ent("CARTESIAN_POINT('',(%s,%s,%s))" % tuple(f(c) for c in pts[i]))
            vp[i] = ent("VERTEX_POINT('',#%d)" % cp)
        return vp[i]

    edges = {}
    def edge(a, b):
        # one EDGE_CURVE per undirected edge, oriented a->b when created
        k = (min(a, b), max(a, b))
        if k not in edges:
            pa, pb = pts[a], pts[b]
            d = [pb[j] - pa[j] for j in range(3)]
            L = math.sqrt(sum(x * x for x in d))
            d = [x / L for x in d]
            cp = ent("CARTESIAN_POINT('',(%s,%s,%s))" % tuple(f(c) for c in pa))
            dr = ent("DIRECTION('',(%s,%s,%s))" % tuple(f(c) for c in d))
            vec = ent("VECTOR('',#%d,1.)" % dr)
            ln = ent("LINE('',#%d,#%d)" % (cp, vec))
            ec = ent("EDGE_CURVE('',#%d,#%d,#%d,.T.)" % (vertex(a), vertex(b), ln))
            edges[k] = (ec, a, b)
        ec, ea, eb = edges[k]
        return ent("ORIENTED_EDGE('',*,*,#%d,%s)" % (ec, ".T." if (ea == a and eb == b) else ".F."))

    face_ids = []
    for loops, (n, w) in merge_coplanar(pts, faces, planes):
        bounds = []
        for li, fc in enumerate(loops):
            oes = [edge(fc[k], fc[(k + 1) % len(fc)]) for k in range(len(fc))]
            loop = ent("EDGE_LOOP('',(%s))" % ",".join("#%d" % e for e in oes))
            bounds.append(ent("%s('',#%d,.T.)" % ("FACE_OUTER_BOUND" if li == 0 else "FACE_BOUND", loop)))
        p0 = pts[loops[0][0]]
        cp = ent("CARTESIAN_POINT('',(%s,%s,%s))" % tuple(f(c) for c in p0))
        nd = ent("DIRECTION('',(%s,%s,%s))" % tuple(f(c) for c in n))
        # reference direction perpendicular to n
        ref = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
        rx = (ref[0] - n[0] * (ref[0] * n[0] + ref[1] * n[1] + ref[2] * n[2]),
              ref[1] - n[1] * (ref[0] * n[0] + ref[1] * n[1] + ref[2] * n[2]),
              ref[2] - n[2] * (ref[0] * n[0] + ref[1] * n[1] + ref[2] * n[2]))
        L = math.sqrt(sum(x * x for x in rx)); rx = tuple(x / L for x in rx)
        rd = ent("DIRECTION('',(%s,%s,%s))" % tuple(f(c) for c in rx))
        ax = ent("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)" % (cp, nd, rd))
        pl = ent("PLANE('',#%d)" % ax)
        face_ids.append(ent("ADVANCED_FACE('',(%s),#%d,.T.)" % (",".join("#%d" % b for b in bounds), pl)))

    shell = ent("CLOSED_SHELL('',(%s))" % ",".join("#%d" % i for i in face_ids))
    brep = ent("MANIFOLD_SOLID_BREP('%s',#%d)" % (name, shell))
    rep = ent("ADVANCED_BREP_SHAPE_REPRESENTATION('',(#%d,#%d),#%d)" % (origin, brep, ctx))
    ent("SHAPE_DEFINITION_REPRESENTATION(#%d,#%d)" % (pds, rep))

    header = (
        "ISO-10303-21;\nHEADER;\n"
        "FILE_DESCRIPTION(('%s'),'2;1');\n"
        "FILE_NAME('%s','2026-10-19T00:00:00',(''),(''),'csg.py','csg.py','');\n"
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n" % (name, name)
    )
    with open(path, "w") as fh:
        fh.write(header)
        fh.write("\n".join(lines))
        fh.write("\nENDSEC;\nEND-ISO-10303-21;\n")
    return len(face_ids)
