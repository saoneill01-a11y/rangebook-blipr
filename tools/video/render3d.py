
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case3d as C
from PIL import Image
from multiprocessing import Pool
OUT = BUILD + "/3d"
def e(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)

def job(args):
    seq, i = args
    fn = f"{OUT}/{seq}_{i:04d}.png"
    if os.path.exists(fn): return
    if seq == "turn":
        P = C.assembly(); az = -118 + 120 * e(i / 119)
        img = C.render(P, 24, az, scale=5.4, center=(59, 65, 28))
    elif seq == "explode":
        k = e(i / 71)
        ex = {"lid": 55 * k, "oled": 55 * k, "pod": 100 * k, "roof": 135 * k, "board": 22 * k, "teensy": 22 * k,
              "radar": (0, -40 * k, 6 * k), "cover": (0, -70 * k, 0), "holder": 12 * k}
        img = C.render(C.assembly(ex), 24, -58, scale=3.55, center=(59, 45, 88))
    elif seq == "build":
        order = ["holder", "radar", "board", "cover", "lid", "pod", "roof"]
        lift = {"holder": 70, "radar": 60, "board": 60, "cover": 70, "lid": 70, "pod": 60, "roof": 50}
        step, f = divmod(i, 30)
        ex, inc = {}, {"base"}
        for j, nm in enumerate(order):
            if j < step or (j == step and True):
                k = 1.0 if j < step else e(f / 29)
                group = {nm} | ({"teensy"} if nm == "board" else set()) | ({"oled"} if nm == "lid" else set())
                for g in group:
                    inc.add(g); ex[g] = lift[nm] * (1 - k)
        img = C.render(C.assembly(ex, include=inc), 32, -52, scale=5.0, center=(59, 62, 40))
    elif seq == "baseonly":
        img = C.render(C.assembly(include={"base"}), 32, -52, scale=5.0, center=(59, 62, 40))
    Image.fromarray((np.clip(img, 0, 1) * 255).astype("uint8"), "RGBA").save(fn)

if __name__ == "__main__":
    jobs = [("baseonly", 0)] + [("turn", i) for i in range(120)] + [("explode", i) for i in range(72)] + [("build", i) for i in range(210)]
    with Pool(2) as p:
        for n, _ in enumerate(p.imap_unordered(job, jobs)):
            if n % 40 == 0: print(n, flush=True)
    print("done")
