"""Short add-on to the assembly video: what's different on circuit board v1.2 (the two 5 V filters on the board).
Make it with:  BLIPR_SCENES=scenes_v12 BLIPR_VIDEO_BUILD=build/v12 BLIPR_VIDEO_TTS=build/tts python3 make_video.py tts|render|join"""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from engine import Scene
from vis import image_view, items_view
import parts as PT

PCB = REPO + "/pcb/out/"
PIC = REPO + "/pictures/out/"
FULL = (0, 0, 1396, 1814)
FILTERS = (40, 470, 560, 560)          # J1, L1, C27, L2, C29, C28, C30 (top-left of the board)
SC = []


def add(*a, **k):
    s = Scene(*a, **k)
    SC.append(s)
    return s


add("v12_intro", "board", "Circuit board v1.2: what's different", [
    "Since the main video was made, the circuit board has a new version: one point two.",
    "It puts both five volt noise filters on the board itself, so nothing is wired by hand.",
    "If your board says v1.1, follow the main video exactly as it is. If it says v1.2, three things change. Here they are.",
], visual=image_view(PCB + "pcb_assembly.png", cams=[(0, FULL), (1, FILTERS)],
                     overlays=[{"at": 1, "kind": "box", "xywh": (150, 530, 330, 400)},
                               {"at": 1, "kind": "tag", "xy": (490, 560), "text": "5 V filters", "delay": 0.4}]),
    notes=[(0, "Board v1.2: order this one"), (1, "Both 5 V filters on the board"), (2, "v1.1 board? The main video as it is")])

add("v12_parts", "board", "1. Six more parts on the board", [
    "One. Six more parts solder onto the board, in the top-left corner beside J1.",
    "L1 and L2 are the twenty-two microhenry inductors, the round drum type, either way round. Each has three holes in a row: the outer two are five millimetres apart, and the left and middle ones three point two millimetres apart, for small drums. Use whichever pair fits.",
    "C27 and C29 are the four hundred and seventy microfarad capacitors: eight millimetres across, legs three and a half millimetres apart. The plus leg goes in the square pad, like every electrolytic.",
    "C28 and C30 are one microfarad ceramics, either way round. Solder the capacitors with the other electrolytics, then the two inductors, pushed down flat.",
], visual=image_view(PCB + "pcb_assembly.png", cams=[(0, FILTERS), (1, (130, 500, 380, 420)), (2, (300, 500, 220, 420)), (3, FILTERS)],
                     overlays=[{"at": 1, "kind": "ring", "xy": (236, 615), "r": 70}, {"at": 1, "kind": "ring", "xy": (236, 786), "r": 70, "delay": 0.3},
                               {"at": 2, "kind": "ring", "xy": (393, 610), "r": 70}, {"at": 2, "kind": "ring", "xy": (393, 786), "r": 70, "delay": 0.3},
                               {"at": 3, "kind": "ring", "xy": (236, 897), "r": 34}, {"at": 3, "kind": "ring", "xy": (395, 897), "r": 34, "delay": 0.3}]),
    notes=[(1, "L1, L2: 22 µH, either way round"), (1, "Three holes: legs 5 mm or 3.2 mm apart"), (2, "C27, C29: 470 µF, 8 mm, legs 3.5 mm"),
           (2, "*+ leg in the square pad"), (3, "C28, C30: 1 µF ceramic"), (3, "Inductors last, pushed down flat")],
    pause=6, do="Pause and fit the six filter parts")

add("v12_r23", "board", "2. R23 and R24 stand up", [
    "Two. R23 and R24, the two one k resistors in the serial link, now stand on end to make room.",
    "Bend one leg back down beside the body, so the resistor stands over the hole inside its drawn square.",
], visual=image_view(PCB + "pcb_assembly.png", cams=[(0, (300, 1000, 300, 300))],
                     overlays=[{"at": 0, "kind": "ring", "xy": (440, 1100), "r": 55}, {"at": 0, "kind": "ring", "xy": (440, 1213), "r": 55, "delay": 0.3}]),
    notes=[(0, "R23, R24: 1 kΩ, standing on end"), (1, "Body over the hole in the square")])

add("v12_skip", "board", "3. Two steps to skip", [
    "Three. Skip two steps of the main video.",
    "The battery holder's red and black wires go straight into J1. No inductor in the red wire, and no capacitors across J1: they're already on the board.",
    "And never cut the ESP32's five volt pin. On v1.2 its filter sits between D1 and the socket, so the module plugs in with all its pins.",
    "Everything else stays the same, and the case fits both boards.",
], visual=items_view([
    (PT.battery_holder, {"with_cell": False}, "battery_holder", "Holder wires", "straight to J1"),
    (PT.esp32, {}, "esp32", "ESP32", "all pins, nothing cut"),
    (PT.inductor, {}, "inductor", "L1, L2 and friends", "on the board, not in the wires"),
], cols=3, line_map=[1, 2, 3]), full=True)

_n = 0
for s in SC:
    if s.pause > 0:
        _n += 1
        s.step = _n
NSTEPS = _n
