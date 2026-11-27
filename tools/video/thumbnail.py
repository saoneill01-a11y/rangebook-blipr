"""YouTube thumbnail (1280x720) for the assembly video, from the build photos.  Run with the venv python."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMG = REPO + "/docs/img/"
OUT = REPO + "/tools/video/build/BLIPR_thumbnail.png"
W, H = 1280, 720
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

c = Image.new("RGB", (W, H), (18, 20, 24))
# finished unit fills the right side
front = cover(Image.open(IMG + "blipr_front.jpg").convert("RGB"), 820, H, 0.55, 0.5)
c.paste(front, (W - 820, 0))
# fade it into the dark left side
fade = Image.new("L", (W, H), 0); d = ImageDraw.Draw(fade)
for x in range(W - 820, W - 520):
    d.line([(x, 0), (x, H)], fill=int(255 * (x - (W - 820)) / 300))
d.rectangle([W - 520, 0, W, H], fill=255)
c = Image.composite(c, Image.new("RGB", (W, H), (18, 20, 24)), fade)

# inside photo as an inset card, bottom left
ins = cover(Image.open(IMG + "blipr_inside.jpg").convert("RGB"), 420, 270, 0.45, 0.5)
card = Image.new("RGB", (ins.width + 10, ins.height + 10), (255, 196, 0)); card.paste(ins, (5, 5))
sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
ImageDraw.Draw(sh).rectangle([20, 20, card.width + 20, card.height + 20], fill=(0, 0, 0, 170))
sh = sh.filter(ImageFilter.GaussianBlur(10))
c.paste(sh, (40, H - card.height - 60), sh)
c.paste(card, (50, H - card.height - 60))

d = ImageDraw.Draw(c)
Y = (255, 196, 0)
def text(xy, s, f, fill, stroke=0):
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
text((52, 40), "BUILD YOUR OWN", font(58, "Bold"), (255, 255, 255), 2)
text((48, 100), "RADAR", font(138, "ExtraBold"), Y, 3)
text((52, 245), "CHRONOGRAPH", font(76, "ExtraBold"), (255, 255, 255), 2)
# tag on the photo
tf = font(34, "Bold"); tag = "Full build · step by step"
tw = d.textlength(tag, font=tf)
d.rounded_rectangle([W - tw - 70, 30, W - 30, 86], 12, fill=Y)
d.text((W - tw - 50, 37), tag, font=tf, fill=(18, 20, 24))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
c.save(OUT); c.convert("RGB").save(OUT[:-4] + ".jpg", quality=92)
print(OUT)
