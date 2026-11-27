"""Short (~21 s, 1920x1080, silent) clip for the MakerWorld video section: photos plus the case 3D animations.
Needs the 3D frames from render3d.py in build/3d (build_, explode_, turn_). Run with the venv python.
Writes tools/video/build/BLIPR_makerworld_clip.mp4."""
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
IMG, F3D = REPO + "/docs/img/", HERE + "/build/3d/"
TMP, OUT = HERE + "/build/mw_clip/", HERE + "/build/BLIPR_makerworld_clip.mp4"
W, H, FPS, XF = 1920, 1080, 30, 12          # XF = crossfade frames
BG, Y, WHITE = (18, 20, 24), (255, 196, 0), (255, 255, 255)
FD = os.path.expanduser("~/Library/Fonts/")


def font(size, w="Bold"):
    p = FD + f"Inter-{w}.otf"
    return ImageFont.truetype(p if os.path.exists(p) else "/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)


def e(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def cover(im, w, h, cx=0.5, cy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int((im.width - w) * cx); y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def caption(c, big, small=None, y=None):
    """Yellow headline and a white line under it, on a dark band at the bottom."""
    band = Image.new("RGBA", (W, 230), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    for i in range(230):
        bd.line([(0, i), (W, i)], fill=(10, 11, 14, int(215 * min(1, i / 90))))
    c.paste(band, (0, H - 230), band)
    d = ImageDraw.Draw(c)
    fb, fs = font(62, "ExtraBold"), font(38, "Bold")
    yb = H - 175 if small else H - 130
    d.text((W / 2 - d.textlength(big, font=fb) / 2, yb), big, font=fb, fill=Y, stroke_width=2, stroke_fill=(0, 0, 0))
    if small:
        d.text((W / 2 - d.textlength(small, font=fs) / 2, yb + 82), small, font=fs, fill=WHITE)


def photo_scene(name, n, big, small, cx=0.5, cy=0.5, zoom=(1.0, 1.08)):
    src = Image.open(IMG + name).convert("RGB")
    base = cover(src, W, H, cx, cy)
    for i in range(n):
        z = zoom[0] + (zoom[1] - zoom[0]) * i / max(1, n - 1)
        cw, ch = W / z, H / z
        fr = base.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.LANCZOS)
        caption(fr, big, small)
        yield fr


def render_scene(seq, idxs, big, small):
    for i in idxs:
        c = Image.new("RGB", (W, H), BG)
        g = ImageDraw.Draw(c)                        # soft lighter centre so the grey case stands out
        for r in range(700, 0, -20):
            v = int(18 + 22 * (1 - r / 700))
            g.ellipse([W / 2 - r * 1.5, 430 - r, W / 2 + r * 1.5, 430 + r], fill=(v, v + 2, v + 6))
        im = Image.open(F3D + f"{seq}_{i:04d}.png").convert("RGBA")
        s = 860 / im.height
        im = im.resize((round(im.width * s), 860), Image.LANCZOS)
        c.paste(im, ((W - im.width) // 2, 10), im)
        caption(c, big, small)
        yield c


def end_card(n):
    for i in range(n):
        c = Image.new("RGB", (W, H), BG)
        ph = cover(Image.open(IMG + "blipr_front.jpg").convert("RGB"), 900, H, 0.55)
        ph = ImageEnhance.Brightness(ph).enhance(0.75)
        c.paste(ph, (W - 900, 0))
        d = ImageDraw.Draw(c)
        d.text((110, 200), "BLIPR", font=font(150, "ExtraBold"), fill=Y)
        d.text((116, 380), "DIY 24 GHz radar chronograph", font=font(50, "Bold"), fill=WHITE)
        lines = ("Full build video on YouTube", "Free files: github.com/saoneill01-a11y/rangebook-blipr",
                 "Shots go to Range Book: rangebook.org")
        for j, s in enumerate(lines):
            a = e((i - 8 - j * 10) / 12)
            col = tuple(int(BG[k] + (v - BG[k]) * a) for k, v in enumerate((220, 224, 230)))
            d.text((116, 520 + j * 70), s, font=font(36, "Bold"), fill=col)
        yield c


scenes = [
    photo_scene("blipr_front.jpg", 105, "BLIPR: build your own radar chronograph",
                "Measures every shot's muzzle velocity. Nothing goes downrange.", 0.55, 0.1, (1.0, 1.05)),
    render_scene("build", range(0, 210, 1), "Prints in 4 parts, no supports",
                 "Battery holder, radar and circuit board drop in. The lid screws on."),
    render_scene("explode", list(range(0, 72)) + [71] * 18, "Optional sensor pod",
                 "Temperature, humidity, air pressure, level and compass"),
    render_scene("turn", range(0, 120), "Screen window, radar window, 1/4-20 tripod mount",
                 "Heat-set inserts throughout"),
    photo_scene("blipr_inside.jpg", 90, "Open source: board, firmware and build guide",
                "Through-hole parts you solder yourself", 0.45, 0.5, (1.06, 1.0)),
    end_card(120),
]

shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)
k, prev_tail = 0, []
for si, sc in enumerate(scenes):
    frames = list(sc)
    if prev_tail:                                   # crossfade the last XF frames of the previous scene
        for j in range(XF):
            Image.blend(prev_tail[j], frames[j], (j + 1) / (XF + 1)).save(TMP + f"{k:05d}.png"); k += 1
        frames = frames[XF:]
    last = si == len(scenes) - 1
    body, prev_tail = (frames, []) if last else (frames[:-XF], frames[-XF:])
    for fr in body:
        fr.save(TMP + f"{k:05d}.png"); k += 1
print(k, "frames,", round(k / FPS, 1), "s")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", TMP + "%05d.png",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k", OUT], check=True)
print(OUT)
