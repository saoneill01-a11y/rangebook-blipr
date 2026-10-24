"""Hand-drawn diagrams for the BLIPR video. Each takes (ctx, c, x, y, w, h)."""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import math, glob, os
import cairo
from PIL import Image
from draw import *
import parts as PT
from vis import card, load_surface


def P(ctx, fn, cx, cy, s, rot=0.0, alpha=1.0, **kw):
    """Draw a part illustration centred at (cx, cy) scaled by s (px per mm)."""
    ctx.save()
    if alpha < 1:
        ctx.push_group()
    ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(s, s)
    fn(ctx, **kw)
    if alpha < 1:
        ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    ctx.restore()


def wire_path(ctx, pts, col, lw=7, prog=1.0, outline=True):
    """Smooth wire through pts (list of xy), drawn to fraction prog."""
    if prog <= 0:
        return
    seg = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        seg.append((a, b, math.hypot(b[0] - a[0], b[1] - a[1])))
    total = sum(s[2] for s in seg)
    goal = total * prog
    path = [pts[0]]
    acc = 0
    for a, b, L in seg:
        if acc + L <= goal:
            path.append(b); acc += L
        else:
            f = (goal - acc) / L if L else 0
            path.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            break
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for pas in ((hexc("#000000", 0.35), lw + 3), (col, lw)) if outline else ((col, lw),):
        setc(ctx, pas[0]); ctx.set_line_width(pas[1])
        ctx.move_to(*path[0])
        for p in path[1:]:
            ctx.line_to(*p)
        ctx.stroke()


def dot(ctx, x, y, r, col):
    ctx.new_path(); setc(ctx, col); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()


def legend(ctx, x, y, items, size=24):
    for i, (col, lab) in enumerate(items):
        yy = y + i * (size + 16)
        setc(ctx, col); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, yy - size * 0.35); ctx.line_to(x + 46, yy - size * 0.35); ctx.stroke()
        text(ctx, lab, x + 62, yy, size, INK)


# ------------------------------------------------------------------ title / outro
def title(ctx, c, x, y, w, h, sub="Assembly, step by step", hero="turn_0119"):
    surf = load_surface(f"{BUILD}/3d/{hero}.png")
    k = ramp(c.t, 0.2, 1.2)
    s = 0.92
    iw, ih = surf.get_width() * s, surf.get_height() * s
    ctx.save(); ctx.translate(x + w - iw - 10, y + (h - ih) / 2 + (1 - k) * 30); ctx.scale(s, s)
    ctx.set_source_surface(surf, 0, 0); ctx.paint_with_alpha(k); ctx.restore()
    a = ramp(c.t, 0.0, 0.8)
    text(ctx, "RANGE BOOK", x + 60, y + 230, 40, CHAPTER_COL["intro"], True, alpha=a)
    text(ctx, "BLIPR", x + 52, y + 370, 160, INK, True, alpha=a)
    text(ctx, "Ballistic Launch Inspection Portable Radar", x + 60, y + 430, 30, INK2, alpha=a)
    b = ramp(c.t, 0.8, 0.8)
    setc(ctx, FOCUS, b); ctx.rectangle(x + 60, y + 470, 120 * b, 6); ctx.fill()
    text(ctx, sub, x + 60, y + 540, 44, INK, weight="semi", alpha=b)
    text(ctx, "Circuit board v1.1  ·  Case v0.8  ·  Firmware 0.2.2 / 0.2.3", x + 60, y + 600, 26, INK2, alpha=b)


# ------------------------------------------------------------------ bench top view
def bench(ctx, c, x, y, w, h, shot_line=1, phone=True, dims=False, aim_bad=False):
    """Top view: rifle pointing up the screen (downrange), shooter at the bottom, BLIPR right of the barrel behind the muzzle."""
    cx = x + w * 0.38
    setc(ctx, hexc("#E9E3D3")); rrect(ctx, x + 40, y + 300, w * 0.62, h - 330, 16); ctx.fill()   # bench
    text(ctx, "BENCH", x + 64, y + h - 50, 22, hexc("#9C8F6B"), True)
    text(ctx, "DOWNRANGE", cx, y + 44, 24, INK2, True, "c")
    arrow(ctx, cx, y + 120, cx, y + 60, INK2, 4, 18)
    # shooter
    setc(ctx, hexc("#55607A")); ctx.arc(cx + 12, y + h - 70, 46, math.pi, 2 * math.pi); ctx.fill()
    dot(ctx, cx + 12, y + h - 96, 26, hexc("#55607A"))
    text(ctx, "you", cx + 12, y + h - 18, 22, INK2, True, "c")
    # rifle: stock at bottom, muzzle at top
    muzzle_y = y + 250
    setc(ctx, hexc("#5B4636")); rrect(ctx, cx - 18, y + h - 300, 36, 190, 10); ctx.fill()
    setc(ctx, hexc("#30343B")); ctx.rectangle(cx - 9, muzzle_y, 18, y + h - 300 - muzzle_y); ctx.fill()
    setc(ctx, hexc("#30343B")); rrect(ctx, cx - 14, y + h - 430, 28, 120, 6); ctx.fill()
    # BLIPR: right of the barrel, behind the muzzle
    bx, by = cx + 120, muzzle_y + 150
    ang = math.radians(18) if aim_bad else 0
    ctx.save(); ctx.translate(bx, by); ctx.rotate(ang)
    setc(ctx, hexc("#8A93A3")); rrect(ctx, -46, -50, 92, 100, 10); ctx.fill()
    setc(ctx, hexc("#C9A23F")); ctx.rectangle(-22, -52, 44, 6); ctx.fill()
    setc(ctx, hexc("#111")); ctx.rectangle(-40, 16, 26, 26); ctx.fill()
    text(ctx, "BLIPR", 6, 0, 18, PAPER, True, "c")
    # beam
    bk = 0.5 + 0.5 * math.sin(c.t * 3)
    setc(ctx, FOCUS, 0.10 + 0.08 * bk)
    ctx.move_to(-20, -54); ctx.line_to(-170, -480); ctx.line_to(130, -480); ctx.line_to(20, -54); ctx.close_path(); ctx.fill()
    ctx.restore()
    # bullet
    ts = c.since(shot_line) if shot_line is not None else -1
    if 0 <= ts:
        tt = (ts % 3.0)
        if tt < 0.9:
            yy = muzzle_y - (tt / 0.9) * 260
            dot(ctx, cx, yy, 7, hexc("#B8860B"))
            setc(ctx, hexc("#FFB300", 0.5 * (1 - tt / 0.9))); ctx.arc(cx, muzzle_y - 6, 24 * (tt / 0.9) + 6, 0, 2 * math.pi); ctx.fill()
    if dims:
        k = c.k(dims) if isinstance(dims, int) else 1
        setc(ctx, INK, k); ctx.set_line_width(2); ctx.set_dash([8, 6])
        ctx.move_to(cx - 60, muzzle_y); ctx.line_to(bx + 70, muzzle_y); ctx.stroke()
        ctx.move_to(cx, by); ctx.line_to(bx - 46, by); ctx.stroke(); ctx.set_dash([])
        tag(ctx, "about 30 cm behind the muzzle", bx + 60, (muzzle_y + by) / 2 - 10, 22, PAPER, INK, k)
        tag(ctx, "about 12 cm to the side", cx + 6, by + 80, 22, PAPER, INK, k)
        arrow(ctx, bx + 54, muzzle_y + 8, bx + 54, by - 52, INK, 3, 14, k)
    if phone:
        px, py = x + w - 270, y + 120
        k = ramp(c.t, c.at(shot_line) + 0.9, 0.4) if shot_line is not None else 1
        setc(ctx, hexc("#16181C")); rrect(ctx, px, py, 230, 440, 34); ctx.fill()
        setc(ctx, PAPER); rrect(ctx, px + 12, py + 14, 206, 412, 26); ctx.fill()
        text(ctx, "Range Book", px + 115, py + 70, 22, INK2, True, "c")
        text(ctx, "2,847", px + 115, py + 210, 64, INK, True, "c", alpha=k)
        text(ctx, "fps", px + 115, py + 252, 26, INK2, True, "c", alpha=k)
        text(ctx, "Shot 7 · avg 2,843", px + 115, py + 320, 22, INK2, False, "c", alpha=k)
        text(ctx, "SD 4.1 · ES 12", px + 115, py + 352, 22, INK2, False, "c", alpha=k)
        # bluetooth hop
        setc(ctx, hexc("#2457C9"), 0.6 * k); ctx.set_line_width(3); ctx.set_dash([6, 8])
        ctx.move_to(bx + 50, by - 20); ctx.curve_to(bx + 200, by - 200, px - 80, py + 300, px - 6, py + 220); ctx.stroke(); ctx.set_dash([])
        text(ctx, "Bluetooth", px - 20, py + 140, 22, hexc("#2457C9"), True, "r", alpha=k)


# ------------------------------------------------------------------ signal path
def signal(ctx, c, x, y, w, h):
    names = [("Radar", "24 GHz, sees the bullet"), ("Amplifier", "boosts the signal ~500x"), ("Teensy 4.1", "measures the speed"),
             ("ESP32-C3", "screen + Bluetooth"), ("Range Book", "on your phone")]
    n = len(names)
    bw, bh = (w - 120 - (n - 1) * 46) / n, 220
    by = y + h / 2 - bh / 2 - 40
    for i, (nm, sub) in enumerate(names):
        bx = x + 60 + i * (bw + 46)
        k = c.k(min(i, len(c.scene.lines) - 1) if i < 2 else 1, 0.5, (i - 1) * 0.6 if i >= 2 else 0)
        k = ramp(c.t, c.at(0) + i * 0.9, 0.5)
        setc(ctx, hexc("#EEF2F7"), k); rrect(ctx, bx, by, bw, bh, 18); ctx.fill()
        setc(ctx, CHAPTER_COL["intro"], k); ctx.set_line_width(3); rrect(ctx, bx, by, bw, bh, 18); ctx.stroke()
        text(ctx, nm, bx + bw / 2, by + 92, 38, INK, True, "c", alpha=k)
        para(ctx, sub, bx + bw / 2, by + 144, bw - 30, 26, INK2, alpha=k, anchor="c")
        if i < n - 1:
            ka = ramp(c.t, c.at(0) + i * 0.9 + 0.5, 0.4)
            arrow(ctx, bx + bw + 6, by + bh / 2, bx + bw + 40, by + bh / 2, INK2, 5, 16, ka)
    # moving pulse
    tt = (c.t - c.at(0) - 4.5) % 4.0
    if c.t > c.at(0) + 4.5:
        px = x + 60 + (w - 120) * (tt / 4.0)
        dot(ctx, px, by + bh + 50, 10, FOCUS)
    setc(ctx, RULE); ctx.rectangle(x + 60, by + bh + 49, w - 120, 2); ctx.fill()
    text(ctx, "Power: one 18650 cell in its holder. The holder's own button turns BLIPR on and off.", x + w / 2, by + bh + 140, 30, INK2, anchor="c",
         alpha=ramp(c.t, c.at(min(2, len(c.scene.lines) - 1)), 0.5))


# ------------------------------------------------------------------ safety
def safety(ctx, c, x, y, w, h, cards=None):
    cards = cards or []
    n = len(cards)
    cols = 2
    rows = math.ceil(n / cols)
    gw, gh = (w - 20) / cols, (h - (rows - 1) * 20) / rows
    for i, (li, head, body) in enumerate(cards):
        r, q = divmod(i, cols)
        cx, cy = x + q * (gw + 20), y + r * (gh + 20)
        k = c.k(li)
        if k <= 0:
            continue
        ctx.push_group()
        card(ctx, cx, cy, gw, gh)
        setc(ctx, BAD); rrect(ctx, cx, cy, 10, gh, 5); ctx.fill()
        warn_icon(ctx, cx + 70, cy + 76, 76)
        text(ctx, head, cx + 130, cy + 94, 42, INK, True)
        para(ctx, body, cx + 44, cy + 170, gw - 90, 33, INK2)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(k)


# ------------------------------------------------------------------ Teensy VIN-VUSB cut
def teensy_cut(ctx, c, x, y, w, h):
    s = 16.0
    cx, cy = x + w / 2 - 120, y + h / 2 - 20
    k0 = c.k(0)
    # zoom: show whole underside then zoom on the pads
    z = lerp(1.0, 1.9, c.k(1, 1.2))
    padx = 61 / 2 - 8.3            # local mm of the pads (USB end at +x)
    ctx.save()
    ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-lerp(0, padx, c.k(1, 1.2)) * s, 0)
    ctx.scale(s, s)
    PT.teensy(ctx, under=True)
    # cut mark
    kc = c.k(2, 1.2)
    if kc > 0:
        setc(ctx, BAD); ctx.set_line_width(0.28); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(padx - 1.2, 0.0); ctx.line_to(padx - 1.2 + 2.4 * kc, 0.0); ctx.stroke()
        if kc < 1:
            P(ctx, PT.knife, padx - 1.2 + 2.4 * kc + 0.4, -3.0, 0.22, -0.9)
    ctx.restore()
    tag(ctx, "Underside, USB end on the right", x + 40, y + 50, 24, PAPER, INK2)
    if c.k(1) > 0:
        tag(ctx, "VIN and VUSB pads, joined by a thin trace", x + 40, y + 100, 24, PAPER, FOCUS, c.k(1))
    km = c.k(3)
    if km > 0:
        mx, my = x + w - 190, y + h - 250
        P(ctx, PT.multimeter, mx, my, 6.0, alpha=km, reading="OL")
        tag(ctx, "No beep = cut", mx, my + 210, 26, PAPER, GOOD, km, "c")


# ------------------------------------------------------------------ correct vs wrong panels
def compare(ctx, c, x, y, w, h, left, right, labels=("Correct", "Wrong"), line=0, line2=None):
    """left/right: fn(ctx, cx, cy, s) drawing; tick and cross badges."""
    gw = (w - 60) / 2
    for i, (fn, lab) in enumerate(((left, labels[0]), (right, labels[1]))):
        li = line if i == 0 else (line2 if line2 is not None else line)
        k = c.k(li, 0.5, 0.0 if i == 0 else (0.0 if line2 is not None else 0.6))
        if k <= 0:
            continue
        bx = x + 20 + i * (gw + 20)
        ctx.push_group()
        setc(ctx, hexc("#F1F7F2") if i == 0 else hexc("#FCF1F1")); rrect(ctx, bx, y + 20, gw, h - 40, 18); ctx.fill()
        fn(ctx, bx + gw / 2, y + h / 2 + 10, c)
        (check if i == 0 else cross)(ctx, bx + 60, y + 80, 64)
        text(ctx, lab, bx + 104, y + 92, 32, GOOD if i == 0 else BAD, True)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(k)


def edge_marker(ctx, x0, x1, y, label="FRONT EDGE (radar side)"):
    setc(ctx, hexc("#1F5E3A")); ctx.rectangle(x0, y - 70, x1 - x0, 70); ctx.fill()
    setc(ctx, hexc("#D9A441")); ctx.rectangle(x0, y - 4, x1 - x0, 4); ctx.fill()
    text(ctx, label, (x0 + x1) / 2, y + 36, 22, INK2, True, "c")


def u3_panel(good):
    def fn(ctx, cx, cy, c):
        edge_marker(ctx, cx - 220, cx + 220, cy + 180)
        s = 22
        # top view of the regulator on the board
        ctx.save(); ctx.translate(cx, cy + 60); ctx.scale(s, s)
        if not good:
            ctx.rotate(math.pi)
        setc(ctx, hexc("#1B1D21")); ctx.move_to(-2.4, 1.3); ctx.line_to(2.4, 1.3); ctx.line_to(2.4, -1.0); ctx.arc_negative(0, -1.0, 2.4, 0, math.pi); ctx.close_path(); ctx.fill()
        setc(ctx, hexc("#9AA0A8")); ctx.set_line_width(0.15); ctx.move_to(-2.4, 1.28); ctx.line_to(2.4, 1.28); ctx.stroke()
        ctx.restore()
        if good:
            for i, nm in enumerate(["GND", "IN", "OUT"]):
                tag(ctx, nm, cx - 56 + i * 56, cy + 130, 20, PAPER, INK, anchor="c")
            text(ctx, "flat face toward the front edge", cx, cy - 90, 26, INK, True, "c")
            arrow(ctx, cx, cy - 70, cx, cy + 70, GOOD, 5, 18)
        else:
            text(ctx, "flat face toward the Teensy", cx, cy - 90, 26, INK, True, "c")
            text(ctx, "U3 gets 5 V backwards", cx, cy - 50, 22, BAD, True, "c")
    return fn


def elec_panel(good):
    def fn(ctx, cx, cy, c):
        s = 18
        top = cy - 60
        # board strip with the two pads exactly under the leads (lead spacing 2.5 mm)
        by = top + (11 / 2 + 5.0) * s + 6
        setc(ctx, hexc("#1F5E3A")); ctx.rectangle(cx - 170, by - 26, 340, 70); ctx.fill()
        for i, sq in enumerate((True, False)):
            px = cx + (-1.25 if i == 0 else 1.25) * s
            setc(ctx, hexc("#D9D9D9"))
            if sq:
                ctx.rectangle(px - 13, by - 13, 26, 26)
            else:
                ctx.arc(px, by, 13, 0, 2 * math.pi)
            ctx.fill()
            dot(ctx, px, by, 5, hexc("#111"))
        text(ctx, "+ square pad", cx - 1.25 * s, by + 80, 24, INK, True, "c")
        ctx.save(); ctx.translate(cx, top)
        if not good:
            ctx.scale(-1, 1)
        ctx.scale(s, s); PT.electrolytic_side(ctx)
        ctx.restore()
        if good:
            text(ctx, "long leg (+) in the square pad", cx, top - 11 / 2 * s - 64, 28, INK, True, "c")
            text(ctx, "stripe (−) away from it", cx, top - 11 / 2 * s - 28, 24, INK2, False, "c")
        else:
            text(ctx, "stripe over the square pad", cx, top - 11 / 2 * s - 64, 28, INK, True, "c")
            text(ctx, "it can swell or pop", cx, top - 11 / 2 * s - 28, 24, BAD, True, "c")
    return fn


# ------------------------------------------------------------------ ESP32 orientation + beep test
def esp_orient(ctx, c, x, y, w, h):
    s = 22
    cx, cy = x + w * 0.30, y + h / 2 + 20
    P(ctx, PT.esp32, cx, cy, s, labels=True)
    text(ctx, "USB socket", cx, cy - 22.5 * s / 2 - 40, 26, INK2, True, "c")
    arrow(ctx, cx - 270, cy - 60, cx - 270, cy - 200, INK2, 4, 16)
    text(ctx, "to the BACK", cx - 270, cy - 20, 22, INK2, True, "c")
    text(ctx, "antenna end:", cx, cy + 22.5 * s / 2 + 40, 22, INK2, True, "c")
    text(ctx, "board's FRONT edge", cx, cy + 22.5 * s / 2 + 68, 22, INK2, True, "c")
    k = c.k(3) if len(c.scene.lines) > 3 else c.k(1)
    if k > 0:
        px, py = cx + 7.62 * s, cy + (-11.25 + 2.4) * s
        ring(ctx, px, py, 24, c.since(3), FOCUS, 5, k)
        tag(ctx, "5V pin", px + 36, py, 26, PAPER, FOCUS, k)
    k2 = c.k(4) if len(c.scene.lines) > 4 else c.k(2)
    if k2 > 0:
        bx = x + w * 0.62
        card(ctx, bx - 20, y + 80, w * 0.38, h - 160, hexc("#F6F7F9"), shadow=False)
        text(ctx, "Beep test (no power)", bx + 10, y + 140, 30, INK, True)
        P(ctx, PT.multimeter, bx + w * 0.17, y + 330, 5.5, reading="000")
        para(ctx, "ESP32 5V pin  →  D1's square pad", bx + 10, y + 530, w * 0.34, 27, INK)
        para(ctx, "ESP32 G pin  →  J1 pin 2", bx + 10, y + 600, w * 0.34, 27, INK)
        text(ctx, "Both must beep.", bx + 10, y + 670, 30, GOOD, True)


# ------------------------------------------------------------------ battery holder wiring
def holder_wiring(ctx, c, x, y, w, h, steps=(0, 1, 2, 3)):
    s = 9.0
    hx, hy = x + 520, y + 175
    P(ctx, PT.battery_holder, hx, hy, s, with_cell=False)
    text(ctx, "18650 holder (no cell yet)", hx - 470, hy - 150, 22, INK2, True)
    # main board corner with J1
    bx, by = x + 760, y + 440
    setc(ctx, hexc("#1F5E3A")); rrect(ctx, bx, by, 470, 300, 14); ctx.fill()
    jx = bx + 230
    jy = {"BAT": by + 110, "GND": by + 160, "+5V": by + 210}
    for nm, py in jy.items():
        setc(ctx, hexc("#D9D9D9"))
        if nm == "+5V":
            ctx.rectangle(jx - 15, py - 15, 30, 30)
        else:
            ctx.new_path(); ctx.arc(jx, py, 15, 0, 2 * math.pi)
        ctx.fill(); dot(ctx, jx, py, 6, hexc("#111"))
        text(ctx, "J1 " + nm, jx - 30, py + 8, 24, hexc("#FFE680"), True, "r")
    text(ctx, "MAIN BOARD", bx + 235, by + 280, 20, hexc("#FFE680"), True, "c")
    pg = (hx + 42 * s, hy - 6 * s); p5 = (hx + 42 * s, hy - 2 * s)
    k1 = c.k(steps[0], 1.4)
    wire_path(ctx, [pg, (x + 1205, pg[1]), (x + 1205, jy["GND"]), (jx, jy["GND"])], WIRE["GND"], 8, k1)
    wire_path(ctx, [p5, (x + 1170, p5[1]), (x + 1170, jy["+5V"]), (jx, jy["+5V"])], WIRE["5V"], 8, k1)
    tabx, taby = hx + 33.5 * s, hy + 3 * s
    k2 = c.k(steps[1], 0.8)
    if k2 > 0:
        ring(ctx, tabx, taby, 20, c.since(steps[1]), FOCUS, 5, k2)
        ctx.save(); ctx.translate(tabx, taby + 80); ctx.rotate(math.pi / 2); ctx.scale(10, 10)
        ctx.push_group(); PT.resistor(ctx, "10k", lead=3.0); ctx.pop_group_to_source(); ctx.paint_with_alpha(k2); ctx.restore()
        setc(ctx, hexc("#3A3F47"), k2 * 0.45); rrect(ctx, tabx - 18, taby + 10, 36, 140, 10); ctx.fill()
    k3 = c.k(steps[2], 1.3)
    wire_path(ctx, [(tabx, taby + 150), (tabx, by + 50), (jx, by + 50), (jx, jy["BAT"])], WIRE["BAT"], 8, k3)
    km = c.k(steps[3]) if len(steps) > 3 else 0
    if km > 0:
        sx_, sy_ = hx - 41.5 * s, hy + 11 * s
        ring(ctx, sx_, sy_, 22, c.since(steps[3]), FOCUS, 5, km)
    # legend of what each step adds (lower left)
    items = [(steps[0], WIRE["5V"], "Red: holder 5V pad → J1 +5V"), (steps[0], WIRE["GND"], "Black: holder GND pad → J1 GND"),
             (steps[1], FOCUS, "R25 (10 kΩ): one leg on the + tab, heat-shrink"), (steps[2], WIRE["BAT"], "Brown: R25's other leg → J1 BAT")]
    if len(steps) > 3:
        items.append((steps[3], INK, "Mode switch → “power on”"))
    for i, (li, col, s_) in enumerate(items):
        k = c.k(li)
        if k <= 0:
            continue
        yy = y + 420 + i * 62
        setc(ctx, col, k); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.new_path(); ctx.move_to(x + 60, yy - 9); ctx.line_to(x + 110, yy - 9); ctx.stroke()
        text(ctx, s_, x + 130, yy, 27, INK, alpha=k)


# ------------------------------------------------------------------ meter + readings table
def readings(ctx, c, x, y, w, h, rows, title="Expect", first=0):
    card(ctx, x, y, w, h)
    text(ctx, title, x + 30, y + 52, 26, INK2, True)
    rh = min(84, (h - 90) / max(1, len(rows)))
    for i, (li, where, val) in enumerate(rows):
        k = c.k(li)
        if k <= 0:
            continue
        yy = y + 90 + i * rh
        setc(ctx, hexc("#F3F5F8"), k); rrect(ctx, x + 20, yy, w - 40, rh - 12, 12); ctx.fill()
        text(ctx, where, x + 40, yy + rh / 2 + 4, 25, INK, alpha=k)
        text(ctx, val, x + w - 40, yy + rh / 2 + 4, 27, GOOD, True, "r", alpha=k, mono=False)


def probes(ctx, red_xy, black_xy, meter_xy, reading, k=1.0, s=5.0):
    mx, my = meter_xy
    P(ctx, PT.multimeter, mx, my, s, alpha=k, reading=reading, probes=False)
    for (px, py), col, off in ((red_xy, BAD, 4), (black_xy, hexc("#1B1B1B"), -4)):
        if px is None:
            continue
        setc(ctx, col, k); ctx.set_line_width(5); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(mx + off * s, my + 12 * s); ctx.curve_to(mx + off * s, my + 40 * s, px, py + 120, px, py + 22); ctx.stroke()
        setc(ctx, col, k); ctx.move_to(px - 7, py + 22); ctx.line_to(px + 7, py + 22); ctx.line_to(px, py + 4); ctx.close_path(); ctx.fill()


# ------------------------------------------------------------------ radar pigtail
def pigtail(ctx, c, x, y, w, h, line0=0):
    pitch = 72
    hx, hy = x + 120, y + 150
    # 1x5 female header, seen from the wire side
    setc(ctx, hexc("#202226")); rrect(ctx, hx - pitch / 2, hy - 30, pitch * 5, 60, 6); ctx.fill()
    pins = [(hx + i * pitch, hy) for i in range(5)]
    for i, (px, py) in enumerate(pins):
        setc(ctx, hexc("#55585E")); ctx.rectangle(px - 12, py - 12, 24, 24); ctx.fill()
        text(ctx, str(i + 1), px, py - 48, 32, INK, True, "c")
    text(ctx, "1×5 female header", hx + 4.5 * pitch + 20, hy - 4, 24, INK2, True)
    text(ctx, "(plugs onto the radar)", hx + 4.5 * pitch + 20, hy + 26, 22, INK2)
    k0 = c.k(line0)
    if k0:
        ring(ctx, pins[0][0], pins[0][1], 30, c.since(line0), FOCUS, 5, k0)
        tag(ctx, "pin 1: mark this end", pins[0][0] - 46, hy - 100, 24, PAPER, FOCUS, k0)
    # J2 on the board
    jx0, jy = x + w - 470, y + h - 150
    setc(ctx, hexc("#1F5E3A")); rrect(ctx, jx0 - 70, jy - 60, 4 * pitch + 100, 150, 14); ctx.fill()
    jn = ["Q", "VCC", "I", "GND"]
    jp = [(jx0 + i * pitch, jy) for i in range(4)]
    for i, (px, py) in enumerate(jp):
        setc(ctx, hexc("#D9D9D9")); ctx.new_path()
        if i == 0:
            ctx.rectangle(px - 16, py - 16, 32, 32)
        else:
            ctx.arc(px, py, 16, 0, 2 * math.pi)
        ctx.fill(); dot(ctx, px, py, 7, hexc("#111"))
        text(ctx, jn[i], px, py + 56, 24, hexc("#FFE680"), True, "c")
    text(ctx, "J2 RADAR", jx0 - 90, jy + 4, 26, INK, True, "r")
    text(ctx, "on the main board", jx0 - 90, jy + 34, 22, INK2, False, "r")
    specs = [(0, WIRE["Q"], "pin 1 → J2 Q (blue)"), (1, WIRE["3V3"], "pin 2 → J2 VCC (orange)"),
             (2, WIRE["I"], "pin 3 → J2 I (green)"), (3, WIRE["GND"], "pin 4 → J2 GND (two black)")]
    for n, (pi, col, lab) in enumerate(specs):
        li = line0 + 1 + n
        k = c.k(li, 1.3)
        px, py = pins[pi]
        tx, ty = jp[pi]
        lane = hy + 150 + n * 34
        wire_path(ctx, [(px, py + 14), (px, lane), (tx, lane), (tx, ty)], col, 9, k)
        if pi == 3:
            wire_path(ctx, [(px + 12, py + 14), (px + 12, lane + 14), (tx + 10, lane + 14), (tx + 10, ty)], col, 9, k)
        if k > 0:
            yy = y + h - 230 + n * 54
            setc(ctx, col, min(1, k * 2)); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.new_path()
            ctx.move_to(x + 50, yy - 9); ctx.line_to(x + 100, yy - 9); ctx.stroke()
            text(ctx, lab, x + 120, yy, 27, INK, alpha=min(1, k * 2))
    k5 = c.k(line0 + 5)
    if k5:
        px, py = pins[4]
        cross(ctx, px, py + 64, 46, k5)
        tag(ctx, "pin 5: NO wire", px + 36, py + 64, 24, PAPER, BAD, k5)
    k6 = c.k(line0 + 6)
    if k6:
        tag(ctx, "Twist I (green) with one black, Q (blue) with the other", x + w - 40, y + 60, 24, PAPER, INK, k6, "r")


# ------------------------------------------------------------------ OLED wiring
def oled_wiring(ctx, c, x, y, w, h, line0=0):
    s = 15
    ox, oy = x + w - 330, y + 500
    P(ctx, PT.oled, ox, oy, s)
    pins = {nm: (ox + (-3.81 + i * 2.54) * s, oy - 12.2 * s) for i, nm in enumerate(["GND", "VCC", "SCL", "SDA"])}
    jx = x + 260
    dest = {"SDA": y + 170, "SCL": y + 240, "VCC": y + 310, "GND": y + 380}
    setc(ctx, hexc("#1F5E3A")); rrect(ctx, jx - 190, y + 110, 240, 330, 14); ctx.fill()
    for i, nm in enumerate(["SDA", "SCL", "VCC", "GND"]):
        py = dest[nm]
        setc(ctx, hexc("#D9D9D9")); ctx.new_path()
        if nm == "GND":
            ctx.rectangle(jx - 16, py - 16, 32, 32)
        else:
            ctx.arc(jx, py, 16, 0, 2 * math.pi)
        ctx.fill(); dot(ctx, jx, py, 7, hexc("#111"))
        text(ctx, nm, jx - 34, py + 9, 26, hexc("#FFE680"), True, "r")
    text(ctx, "J3 OLED", jx - 70, y + 470, 26, INK, True, "c")
    text(ctx, "on the main board", jx - 70, y + 500, 22, INK2, False, "c")
    cols = {"GND": WIRE["GND"], "VCC": WIRE["3V3"], "SCL": WIRE["SCL"], "SDA": WIRE["SDA"]}
    lane = {"SDA": y + 100, "SCL": y + 170, "VCC": y + 240, "GND": y + 296}
    colx = {"SDA": jx + 110, "SCL": jx + 160, "VCC": jx + 210, "GND": jx + 260}
    for n, nm in enumerate(["GND", "VCC", "SCL", "SDA"]):
        k = c.k(line0 + 1 + (0 if n < 2 else 1), 1.4, 0.0 if n % 2 == 0 else 0.7)
        px, py = pins[nm]
        wire_path(ctx, [(px, py), (px, lane[nm]), (colx[nm], lane[nm]), (colx[nm], dest[nm]), (jx, dest[nm])], cols[nm], 9, k)
    k = c.k(line0 + 3)
    if k:
        tag(ctx, "Go by the labels printed on YOUR screen", ox, oy + 14 * s + 40, 26, PAPER, FOCUS, k, "c")


# ------------------------------------------------------------------ software mockups
def window(ctx, x, y, w, h, title_s):
    setc(ctx, hexc("#000000", 0.08)); rrect(ctx, x + 4, y + 6, w, h, 14); ctx.fill()
    setc(ctx, PAPER); rrect(ctx, x, y, w, h, 14); ctx.fill()
    setc(ctx, hexc("#E7EAEE")); rrect(ctx, x, y, w, 52, 14); ctx.fill(); ctx.rectangle(x, y + 30, w, 22); ctx.fill()
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        dot(ctx, x + 28 + i * 26, y + 26, 8, hexc(col))
    text(ctx, title_s, x + w / 2, y + 34, 22, INK2, True, "c")


def ide(ctx, c, x, y, w, h, rows, title_s="Arduino IDE 2  ·  Tools menu", first=0, intro=None):
    window(ctx, x + 20, y + 20, w - 40, h - 40, title_s)
    shown = 0
    for i, (li, key, val) in enumerate(rows):
        k = c.k(li, 0.5, (i - [r[0] for r in rows].index(li)) * 0.5)
        if k <= 0:
            continue
        shown += 1
        yy = y + 110 + i * 96
        setc(ctx, hexc("#F3F5F8"), k); rrect(ctx, x + 50, yy, w - 100, 80, 12); ctx.fill()
        text(ctx, key, x + 80, yy + 52, 30, INK2, alpha=k)
        text(ctx, val, x + w - 80, yy + 52, 32, INK, True, "r", alpha=k)
    if intro and shown == 0:
        k = c.k(0)
        lines = intro.split("\n")
        for j, ln in enumerate(lines):
            text(ctx, ln, x + w / 2, y + h / 2 - 20 + j * 56, 40 if j == 0 else 30, INK if j == 0 else INK2, j == 0, "c", alpha=k)


def serial(ctx, c, x, y, w, h, lines_spec, title_s="Serial Monitor  ·  115200 baud"):
    window(ctx, x + 20, y + 20, w - 40, h - 40, title_s)
    setc(ctx, hexc("#0F1115")); ctx.rectangle(x + 20, y + 72, w - 40, h - 92 - 10); ctx.fill()
    yy = y + 130
    acc = {}
    for li, s, col in lines_spec:
        base = c.at(li) if isinstance(li, int) else li
        t0 = base + acc.get(li, 0.0)
        acc[li] = acc.get(li, 0.0) + len(s) / 60 + 0.25
        if c.t < t0:
            continue
        n = int((c.t - t0) * 60)
        shown = s[:n]
        text(ctx, shown, x + 50, yy, 26, col or hexc("#D7DCE3"), mono=True)
        yy += 44


def phone(ctx, c, x, y, w, h, screens):
    """screens: [(line, fn(ctx, px, py, pw, ph, c))] drawn inside a phone frame."""
    pw, ph = 340, 680
    px, py = x + w / 2 - pw / 2, y + h / 2 - ph / 2
    setc(ctx, hexc("#16181C")); rrect(ctx, px - 14, py - 14, pw + 28, ph + 28, 48); ctx.fill()
    setc(ctx, PAPER); rrect(ctx, px, py, pw, ph, 36); ctx.fill()
    cur = screens[0][1]
    for li, fn in screens:
        if c.t >= c.at(li):
            cur = fn
    ctx.save(); rrect(ctx, px, py, pw, ph, 36); ctx.clip(); cur(ctx, px, py, pw, ph, c); ctx.restore()


def scr_connect(ctx, px, py, pw, ph, c):
    text(ctx, "Range Book", px + 30, py + 70, 26, INK2, True)
    text(ctx, "BLIPR Chronograph", px + 30, py + 112, 30, INK, True)
    setc(ctx, CHAPTER_COL["test"]); rrect(ctx, px + 30, py + 170, pw - 60, 70, 16); ctx.fill()
    text(ctx, "Connect chronograph", px + pw / 2, py + 214, 24, PAPER, True, "c")
    setc(ctx, hexc("#F3F5F8")); rrect(ctx, px + 30, py + 280, pw - 60, 200, 16); ctx.fill()
    text(ctx, "Pick a device", px + 50, py + 320, 22, INK2, True)
    setc(ctx, hexc("#E4ECFA")); rrect(ctx, px + 44, py + 340, pw - 88, 56, 10); ctx.fill()
    text(ctx, "RB BLIPR", px + 64, py + 377, 24, INK, True)


def scr_shot(ctx, px, py, pw, ph, c):
    text(ctx, "BLIPR Chronograph", px + 30, py + 70, 26, INK, True)
    tag(ctx, "Connected", px + 30, py + 110, 20, PAPER, GOOD)
    text(ctx, "2,700", px + pw / 2, py + 270, 84, INK, True, "c")
    text(ctx, "fps  ·  test shot", px + pw / 2, py + 316, 24, INK2, True, "c")
    setc(ctx, hexc("#F3F5F8")); rrect(ctx, px + 30, py + 520, pw - 60, 70, 16); ctx.fill()
    text(ctx, "Test shot", px + pw / 2, py + 564, 24, INK, True, "c")


# ------------------------------------------------------------------ print settings
def print_table(ctx, c, x, y, w, h, rows):
    card(ctx, x, y, w, h)
    cols = [0.0, 0.25, 0.47]
    heads = ["Part", "Lay it on the bed", "Settings (ASA)"]
    for j, hd in enumerate(heads):
        text(ctx, hd, x + 36 + cols[j] * w, y + 62, 28, INK2, True)
    rh = (h - 100) / len(rows)
    for i, (li, a, b, cc) in enumerate(rows):
        k = c.k(li)
        if k <= 0:
            continue
        yy = y + 90 + i * rh
        setc(ctx, hexc("#F3F5F8"), k); rrect(ctx, x + 18, yy, w - 36, rh - 12, 12); ctx.fill()
        text(ctx, a, x + 36, yy + 50, 32, INK, True, alpha=k)
        para(ctx, b, x + 36 + cols[1] * w, yy + 50, w * 0.21, 29, INK, alpha=k)
        para(ctx, cc, x + 36 + cols[2] * w, yy + 50, w * 0.5, 29, BAD if "NOT" in cc else INK, alpha=k)


# ------------------------------------------------------------------ heat-set insert cross-section
def insert_section(good, depth_label="7.5 mm deep"):
    def fn(ctx, cx, cy, c):
        s = 28
        wall = hexc("#9AA4B5")
        # plastic block with a hole
        setc(ctx, wall); ctx.rectangle(cx - 6 * s, cy - 3 * s, 12 * s, 9 * s); ctx.fill()
        setc(ctx, PAPER); ctx.rectangle(cx - 2.05 * s, cy - 3 * s, 4.1 * s, 7.5 * s); ctx.fill()
        text(ctx, "4.1 mm hole", cx - 6 * s - 12, cy - 2 * s, 22, INK2, True, "r")
        text(ctx, depth_label, cx - 6 * s - 12, cy - 2 * s + 30, 22, INK2, True, "r")
        ctx.save(); ctx.translate(cx, cy - 3 * s + (0.3 if good else -0.8) * s + 2.85 * s)
        if not good:
            ctx.rotate(math.radians(10))
        ctx.scale(s, s); PT.insert(ctx, d=4.6, L=5.7); ctx.restore()
        # melted plastic hugging the insert
        if good:
            text(ctx, "straight, a hair below the top", cx, cy + 6 * s + 44, 24, INK, True, "c")
        else:
            text(ctx, "tilted and sticking up", cx, cy + 6 * s + 44, 24, INK, True, "c")
            text(ctx, "the screw won't line up", cx, cy + 6 * s + 78, 22, BAD, True, "c")
    return fn


# ------------------------------------------------------------------ radar foam + alignment
def radar_tape(ctx, c, x, y, w, h, line0=0):
    s = 22
    cx, cy = x + w * 0.42, y + h / 2 + 10
    rw, rd = 25 * s, 6 * s
    foam = hexc("#F4F1E6"); edge = hexc("#B9B39C")
    text(ctx, "Radar from above", cx, y + 70, 30, INK, True, "c")
    text(ctx, "FRONT: antenna face → window", cx, cy - rd / 2 - 70, 26, INK2, True, "c")
    arrow(ctx, cx - 240, cy - rd / 2 - 40, cx - 240, cy - rd / 2 - 110, INK2, 4, 16)
    setc(ctx, hexc("#1F6B3A")); ctx.rectangle(cx - rw / 2, cy - rd / 2, rw, rd); ctx.fill()
    setc(ctx, hexc("#C98F2C")); ctx.rectangle(cx - rw / 2, cy - rd / 2, rw, 0.8 * s); ctx.fill()
    for i in range(5):
        setc(ctx, GOLD_PIN); ctx.rectangle(cx + (-5.08 + i * 2.54) * s - 5, cy + rd / 2 - 4, 10, 30); ctx.fill()
    text(ctx, "BACK: pins", cx, cy + rd / 2 + 150, 26, INK2, True, "c")
    def strip(x0, y0, ww, hh, k):
        setc(ctx, foam, k); ctx.rectangle(x0, y0, ww, hh); ctx.fill()
        setc(ctx, edge, k); ctx.set_line_width(2); ctx.rectangle(x0, y0, ww, hh); ctx.stroke()
    k1 = c.k(line0)
    if k1:
        strip(cx - rw / 2 - 1.2 * s, cy - rd / 2, 1.2 * s, rd, k1)
        strip(cx + rw / 2, cy - rd / 2, 1.2 * s, rd, k1)
        tag(ctx, "foam", cx - rw / 2 - 40, cy, 26, PAPER, INK, k1, "r")
        tag(ctx, "foam", cx + rw / 2 + 40, cy, 26, PAPER, INK, k1)
    k2 = c.k(line0 + 1)
    if k2:
        strip(cx - rw / 2 + 60, cy + rd / 2 + 30, rw - 120, 1.2 * s, k2)
        tag(ctx, "foam across the back (beside the pins)", cx, cy + rd / 2 + 100, 24, PAPER, INK, k2, "c")
    k3 = c.k(line0 + 2)
    if k3:
        bx = x + w * 0.88
        text(ctx, "Side view", bx, y + 70, 30, INK, True, "c")
        setc(ctx, hexc("#1F6B3A")); ctx.rectangle(bx - 30, y + 330, 60, 300); ctx.fill()
        strip(bx - 30, y + 310, 60, 20, k3)
        tag(ctx, "20 mm strip on top", bx, y + 125, 24, PAPER, INK, k3, "c")
        setc(ctx, hexc("#9AA4B5"), k3); ctx.rectangle(bx - 50, y + 190 + 30 * (1 - k3), 100, 36); ctx.fill()
        text(ctx, "lid rib", bx + 60, y + 215 + 30 * (1 - k3), 22, INK2, True, alpha=k3)
        arrow(ctx, bx, y + 236, bx, y + 302, FOCUS, 5, 16, k3)


GOLD_PIN = hexc("#D8A93B")


def radar_align(good):
    def fn(ctx, cx, cy, c):
        s = 10
        cy = cy + 120
        setc(ctx, hexc("#9AA4B5")); ctx.rectangle(cx - 22 * s, cy - 14 * s, 44 * s, 3 * s); ctx.fill()
        setc(ctx, hexc("#EDEBE3")); ctx.rectangle(cx - 13 * s, cy - 14 * s, 26 * s, 3 * s); ctx.fill()
        text(ctx, "front wall + window", cx - 17.5 * s, cy - 14 * s - 12, 20, INK2, True, "c")
        ctx.save(); ctx.translate(cx, cy - 7.5 * s)
        if not good:
            ctx.rotate(math.radians(9)); ctx.translate(0, 1.2 * s)
        setc(ctx, FOCUS, 0.14); ctx.move_to(-10 * s, -3 * s); ctx.line_to(-19 * s, -27 * s); ctx.line_to(19 * s, -27 * s); ctx.line_to(10 * s, -3 * s); ctx.close_path(); ctx.fill()
        setc(ctx, hexc("#1F6B3A")); ctx.rectangle(-12.5 * s, -3 * s, 25 * s, 6 * s); ctx.fill()
        setc(ctx, hexc("#C98F2C")); ctx.rectangle(-12.5 * s, -3 * s, 25 * s, 0.7 * s); ctx.fill()
        ctx.restore()
        text(ctx, "radar (seen from above)", cx, cy + 2 * s, 20, INK2, True, "c")
        if good:
            text(ctx, "flat against the window frame", cx, cy + 9 * s, 26, INK, True, "c")
            text(ctx, "beam straight downrange", cx, cy + 9 * s + 34, 24, INK2, True, "c")
        else:
            text(ctx, "tipped in the pocket", cx, cy + 9 * s, 26, INK, True, "c")
            text(ctx, "beam points off to the side", cx, cy + 9 * s + 34, 24, BAD, True, "c")
    return fn


# ------------------------------------------------------------------ QT cable chain
def qt_chain(ctx, c, x, y, w, h, line0=0):
    jx = x + 210
    names = ["SCL", "SDA", "3V3", "GND"]
    setc(ctx, hexc("#1F5E3A")); rrect(ctx, x + 60, y + 430, 210, 270, 14); ctx.fill()
    jp = {}
    for i, nm in enumerate(names):
        py = y + 480 + i * 56
        jp[nm] = py
        setc(ctx, hexc("#202226")); ctx.rectangle(jx - 18, py - 18, 36, 36); ctx.fill()
        dot(ctx, jx, py, 7, hexc("#666"))
        text(ctx, nm, jx - 34, py + 9, 24, hexc("#FFE680"), True, "r")
    text(ctx, "J4 on the main board", x + 165, y + 735, 22, INK2, True, "c")
    sx, sy, ss = x + 560, y + 250, 11
    dx, dy, ds = x + 1000, y + 250, 10
    P(ctx, PT.stemma_board, sx, sy, ss, label="SHT45")
    P(ctx, PT.dfrobot, dx, dy, ds)
    text(ctx, "SHT45 (far-side end)", sx, y + 120, 26, INK, True, "c")
    text(ctx, "DFRobot 10-DoF (gun-side end)", dx, y + 120, 26, INK, True, "c")
    cols = {"GND": WIRE["GND"], "3V3": WIRE["5V"], "SDA": WIRE["SDA"], "SCL": WIRE["SCL"]}
    order = ["GND", "3V3", "SDA", "SCL"]
    k1 = c.k(line0, 1.6)
    for n, nm in enumerate(order):
        vx = x + 330 + (3 - n) * 12
        ty = sy + 15 - n * 10
        wire_path(ctx, [(jx + 18, jp[nm]), (vx, jp[nm]), (vx, ty), (sx - 8.5 * ss - 26, ty)], cols[nm], 6, k1, outline=False)
    if k1:
        tag(ctx, "150 mm STEMMA QT-to-pins cable", x + 40, y + 40, 24, PAPER, INK, min(1, k1 * 2))
    k2 = c.k(line0 + 1, 1.2)
    for n, nm in enumerate(order):
        o = (n - 1.5) * 8
        wire_path(ctx, [(sx + 8.5 * ss + 26, sy + o), (x + 760 + o, sy + o), (x + 760 + o, y + 420 + o), (dx - o, y + 420 + o), (dx - o, dy + 11 * ds + 4)],
                  cols[nm], 6, k2, outline=False)
    if k2:
        tag(ctx, "to-pins cable + DFRobot's Gravity cable", x + 770, y + 470, 22, PAPER, INK, min(1, k2 * 2))
    k3 = c.k(line0 + 2)
    if k3:
        bx, by = x + 560, y + 530
        card(ctx, bx, by, w - 600, 220, hexc("#F6F7F9"), shadow=False)
        text(ctx, "DFRobot pin labels", bx + 28, by + 46, 26, INK, True, alpha=k3)
        for i, (col, s_) in enumerate(((WIRE["5V"], "red → +"), (WIRE["GND"], "black → −"), (WIRE["SCL"], "yellow → C/R"), (WIRE["SDA"], "blue → D/T"))):
            xx = bx + 28 + (i % 2) * (w - 600) / 2
            yy = by + 100 + (i // 2) * 48
            setc(ctx, col, k3); ctx.set_line_width(9); ctx.new_path(); ctx.move_to(xx, yy - 9); ctx.line_to(xx + 40, yy - 9); ctx.stroke()
            text(ctx, s_, xx + 54, yy, 25, INK, alpha=k3)
        text(ctx, "Switch: I2C   ·   A0 and A1: 0", bx + 28, by + 196, 25, FOCUS, True, alpha=k3)


# ------------------------------------------------------------------ OLED animation frames
_gif = {}


def gif_frames(path):
    if path not in _gif:
        im = Image.open(path)
        frames, durs = [], []
        try:
            while True:
                frames.append(im.convert("RGBA").copy()); durs.append(im.info.get("duration", 100) / 1000)
                im.seek(im.tell() + 1)
        except EOFError:
            pass
        from draw import image_surface_from_pil
        _gif[path] = ([image_surface_from_pil(f) for f in frames], durs)
    return _gif[path]


def oled_play(ctx, c, x, y, w, h, path, t0_line=0, label=None):
    frames, durs = gif_frames(path)
    t = max(0, c.t - c.at(t0_line))
    total = sum(durs)
    t = t % total
    i = 0
    while i < len(durs) - 1 and t > durs[i]:
        t -= durs[i]; i += 1
    surf = frames[i]
    iw, ih = surf.get_width(), surf.get_height()
    s = min((w - 120) / iw, (h - 160) / ih)
    dw, dh = iw * s, ih * s
    ox, oy = x + (w - dw) / 2, y + (h - dh) / 2 - 10
    setc(ctx, hexc("#1E4FA3")); rrect(ctx, ox - 40, oy - 60, dw + 80, dh + 100, 18); ctx.fill()
    ctx.save(); ctx.translate(ox, oy); ctx.scale(s, s); ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_NEAREST); ctx.paint(); ctx.restore()
    if label:
        text(ctx, label, x + w / 2, y + h - 30, 24, INK2, True, "c")


# ------------------------------------------------------------------ troubleshooting cards
def trouble(ctx, c, x, y, w, h, items):
    n = len(items)
    rows = math.ceil(n / 2)
    gw, gh = (w - 20) / 2, (h - (rows - 1) * 16) / rows
    for i, (li, sym, fix) in enumerate(items):
        r, q = divmod(i, 2)
        cx, cy = x + q * (gw + 20), y + r * (gh + 16)
        k = c.k(li)
        if k <= 0:
            continue
        ctx.push_group()
        card(ctx, cx, cy, gw, gh)
        setc(ctx, CHAPTER_COL["trouble"]); rrect(ctx, cx, cy, 10, gh, 5); ctx.fill()
        text(ctx, sym, cx + 40, cy + 62, 36, INK, True)
        para(ctx, fix, cx + 40, cy + 118, gw - 80, 29, INK2)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(k)


def outro(ctx, c, x, y, w, h):
    title(ctx, c, x, y, w, h, sub="Built. Now go shoot.", hero="turn_0060")


# ------------------------------------------------------------------ op-amp pin voltages
def opamp_volts(ctx, c, x, y, w, h, line0=0):
    s = 34
    cx, cy = x + w / 2, y + h / 2 + 30
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s); PT.opamp_chip(ctx); ctx.restore()
    text(ctx, "MCP6022, seen from above, notch at the top", cx, y + 70, 28, INK, True, "c")
    pins = {}
    for i in range(4):
        pins[i + 1] = (cx - 3.81 * s, cy + (-3.81 + i * 2.54) * s)
        pins[8 - i] = (cx + 3.81 * s, cy + (-3.81 + i * 2.54) * s)
    for n, (px, py) in pins.items():
        text(ctx, str(n), px + (-40 if n <= 4 else 40), py + 10, 30, INK, True, "c")
    k0 = c.k(line0)
    if k0:
        ring(ctx, cx, cy - 4.8 * s, 30, c.since(line0), FOCUS, 5, k0)
        tag(ctx, "notch = pin 1 end", cx + 50, cy - 4.8 * s - 10, 24, PAPER, FOCUS, k0)
    specs = [(line0 + 1, [8], "3.25–3.35 V", WIRE["3V3"]), (line0 + 1, [3, 5], "1.60–1.70 V", hexc("#2457C9")),
             (line0 + 1, [1, 7], "1.60–1.70 V", GOOD), (line0 + 1, [4], "0 V (ground)", INK)]
    for j, (li, ns, val, col) in enumerate(specs):
        k = ramp(c.t, c.at(li) + j * 1.2, 0.4)
        if k <= 0:
            continue
        for n in ns:
            px, py = pins[n]
            left = n <= 4
            tag(ctx, "pin %d: %s" % (n, val), px + (-80 if left else 80), py, 24, PAPER, col, k, "r" if left else "l")


def pigtail_check(ctx, c, x, y, w, h):
    pitch = 80
    hx, hy = x + 200, y + 200
    setc(ctx, hexc("#202226")); rrect(ctx, hx - pitch / 2, hy - 32, pitch * 5, 64, 6); ctx.fill()
    pins = [(hx + i * pitch, hy) for i in range(5)]
    cols = [WIRE["Q"], WIRE["3V3"], WIRE["I"], WIRE["GND"], None]
    for i, (px, py) in enumerate(pins):
        setc(ctx, hexc("#55585E")); ctx.rectangle(px - 13, py - 13, 26, 26); ctx.fill()
        text(ctx, str(i + 1), px, py - 52, 34, INK, True, "c")
        if cols[i]:
            wire_path(ctx, [(px, py + 14), (px, py + 140)], cols[i], 10)
    text(ctx, "your pigtail header", hx - pitch / 2, hy + 190, 24, INK2, True)
    k1 = c.k(1)
    if k1:
        for (i, target, col) in ((1, "U3 OUT leg (right-hand leg)", WIRE["3V3"]), (3, "ground (J1 pin 2)", INK)):
            px, py = pins[i]
            ring(ctx, px, py, 30, c.since(1), FOCUS, 5, k1)
        P(ctx, PT.multimeter, x + w - 200, y + 230, 6.0, alpha=k1, reading="000")
        tag(ctx, "beep", x + w - 200, y + 420, 30, PAPER, GOOD, k1, "c")
        tag(ctx, "Pin 2  →  U3 output leg", x + 100, y + h - 200, 30, PAPER, WIRE["3V3"], k1)
        tag(ctx, "Pin 4  →  ground", x + 100, y + h - 130, 30, PAPER, INK, k1)
    k2 = c.k(2)
    if k2:
        setc(ctx, PAPER, k2); ctx.rectangle(x, y, w, h); ctx.fill()
        rx, ry = x + w / 2 - 160, y + h / 2 + 40
        P(ctx, PT.radar, rx, ry, 13, side="back", alpha=k2)
        text(ctx, "Radar, seen from the back", rx, ry + 13 * 13 + 50, 26, INK2, True, "c", alpha=k2)
        p1x, p1y = rx - 5.08 * 13, ry - 10.4 * 13
        ring(ctx, p1x, p1y, 26, c.since(2), FOCUS, 5, k2)
        tag(ctx, "pin 1 to pin 1", p1x - 40, p1y - 60, 28, PAPER, FOCUS, k2, "r")
        bx = x + w - 330
        card(ctx, bx, y + 150, 280, 300, hexc("#FFF7D6"), shadow=False)
        para(ctx, "Touch something grounded first. Hold the radar by its edges.", bx + 24, y + 210, 236, 27, INK, alpha=k2)
