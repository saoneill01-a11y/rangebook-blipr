"""Independent check: read the Gerber/drill files back (not the design data) and draw them, like a fab's viewer would."""
import re, sys, os, math
from PIL import Image, ImageDraw

PX = 20.0   # pixels per mm
W, H = 70.0, 90.0

def render(path, w=W, h=H):
    img = Image.new("L", (int(w * PX) + 1, int(h * PX) + 1), 0)
    d = ImageDraw.Draw(img)
    s = open(path).read()
    ap = {}
    for m in re.finditer(r"%ADD(\d+)([CRO]),([\d.]+)(?:X([\d.]+))?\*%", s):
        ap[int(m.group(1))] = (m.group(2), float(m.group(3)), float(m.group(4)) if m.group(4) else None)
    cur, x, y, dark, region, rpts = None, 0.0, 0.0, True, False, []
    T = lambda xx, yy: (xx * PX, (h - yy) * PX)
    col = lambda: 255 if dark else 0
    body = s.split("\n")
    for line in body:
        line = line.strip()
        if line.startswith("%LP"):
            dark = line[3] == "D"; continue
        if line.startswith("%") or line.startswith("G04") or not line:
            continue
        if line == "G36*":
            region, rpts = True, []; continue
        if line == "G37*":
            if len(rpts) >= 3:
                d.polygon([T(*p) for p in rpts], fill=col())
            region = False; continue
        m = re.match(r"^D(\d+)\*$", line)
        if m and int(m.group(1)) >= 10:
            cur = int(m.group(1)); continue
        m = re.match(r"^X(-?\d+)Y(-?\d+)D0([123])\*$", line)
        if not m:
            continue
        nx, ny, op = int(m.group(1)) / 1e6, int(m.group(2)) / 1e6, m.group(3)
        if region:
            if op == "2":
                if len(rpts) >= 3:
                    d.polygon([T(*p) for p in rpts], fill=col())
                rpts = [(nx, ny)]
            else:
                rpts.append((nx, ny))
            x, y = nx, ny
            continue
        a = ap.get(cur)
        if op == "3" and a:
            cx, cy = T(nx, ny)
            if a[0] == "C":
                r = a[1] / 2 * PX
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col())
            elif a[0] == "R":
                d.rectangle([cx - a[1] / 2 * PX, cy - a[2] / 2 * PX, cx + a[1] / 2 * PX, cy + a[2] / 2 * PX], fill=col())
            else:
                ww, hh = a[1] / 2 * PX, a[2] / 2 * PX
                rr = min(ww, hh)
                d.rounded_rectangle([cx - ww, cy - hh, cx + ww, cy + hh], radius=rr, fill=col())
        elif op == "1" and a:
            r = a[1] / 2 * PX
            p0, p1 = T(x, y), T(nx, ny)
            d.line([p0, p1], fill=col(), width=max(1, int(round(a[1] * PX))))
            for p in (p0, p1):
                d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col())
        x, y = nx, ny
    return img

def drills(path, h=H):
    holes = []
    tools = {}
    t = None
    for line in open(path):
        line = line.strip()
        m = re.match(r"^T(\d+)C([\d.]+)$", line)
        if m:
            tools[m.group(1)] = float(m.group(2)); continue
        m = re.match(r"^T(\d+)$", line)
        if m:
            t = tools[m.group(1)]; continue
        m = re.match(r"^X([-\d.]+)Y([-\d.]+)$", line)
        if m:
            holes.append((float(m.group(1)), float(m.group(2)), t))
    return holes

def composite(gdir, out, side="top"):
    pre = os.path.join(gdir, "rbblipr-")
    cu = render(pre + ("F_Cu.gtl" if side == "top" else "B_Cu.gbl"))
    mask = render(pre + ("F_Mask.gts" if side == "top" else "B_Mask.gbs"))
    silk = render(pre + "F_Silk.gto") if side == "top" else None
    sz = cu.size
    rgb = Image.new("RGB", sz, (20, 70, 40))
    px = rgb.load(); c = cu.load(); m = mask.load(); s = silk.load() if silk else None
    for j in range(sz[1]):
        for i in range(sz[0]):
            if c[i, j]:
                px[i, j] = (215, 175, 60) if m[i, j] else (60, 120, 70)    # bare copper (gold) where the mask opens
            if s and s[i, j] and not m[i, j]:
                px[i, j] = (245, 245, 245)
    d = ImageDraw.Draw(rgb)
    for f in ("PTH.drl", "NPTH.drl"):
        for x, y, t in drills(pre + f):
            cx, cy = x * PX, (H - y) * PX; r = t / 2 * PX
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0))
    if side == "bottom":
        rgb = rgb.transpose(Image.FLIP_LEFT_RIGHT)
    rgb.save(out)

if __name__ == "__main__":
    g = sys.argv[1] if len(sys.argv) > 1 else "out/gerber"
    composite(g, "out/gerber_view_top.png", "top")
    composite(g, "out/gerber_view_bottom.png", "bottom")
    print("ok")
