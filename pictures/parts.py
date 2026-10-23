"""Drawing kit for picture-style wiring diagrams: boards and parts drawn to look like the real thing,
with every pin labelled, and wires drawn as coloured curves. Units are arbitrary 'mm' on a big canvas."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, PathPatch, Ellipse, Wedge
from matplotlib.path import Path

INK = "#1d1d1d"
FONT = "DejaVu Sans"
plt.rcParams["font.family"] = FONT

WIRE = {  # colour per kind of connection
    "5V": "#d62728", "GND": "#202020", "3V3": "#ff8c00", "3V3A": "#ff8c00", "3V3OP": "#e0a000", "BAT": "#8c2d04",
    "I": "#2ca02c", "Q": "#1f77b4", "TX": "#e6c200", "RX": "#9467bd", "SDA": "#1f77b4", "SCL": "#e6c200",
    "SENSE": "#a0522d", "VCO": "#7f7f7f", "VREF": "#17becf", "SIG": "#2ca02c", "DATA": "#e6c200",
}

def canvas(w, h, title=None, sub=None, dpi=170):
    fig = plt.figure(figsize=(w / 25.4, h / 25.4), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), w, h, color="white", zorder=-10))
    if title:
        ax.text(6, h - 7, title, fontsize=17, fontweight="bold", va="top", color=INK)
    if sub:
        ax.text(6, h - 17, sub, fontsize=10.5, va="top", color="#444", wrap=True)
    return fig, ax

def save(fig, path):
    fig.savefig(path, dpi=fig.dpi, facecolor="white")
    plt.close(fig)

def label(ax, x, y, s, size=8.5, color=INK, ha="center", va="center", box=False, bold=False, rot=0, z=20, fc="white", ec="#999"):
    kw = {}
    if box:
        kw["bbox"] = dict(boxstyle="round,pad=0.25", fc=fc, ec=ec, lw=0.6)
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight="bold" if bold else "normal", rotation=rot, zorder=z, **kw)

def board(ax, x, y, w, h, color, r=1.5, ec=None, z=1, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%g" % r, fc=color, ec=ec or "#00000055", lw=lw, zorder=z))

def pin(ax, x, y, name=None, side="up", color="#d9b24a", hi=False, size=7, r=0.9, z=6, lbl_color=None, dist=2.6):
    ax.add_patch(Circle((x, y), r * (1.35 if hi else 1), fc=color if not hi else "#ffd34d", ec="#5c4a12" if not hi else "#d62728", lw=0.6 if not hi else 1.6, zorder=z))
    ax.add_patch(Circle((x, y), r * 0.45, fc="#3a3a3a", zorder=z + 0.1))
    if name:
        if hi:   # used pins: name goes on the other side (wires leave on the outside), boxed so it reads over the board
            side = {"up": "down", "down": "up", "left": "right", "right": "left"}[side]
        dx, dy, ha, va, rot = {"up": (0, dist, "center", "bottom", 90), "down": (0, -dist, "center", "top", 90),
                               "left": (-dist, 0, "right", "center", 0), "right": (dist, 0, "left", "center", 0)}[side]
        kw = dict(bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#d62728", lw=0.6)) if hi else {}
        ax.text(x + dx, y + dy, name, fontsize=size, ha=ha, va=va, rotation=rot, zorder=z + 10 if hi else z + 1,
                color=lbl_color or ("#b00000" if hi else "#f2f2f2"), fontweight="bold" if hi else "normal", **kw)
    return (x, y)

def wire(ax, a, b, kind="SIG", via=None, lw=2.6, text=None, tpos=0.5, z=8, bend=0.0, style="-", tsize=7.5, straight=False):
    """a, b: points. via: list of extra points (smooth curve through them). bend: sideways bulge of a plain curve."""
    col = WIRE.get(kind, kind)
    pts = [a] + (via or []) + [b]
    if straight:
        xs = np.array([p[0] for p in pts], float); ys = np.array([p[1] for p in pts], float)
    elif len(pts) == 2:
        (x0, y0), (x1, y1) = a, b
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = -(y1 - y0), (x1 - x0)
        L = math.hypot(nx, ny) or 1
        c = (mx + nx / L * bend, my + ny / L * bend)
        t = np.linspace(0, 1, 60)
        xs = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * c[0] + t ** 2 * x1
        ys = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * c[1] + t ** 2 * y1
    else:
        # Catmull-Rom through the points
        P = np.array(pts, float)
        P = np.vstack([P[0], P, P[-1]])
        xs, ys = [], []
        for i in range(1, len(P) - 2):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            for t in np.linspace(0, 1, 25):
                q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
                xs.append(q[0]); ys.append(q[1])
        xs, ys = np.array(xs), np.array(ys)
    ax.plot(xs, ys, color="white", lw=lw + 2.2, solid_capstyle="round", zorder=z - 0.1)
    ax.plot(xs, ys, color=col, lw=lw, solid_capstyle="round", zorder=z, ls=style)
    for p in (a, b):
        ax.add_patch(Circle(p, 0.75, fc=col, ec="white", lw=0.6, zorder=z + 0.2))
    if text:
        k = int(tpos * (len(xs) - 1))
        label(ax, xs[k], ys[k], text, size=tsize, box=True, ec=col, z=z + 1)
    return xs, ys

# ------------------------------------------------------------------ modules
def teensy(ax, x, y, s=1.0, hi=(), usb="right", names=True, fs=None):
    """Teensy 4.1 top view, 61 x 18. Returns {pin label: (x, y)} for both edge rows.
    usb='right': USB at the right; the rear row (GND,0,1,...) is at the top."""
    W, H = 61 * s, 18 * s
    board(ax, x, y, W, H, "#2e7d32", r=1.2 * s, z=2)
    # USB micro-B
    ux = x + W - 1 * s if usb == "right" else x - 6 * s
    ax.add_patch(Rectangle((ux, y + H / 2 - 4 * s), 7 * s, 8 * s, fc="#c8c8c8", ec="#666", zorder=3))
    ax.add_patch(Rectangle((x + 22 * s, y + 5 * s), 10 * s, 10 * s, fc="#151515", zorder=3))
    label(ax, x + 27 * s, y + 10 * s, "i.MX\nRT1062", size=5.5 * s, color="#999")
    ax.add_patch(Rectangle((x - 0.5 * s, y + 3 * s), 12 * s, 12 * s, fc="#b0b0b0", ec="#555", zorder=3))
    label(ax, x + 5.5 * s, y + 9 * s, "microSD", size=5.5 * s, color="#333")
    ax.add_patch(Rectangle((x + 40 * s, y + 6.5 * s), 5 * s, 3 * s, fc="#f2f2f2", ec="#555", zorder=3))
    label(ax, x + 42.5 * s, y + 4.8 * s, "PGM", size=4.5 * s, color="#ddd")
    label(ax, x + 33 * s, y + H - 3.3 * s, "TEENSY 4.1", size=7.5 * s, color="white", bold=True)
    rear = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "3.3V", "24", "25", "26", "27", "28", "29", "30", "31", "32"]
    front = ["VIN", "GND", "3.3V", "23", "22", "21", "20", "19", "18", "17", "16", "15", "14", "13", "GND", "41", "40", "39", "38", "37", "36", "35", "34", "33"]
    pins = {}
    for i in range(24):
        px = x + W - (1.27 + i * 2.54) * s
        for row, lst, py, side in (("rear", rear, y + H - 1.3 * s, "up"), ("front", front, y + 1.3 * s, "down")):
            nm = lst[i]
            key = nm if nm not in pins else nm + "#%s%d" % (row[0], i)
            h = nm in hi and (nm != "GND" or (row, i) in (("rear", 0), ("front", 1)))
            pin(ax, px, py, nm if names else None, side, hi=h, size=fs or 5.6 * s, r=0.75 * s, lbl_color="#c00000" if h else "#333", dist=2.0 * s)
            pins[key] = (px, py)
            pins["%s:%d" % (row, i)] = (px, py)
    return pins

def esp32c3(ax, x, y, s=1.0, hi=(), names=True, fs=None):
    """ESP32-C3 SuperMini seen from the CHIP side (the way it plugs into the board), USB at the TOP, 18 wide x 22.5 tall.
    Left column 5,6,7,8,9,10,20,21 from the USB end; right column 5V,GND,3V3,4,3,2,1,0.
    (The names are printed on the underside, where they read the other way round.)"""
    W, H = 18 * s, 22.5 * s
    board(ax, x, y, W, H, "#1b1b1b", r=1.0 * s, z=2)
    ax.add_patch(Rectangle((x + W / 2 - 4.5 * s, y + H - 2.5 * s), 9 * s, 4.2 * s, fc="#c8c8c8", ec="#666", zorder=3))
    label(ax, x + W / 2, y + H + 3.0 * s, "USB-C", size=6 * s, color="#555")
    ax.add_patch(Rectangle((x + W / 2 - 3.5 * s, y + 8.5 * s), 7 * s, 7 * s, fc="#2a2a2a", ec="#777", zorder=3))
    label(ax, x + W / 2, y + 12 * s, "C3", size=6 * s, color="#bbb")
    ax.add_patch(Rectangle((x + W / 2 - 3 * s, y + 0.8 * s), 6 * s, 2.2 * s, fc="#e8e8e8", ec="#999", zorder=3))
    label(ax, x + W / 2, y + 4.3 * s, "antenna", size=4.8 * s, color="#aaa")
    for bx, nm in ((x + 4 * s, "BOOT"), (x + W - 4 * s, "RST")):
        ax.add_patch(Rectangle((bx - 1.5 * s, y + H - 7.5 * s), 3 * s, 2.2 * s, fc="#ddd", ec="#777", zorder=3))
        label(ax, bx, y + H - 9.1 * s, nm, size=4.3 * s, color="#bbb")
    L = ["5", "6", "7", "8", "9", "10", "20", "21"]
    R = ["5V", "GND", "3V3", "4", "3", "2", "1", "0"]
    pins = {}
    for i in range(8):
        py = y + H - 2.4 * s - 2.54 * i * s - 1.0 * s
        pins[L[i]] = pin(ax, x + 1.3 * s, py, L[i] if names else None, "left", hi=L[i] in hi, size=fs or 6.2 * s, r=0.75 * s, lbl_color="#c00000" if L[i] in hi else "#333", dist=2.0 * s)
        pins[R[i]] = pin(ax, x + W - 1.3 * s, py, R[i] if names else None, "right", hi=R[i] in hi, size=fs or 6.2 * s, r=0.75 * s, lbl_color="#c00000" if R[i] in hi else "#333", dist=2.0 * s)
    return pins

def radar(ax, x, y, s=1.0, back=True, top=False):
    """K-LC5 seen from the back (component side) with its 5-pin header along the bottom edge (top=True: along the top). 25 x 25."""
    W = 25 * s
    board(ax, x, y, W, W, "#26508a", r=0.8 * s, z=2)
    cy = y + (8 if top else 9) * s
    ax.add_patch(Rectangle((x + 4 * s, cy), 17 * s, 10 * s, fc="#cfcfcf", ec="#777", zorder=3))
    label(ax, x + W / 2, cy + 5 * s, "K-LC5\nback side", size=6.5 * s, color="#333")
    names = {1: "1  Q", 2: "2  VCC", 3: "3  I", 4: "4  GND", 5: "5  VCO"}
    pins = {}
    for i in range(5):
        px = x + W / 2 + (i - 2) * 2.54 * s
        if top:
            pins[i + 1] = pin(ax, px, y + W - 3 * s, None, "up", size=6.2 * s, r=0.75 * s)
            ax.text(px, y + W - 5.0 * s, str(i + 1), fontsize=6.0 * s, ha="center", va="top", color="white", zorder=7, fontweight="bold")
        else:
            pins[i + 1] = pin(ax, px, y + 3 * s, names[i + 1], "down", size=6.2 * s, r=0.75 * s, lbl_color="#222", dist=2.2 * s)
    return pins

def oled(ax, x, y, s=1.0, order=("GND", "VCC", "SCL", "SDA")):
    W = 27 * s
    board(ax, x, y, W, W, "#1e4fa8", r=1.0 * s, z=2)
    ax.add_patch(Rectangle((x + 1 * s, y + 3 * s), W - 2 * s, 15 * s, fc="#0a0a0a", ec="#444", zorder=3))
    label(ax, x + W / 2, y + 10.5 * s, "2,712\nfps", size=8 * s, color="#e8f4ff", bold=True)
    pins = {}
    for i, nm in enumerate(order):
        px = x + W / 2 + (i - 1.5) * 2.54 * s
        pins[nm] = pin(ax, px, y + W - 2.2 * s, None, "up", size=6 * s, r=0.75 * s)
        ax.text(px, y + W - 4.0 * s, nm, fontsize=5.4 * s, ha="center", va="top", rotation=90, color="white", zorder=7)
    return pins

def shield(ax, x, y, s=1.0):
    """18650 battery shield seen from above: holder with cell, USB-C, its own switch, header 5V/GND and 3V/GND."""
    W, H = 100 * s, 30 * s
    board(ax, x, y, W, H, "#2457a5", r=1.2 * s, z=2)
    # holder + cell
    ax.add_patch(FancyBboxPatch((x + 12 * s, y + 4 * s), 72 * s, 22 * s, boxstyle="round,pad=0,rounding_size=2", fc="#111", ec="#333", zorder=3))
    ax.add_patch(FancyBboxPatch((x + 15 * s, y + 6.5 * s), 66 * s, 17 * s, boxstyle="round,pad=0,rounding_size=8", fc="#3a7d3a", ec="#222", zorder=4))
    label(ax, x + 48 * s, y + 15 * s, "18650 cell", size=8 * s, color="white", bold=True)
    ax.add_patch(Rectangle((x + 81 * s, y + 12 * s), 2.5 * s, 6 * s, fc="#ccc", zorder=4))
    label(ax, x + 87.5 * s, y + 21.5 * s, "+ end", size=6 * s, color="white", bold=True)
    label(ax, x + 9.5 * s, y + 21.5 * s, "− end", size=6 * s, color="white", bold=True)
    pins = {"BAT+": (x + 84.5 * s, y + 15 * s)}
    ax.add_patch(Circle(pins["BAT+"], 1.0 * s, fc="#e0e0e0", ec="#555", zorder=5))
    # USB-C and switch at the left end
    ax.add_patch(Rectangle((x - 1.5 * s, y + 12 * s), 5 * s, 6 * s, fc="#c8c8c8", ec="#666", zorder=3))
    label(ax, x + 2 * s, y + 9.5 * s, "USB-C\n(charge)", size=5 * s, color="white")
    ax.add_patch(Rectangle((x + 4 * s, y + H - 4 * s), 6 * s, 3 * s, fc="#eee", ec="#555", zorder=3))
    label(ax, x + 7 * s, y + H - 6 * s, "its button:\nON / OFF", size=4.6 * s, color="white")
    # header at the right end
    for i, nm in enumerate(("5V", "GND", "5V", "GND")):
        pins["%s%d" % (nm, i)] = pin(ax, x + W - 7 * s, y + 4 * s + i * 2.54 * s, nm, "right", size=6 * s, r=0.75 * s, lbl_color="white", dist=1.7 * s)
    for i, nm in enumerate(("3V", "GND")):
        pin(ax, x + W - 12 * s, y + 4 * s + i * 2.54 * s, nm, "left", size=5 * s, r=0.65 * s, lbl_color="#ccd", dist=1.6 * s)
    return pins

def dpdt(ax, x, y, s=1.0):
    """6-tab slide switch seen from the tab side: two rows (A, B) of three tabs. Returns tab positions."""
    W, H = 26 * s, 13 * s
    board(ax, x, y, W, H, "#2b2b2b", r=0.8 * s, z=2)
    ax.add_patch(Rectangle((x + W / 2 - 3 * s, y + H - 1 * s), 6 * s, 4 * s, fc="#555", ec="#222", zorder=1.5))
    label(ax, x + W / 2, y + H + 4.5 * s, "slider", size=6 * s, color="#555")
    tabs = {}
    for r, ry in (("A", y + H * 0.7), ("B", y + H * 0.3)):
        for i, nm in enumerate(("end1", "mid", "end2")):
            px = x + W / 2 + (i - 1) * 7 * s
            ax.add_patch(Rectangle((px - 1.0 * s, ry - 1.6 * s), 2.0 * s, 3.2 * s, fc="#d0d0d0", ec="#666", zorder=3))
            tabs[r + nm] = (px, ry)
        label(ax, x - 2 * s, ry, "row " + r, size=6.5 * s, ha="right", color="#333", bold=True)
    return tabs

def dip8(ax, x, y, s=1.0, name="MCP6022", names=None):
    """DIP-8 top view, notch at the top, pins 1-4 down the left, 5-8 up the right. x,y = centre."""
    W, H = 9 * s, 11 * s
    ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H, boxstyle="round,pad=0,rounding_size=0.6", fc="#1a1a1a", ec="#000", zorder=3))
    ax.add_patch(Wedge((x, y + H / 2), 1.3 * s, 180, 360, fc="white", zorder=3.1))
    ax.add_patch(Circle((x - W / 2 + 1.6 * s, y + H / 2 - 1.8 * s), 0.5 * s, fc="#777", zorder=3.2))
    label(ax, x, y - 1.2 * s, name, size=min(6 * s, 13), color="#ddd", rot=90)
    pins = {}
    for i in range(4):
        py = y + 3.81 * s - i * 2.54 * s
        ax.add_patch(Rectangle((x - W / 2 - 1.8 * s, py - 0.45 * s), 1.8 * s, 0.9 * s, fc="#c8c8c8", ec="#666", zorder=2.9))
        pins[i + 1] = (x - W / 2 - 1.8 * s, py)
        label(ax, x - W / 2 + 0.9 * s, py, str(i + 1), size=5.2 * s, color="#ddd")
    for i in range(4):
        py = y - 3.81 * s + i * 2.54 * s
        ax.add_patch(Rectangle((x + W / 2, py - 0.45 * s), 1.8 * s, 0.9 * s, fc="#c8c8c8", ec="#666", zorder=2.9))
        pins[5 + i] = (x + W / 2 + 1.8 * s, py)
        label(ax, x + W / 2 - 0.9 * s, py, str(5 + i), size=5.2 * s, color="#ddd")
    if names:
        for k, nm in names.items():
            px, py = pins[k]
            ax.text(px + (-1.2 * s if k <= 4 else 1.2 * s), py, nm, fontsize=5.6 * s, ha="right" if k <= 4 else "left", va="center", color="#333", zorder=6)
    return pins

def to92(ax, x, y, s=1.0, legs=("GND", "IN", "OUT"), name="MCP\n1700"):
    """TO-92 seen from the flat (printed) face, legs down. x,y = centre of the body. Leg names written above the body."""
    ax.add_patch(Rectangle((x - 2.6 * s, y - 2.5 * s), 5.2 * s, 5.0 * s, fc="#1a1a1a", zorder=3))
    label(ax, x, y + 0.2 * s, name, size=min(4.4 * s, 6.0), color="#ccc")
    pins = {}
    for i, nm in enumerate(legs):
        lx = x + (i - 1) * 2.0 * s
        ax.add_patch(Rectangle((lx - 0.25 * s, y - 9 * s), 0.5 * s, 6.5 * s, fc="#bbb", ec="#777", zorder=2.9))
        pins[nm] = (lx, y - 9 * s)
        ax.text(x - 3.4 * s, y - 5.5 * s - i * 2.6, "", fontsize=1)
    lab = "  ".join("%d %s" % (i + 1, nm) for i, nm in enumerate(legs))
    label(ax, x, y + 2.5 * s + 2.2, lab, size=6.6, color="#222", bold=True)
    label(ax, x, y + 2.5 * s + 5.6, "flat face toward you, legs down", size=6.0, color="#555")
    return pins

BANDS = {0: "#000000", 1: "#8b4513", 2: "#e00000", 3: "#ff8c00", 4: "#ffd700", 5: "#2e8b57", 6: "#1e5bd6", 7: "#8a2be2", 8: "#808080", 9: "#ffffff"}
def bands_for(ohms):
    e = 0
    v = ohms
    while v >= 100:
        v /= 10; e += 1
    d = int(round(v))
    if d < 10:
        d *= 10; e -= 1
    return [d // 10, d % 10, e]

def bands5_for(ohms):
    e = 0
    v = ohms
    while v >= 1000:
        v /= 10; e += 1
    d = int(round(v))
    while d < 100:
        d *= 10; e -= 1
    return [d // 100, (d // 10) % 10, d % 10, e]

def resistor(ax, a, b, ohms, name=None, s=1.0, val=None, z=4, five=False):
    """axial resistor between points a and b (leads drawn), body in the middle with colour bands."""
    (x0, y0), (x1, y1) = a, b
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    L = math.hypot(x1 - x0, y1 - y0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.plot([x0, x1], [y0, y1], color="#999", lw=1.6, zorder=z - 0.2)
    bw, bh = min(L * 0.62, 6.5 * s), 2.3 * s
    tr = matplotlib.transforms.Affine2D().rotate_deg_around(mx, my, ang) + ax.transData
    ax.add_patch(FancyBboxPatch((mx - bw / 2, my - bh / 2), bw, bh, boxstyle="round,pad=0,rounding_size=%g" % (bh / 2.2), fc="#d8c48a", ec="#8c7a4a", lw=0.6, zorder=z, transform=tr))
    bs = bands5_for(ohms) if five else bands_for(ohms)
    if five:
        ax.patches[-1].set_facecolor("#7fb2e5"); ax.patches[-1].set_edgecolor("#4a7fb0")
    MULT = {-2: "#c0c0c0", -1: "#c9a227"}
    for k, d in enumerate(bs):
        bx = mx - bw / 2 + bw * (0.18 + (0.13 if five else 0.17) * k)
        col = BANDS[d] if d >= 0 else MULT[d]
        ax.add_patch(Rectangle((bx - 0.35 * s, my - bh / 2), 0.7 * s, bh, fc=col, ec="#00000033", lw=0.3, zorder=z + 0.1, transform=tr))
    ax.add_patch(Rectangle((mx + bw / 2 - bw * 0.14 - 0.35 * s, my - bh / 2), 0.7 * s, bh, fc="#8b4513" if five else "#c9a227", zorder=z + 0.1, transform=tr))
    if name:
        side_label(ax, mx, my, ang, "%s  %s" % (name, val or fmt_ohm(ohms)), 2.2 * s, 6.4 * s)

def side_label(ax, mx, my, ang, txt, off, size):
    a = math.radians(ang)
    if abs(math.cos(a)) >= abs(math.sin(a)):      # part lies left-right: label above
        label(ax, mx, my + off + 1.6, txt, size=size, color="#222")
    else:                                          # part stands up: label to the right
        ax.text(mx + off + 0.6, my, txt, fontsize=size, ha="left", va="center", color="#222", zorder=20)

def fmt_ohm(o):
    return ("%gk" % (o / 1000)) if o >= 1000 else ("%gΩ" % o)

def ceramic(ax, a, b, code, name=None, val=None, s=1.0, z=4):
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.plot([x0, mx, x1], [y0, my, y1], color="#999", lw=1.4, zorder=z - 0.2)
    ax.add_patch(Ellipse((mx, my), 4.2 * s, 3.6 * s, fc="#e3a33a", ec="#9a6a17", lw=0.6, zorder=z))
    label(ax, mx, my, code, size=5.6 * s, color="#3a2400", bold=True, z=z + 0.2)
    if name:
        side_label(ax, mx, my, math.degrees(math.atan2(y1 - y0, x1 - x0)), "%s  %s" % (name, val or code), 2.6 * s, 6.2 * s)

def electrolytic(ax, plus, minus, name=None, val=None, s=1.0, z=4):
    (x0, y0), (x1, y1) = plus, minus
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.plot([x0, mx, x1], [y0, my, y1], color="#999", lw=1.4, zorder=z - 0.2)
    ax.add_patch(Circle((mx, my), 2.6 * s, fc="#2a3f8f", ec="#111", lw=0.6, zorder=z))
    # minus stripe on the minus side
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    ax.add_patch(Wedge((mx, my), 2.6 * s, math.degrees(math.atan2(uy, ux)) - 40, math.degrees(math.atan2(uy, ux)) + 40, fc="#d9d9d9", zorder=z + 0.1))
    label(ax, mx - ux * 1.2 * s, my - uy * 1.2 * s, "+", size=7 * s, color="white", bold=True, z=z + 0.2)
    if name:
        side_label(ax, mx, my, math.degrees(math.atan2(dy, dx)), "%s  %s" % (name, val or ""), 3.0 * s, 6.2 * s)

def diode(ax, anode, cathode, name="D1", val="1N5817", s=1.0, z=4):
    (x0, y0), (x1, y1) = anode, cathode
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.plot([x0, x1], [y0, y1], color="#999", lw=1.6, zorder=z - 0.2)
    tr = matplotlib.transforms.Affine2D().rotate_deg_around(mx, my, ang) + ax.transData
    bw, bh = 5.4 * s, 2.7 * s
    ax.add_patch(Rectangle((mx - bw / 2, my - bh / 2), bw, bh, fc="#151515", zorder=z, transform=tr))
    ax.add_patch(Rectangle((mx + bw / 2 - 1.2 * s, my - bh / 2), 0.8 * s, bh, fc="#dcdcdc", zorder=z + 0.1, transform=tr))
    nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
    if ny < 0:
        nx, ny = -nx, -ny
    label(ax, mx + nx * 3.6 * s, my + ny * 3.6 * s, "%s %s (stripe → ESP32)" % (name, val), size=6.2 * s, color="#222")

def bus(ax, x0, x1, y, kind, text, lw=4.5, z=5):
    col = WIRE.get(kind, kind)
    ax.plot([x0, x1], [y, y], color=col, lw=lw, solid_capstyle="round", zorder=z)
    label(ax, x0 - 1.5, y, text, size=7.5, ha="right", color=col, bold=True)

def note(ax, x, y, s, size=8.6, w=None, color="#333", box=True, ha="left", va="top"):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, zorder=30, wrap=True,
            bbox=dict(boxstyle="round,pad=0.45", fc="#fffbe6", ec="#e0c56e", lw=0.8) if box else None)

def legend(ax, x, y, items, size=8):
    for i, (kind, txt) in enumerate(items):
        yy = y - i * 4.2
        ax.plot([x, x + 7], [yy, yy], color=WIRE.get(kind, kind), lw=3, solid_capstyle="round")
        ax.text(x + 9, yy, txt, fontsize=size, va="center", color="#333")

def gnd(ax, x, y, s=1.0, z=9):
    """ground symbol hanging below (x, y)"""
    ax.plot([x, x], [y, y - 2.2 * s], color=WIRE["GND"], lw=2.2, zorder=z)
    for k, w in enumerate((3.2, 2.1, 1.0)):
        ax.plot([x - w * s, x + w * s], [y - 2.2 * s - k * 0.9 * s] * 2, color=WIRE["GND"], lw=2.0, zorder=z)
