"""Placement check: courtyard overlaps, mounting-hole keepouts, board edge; draws a quick placement picture."""
import sys, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import importlib
import design as D

def body_box(p):
    fp = p["fp"]; b = fp["body"]
    xs, ys = [], []
    for (nm, dx, dy, sh, w, h, dr) in fp["pads"]:
        xs += [dx - w / 2, dx + w / 2]; ys += [dy - h / 2, dy + h / 2]
    if b[0] == "rect":
        xs += [-b[1] / 2, b[1] / 2]; ys += [-b[2] / 2, b[2] / 2]
    elif b[0] == "circle":
        xs += [-b[1] / 2, b[1] / 2]; ys += [-b[1] / 2, b[1] / 2]
    elif b[0] == "to92":
        xs += [-2.5, 2.5]; ys += [-1.6, 2.6]
    elif b[0] == "dip":
        xs += [-b[1] / 2, b[1] / 2]; ys += [-b[2] / 2, b[2] / 2]
    elif b[0] == "module":
        n, sep, pitch = b[1], b[2], b[3]
        if n == 24:   # Teensy 61 x 18
            xs += [1.27, 1.27 - 61.0]; ys += [-9.0, 9.0]
        else:         # ESP32-C3 SuperMini 22.5 x 18; ~2.4 mm past the end pins
            xs += [2.4, 2.4 - 22.5]; ys += [-9.0, 9.0]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cs = [D.rot(x, y, p["rot"]) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return (p["x"] + min(c[0] for c in cs), p["y"] + min(c[1] for c in cs), p["x"] + max(c[0] for c in cs), p["y"] + max(c[1] for c in cs))

def check(verbose=True):
    probs = []
    boxes = {r: body_box(p) for r, p in D.P.items()}
    m = 0.2
    refs = list(boxes)
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            a, b = boxes[refs[i]], boxes[refs[j]]
            if {refs[i], refs[j]} & {"U4", "U5"}:
                continue   # modules sit above the board on sockets; checked by pads below
            if a[0] < b[2] + m and b[0] < a[2] + m and a[1] < b[3] + m and b[1] < a[3] + m:
                probs.append("overlap %s %s" % (refs[i], refs[j]))
    pw = D.pads_world()
    for (r, nm, x, y, sh, w, h, dr, ro) in pw:
        for hx, hy in D.HOLES:
            if math.hypot(x - hx, y - hy) < D.HOLE_KEEPOUT + max(w, h) / 2:
                probs.append("hole keepout %s-%s" % (r, nm))
        if x - w / 2 < 0.5 or x + w / 2 > D.BOARD_W - 0.5 or y - h / 2 < 0.5 or y + h / 2 > D.BOARD_H - 0.5:
            probs.append("edge %s-%s" % (r, nm))
    # pad-to-pad spacing (any two pads of different parts closer than 0.4 mm edge to edge)
    for i in range(len(pw)):
        for j in range(i + 1, len(pw)):
            a, b = pw[i], pw[j]
            if a[0] == b[0]:
                continue
            d = math.hypot(a[2] - b[2], a[3] - b[3]) - max(a[5], a[6]) / 2 - max(b[5], b[6]) / 2
            if d < 0.4:
                probs.append("pads %s-%s / %s-%s gap %.2f" % (a[0], a[1], b[0], b[1], d))
    # modules over parts: U4/U5 footprints vs other parts (parts under a socketed module must be short; flag them)
    for mref in ("U4", "U5"):
        mb = boxes[mref]
        for r, b in boxes.items():
            if r in ("U4", "U5"):
                continue
            if b[0] < mb[2] and mb[0] < b[2] and b[1] < mb[3] and mb[1] < b[3]:
                probs.append("under %s: %s" % (mref, r))
    if verbose:
        for p in probs:
            print(p)
        print(len(probs), "problems")
    return probs, boxes

def draw(path):
    probs, boxes = check(False)
    fig, ax = plt.subplots(figsize=(7, 9), dpi=130)
    ax.add_patch(plt.Rectangle((0, 0), D.BOARD_W, D.BOARD_H, fill=False, lw=1.2))
    for hx, hy in D.HOLES:
        ax.add_patch(plt.Circle((hx, hy), D.HOLE_D / 2, fill=False, color="k"))
        ax.add_patch(plt.Circle((hx, hy), D.HOLE_KEEPOUT, fill=False, color="r", ls=":"))
    for r, b in boxes.items():
        ax.add_patch(plt.Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, color="#888" if r in ("U4", "U5") else "#06c", lw=0.6))
        ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, r, ha="center", va="center", fontsize=5)
    for (r, nm, x, y, sh, w, h, dr, ro) in D.pads_world():
        ax.add_patch(plt.Circle((x, y), w / 2, color="#c80", alpha=0.6))
    ax.set_xlim(-2, D.BOARD_W + 2); ax.set_ylim(-2, D.BOARD_H + 2); ax.set_aspect("equal")
    ax.set_title("placement (front edge at bottom)")
    plt.savefig(path, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    check()
    draw(sys.argv[1] if len(sys.argv) > 1 else "/tmp/place.png")
