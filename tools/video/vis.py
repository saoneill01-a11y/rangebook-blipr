"""Reusable visuals: images with a moving camera, the board, 3D frame sequences, cards and diagrams."""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import math, os, glob
import cairo
from PIL import Image
from draw import *
import parts as PT
import board as board_mod

_img_cache = {}


def load_surface(path, max_w=None):
    key = (path, max_w)
    if key not in _img_cache:
        im = Image.open(path).convert("RGBA")
        if max_w and im.width > max_w:
            im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
        _img_cache[key] = image_surface_from_pil(im)
    return _img_cache[key]


def card(ctx, x, y, w, h, col=PAPER, r=18, shadow=True):
    if shadow:
        setc(ctx, hexc("#000000", 0.06)); rrect(ctx, x + 3, y + 5, w, h, r); ctx.fill()
    setc(ctx, col); rrect(ctx, x, y, w, h, r); ctx.fill()


def interp_cam(cams, c, t):
    """cams: [(line, value_tuple)], eased 1.0 s moves starting at each line."""
    cur = cams[0][1]
    for li, val in cams[1:]:
        t0 = c.at(li) if isinstance(li, int) else li
        k = ramp(t, t0, 1.1)
        if k <= 0:
            break
        cur = tuple(lerp(a, b, k) for a, b in zip(cur, val))
    return cur


# ------------------------------------------------------------------ overlays (screen space)
def draw_overlay(ctx, o, c, P):
    """o: dict with 'at' (line) and 'kind'; P maps source coords -> screen."""
    li = o.get("at", 0)
    t0 = c.at(li) + o.get("delay", 0.0) if isinstance(li, int) else li
    if c.t < t0:
        return
    if "until" in o:
        u = o["until"]
        tu = c.at(u) if isinstance(u, int) else u
        if c.t > tu:
            return
    k = ramp(c.t, t0, 0.4)
    tt = c.t - t0
    kind = o["kind"]
    col = o.get("col", FOCUS)
    if kind == "ring":
        x, y = P(*o["xy"]); r = o.get("r", 40)
        ring(ctx, x, y, r * (0.6 + 0.4 * k), tt, col, o.get("lw", 6), k)
    elif kind == "box":
        x0, y0 = P(o["xywh"][0], o["xywh"][1]); x1, y1 = P(o["xywh"][0] + o["xywh"][2], o["xywh"][1] + o["xywh"][3])
        box_focus(ctx, min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), tt, col, o.get("lw", 6), k)
    elif kind == "arrow":
        x0, y0 = P(*o["from"]); x1, y1 = P(*o["to"])
        arrow(ctx, x0, y0, x1, y1, col, o.get("lw", 7), 26, 1.0, ease(min(1, tt / 0.6)))
    elif kind == "tag":
        x, y = P(*o["xy"])
        tag(ctx, o["text"], x, y, o.get("size", 28), o.get("fg", PAPER), col, k, o.get("anchor", "l"))
    elif kind == "check":
        x, y = P(*o["xy"]); check(ctx, x, y, o.get("s", 64), k)
    elif kind == "cross":
        x, y = P(*o["xy"]); cross(ctx, x, y, o.get("s", 64), k)
    elif kind == "label":
        x, y = P(*o["xy"])
        text(ctx, o["text"], x, y, o.get("size", 28), o.get("col", INK), True, o.get("anchor", "l"), alpha=k)
    elif kind == "fn":
        o["fn"](ctx, c, P, k, tt)


# ------------------------------------------------------------------ image with camera
def image_view(path, cams=None, overlays=None, max_w=2600, pad=24, frame=True, bgcol=PAPER):
    surf = load_surface(path, max_w)
    iw, ih = surf.get_width(), surf.get_height()
    cams = cams or [(0, (0, 0, iw, ih))]

    def vis(ctx, c):
        x, y, w, h = c.rect
        if frame:
            card(ctx, x, y, w, h, bgcol)
        bx, by, bw, bh = x + pad, y + pad, w - 2 * pad, h - 2 * pad
        sx, sy, sw, sh = interp_cam(cams, c, c.t)
        # keep the crop's aspect = box aspect (expand the crop)
        ar = bw / bh
        if sw / sh > ar:
            nh = sw / ar; sy -= (nh - sh) / 2; sh = nh
        else:
            nw = sh * ar; sx -= (nw - sw) / 2; sw = nw
        ctx.save(); ctx.rectangle(bx, by, bw, bh); ctx.clip()
        setc(ctx, bgcol); ctx.rectangle(bx, by, bw, bh); ctx.fill()
        ctx.translate(bx, by); ctx.scale(bw / sw, bh / sh); ctx.translate(-sx, -sy)
        ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD); ctx.paint()
        ctx.restore()
        P = lambda u, v: (bx + (u - sx) * bw / sw, by + (v - sy) * bh / sh)
        for o in overlays or []:
            draw_overlay(ctx, o, c, P)
    return vis


# ------------------------------------------------------------------ board
def board_view(board, cams, place=None, overlays=None, chips=None, sockets=None, fheaders=None, modules=None, extra=None,
               traces=True, labels=True):
    """cams: [(line, (cx, cy, mm_wide))]; place: [(line, delay, [refs], stagger)];
    chips/sockets/fheaders/modules: [(line, delay, ref)]."""
    def prog(spec, c):
        out = {}
        for li, delay, refs, *st in spec or []:
            stg = st[0] if st else 0.25
            refs = refs if isinstance(refs, (list, tuple)) else [refs]
            for j, r in enumerate(refs):
                t0 = (c.at(li) if isinstance(li, int) else li) + delay + j * stg
                out[r] = max(out.get(r, 0), ramp(c.t, t0, 0.5))
        return out

    def vis(ctx, c):
        x, y, w, h = c.rect
        card(ctx, x, y, w, h, hexc("#E6E9EE"))
        cx, cy, mm = interp_cam(cams, c, c.t)
        S = min(w / mm, h / (mm * h / w)) if False else w / mm
        board.view((x, y, w, h), cx, cy, S)
        pl = prog(place, c)
        ch = prog([(a, b, [r]) for a, b, r in (chips or [])], c)
        so = prog([(a, b, [r]) for a, b, r in (sockets or [])], c)
        fh = prog([(a, b, [r]) for a, b, r in (fheaders or [])], c)
        mo = prog([(a, b, [r]) for a, b, r in (modules or [])], c)

        def ex(cx_):
            for r, k in so.items():
                if k > 0:
                    board.socket(cx_, r, k)
            for r, k in fh.items():
                if k > 0:
                    board.female_headers(cx_, r, k)
        for r in so:
            pl[r + "s"] = so[r]
        board.draw(ctx, placed=pl, chips=ch, modules=mo, extra=ex, show_traces=traces, labels=labels)
        if extra:
            extra(ctx, c, board)
        # highlight parts while they are being placed
        for li, delay, refs, *st in place or []:
            if delay < -50:
                continue
            stg = st[0] if st else 0.25
            refs = refs if isinstance(refs, (list, tuple)) else [refs]
            for j, r in enumerate(refs):
                t0 = (c.at(li) if isinstance(li, int) else li) + delay + j * stg
                dt = c.t - t0
                if 0 <= dt <= 3.2 and r in board_mod.D.P:
                    a = min(1, dt / 0.3) * min(1, (3.2 - dt) / 0.6)
                    bx, by, bw, bh = board.part_box(r, 1.0)
                    box_focus(ctx, bx, by, bw, bh, dt, FOCUS, 4, a, 8)
        P = lambda u, v: board.w2s(u, v)
        for o in overlays or []:
            draw_overlay(ctx, o, c, P)
    return vis


# ------------------------------------------------------------------ 3D frame sequences
_seq_cache = {}
_seq_lru = {}


def _seq_surface(path):
    if path not in _seq_lru:
        if len(_seq_lru) > 12:
            old = _seq_lru.pop(next(iter(_seq_lru)))
            old.finish(); release(old)
        im = Image.open(path).convert("RGBA")
        _seq_lru[path] = image_surface_from_pil(im)
    return _seq_lru[path]


def seq_frames(name):
    if name not in _seq_cache:
        _seq_cache[name] = sorted(glob.glob(f"{BUILD}/3d/{name}_*.png"))
    return _seq_cache[name]


def seq_view(name, play, overlays=None, bgcol=PAPER, frame=True, zoom=1.0):
    """play: [(line, delay, f0, f1, seconds)] segments; between them the last frame holds."""
    frames = seq_frames(name)

    def vis(ctx, c):
        x, y, w, h = c.rect
        if frame:
            card(ctx, x, y, w, h, bgcol)
        fi = play[0][2]
        for li, delay, f0, f1, secs in play:
            t0 = (c.at(li) if isinstance(li, int) else li) + delay
            if c.t >= t0:
                k = ease(min(1, (c.t - t0) / secs)) if secs > 0 else 1
                fi = int(round(f0 + (f1 - f0) * k))
        fi = max(0, min(len(frames) - 1, fi))
        surf = _seq_surface(frames[fi])
        iw, ih = surf.get_width(), surf.get_height()
        s = min(w / iw, h / ih) * zoom
        dw, dh = iw * s, ih * s
        ox, oy = x + (w - dw) / 2, y + (h - dh) / 2
        ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
        ctx.translate(ox, oy); ctx.scale(s, s); ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD); ctx.paint(); ctx.restore()
        P = lambda u, v: (ox + u * s, oy + v * s)
        for o in overlays or []:
            draw_overlay(ctx, o, c, P)
    return vis


# ------------------------------------------------------------------ item cards (checklist)
_INK = {}


def _ink(i, fn, kw):
    key = (fn.__name__, tuple(sorted(kw.items())))
    if key not in _INK:
        rec = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
        cc = cairo.Context(rec)
        fn(cc, **kw)
        _INK[key] = rec.ink_extents()
    return _INK[key]


def items_view(items, cols=4, title=None, start_line=0, stagger=0.35, line_map=None):
    """items: [(draw_fn, kwargs, size_key, label, sub)]; each appears in turn."""
    def vis(ctx, c):
        x, y, w, h = c.rect
        top = y
        if title:
            text(ctx, title, x + 8, y + 34, 30, INK2, True)
            top += 52
        rows = math.ceil(len(items) / cols)
        gw, gh = (w + 20) / cols - 20, (h - (top - y) + 20) / rows - 20
        for i, (fn, kw, sk, label, sub) in enumerate(items):
            r, q = divmod(i, cols)
            cx, cy = x + q * (gw + 20), top + r * (gh + 20)
            li = line_map[i] if line_map else start_line
            t0 = c.at(li) + (0 if line_map else i * stagger)
            k = ramp(c.t, t0, 0.45)
            if k <= 0:
                continue
            ctx.save()
            ctx.translate(0, (1 - k) * 30)
            ctx.push_group()
            card(ctx, cx, cy, gw, gh)
            ex_, ey_, iw, ih = _ink(i, fn, kw)
            boxh = gh - 100
            s = min((gw - 60) / iw, boxh / ih, 12.0)
            ctx.save(); ctx.translate(cx + gw / 2, cy + 22 + boxh / 2); ctx.scale(s, s); ctx.translate(-(ex_ + iw / 2), -(ey_ + ih / 2)); fn(ctx, **kw); ctx.restore()
            text(ctx, label, cx + gw / 2, cy + gh - 46, 24, INK, True, "c")
            if sub:
                text(ctx, sub, cx + gw / 2, cy + gh - 16, 19, INK2, False, "c")
            ctx.pop_group_to_source(); ctx.paint_with_alpha(k)
            ctx.restore()
    return vis


# ------------------------------------------------------------------ composition helpers
def split(*vis_list, weights=None, gap=24, vertical=False):
    weights = weights or [1] * len(vis_list)

    def vis(ctx, c):
        x, y, w, h = c.rect
        tot = sum(weights)
        pos = 0
        for v, wt in zip(vis_list, weights):
            if vertical:
                hh = (h - gap * (len(vis_list) - 1)) * wt / tot
                r = (x, y + pos, w, hh); pos += hh + gap
            else:
                ww = (w - gap * (len(vis_list) - 1)) * wt / tot
                r = (x + pos, y, ww, h); pos += ww + gap
            sub = type(c)(c.scene, c.t, r)
            ctx.save(); ctx.rectangle(*r); ctx.clip(); v(ctx, sub); ctx.restore()
    return vis


def switch(pairs):
    """pairs: [(line, vis)] - crossfade to each vis at its line."""
    def vis(ctx, c):
        cur, prev, k = pairs[0][1], None, 1.0
        for li, v in pairs[1:]:
            t0 = c.at(li) if isinstance(li, int) else li
            if c.t >= t0:
                prev, cur = cur, v
                k = ramp(c.t, t0, 0.5)
        if prev is not None and k < 1:
            prev(ctx, c)
            ctx.push_group(); cur(ctx, c); ctx.pop_group_to_source(); ctx.paint_with_alpha(k)
        else:
            cur(ctx, c)
    return vis


def drawing(fn, bgcol=PAPER):
    """Wrap a custom draw fn(ctx, c, x, y, w, h)."""
    def vis(ctx, c):
        x, y, w, h = c.rect
        card(ctx, x, y, w, h, bgcol)
        fn(ctx, c, x, y, w, h)
    return vis
