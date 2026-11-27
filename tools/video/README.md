# BLIPR assembly video

Scripts that make the narrated, step-by-step assembly video (about 39 minutes, 1080p) straight from the design
files in this repo: the board drawings come from `pcb/design.py`, the 3D case views from the STL files in
`case/out/`, and the wiring pictures and screen animations from `pictures/out/`. Change the design, re-run, and
the video follows. The finished MP4 is not kept in git (too large for GitHub).

Current version (Nov 26, 2026): circuit board v1.1, case v0.12, Teensy 0.2.8, ESP32 0.2.20, with both 5 V filters,
the direct-wired screen, the dark-while-listening screen, and Sean's photos of the first build at the start and end.

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | Welcome: what BLIPR does, exploded view of every part, the plan |
| 1:29 | What you need: parts, the two 5 V filters, case hardware, tools, optional sensor kit |
| 5:04 | Safety |
| 5:41 | Get ready: sort parts, cut the Teensy's VIN–VUSB trace |
| 6:52 | Circuit board: soldering, lowest parts first, ESP32 direction check |
| 14:19 | Power checks: battery holder wiring and its 5 V filter, checkpoints 1 and 2 |
| 18:08 | Wiring: radar pigtail, the screen (soldered wires, no header), checkpoint 3 |
| 21:55 | Firmware: Arduino IDE, Teensy (fs=500000), ESP32 (out of its socket), the ESP32's 5 V filter, test shot from Range Book |
| 26:24 | The case: printing, inserts, holder, radar, board, cover, screen, lid |
| 30:58 | Sensor pod (optional) |
| 32:59 | First test: power-up, level, dark means listening, compass, bench placement, speed window, first shot |
| 36:44 | Troubleshooting, including noise and interference (`live`, `rec`) |

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
