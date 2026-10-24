"""Scene timeline, layout, narration audio and frame rendering for the BLIPR video."""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import os, math, json, subprocess, hashlib, wave
import numpy as np
import cairo
from draw import *

FPS = 24
VOICE = "af_heart"
SPEED = 0.94
GAP = 0.45          # silence between narration lines
LEAD = 0.7          # silence before the first line

STAGE = (40, 104, 1260, 780)          # visual area when notes are shown
STAGE_FULL = (40, 104, 1840, 780)     # visual area without notes
NOTES = (1330, 104, 550, 780)
CAPTION = (40, 902, 1840, 134)

_tts = None


SAY = [("RB BLIPR", "R B Blipper"), ("BliprTeensy", "Blipper Teensy"), ("BliprBLE", "Blipper B L E"), ("BLIPR", "Blipper"), ("1N5817", "one N five eight one seven"),
       ("MCP6022", "M C P six oh two two"), ("MCP1700", "M C P seventeen hundred"), ("K-LC5", "K L C five"), ("ESP32-C3", "E S P thirty-two C three"),
       ("ESP32C3", "E S P thirty-two C three"), ("ESP32", "E S P thirty-two"), ("SHT45", "S H T forty-five"), ("VCC", "V C C"), ("I2C", "I squared C"),
       ("18650", "eighteen six fifty"), ("M2.5", "M two point five"), ("RFbeam", "R F beam"), ("OLED", "O L E D"), ("SDA", "S D A"), ("SCL", "S C L"),
       ("GPIO", "G P I O"), ("USB-C", "U S B C"), ("IDE", "I D E"), ("STEMMA QT", "stemma Q T"), ("DFRobot", "D F Robot"), ("A0 and A1", "A zero and A one"),
       ("Ω", " ohm"), ("µF", " microfarad")]


def say_text(s):
    for a, b in SAY:
        s = s.replace(a, b)
    return s


def tts(textline, path):
    global _tts
    if os.path.exists(path):
        return
    if _tts is None:
        from kokoro_onnx import Kokoro
        _tts = Kokoro(TTS + "/kokoro-v1.0.onnx", TTS + "/voices-v1.0.bin")
    import soundfile as sf
    say = say_text(textline)
    s, sr = _tts.create(say, voice=VOICE, speed=SPEED, lang="en-us")
    sf.write(path, s, sr)


def wav_len(path):
    import soundfile as sf
    info = sf.info(path)
    return info.frames / info.samplerate


class Scene:
    def __init__(self, sid, chapter, title, lines, visual=None, notes=None, pause=0.0, full=False, step=None, tail=0.6,
                 do=None, holds=None):
        """lines: narration sentences (each shown as a caption).
        notes: list of (line_index, text) shown in the side panel from that line on.
        pause: seconds of 'do it now' hold after the narration (shown with a PAUSE badge).
        holds: {line_index: extra seconds after that line}."""
        self.sid, self.chapter, self.title, self.lines = sid, chapter, title, lines
        self.visual, self.notes, self.pause, self.full = visual, notes or [], pause, full
        self.step, self.tail, self.do, self.holds = step, tail, do, holds or {}
        self.starts, self.ends, self.dur = [], [], 0.0

    def prepare(self):
        os.makedirs(f"{BUILD}/audio", exist_ok=True)
        t = LEAD
        self.files = []
        for i, ln in enumerate(self.lines):
            h = hashlib.md5((VOICE + str(SPEED) + say_text(ln)).encode()).hexdigest()[:12]
            fn = f"{BUILD}/audio/{h}.wav"
            tts(ln, fn)
            d = wav_len(fn)
            self.files.append(fn)
            self.starts.append(t)
            self.ends.append(t + d)
            t += d + GAP + self.holds.get(i, 0.0)
        self.speech_end = t
        self.pause_start = t
        self.dur = t + self.pause + self.tail
        return self.dur

    def at(self, i):
        """start time of narration line i (negative i counts from the end; len(lines) = pause start)."""
        if i >= len(self.lines):
            return self.pause_start
        return self.starts[i]

    def line_at(self, t):
        cur = None
        for i, s in enumerate(self.starts):
            if t >= s - 0.05:
                cur = i
        return cur

    def audio(self, sr=24000):
        import soundfile as sf
        n = int(round(self.dur * FPS)) / FPS
        buf = np.zeros(int(n * sr) + 1, np.float32)
        for fn, s in zip(self.files, self.starts):
            a, r = sf.read(fn, dtype="float32")
            assert r == sr
            i0 = int(s * sr)
            buf[i0:i0 + len(a)] += a[:max(0, len(buf) - i0)]
        return buf, sr


class Ctx:
    """What a visual function gets each frame."""
    def __init__(self, scene, t, rect):
        self.scene, self.t, self.rect = scene, t, rect

    def at(self, i):
        return self.scene.at(i)

    def k(self, i, dur=0.5, delay=0.0):
        """0..1 ease starting at narration line i (+delay)."""
        return ramp(self.t, self.scene.at(i) + delay, dur)

    def since(self, i, delay=0.0):
        return self.t - self.scene.at(i) - delay


# ------------------------------------------------------------------ chrome
def draw_chrome(ctx, sc, t, total_t, video_t, video_total, nsteps):
    col = CHAPTER_COL.get(sc.chapter, INK)
    setc(ctx, BG); ctx.paint()
    # top bar
    setc(ctx, PAPER); ctx.rectangle(0, 0, W, 84); ctx.fill()
    setc(ctx, RULE); ctx.rectangle(0, 84, W, 2); ctx.fill()
    setc(ctx, col); ctx.rectangle(0, 0, 14, 84); ctx.fill()
    chap = CHAPTER_NAME.get(sc.chapter, sc.chapter).upper()
    wtag = tag(ctx, chap, 40, 42, 22, PAPER, col)
    text(ctx, sc.title, 40 + wtag + 22, 52, 34, INK, weight="semi")
    if sc.step:
        text(ctx, "STEP %d OF %d" % (sc.step, nsteps), W - 40, 52, 24, INK2, True, "r")
    # notes panel
    if not sc.full:
        x, y, w, h = NOTES
        setc(ctx, PAPER); rrect(ctx, x, y, w, h, 18); ctx.fill()
        setc(ctx, col); rrect(ctx, x, y, w, 8, 4); ctx.fill()
        text(ctx, "ON THE BENCH", x + 28, y + 50, 20, col, True)
        yy = y + 92
        for (li, s) in sc.notes:
            k = ramp(t, sc.at(li) if li >= 0 else 0, 0.45)
            if k <= 0:
                continue
            col_txt = INK
            bold = False
            if s.startswith("!"):
                s = s[1:]; col_txt = BAD; bold = True
            elif s.startswith("*"):
                s = s[1:]; bold = True
            setc(ctx, col, k); ctx.arc(x + 36, yy - 9, 6, 0, 2 * math.pi); ctx.fill()
            hgt = para(ctx, s, x + 56, yy, w - 84, 26, col_txt, bold, 1.28, alpha=k)
            yy += hgt + 16
    # caption
    x, y, w, h = CAPTION
    setc(ctx, PAPER); rrect(ctx, x, y, w, h, 18); ctx.fill()
    li = sc.line_at(t)
    if li is not None and t < sc.ends[li] + GAP * 0.9 + sc.holds.get(li, 0):
        a = min(ramp(t, sc.starts[li] - 0.05, 0.18), 1.0)
        lines = wrap(ctx, sc.lines[li], w - 80, 34)
        y0 = y + h / 2 + 12 - (len(lines) - 1) * 21
        for i, ln in enumerate(lines[:3]):
            text(ctx, ln, x + w / 2, y0 + i * 42, 34, INK, anchor="c", alpha=a)
    # pause badge
    if sc.pause > 0 and t >= sc.pause_start:
        k = ramp(t, sc.pause_start, 0.35)
        msg = sc.do or "Pause the video and do this step"
        setc(ctx, col, k); rrect(ctx, x + 30, y + 26, w - 60, h - 52, 14); ctx.fill()
        # pause glyph
        setc(ctx, PAPER, k); ctx.rectangle(x + 62, y + 44, 12, 46); ctx.fill(); ctx.rectangle(x + 84, y + 44, 12, 46); ctx.fill()
        text(ctx, msg, x + 122, y + h / 2 + 12, 34, PAPER, True, alpha=k)
        left = max(0, sc.pause_start + sc.pause - t)
        text(ctx, "%d s" % math.ceil(left), x + w - 60, y + h / 2 + 12, 30, PAPER, True, "r", alpha=k * 0.85)
    # progress
    setc(ctx, RULE); ctx.rectangle(0, 1072, W, 8); ctx.fill()
    setc(ctx, col); ctx.rectangle(0, 1072, W * video_t / max(video_total, 1e-6), 8); ctx.fill()


CHAPTER_NAME = {
    "intro": "Welcome", "kit": "What you need", "safety": "Safety", "prep": "Get ready", "board": "Circuit board",
    "power": "Power checks", "wiring": "Wiring", "case": "The case", "sensors": "Sensor pod", "firmware": "Firmware",
    "test": "First test", "trouble": "Troubleshooting",
}


# ------------------------------------------------------------------ render
def render_scene(sc, idx, video_t0, video_total, nsteps, out_mp4, preview_every=None):
    rect = STAGE_FULL if sc.full else STAGE
    nframes = int(round(sc.dur * FPS))
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                             "-pix_fmt", "yuv420p", "-tune", "animation", out_mp4], stdin=subprocess.PIPE)
    last = None
    for f in range(nframes):
        t = f / FPS
        ctx.save()
        draw_chrome(ctx, sc, t, sc.dur, video_t0 + t, video_total, nsteps)
        if sc.visual:
            ctx.save()
            x, y, w, h = rect
            ctx.rectangle(x, y, w, h); ctx.clip()
            sc.visual(ctx, Ctx(sc, t, rect))
            ctx.restore()
        ctx.restore()
        surf.flush()
        proc.stdin.write(bytes(surf.get_data()))
        if preview_every and f % preview_every == 0:
            surf.write_to_png(f"{BUILD}/preview/{sc.sid}_{f:05d}.png")
    proc.stdin.close()
    proc.wait()
    return nframes


def write_wav(path, buf, sr):
    import soundfile as sf
    sf.write(path, buf, sr)
