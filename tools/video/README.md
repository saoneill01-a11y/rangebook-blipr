# BLIPR assembly video

Scripts that make the narrated, step-by-step assembly video (about 38 minutes, 1080p) straight from the design
files in this repo: the board drawings come from `pcb/design.py`, the 3D case views from the STL files in
`case/out/`, and the wiring pictures and screen animations from `pictures/out/`. Change the design, re-run, and
the video follows. The finished MP4 is not kept in git (too large for GitHub).

Current version (Nov 26, 2026): circuit board v1.2 (both 5 V filters on the board: L1/L2 with three holes, C27-C30,
R23/R24 standing), case v0.12, Teensy 0.2.8, ESP32 0.2.20, the direct-wired screen and the dark-while-listening
screen, with Sean's photos of the first build at the start and end. v1.1 boards: one line in the parts chapter points
to the build guide's "If you have a v1.1 board" section. (`scenes_v12.py` is the older 2-minute add-on for the v1.1
video; not needed with this one.)

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | Welcome: what BLIPR does, getting Range Book (rangebook.org, the App Store app), every part, the plan |
| 1:56 | What you need: parts, the two 5 V filters, case hardware, tools, optional sensor kit |
| 5:37 | Safety |
| 6:14 | Get ready: sort parts, cut the Teensy's VIN–VUSB trace |
| 7:25 | Circuit board: soldering, lowest parts first, the filter parts (L1/L2, C27–C30), ESP32 direction check |
| 15:44 | Power checks: battery holder straight to J1, checkpoints 1 and 2 |
| 18:52 | Wiring: radar pigtail (short wires, one ground), the screen (jumpers on its pins or soldered pads), checkpoint 3 |
| 22:38 | Firmware: Arduino IDE, Teensy (fs=500000), ESP32, test shot from Range Book |
| 26:00 | The case: printing, inserts, holder, radar (hot glue), board, cover, screen, lid |
| 30:34 | Sensor pod (optional) |
| 32:37 | First test: power-up, level, dark means listening, compass, bench placement, speed window, first shot |
| 36:22 | Troubleshooting, including noise and interference (`live`, `rec`) |

Every hands-on step ends with a "Pause and …" bar so a viewer can stop and do it.

## Making it

Needs Python 3 with `pycairo numpy pillow matplotlib soundfile kokoro-onnx trimesh`, `ffmpeg`, and the Inter and
DejaVu Sans Mono fonts (on a Mac: `brew install cairo pkg-config ffmpeg` and `brew install --cask font-inter font-dejavu`). The voice is
Kokoro (open-source text-to-speech): put `kokoro-v1.0.onnx` and `voices-v1.0.bin` from
github.com/thewh1teagle/kokoro-onnx/releases in `build/tts/`.

    python3 render3d.py          # 3D case frames (a few minutes)
    python3 make_video.py tts    # narration audio, prints the length
    python3 make_video.py stills # one picture per narration line, for checking
    python3 make_video.py render # every scene (about 40 min on 1 CPU; give it scene ids to do a few)
    python3 make_video.py join   # build/BLIPR_assembly.mp4

| File | What |
|---|---|
| `scenes.py` | Every scene: narration lines, the side notes, what is shown |
| `diagrams.py` | Hand-drawn diagrams (wiring, checks, correct vs wrong) |
| `board.py` | The v1.1 board drawn from `pcb/design.py`, parts soldering in one by one |
| `case3d.py`, `render3d.py` | 3D case views from the STL files |
| `parts.py` | Drawings of each part and tool |
| `engine.py`, `vis.py`, `draw.py` | Timing, captions, layout, drawing helpers |

Thumbnail (1280x720, for YouTube): `python thumbnail.py` writes `build/BLIPR_thumbnail.jpg` from the photos in `docs/img/`.
