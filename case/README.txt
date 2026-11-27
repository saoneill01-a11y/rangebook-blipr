Range Book BLIPR - case files, v0.12

SIDES: "+X side" is the side wall with the Teensy's USB hole. On the bench it faces the gun and you
(you sit behind it, across the gun, with the chronograph at about 1 o'clock). The "far side" is the other one.

WHAT CHANGED IN v0.12 (lids only: lid_oled and lid_sensors; every other part is the same as v0.11)
  - Screen window 1 mm taller (12 -> 13 mm), on its front edge (toward the sensor pod): that edge hid the top line of
    the screen (battery icon and small text). The back edge is unchanged. Picture: out/oled_window_v012.png.

WHAT CHANGED IN v0.11 (base only; every other part is the same as v0.10)
  - Clean-up beside the two left battery-holder pads: the old front cross wall's stub, the wider foot of the
    front-left corner column (up to 10.4 mm) and the foot and two thin horns of the rear-left column behind its pad
    (up to 7.4 mm) are gone. Pads, screw holes and corner columns unchanged. Pictures: out/pad_cleanup_check.png.

WHAT CHANGED IN v0.10 (base only; every other part is the same as v0.9)
  - Teensy USB hole in the right wall raised: 13.5 mm wide x 8 mm tall, 24-32 mm up from the case bottom
    (was 16-26.5 mm, which missed the USB with the Teensy in its 8.5 mm sockets: the USB sits ~27.5 mm up).
    The old lower part is filled in. Fits a 12 x 5.5 mm micro-USB plug. Last two BASE_EDITS in the script.

WHAT CHANGED IN v0.9 (base only; every other part is the same as v0.8)
  - Battery-holder pads: all four are now 8 mm round pads (were 10 mm; the plastic hit parts on the underside of
    the holder board), with 2.9 mm screw holes (were 2.8: the screws went in tighter than they needed to).
    The two left pads, which were part of Sean's model and joined to the wall, are rebuilt the same way as the
    right two. Same positions and the same 7.4 mm height. HOLDER_PAD_D / HOLDER_HOLE_D in the script.

WHAT CHANGED IN v0.8 (base and lids; front cover, pod and roof are the same as v0.7)
  - The base is now Sean's own CAD edit (user_edits/base_from_sean_2026-10-22.stl), used as the master:
    mounts for the battery holder, a USB-C charging hole and a hole to press the holder's own power
    button through, both in the side wall. The old slide-switch and charge slots are gone. No separate
    power switch: the holder's button turns BLIPR on and off.
  - Radar pocket: 0.2 mm wider each side and 0.2 mm deeper, for 1 mm x 5 mm foam tape on the radar's two
    sides and back. The module is pushed forward against the window by the foam; no crush ribs.
  - Battery bay: the border walls (down its side and across its front) are gone; the holder screws to its
    4 pads. The two pads that now stand alone are plain 10 mm round pads with the same 2.8 mm holes.
    The floor where the tripod post used to be is flat again.
  - Sensor pod for the DFRobot Gravity 10-DoF IMU (SEN0696), which replaces both the Adafruit IMU and
    the BMP390: same 66 x 50 mm pod, two boards, cable slot moved to the back (nearer J4), pod screws
    moved 7.3 mm into the gap between the boards (the lid's inserts moved with them).
  - Every M3 heat-set insert hole is 7.5 mm deep (lid corner columns were 6, board posts 5, the pod's
    lid risers 6), so the common 7 mm long inserts fit as well as short ones. The pod risers under
    lid_sensors are 1 mm longer (7 mm) to keep plastic under their holes. INSERT_DEPTH in the script.
  - Power-button opening in the left wall: a 14 mm wide x 10 mm tall slot with round ends (Sean's 8 mm
    hole was too small; it can't go taller without hitting parts inside), same centre.
    BUTTON_SLOT_W / BUTTON_HOLE_D in the script.
  - Tripod mount: moved 7 mm toward the battery side, to the estimated balance point with everything in
    (the cell and holder make that side heavier). Its post inside is shorter (top 10.6 mm above the
    case bottom), leaving 3.8 mm under the circuit board: trim the solder tails of R19-R22, C26, J3 and
    J4 to 2 mm or less. The hole is 7.15 mm across and 9 mm deep for Sean's 1/4-20 heat-set inserts
    (7.0 was too tight). TRIPOD_IX/IY, TRIPOD_HOLE_D, TRIPOD_HOLE_DEPTH in the script.
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
  - Two 8 mm risers hang under the lid (7 mm from v0.8) at the pod's screw spots. Press an M3 heat-set insert into
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
  lid_sensors.stl / .step            lid_oled plus the pod's 2 insert risers and its cable slot (pod's back
                                     corner, far side). Print top-face down; the risers point up.
  sensor_pod.stl / .step             vented pod, 66 x 50 x 20 mm, for two boards side by side (v0.8):
                                     the SHT45 at the far-side end on 4 posts (4 x M2.5 x 6 brass screws), and
                                     the DFRobot Gravity 10-DoF IMU (SEN0696: compass, level and BMP581 pressure)
                                     at the +X (gun-side) end. Its two 3 mm holes are at the front, on 6 mm posts
                                     taking 2 x M3 x 6 brass screws; two plain rest posts hold up its plug end,
                                     which faces you, with 14 mm behind it for the plug and wires. A small arrow
                                     under it points to the front. The cable slot is in the back corner on the
                                     far side, nearest J4. The two pod-to-lid screws sit in the gap between the
                                     boards (screw the pod down before fitting the IMU board).
                                     A column in each inside corner takes a roof screw. Print upright.
                                     The vent slots have 2 mm uprights (3 on the long sides, 2 on the short
                                     sides), so no bridge is longer than 17 mm; no supports needed.
  sensor_pod_roof.stl / .step        shade roof; print flat face down; light-coloured filament. Held by 4 M2.5 x 6 mm
                                     brass screws into the pod's corner columns (its lip is notched to clear them)

  The posts suit Adafruit's 1.0 x 0.7 in STEMMA QT boards, whose 2.5 mm holes sit 0.1 in from each
  corner (20.32 x 12.7 mm apart). Check yours when they arrive; if they don't line up, change
  SQ_HOLE_DX / SQ_HOLE_DY in the script. The 2.2 mm pilot holes let the screws cut their own thread:
  drive each one slowly until the board is snug, then stop (over-tightening strips plastic threads).
  Use brass (or nylon) screws, not steel: the IMU's compass is a few millimetres from its screws, and
  steel ones would bend the field it measures.

  Cables (v0.8): J4 -> SHT45 -> DFRobot 10-DoF, one chain. A 150 mm STEMMA QT-to-pins cable from J4 on
  the main board up through the lid slot, along the SHT45 to its front socket; then from the SHT45's back
  socket to the DFRobot's Gravity cable: a STEMMA QT-to-male-pins cable (Adafruit 4209) plugs into its
  wires if they end in female sockets, or splice a cut 100 mm STEMMA QT cable to them. Match by the
  DFRobot's pin labels: red -> +, black -> -, yellow SCL -> C/R, blue SDA -> D/T. Set its I2C/UART
  switch to I2C and A0/A1 to 0 (address 0x4A). The BMP390 is no longer needed (the BMP581 replaces it);
  POD_BMP390 = True in the script brings back the 3-board pod (75 x 56 mm) if you'd rather keep it. Use brass or nylon screws to hold the pod on the
  lid too if you have them (steel ones 20 mm or more from the compass are calibrated out, but brass is simpler).

Outside size: 118.8 x 130.8 x 36.4 mm, plus the 2.4 mm lid.
Hardware (v0.8 adds): 4 x M2 x 4 screws (screen), battery-holder screws to suit its 2.8 mm holes
          (M3 x 6 self-tapping screws cut their own thread in a 2.8 mm hole), ~150 mm of
          1 mm x 5 mm foam tape (radar sides, back and top).
Hardware: 8 x M3 heat-set inserts (4.1 mm holes), 4 x M3x8 (lid), 4 x M3x6 (board),
          1 x 1/4-20 heat-set insert, up to 9 mm long (7.15 mm hole, 9 mm deep) for a tripod.
          Sensor pod: 2 x M3x8 + 2 more M3 heat-set inserts (in the lid's risers).  SHT45 and pod roof: 8 x M2.5x6 brass screws; DFRobot IMU: 2 x M3x6 brass screws.

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
