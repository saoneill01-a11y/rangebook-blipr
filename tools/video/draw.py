"""Cairo drawing helpers for the BLIPR build video."""
import math, cairo

W, H = 1920, 1080

# ---------------------------------------------------------------- palette
def hexc(h, a=1.0):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

BG = hexc("#F3F4F6")
INK = hexc("#121621")
INK2 = hexc("#4A5263")
PAPER = hexc("#FFFFFF")
RULE = hexc("#D5D9E0")
FOCUS = hexc("#E8197D")      # magenta: "look here" (not used by any wire)
GOOD = hexc("#16A34A")
BAD = hexc("#DC2626")
WARN = hexc("#F59E0B")
NOTE_BG = hexc("#FFF7D6")

# wire colours (same as the build guide's wiring pictures)
WIRE = {
    "5V": hexc("#D7263D"), "BAT": hexc("#8B4513"), "GND": hexc("#1B1B1B"), "3V3": hexc("#F28C28"),
    "I": hexc("#2E9E44"), "Q": hexc("#1F6FC0"), "SDA": hexc("#1F6FC0"), "SCL": hexc("#E3B505"),
}

CHAPTER_COL = {
    "intro": hexc("#334155"), "kit": hexc("#0E7490"), "safety": hexc("#DC2626"), "prep": hexc("#7C3AED"),
    "board": hexc("#15803D"), "power": hexc("#D97706"), "wiring": hexc("#1D4ED8"), "case": hexc("#9333EA"),
    "sensors": hexc("#0F766E"), "firmware": hexc("#4338CA"), "test": hexc("#BE123C"), "trouble": hexc("#B45309"),
}

FONT = "Inter"
MONO = "DejaVu Sans Mono"


def setc(ctx, c, a=None):
    if a is not None:
        ctx.set_source_rgba(c[0], c[1], c[2], (c[3] if len(c) > 3 else 1) * a)
    else:
        ctx.set_source_rgba(*c) if len(c) == 4 else ctx.set_source_rgb(*c)


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def font(ctx, size, bold=False, mono=False, weight=None):
    fam = MONO if mono else FONT
    if weight == "semi" and not mono:
        fam = "Inter SemiBold"; bold = False
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text(ctx, s, x, y, size=28, col=INK, bold=False, anchor="l", mono=False, alpha=1.0, weight=None):
    """anchor: l / c / r (horizontal); y is the baseline."""
    font(ctx, size, bold, mono, weight)
    e = ctx.text_extents(s)
    if anchor == "c":
        x -= e.x_advance / 2
    elif anchor == "r":
        x -= e.x_advance
    setc(ctx, col, alpha)
    ctx.move_to(x, y)
    ctx.show_text(s)
    return e.x_advance


def text_w(ctx, s, size=28, bold=False, mono=False, weight=None):
    font(ctx, size, bold, mono, weight)
    return ctx.text_extents(s).x_advance


def wrap(ctx, s, maxw, size=28, bold=False, weight=None):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if text_w(ctx, t, size, bold, weight=weight) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur:
        lines.append(cur)
    return lines


def para(ctx, s, x, y, maxw, size=28, col=INK, bold=False, lh=1.32, alpha=1.0, anchor="l", weight=None):
    lines = wrap(ctx, s, maxw, size, bold, weight)
    for i, ln in enumerate(lines):
        text(ctx, ln, x, y + i * size * lh, size, col, bold, anchor, alpha=alpha, weight=weight)
    return len(lines) * size * lh


def arrow(ctx, x0, y0, x1, y1, col=FOCUS, lw=6, head=22, alpha=1.0, prog=1.0):
    """Straight arrow drawn from (x0,y0) toward (x1,y1); prog 0..1 grows it."""
    x1 = x0 + (x1 - x0) * prog
    y1 = y0 + (y1 - y0) * prog
    a = math.atan2(y1 - y0, x1 - x0)
    setc(ctx, col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0)
    ctx.line_to(x1 - math.cos(a) * head * 0.6, y1 - math.sin(a) * head * 0.6)
    ctx.stroke()
    ctx.move_to(x1, y1)
    ctx.line_to(x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45))
    ctx.line_to(x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))
    ctx.close_path()
    ctx.fill()


def curve_arrow(ctx, pts, col=FOCUS, lw=6, head=22, alpha=1.0):
    """Arrow along a cubic: pts = (p0, c1, c2, p1)."""
    (x0, y0), (a1, b1), (a2, b2), (x1, y1) = pts
    setc(ctx, col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0)
    ctx.curve_to(a1, b1, a2, b2, x1, y1)
    ctx.stroke()
    a = math.atan2(y1 - b2, x1 - a2)
    ctx.move_to(x1 + math.cos(a) * 4, y1 + math.sin(a) * 4)
    ctx.line_to(x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45))
    ctx.line_to(x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))
    ctx.close_path()
    ctx.fill()


def ring(ctx, x, y, r, t=0.0, col=FOCUS, lw=6, alpha=1.0):
    """Pulsing focus ring."""
    pulse = 1 + 0.08 * math.sin(t * 2 * math.pi * 1.2)
    ctx.new_path()
    setc(ctx, col, alpha)
    ctx.set_line_width(lw)
    ctx.arc(x, y, r * pulse, 0, 2 * math.pi)
    ctx.stroke()
    setc(ctx, col, alpha * 0.25 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.2)))
    ctx.set_line_width(lw * 2.2)
    ctx.new_path()
    ctx.arc(x, y, r * pulse + lw * 1.6, 0, 2 * math.pi)
    ctx.stroke()


def box_focus(ctx, x, y, w, h, t=0.0, col=FOCUS, lw=6, alpha=1.0, r=10):
    p = 4 * math.sin(t * 2 * math.pi * 1.2)
    setc(ctx, col, alpha)
    ctx.set_line_width(lw)
    rrect(ctx, x - p, y - p, w + 2 * p, h + 2 * p, r)
    ctx.stroke()


def tag(ctx, s, x, y, size=26, fg=PAPER, bg=FOCUS, alpha=1.0, anchor="l", pad=12, bold=True):
    """Label pill; (x,y) = left-middle (or centre/right with anchor)."""
    w = text_w(ctx, s, size, bold) + 2 * pad
    h = size + pad * 1.2
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    setc(ctx, bg, alpha)
    rrect(ctx, x, y - h / 2, w, h, h / 2.4)
    ctx.fill()
    text(ctx, s, x + pad, y + size * 0.36, size, fg, bold, alpha=alpha)
    return w


def check(ctx, x, y, s=60, alpha=1.0):
    ctx.new_path()
    setc(ctx, GOOD, alpha)
    ctx.arc(x, y, s / 2, 0, 2 * math.pi); ctx.fill()
    setc(ctx, PAPER, alpha)
    ctx.set_line_width(s * 0.12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x - s * 0.22, y + s * 0.02); ctx.line_to(x - s * 0.05, y + s * 0.18); ctx.line_to(x + s * 0.24, y - s * 0.16)
    ctx.stroke()


def cross(ctx, x, y, s=60, alpha=1.0):
    ctx.new_path()
    setc(ctx, BAD, alpha)
    ctx.arc(x, y, s / 2, 0, 2 * math.pi); ctx.fill()
    setc(ctx, PAPER, alpha)
    ctx.set_line_width(s * 0.12); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    d = s * 0.18
    ctx.move_to(x - d, y - d); ctx.line_to(x + d, y + d); ctx.move_to(x + d, y - d); ctx.line_to(x - d, y + d)
    ctx.stroke()


def warn_icon(ctx, x, y, s=60, alpha=1.0):
    setc(ctx, WARN, alpha)
    ctx.move_to(x, y - s / 2); ctx.line_to(x + s / 2, y + s * 0.4); ctx.line_to(x - s / 2, y + s * 0.4); ctx.close_path(); ctx.fill()
    text(ctx, "!", x, y + s * 0.3, s * 0.62, INK, True, "c", alpha=alpha)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ramp(t, t0, dur=0.4):
    """0 before t0, eases to 1 over dur."""
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return ease((t - t0) / dur)


def lerp(a, b, k):
    return a + (b - a) * k


_KEEP = {}


def release(surf):
    _KEEP.pop(id(surf), None)


def image_surface_from_pil(im):
    """PIL RGBA image -> cairo ImageSurface (premultiplied BGRA)."""
    import numpy as np
    im = im.convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    alpha = a[:, :, 3:4] / 255.0
    rgb = a[:, :, :3] * alpha
    bgra = np.dstack([rgb[:, :, 2], rgb[:, :, 1], rgb[:, :, 0], a[:, :, 3]]).astype(np.uint8)
    h, w = bgra.shape[:2]
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    buf = bytearray(stride * h)
    import numpy as np2
    arr = np2.frombuffer(buf, dtype=np2.uint8).reshape(h, stride)
    arr[:, :w * 4] = bgra.reshape(h, w * 4)
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, stride)
    _KEEP[id(surf)] = buf
    return surf


def paint_image(ctx, surf, x, y, w, h, alpha=1.0, src=None):
    """Draw surf scaled into (x,y,w,h). src = (sx,sy,sw,sh) crop in image pixels."""
    iw, ih = surf.get_width(), surf.get_height()
    sx, sy, sw, sh = src if src else (0, 0, iw, ih)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.translate(x, y)
    ctx.scale(w / sw, h / sh)
    ctx.translate(-sx, -sy)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def fit(iw, ih, bw, bh):
    s = min(bw / iw, bh / ih)
    return iw * s, ih * s
