# BLIPR assembly video

Scripts that make the narrated, step-by-step assembly video (about 32 minutes, 1080p) straight from the design
files in this repo: the board drawings come from `pcb/design.py`, the 3D case views from the STL files in
`case/out/`, and the wiring pictures and screen animations from `pictures/out/`. Change the design, re-run, and
the video follows. The finished MP4 is not kept in git (too large for GitHub).

## Chapters

| Time | Chapter |
|---|---|
| 0:00 | Welcome: what BLIPR does, exploded view of every part, the plan |
| 1:29 | What you need: parts, case hardware, tools, optional sensor kit |
| 4:19 | Safety |
| 4:56 | Get ready: sort parts, cut the Teensy's VIN–VUSB trace |
| 6:01 | Circuit board: soldering, lowest parts first, ESP32 direction check |
| 13:14 | Power checks: battery holder wiring, checkpoints 1 and 2 |
| 15:55 | Wiring: radar pigtail, screen, checkpoint 3 |
| 19:02 | Firmware: Arduino IDE, Teensy, ESP32, test shot from Range Book |
| 21:52 | The case: printing, inserts, holder, radar, board, cover, screen, lid |
| 26:20 | Sensor pod (optional) |
| 28:21 | First test: power-up, level, compass, bench placement, first shot |
| 30:30 | Troubleshooting |

Every hands-on step ends with a "Pause and …" bar so a viewer can stop and do it.

## Making it

Needs Python 3 with `pycairo numpy pillow matplotlib soundfile kokoro-onnx`, and `ffmpeg`. The voice is
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
