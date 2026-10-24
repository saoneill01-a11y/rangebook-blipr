"""The v1.1 main board, drawn from pcb/design.py (exact part positions), with parts that can be 'soldered in'."""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import sys, math, cairo
sys.path.insert(0, REPO + "/pcb")
import design as D
import fab
import parts as PT
from draw import setc, hexc, rrect, font, PAPER, WIRE

import os as _os
_cwd = _os.getcwd(); _os.chdir(REPO + "/pcb")
PADS, WIRES, VIAS = fab.load()
_os.chdir(_cwd)
PADMAP = {(p["ref"], p["pin"]): p for p in PADS}

BOARD_COL = hexc("#1F5E3A")
SILK = hexc("#F4F4F4")
LABEL = hexc("#FFE680")

ALL_R = [r for r in D.P if r.startswith("R")]
ALL_C = [r for r in D.P if r.startswith("C")]
ELEC = [r for r in ALL_C if D.P[r]["fp"]["body"][0] == "circle"]
CERAMIC = [r for r in ALL_C if r not in ELEC]
VAL_TO_CODE = {"10": "10", "100": "100", "330": "330", "470": "470", "1k": "1k", "4.7k": "4.7k", "10k": "10k", "100k": "100k"}


def pad(ref, pin):
    return PADMAP[(ref, pin)]


class Board:
    def __init__(self):
        self.vp = (0, 0, 1280, 830)
        self.cx, self.cy, self.S = 35.0, 45.0, 8.0

    def view(self, vp, cx, cy, S):
        self.vp, self.cx, self.cy, self.S = vp, cx, cy, S

    def w2s(self, x, y):
        vx, vy, vw, vh = self.vp
        return vx + vw / 2 + (x - self.cx) * self.S, vy + vh / 2 - (y - self.cy) * self.S

    def apply(self, ctx):
        vx, vy, vw, vh = self.vp
        ctx.translate(vx + vw / 2, vy + vh / 2)
        ctx.scale(self.S, -self.S)
        ctx.translate(-self.cx, -self.cy)

    # ------------------------------------------------------------ draw
    def draw(self, ctx, placed=None, dim=None, show_traces=True, labels=True, chips=None, modules=None, extra=None):
        """placed: {ref: progress 0..1}; chips: {'U1': p, 'U2': p}; modules: {'U4': p, 'U5': p}."""
        placed = placed or {}
        chips = chips or {}
        modules = modules or {}
        vx, vy, vw, vh = self.vp
        ctx.save()
        ctx.rectangle(vx, vy, vw, vh); ctx.clip()
        self.apply(ctx)
        # board + shadow
        setc(ctx, hexc("#000000", 0.18)); rrect(ctx, 0.8, -1.2, D.BOARD_W, D.BOARD_H, 1.2); ctx.fill()
        setc(ctx, BOARD_COL); rrect(ctx, 0, 0, D.BOARD_W, D.BOARD_H, 1.0); ctx.fill()
        if show_traces:
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for w in WIRES:
                setc(ctx, hexc("#E8A33A", 0.20) if w["layer"] == "F.Cu" else hexc("#4AA3DF", 0.10))
                ctx.set_line_width(w["w"])
                pts = w["pts"]; ctx.move_to(*pts[0])
                for p in pts[1:]:
                    ctx.line_to(*p)
                ctx.stroke()
        for p in PADS:
            setc(ctx, hexc("#D9D9D9"))
            if p["sh"] == "rect":
                ctx.rectangle(p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["w"], p["h"])
            else:
                ctx.arc(p["x"], p["y"], max(p["w"], p["h"]) / 2, 0, 2 * math.pi)
            ctx.fill()
            setc(ctx, hexc("#111111")); ctx.arc(p["x"], p["y"], p["dr"] / 2, 0, 2 * math.pi); ctx.fill()
        for hx, hy in D.HOLES:
            setc(ctx, PAPER); ctx.arc(hx, hy, D.HOLE_D / 2, 0, 2 * math.pi); ctx.fill()
        # silk outlines
        ctx.set_line_width(0.16)
        for ref, pp in D.P.items():
            for path in fab.outline_paths(ref, pp):
                setc(ctx, SILK, 0.85)
                ctx.move_to(*path[0])
                for q in path[1:]:
                    ctx.line_to(*q)
                ctx.stroke()
        if labels:
            self._labels(ctx, placed, chips, modules)
        # parts
        for ref, k in placed.items():
            if k > 0 and ref in D.P:
                self._part(ctx, ref, k)
        for ref, k in chips.items():
            if k > 0:
                self._chip(ctx, ref, k)
        for ref, k in modules.items():
            if k > 0:
                self._module(ctx, ref, k)
        if extra:
            extra(ctx)
        ctx.restore()

    def _text(self, ctx, s, x, y, size, col, rot=0, bold=True, alpha=1.0):
        ctx.save(); ctx.translate(x, y); ctx.scale(1, -1); ctx.rotate(-math.radians(rot))
        font(ctx, size, bold); setc(ctx, col, alpha)
        lines = s.split("\n")
        for i, ln in enumerate(lines):
            e = ctx.text_extents(ln)
            ctx.move_to(-e.x_advance / 2, size * 0.36 + (i - (len(lines) - 1) / 2) * size * 1.05)
            ctx.show_text(ln)
        ctx.restore()

    def _labels(self, ctx, placed, chips, modules):
        for ref, pp in D.P.items():
            if placed.get(ref, 0) >= 1:
                continue
            lp = fab.label_pos(ref, pp)
            if ref in ("U1", "U2"):
                if chips.get(ref, 0) < 1 and placed.get(ref + "s", 0) < 1:
                    self._text(ctx, ref + "\nMCP6022", pp["x"], pp["y"], 0.95, LABEL)
                continue
            if ref == "U3":
                self._text(ctx, "U3", pp["x"], pp["y"] + 3.4, 0.95, LABEL)
                continue
            if lp:
                txt = ref + ("\n" + pp["value"] if ref[0] in "RCD" else "")
                self._text(ctx, txt, lp[0], lp[1], 0.78, LABEL, lp[2])
        for ref, nm in (("J1", "J1 POWER"), ("J2", "J2 RADAR  Q VCC I GND"), ("J3", "J3 OLED"), ("J4", "J4 SENSORS"), ("J5", "J5 not used")):
            pp = D.P[ref]
            n = len(pp["fp"]["pads"])
            if ref == "J2":
                self._text(ctx, nm, pp["x"] + 2.0, pp["y"] - 3.2, 0.95, LABEL)
            else:
                self._text(ctx, nm, pp["x"] + 2.6, pp["y"] + n * 1.27 + 0.9, 0.8, LABEL)
        for jr in ("J1", "J3", "J4"):
            names = fab.HEADER_PINS[jr]
            for i, nm in enumerate(names):
                q = pad(jr, str(i + 1))
                self._text(ctx, nm, q["x"] + 2.6, q["y"], 0.72, LABEL)
        if modules.get("U5", 0) < 1:
            self._text(ctx, "U5  Teensy 4.1\nUSB to the right edge", 38, 75, 1.6, LABEL)
        if modules.get("U4", 0) < 1:
            u = D.P["U4"]
            self._text(ctx, "U4 ESP32-C3\nchip side up\nUSB to the back", u["x"], u["y"] - 9.0, 0.9, LABEL)
            for row, names in (("A", D.E_RIGHT), ("B", D.E_LEFT)):
                for i, nm in enumerate(names):
                    q = pad("U4", "%s%d" % (row, i))
                    self._text(ctx, nm, q["x"] + (-1.9 if row == "A" else 1.9), q["y"], 0.72, LABEL)

    def _enter(self, ctx, x, y, k):
        """Drop-in animation: scale 1.35 -> 1 with a fading shadow."""
        s = 1 + 0.35 * (1 - k)
        ctx.translate(x, y)
        ctx.scale(s, s)
        return k

    def _part(self, ctx, ref, k):
        pp = D.P[ref]; fp = pp["fp"]; b = fp["body"]
        ctx.save()
        ctx.push_group()
        self._enter(ctx, pp["x"], pp["y"], k)
        ctx.rotate(math.radians(pp["rot"]))
        if ref.startswith("R"):
            pitch = 10.16
            PT.resistor(ctx, VAL_TO_CODE.get(pp["value"], "10k"), lead=pitch / 2 - 3.15)
        elif ref == "D1":
            PT.diode(ctx, lead=10.16 / 2 - 2.6)
        elif ref in ELEC:
            PT.electrolytic_top(ctx, d=b[1], minus_dir=0.0)
        elif ref in CERAMIC:
            setc(ctx, PT.LEAD); ctx.set_line_width(0.5); ctx.move_to(-2.54, 0); ctx.line_to(2.54, 0); ctx.stroke()
            PT.ceramic(ctx, top=True)
        elif ref == "U3":
            setc(ctx, hexc("#1B1D21"))
            ctx.move_to(-2.4, -1.3); ctx.line_to(2.4, -1.3); ctx.line_to(2.4, 1.0); ctx.arc(0, 1.0, 2.4, 0, math.pi); ctx.close_path(); ctx.fill()
            setc(ctx, hexc("#9AA0A8")); ctx.set_line_width(0.25); ctx.move_to(-2.4, -1.25); ctx.line_to(2.4, -1.25); ctx.stroke()
        elif ref.startswith("J"):
            n = len(fp["pads"])
            ctx.translate((n - 1) * 2.54 / 2 - 2.54 * (n - 1) / 2, 0)
            ctx.scale(1, -1)
            (PT.header_female if ref == "J4" else PT.header_male)(ctx, n)
            ctx.translate(-(n - 1) * 2.54 / 2, 0)
        elif ref in ("U1s", "U2s"):
            pass
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(min(1.0, k * 1.5))
        ctx.restore()

    def socket(self, ctx, ref, k):
        pp = D.P[ref]
        ctx.save(); ctx.push_group()
        self._enter(ctx, pp["x"], pp["y"], k)
        ctx.rotate(math.radians(pp["rot"])); ctx.scale(1, -1)
        PT.dip_socket(ctx)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, k * 1.5)); ctx.restore()

    def _chip(self, ctx, ref, k):
        pp = D.P[ref]
        ctx.save(); ctx.push_group()
        self._enter(ctx, pp["x"], pp["y"], k)
        ctx.rotate(math.radians(pp["rot"])); ctx.scale(1, -1)
        PT.opamp_chip(ctx)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, k * 1.5)); ctx.restore()

    def female_headers(self, ctx, which, k):
        ctx.save(); ctx.push_group()
        if which == "U5":
            for sy in (-7.62, 7.62):
                ctx.save(); ctx.translate(68.0 - 23 * 2.54 / 2, 75.0 + sy); PT.header_female(ctx, 24); ctx.restore()
        else:
            for sx in (-7.62, 7.62):
                ctx.save(); ctx.translate(17.0 + sx, 20.4 - 7 * 2.54 / 2); PT.header_female(ctx, 8, along="y"); ctx.restore()
        ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, k * 1.5)); ctx.restore()

    def _module(self, ctx, ref, k):
        ctx.save(); ctx.push_group()
        if ref == "U5":
            self._enter(ctx, 68.0 + 1.27 - 30.5, 75.0, k)
            ctx.scale(1, -1)
            PT.teensy(ctx)
        else:
            self._enter(ctx, 17.0, 20.4 + 2.4 - 11.25, k)
            ctx.scale(1, -1)
            PT.esp32(ctx, labels=False)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, k * 1.5)); ctx.restore()

    # helpers for overlays (screen coords)
    def part_xy(self, ref):
        pp = D.P[ref]
        return self.w2s(pp["x"], pp["y"])

    def pad_xy(self, ref, pin):
        p = pad(ref, pin)
        return self.w2s(p["x"], p["y"])

    def part_box(self, ref, margin=1.5):
        xs, ys = [], []
        for p in PADS:
            if p["ref"] == ref:
                xs.append(p["x"]); ys.append(p["y"])
        pp = D.P[ref]
        b = pp["fp"]["body"]
        if b[0] == "circle":
            r = b[1] / 2
            xs += [pp["x"] - r, pp["x"] + r]; ys += [pp["y"] - r, pp["y"] + r]
        x0, y0 = self.w2s(min(xs) - margin, max(ys) + margin)
        x1, y1 = self.w2s(max(xs) + margin, min(ys) - margin)
        return x0, y0, x1 - x0, y1 - y0
