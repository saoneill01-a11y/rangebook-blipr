Range Book BLIPR - case files, v0.8

SIDES: "+X side" is the side wall with the Teensy's USB hole. On the bench it faces the gun and you
(you sit behind it, across the gun, with the chronograph at about 1 o'clock). The "far side" is the other one.

WHAT CHANGED IN v0.8 (base and lids; front cover, pod and roof are the same as v0.7)
  - The base is now Sean's own CAD edit (user_edits/base_from_sean_2026-10-22.stl), used as the master:
    mounts for the battery holder, a USB-C charging hole and a hole to press the holder's own power
    button through, both in the side wall. The old slide-switch and charge slots are gone. No separate
    power switch: the holder's button turns BLIPR on and off.
  - Radar pocket: 0.2 mm wider each side and 0.2 mm deeper, for 1 mm x 5 mm foam tape on the radar's two
    sides and back. The module is pushed forward against the window by the foam; no crush ribs.
  - Power-button hole in the left wall: 10 mm across (Sean's 8 mm was a little small), same centre.
    BUTTON_HOLE_D in the script.
  - Tripod hole under the base: 7 mm across and 9 mm deep (was 8.4 x 13.4), to suit Sean's 1/4-20
    heat-set inserts. TRIPOD_HOLE_D / TRIPOD_HOLE_DEPTH in the script if yours differ.
  - Every lid with a screen (lid_oled, lid_sensors) has Sean's screen mount: 4 pads in the pocket's corners,
    1 mm proud of the underside, with 1.7 mm pilot holes for 4 x M2 x 4 screws (tested and fits).
  - Every lid has a radar hold-down rib underneath (18 x 3 mm, 5.3 mm long). It stops 0.7 mm above the
    radar's top edge: put a 20 mm strip of the same foam tape on the radar's top edge and the lid
    presses it down lightly, so the module can't rattle or tip back.

WHAT CHANGED IN v0.7 (lids only; base, front cover, pod and roof are the same as v0.6)
  - Screen moved to the back corner on the +X side, nearest you, so nothing is between you and it.
    Its window is 14.4 mm from the lid's back edge and 14.4 mm from its +X edge.
  - Sensor pod moved to the front corner on the far side, diagonally away from the screen. The IMU end
    of the pod still points to the +X side, clear of the battery bay. It doesn't touch the radar: the
    pod is above and behind the antenna, and the beam goes forward.
  - Two 8 mm risers hang 6 mm under the lid at the pod's screw spots. Press an M3 heat-set insert into
    each from the top (the pod hides them), then hold the pod down with 2 x M3x8. No nuts.
  - No ammo-probe jack hole (the probe isn't used: your ammo sits at air temperature).
  - BLIPR (Ballistic Launch Inspection Portable Radar) is cut into the lid, 12 mm tall, centred under the
    sensor pod as you see it from your seat, 8 mm behind it.
  - The screen now sits over the Teensy, about 5 mm above it. Solder the screen's 4 wires straight to
    its pads (or bend the header pins flat) rather than using a straight header with Dupont plugs.

WHAT CHANGED IN v0.6 (base and front cover are the same as v0.5)
  - Lids: "BLIP" is cut 0.6 mm into the top, in the front half, reading from behind (where you sit).
    Printed top-face down as before, the letters come out crisp on the bed side.
  - Sensor pod: the vent slots have 2 mm uprights (bridges no longer than 17 mm); the sensor boards
    are screwed down (4 x M2.5x6 brass each, into 5 mm posts) instead of sitting on pegs; a column in
    each inside corner, rounded and filleted into the walls, takes a roof screw.
  - Pod roof: 4 screw holes, and its lip is notched to clear the corner columns.
  - The script is now blipr_case.py (was chronograph_case.py, then blip_case.py).

WHAT CHANGED IN v0.5 (base only; every other part is the same as v0.4)
  - The Teensy USB hole in the right wall now reaches 7 mm lower (it is 17 mm tall instead of 10),
    so the plug fits whether the Teensy sits on 8.5 mm female headers or lower.
  - The battery shield still sits on foam tape in its bay for now; standoffs for it come once
    the shield arrives and can be measured.

WHAT CHANGED IN v0.4
  The compass/level board (IMU) moved off the case floor and into the sensor pod, and the pod moved
  from over the battery bay to the rear-right of the lid. The 18650's steel can and the battery
  shield's switching converter upset a compass; the IMU now sits at the end of the pod farthest
  from them. base.stl lost the floor pegs (nothing else changed). imu_mount is gone.
  Already printed base v0.3? Keep it: just don't mount the IMU on its floor pegs.
  Already printed lid_sensors or sensor_pod from v0.3? Reprint both: the pod is bigger now and its
  screw holes and cable slot moved.

PRINT FILES (out/)
  base.stl / base.step               main body (v0.8, Sean's CAD + wider radar pocket); print floor-down
  lid_oled.stl / lid_oled.step       lid with a window for the 0.96" OLED; print top-face down
  lid_plain.stl / lid_plain.step     lid without the screen window
  front_cover.stl / front_cover.step thin radar window cover (0.9 mm window); print flat, smooth face down,
                                     non-black filament, 0.15 mm layers, 100% infill
  front_cover_thin.stl / .step       same cover with a 0.5 mm window (print at 0.1 mm layers)

  SENSOR KIT PARTS (build guide: Sensors tab)
  lid_sensors.stl / .step            lid_oled plus the pod's 2 insert risers and its cable slot (front
                                     corner, far side). Print top-face down; the risers point up.
  sensor_pod.stl / .step             vented pod, 66 x 50 x 20 mm, for all three boards side by side, long
                                     sides front-to-back: SHT45 at the far-side end, BMP390 in the middle,
                                     IMU at the +X end (a small arrow in front of it points to the front). Each
                                     board sits on 4 posts, 5 mm tall, and is held by 4 M2.5 x 6 mm brass screws that thread
                                     straight into the posts. A column in each inside corner takes
                                     a roof screw. Print upright.
                                     The vent slots have 2 mm uprights (2 on the long sides, 1 on the
                                     short sides), so no bridge is longer than 17 mm; no supports needed.
  sensor_pod_roof.stl / .step        shade roof; print flat face down; light-coloured filament. Held by 4 M2.5 x 6 mm
                                     brass screws into the pod's corner columns (its lip is notched to clear them)

  The posts suit Adafruit's 1.0 x 0.7 in STEMMA QT boards, whose 2.5 mm holes sit 0.1 in from each
  corner (20.32 x 12.7 mm apart). Check yours when they arrive; if they don't line up, change
  SQ_HOLE_DX / SQ_HOLE_DY in the script. The 2.2 mm pilot holes let the screws cut their own thread:
  drive each one slowly until the board is snug, then stop (over-tightening strips plastic threads).
  Use brass (or nylon) screws, not steel: the IMU's compass is a few millimetres from its screws, and
  steel ones would bend the field it measures.

  Cables: a 150 mm STEMMA QT-to-pins cable from J4 on the main board up through the lid slot to the
  SHT45, then 100 mm cables SHT45 -> BMP390 -> IMU. Use brass or nylon screws to hold the pod on the
  lid too if you have them (steel ones 20 mm or more from the compass are calibrated out, but brass is simpler).

Outside size: 118.8 x 130.8 x 36.4 mm, plus the 2.4 mm lid.
Hardware (v0.8 adds): 4 x M2 x 4 screws (screen), battery-holder screws to suit its 2.8 mm holes
          (M3 x 6 self-tapping screws cut their own thread in a 2.8 mm hole), ~150 mm of
          1 mm x 5 mm foam tape (radar sides, back and top).
Hardware: 8 x M3 heat-set inserts (4.1 mm holes), 4 x M3x8 (lid), 4 x M3x6 (board),
          1 x 1/4-20 heat-set insert, up to 9 mm long (7 mm hole, 9 mm deep) for a tripod.
          Sensor pod: 2 x M3x8 + 2 more M3 heat-set inserts (in the lid's risers).  Sensor boards and pod roof: 16 x M2.5x6 brass screws.

CHANGING THE CASE
  All sizes are at the top of blipr_case.py. Edit a number, then run:
      python3 blipr_case.py
  It rebuilds every STEP and STL in out/. csg.py (included) builds the lids, pod and cover.
  The base starts from Sean's mesh in user_edits/ and the script applies BASE_EDITS to it, which needs
      pip install trimesh manifold3d cadquery-ocp
  To change the base in CAD: edit base.step, export an STL, put it in user_edits/ and point
  BASE_SOURCE at it. tools/step_tools.py can report sizes of a STEP or diff two of them.
  Optional previews (needs numpy + matplotlib): python3 render.py

NOTES
  - STEP files are true solids with flat faces. Round features (holes, corners) are made
    of many small flat faces, which is fine for measuring and simple edits in Fusion,
    FreeCAD or Onshape.
  - Expect one round of adjustments once the real parts are measured (see the build guide).
