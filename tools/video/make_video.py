
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import sys, os, subprocess, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cairo
import engine as E
from engine import FPS, BUILD
import importlib
S = importlib.import_module(os.environ.get("BLIPR_SCENES", "scenes"))   # scenes_v12 = the v1.2 add-on

mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
only = sys.argv[2].split(",") if len(sys.argv) > 2 else None

total = 0.0
starts = []
for sc in S.SC:
    sc.prepare()
    starts.append(total)
    total += round(sc.dur * FPS) / FPS
print("scenes", len(S.SC), "total %.1f s (%.1f min)" % (total, total / 60), flush=True)

if mode == "tts":
    sys.exit(0)

if mode == "stills":
    os.makedirs(f"{BUILD}/stills", exist_ok=True)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, E.W, E.H)
    for sc, t0 in zip(S.SC, starts):
        if only and sc.sid not in only:
            continue
        times = [min(sc.ends[i] - 0.1, sc.starts[i] + 3.0) for i in range(len(sc.lines))]
        if sc.pause:
            times.append(sc.pause_start + 1.0)
        for j, t in enumerate(times):
            ctx = cairo.Context(surf)
            E.draw_chrome(ctx, sc, t, sc.dur, t0 + t, total, S.NSTEPS)
            if sc.visual:
                rect = E.STAGE_FULL if sc.full else E.STAGE
                ctx.save(); ctx.rectangle(*rect); ctx.clip()
                sc.visual(ctx, E.Ctx(sc, t, rect)); ctx.restore()
            surf.write_to_png(f"{BUILD}/stills/{sc.sid}_{j}.png")
        print(sc.sid, len(times), flush=True)

if mode == "render":
    os.makedirs(f"{BUILD}/scenes", exist_ok=True)
    for i, (sc, t0) in enumerate(zip(S.SC, starts)):
        if only and sc.sid not in only:
            continue
        mp4 = f"{BUILD}/scenes/{i:03d}_{sc.sid}.mp4"
        wav = f"{BUILD}/scenes/{i:03d}_{sc.sid}.wav"
        buf, sr = sc.audio()
        n = round(sc.dur * FPS)
        need = int(round(n / FPS * sr))
        buf = np.pad(buf, (0, max(0, need - len(buf))))[:need]
        E.write_wav(wav, buf, sr)
        if not os.path.exists(mp4):
            E.render_scene(sc, i, t0, total, S.NSTEPS, mp4 + ".tmp.mp4")
            os.rename(mp4 + ".tmp.mp4", mp4)
        print("rendered", i, sc.sid, "%.1fs" % sc.dur, flush=True)

if mode == "join":
    names = [f"{i:03d}_{sc.sid}" for i, sc in enumerate(S.SC)]
    with open(f"{BUILD}/concat.txt", "w") as f:
        for n in names:
            f.write(f"file '{BUILD}/scenes/{n}.mp4'\n")
    import soundfile as sf
    allaudio = []
    for n in names:
        a, sr = sf.read(f"{BUILD}/scenes/{n}.wav", dtype="float32")
        allaudio.append(a)
    a = np.concatenate(allaudio)
    peak = np.abs(a).max()
    if peak > 0.98:
        a = a * (0.98 / peak)
    sf.write(f"{BUILD}/narration.wav", a, sr)
    out = sys.argv[3] if len(sys.argv) > 3 else f"{BUILD}/BLIPR_assembly.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{BUILD}/concat.txt", "-i", f"{BUILD}/narration.wav",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out)
