"""MakerWorld cover pictures (4:3 and 3:4), same look as the YouTube thumbnail.  Run with the venv python.
Writes tools/video/build/BLIPR_makerworld_4x3.jpg (1440x1080) and BLIPR_makerworld_3x4.jpg (1080x1440)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMG = REPO + "/docs/img/"
OUTDIR = REPO + "/tools/video/build/"
BG = (18, 20, 24); Y = (255, 196, 0); WHITE = (255, 255, 255)
F = os.path.expanduser("~/Library/Fonts/")


def font(size, w="Bold"):
    for n in (f"Inter-{w}.otf", f"InterDisplay-{w}.otf", "Inter-Bold.ttf"):
        if os.path.exists(F + n): return ImageFont.truetype(F + n, size)
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)


def cover(im, w, h, cx=0.5, cy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int((im.width - w) * cx); y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def inset(c, w, h, x, y):
    ins = cover(Image.open(IMG + "blipr_inside.jpg").convert("RGB"), w, h, 0.45, 0.5)
    card = Image.new("RGB", (w + 12, h + 12), Y); card.paste(ins, (6, 6))
    sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([20, 20, card.width + 20, card.height + 20], fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    c.paste(sh, (x - 10, y), sh)
    c.paste(card, (x, y))


def tag(d, right, top, size):
    tf = font(size, "Bold"); s = "Full build · step by step"
    tw = d.textlength(s, font=tf); pad = size * 0.6
    d.rounded_rectangle([right - tw - 2 * pad, top, right, top + size * 1.65], 14, fill=Y)
    d.text((right - tw - pad, top + size * 0.2), s, font=tf, fill=BG)


def title(d, x, y, scale, center=None):
    lines = (("BUILD YOUR OWN", 58, "Bold", WHITE, 2, 0), ("RADAR", 138, "ExtraBold", Y, 3, 60),
             ("CHRONOGRAPH", 76, "ExtraBold", WHITE, 2, 205))
    for s, size, w, fill, stroke, dy in lines:
        f = font(round(size * scale), w)
        xx = x if center is None else center - d.textlength(s, font=f) / 2
        d.text((xx, y + dy * scale), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def landscape():  # 4:3
    W, H = 1440, 1080; PW = 1000
    c = Image.new("RGB", (W, H), BG)
    c.paste(cover(Image.open(IMG + "blipr_front.jpg").convert("RGB"), PW, H, 0.55, 0.5), (W - PW, 0))
    fade = Image.new("L", (W, H), 0); d = ImageDraw.Draw(fade)
    for x in range(W - PW, W - PW + 340):
        d.line([(x, 0), (x, H)], fill=int(255 * (x - (W - PW)) / 340))
    d.rectangle([W - PW + 340, 0, W, H], fill=255)
    c = Image.composite(c, Image.new("RGB", (W, H), BG), fade)
    inset(c, 520, 340, 60, H - 340 - 80)
    d = ImageDraw.Draw(c)
    title(d, 60, 70, 1.12)
    tag(d, W - 40, 40, 38)
    return c


def portrait():  # 3:4
    W, H = 1080, 1440; PH = 1060
    c = Image.new("RGB", (W, H), BG)
    c.paste(cover(Image.open(IMG + "blipr_front.jpg").convert("RGB"), W, PH, 0.6, 0.5), (0, H - PH))
    fade = Image.new("L", (W, H), 0); d = ImageDraw.Draw(fade)
    top = H - PH
    for y in range(top, top + 260):
        d.line([(0, y), (W, y)], fill=int(255 * (y - top) / 260))
    d.rectangle([0, top + 260, W, H], fill=255)
    c = Image.composite(c, Image.new("RGB", (W, H), BG), fade)
    inset(c, 430, 290, 40, H - 290 - 60)
    d = ImageDraw.Draw(c)
    title(d, 0, 60, 1.2, center=W / 2)
    tag(d, W - 40, 430, 36)
    return c


os.makedirs(OUTDIR, exist_ok=True)
for name, im in (("4x3", landscape()), ("3x4", portrait())):
    p = OUTDIR + f"BLIPR_makerworld_{name}.jpg"
    im.save(p, quality=92); print(p, im.size)
