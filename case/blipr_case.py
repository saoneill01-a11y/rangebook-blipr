"""
Range Book BLIPR (Ballistic Launch Inspection Portable Radar) - parametric case (v0.7, draft from datasheet / nominal sizes).

Run:  python3 blipr_case.py
Needs only Python 3 (csg.py sits next to this file). Writes STEP + STL for:
  base, lid_oled, lid_plain, front_cover, front_cover_thin,
  lid_sensors (lid_oled plus risers, insert holes and a cable slot for the sensor pod), sensor_pod, sensor_pod_roof
  (v0.4: the compass/level IMU moved from the case floor into the sensor pod, and the pod moved off the battery)

All sizes in mm. Change a number below and re-run. Coordinates:
  X = left -> right (looking at the FRONT, where the radar faces downrange)
  Y = front -> back   (front face is Y = 0)
  Z = bottom -> top
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csg import *

# ------------------------------------------------------------------ parameters
WALL = 2.4          # side wall thickness (6 perimeters at 0.4 mm)
FLOOR = 2.4         # floor thickness
LID_T = 2.4         # lid thickness
R_OUT = 6.0         # outer corner radius
IW, ID, IH = 114.0, 126.0, 34.0   # inside width (X), depth (Y), height (Z)

OW, OD = IW + 2 * WALL, ID + 2 * WALL
x0, y0, z0 = WALL, WALL, FLOOR    # inside origin (front-left-bottom inside corner)

# --- lid screws: M3 heat-set inserts in corner columns
COL = 8.0           # corner column size
INSERT_D = 4.1      # M3 heat-set insert hole (check your insert's spec)
INSERT_DEPTH = 6.0
SCREW_CLEAR = 3.4   # M3 clearance hole in lid

# --- main perfboard (70 x 90) on 4 posts
BOARD_W, BOARD_D = 70.0, 90.0
BOARD_IX, BOARD_IY = 43.0, 25.0     # board front-left corner, inside coordinates
POST_H = 12.0       # tall posts: room for the tripod insert boss underneath
POST_D = 7.0
HOLE_INSET = 3.0    # mounting-hole centres from board edges (typical 70x90 board)

# --- battery bay (18650 shield)
BAY_W = 34.0        # inside width of bay (X)
BAY_IY0, BAY_IY1 = 12.0, ID   # bay front stop .. rear wall
BAY_WALL_H = 8.0

# --- radar (RFbeam K-LC5: 25 x 25 x 6 mm)
RADAR_CX = BOARD_IX + BOARD_W / 2   # radar centre X (inside coords)
RADAR_W = 25.0
RADAR_CLR = 0.6     # clearance around module
RADAR_LEDGE = 3.0   # module sits this high above the floor
RADAR_DEPTH = 6.6   # pocket depth (module is 6 mm incl. pins)
RADAR_CZ = RADAR_LEDGE + RADAR_W / 2   # module centre height above floor

# --- front cover (separate, printed flat)
COVER_T = 2.0       # frame thickness
WINDOW_T = 0.9      # thin window thickness (radar looks through this)
WINDOW_T_THIN = 0.5 # the extra-thin version (front_cover_thin)
COVER_W = 44.0
COVER_SLOT = COVER_T + 0.25
COVER_H = IH - 0.3
WINDOW_W, WINDOW_H = 32.0, 28.0

HOLDER_T = 4.0      # cover holder block depth (Y), includes slot
FRONT_OPEN_W, FRONT_OPEN_H = 34.0, 30.0

# --- rear wall openings
TEENSY_IY = BOARD_IY + 75.0          # Teensy lies left-right; its USB faces the RIGHT wall, centred 75 mm back from the board's front edge
TEENSY_USB_Z = POST_H + 1.6 + 8.5 + 1.6 + 1.5   # above floor (Teensy on 8.5 mm female headers)
USB_W, USB_H = 13.0, 10.0
USB_EXTRA_DOWN = 7.0  # v0.5: the hole also reaches 7 mm lower (Teensy sitting lower than the 8.5 mm headers assumed)
CHG_IX, CHG_W, CHG_Z0, CHG_Z1 = BAY_W / 2, 16.0, 0.5, 12.5    # battery charge port slot
SW_IX, SW_Z, SW_W, SW_H = 50.0, 26.0, 7.0, 3.5               # slide-switch lever slot

# --- tripod mount (1/4-20 heat-set insert) under the case
TRIPOD_IX, TRIPOD_IY = 41.5, 62.0
TRIPOD_HOLE_D = 8.4    # check your insert's recommended hole size
TRIPOD_BOSS_D = 14.0
TRIPOD_INNER_H = 11.5  # boss height above the floor (stays 0.5 mm under the board)

# --- OLED window in lid (0.96" SSD1306 module, ~27 x 27 mm board)
# v0.7: the screen sits in the back corner on the gun side (+X), nearest the shooter, its window the same
# distance (14.4 mm) from the lid's back edge and +X edge. The module's header edge faces the front.
OLED_IX, OLED_IY = 90.0, 105.0        # centre of the module (inside coords)
OLED_WIN_W, OLED_WIN_H = 24.0, 12.0
OLED_WIN_OFFSET = 3.0                 # window centre is this far toward the BACK of module centre
OLED_POCKET = 28.4
OLED_POCKET_D = 1.0
# v0.8 (Sean's design, tested): the screen screws in with 4 x M2 into pads in the pocket's corners. The pads fill the
# corners and stand OLED_PAD_DROP below the lid; holes are 1.7 mm pilots for M2 screws (M2 x 4 is about right).
OLED_PAD_W, OLED_PAD_D, OLED_PAD_DROP, OLED_PILOT = 6.0, 4.3, 1.0, 1.7
OLED_HOLES = [(-11.9, -11.95), (11.9, -11.95), (-11.9, 12.05), (11.6, 12.05)]   # from the module centre, as measured
# radar hold-down: a rib under every lid that comes down to just above the radar's top edge (1 mm foam on it)
RADAR_RIB_LEN, RADAR_RIB_T, RADAR_FOAM, RADAR_SQUEEZE = 18.0, 3.0, 1.0, 0.3

# --- optional sensor kit (see the build guide's Sensors tab)
# v0.4: the pod holds all three boards (SHT45, BMP390 and the compass/level IMU) and sits on the rear-right of the
# lid, clear of the battery bay (the 18650's steel can and the shield's boost converter upset a compass).
POD_IX, POD_IY = 38.0, 34.0           # sensor pod centre on the lid (inside coords), v0.7: front corner on the far side
                                      # from the gun (-X), diagonally away from the screen; the IMU end (+X) stays clear of the battery bay
POD_RISER_D, POD_RISER_H = 8.0, 6.0   # risers under the lid for the pod's two M3 heat-set inserts
POD_W, POD_D, POD_H = 66.0, 50.0, 20.0   # W left-right, D front-back
POD_WALL, POD_FLOOR = 1.6, 2.0
POD_SCREW_DY = 19.0                   # M3 screws at +/- this from the pod centre (front-back), on the centre line
POD_ROOF_SX, POD_ROOF_SY = 28.4, 20.4   # roof screws (M2.5 brass, self-threading) at the 4 inside corners
POD_ROOF_PILOT, POD_ROOF_CLEAR, POD_ROOF_BOSS = 2.2, 2.9, 5.6
POD_COL_R, POD_COL_FILLET = 2.0, 1.2   # rounded exposed edge of each corner column / fillets where it meets the walls
POD_POST_W = 2.0          # uprights splitting the pod's vent slots (shorter bridges when printing)
POD_BOARD_DX = 21.0                   # board centres at -21 (SHT45), 0 (BMP390), +21 (IMU): long sides front-to-back
POD_CABLE_X, POD_CABLE_Y = -21.0, -19.0   # cable slot centre, pod coords (front-left corner, under nothing)
POD_CABLE_W, POD_CABLE_D = 8.0, 7.0   # slot for the STEMMA QT cable through pod floor and lid
NAME_TEXT = "BLIPR"
NAME_H, NAME_STROKE, NAME_DEPTH = 12.0, 2.4, 0.6
NAME_GAP = 8.0                         # BLIPR sits this far behind the sensor pod (toward you), centred under it
NAME_IX = POD_IX                       # centred under the pod, as seen from your seat
NAME_IY = POD_IY + POD_D / 2 + NAME_GAP + NAME_H / 2
SITE_TEXT, SITE_SIZE = "", 5.5   # small font lettering, e.g. "rangebook.org" (off for now: too fine to print well on the bed side)
SITE_FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
SITE_END_IX, SITE_EDGE = 11.0, 5.0      # where the text ends (inside X) / gap from the lid's back edge (mm)
# --- STEMMA QT sensor boards (Adafruit 1.0" x 0.7"): mounting holes 0.1" in from each corner
SQ_HOLE_DX, SQ_HOLE_DY = 20.32, 12.7   # hole spacing along the long and short side
SQ_STANDOFF_D, SQ_STANDOFF_H = 4.8, 5.0
SQ_PILOT_D = 2.2                      # pilot hole for an M2.5 x 6 mm brass screw to thread into (board holes are 2.5 mm)
SEG = 40   # facets per circle

def X(ix): return x0 + ix
def Y(iy): return y0 + iy
def Z(iz): return z0 + iz


def stemma_mount(cx, cy, z, along_y=False):
    """4 screw standoffs for an Adafruit 1.0 x 0.7 in STEMMA QT board, centred at (cx, cy), standing on z.
    Returns (solid parts, pilot holes to subtract afterwards)."""
    parts, holes = [], []
    hx, hy = (SQ_HOLE_DY / 2, SQ_HOLE_DX / 2) if along_y else (SQ_HOLE_DX / 2, SQ_HOLE_DY / 2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * hx, cy + sy * hy
            parts.append(cyl_z(px, py, SQ_STANDOFF_D / 2, z - 0.3, z + SQ_STANDOFF_H, SEG))
            holes.append(cyl_z(px, py, SQ_PILOT_D / 2, z + 0.37, z + SQ_STANDOFF_H + 1, 24))
    return parts, holes


def front_arrow(cx, cy, z, h=0.6, size=5.0):
    """raised arrow pointing toward the front (-Y), standing on z"""
    return union_all([prism([(cx - size / 2, cy + size * 0.1), (cx, cy - size * 0.9), (cx + size / 2, cy + size * 0.1)], z - 0.2, z + h),
                      box(cx - size * 0.18, cy + size * 0.05, z - 0.2, cx + size * 0.18, cy + size * 1.1, z + h)])


def base():
    shell = rbox(0, 0, 0, OW, OD, FLOOR + IH, R_OUT) - rbox(x0, y0, z0, x0 + IW, y0 + ID, z0 + IH + 5, R_OUT - WALL)
    adds = []
    # corner columns
    for cx, cy in [(0, 0), (IW - COL, 0), (0, ID - COL), (IW - COL, ID - COL)]:
        adds.append(box(X(cx) - 0.5, Y(cy) - 0.5, z0 - 0.5, X(cx + COL) + 0.5 if cx > 0 else X(cx + COL),
                        Y(cy + COL) + 0.5 if cy > 0 else Y(cy + COL), Z(IH)))
    # board posts
    for hx in (HOLE_INSET, BOARD_W - HOLE_INSET):
        for hy in (HOLE_INSET, BOARD_D - HOLE_INSET):
            adds.append(cyl_z(X(BOARD_IX + hx), Y(BOARD_IY + hy), POST_D / 2, z0 - 0.5, Z(POST_H), SEG))
    # battery bay: divider wall + front stop
    adds.append(box(X(BAY_W), Y(BAY_IY0 - 2), z0 - 0.5, X(BAY_W + 2), Y(ID) + 0.5, Z(BAY_WALL_H)))
    adds.append(box(x0 - 0.5, Y(BAY_IY0 - 2), z0 - 0.5, X(BAY_W + 2), Y(BAY_IY0), Z(BAY_WALL_H)))
    # front cover holder + radar pocket block
    hw = COVER_W / 2 + 4.0
    adds.append(box(X(RADAR_CX - hw), y0 - 0.5, z0 - 0.5, X(RADAR_CX + hw), Y(HOLDER_T), Z(IH)))
    pw = RADAR_W / 2 + RADAR_CLR + 2.4
    adds.append(box(X(RADAR_CX - pw), Y(HOLDER_T) - 0.5, z0 - 0.5, X(RADAR_CX + pw), Y(HOLDER_T + RADAR_DEPTH + 1.6), Z(RADAR_W + RADAR_LEDGE + 1.5)))
    # tripod boss inside
    adds.append(cyl_z(X(TRIPOD_IX), Y(TRIPOD_IY), TRIPOD_BOSS_D / 2, z0 - 0.5, Z(TRIPOD_INNER_H), SEG))
    t = time.time()
    s = shell.union(union_all(adds))
    print("  base adds", round(time.time() - t, 1), "s", len(s.polys), "polys")

    cuts = []
    # lid insert holes
    for cx, cy in [(0, 0), (IW - COL, 0), (0, ID - COL), (IW - COL, ID - COL)]:
        cuts.append(cyl_z(X(cx + COL / 2), Y(cy + COL / 2), INSERT_D / 2, Z(IH - INSERT_DEPTH), Z(IH) + 1, SEG))
    # board post insert holes
    for hx in (HOLE_INSET, BOARD_W - HOLE_INSET):
        for hy in (HOLE_INSET, BOARD_D - HOLE_INSET):
            cuts.append(cyl_z(X(BOARD_IX + hx), Y(BOARD_IY + hy), INSERT_D / 2, Z(POST_H - 5.0), Z(POST_H) + 1, SEG))
    # front wall opening (radar window)
    cuts.append(box(X(RADAR_CX - FRONT_OPEN_W / 2), -1, Z(RADAR_CZ - FRONT_OPEN_H / 2), X(RADAR_CX + FRONT_OPEN_W / 2), y0 + 0.01, Z(RADAR_CZ + FRONT_OPEN_H / 2)))
    # cover slot (open at top) directly behind the front wall
    cuts.append(box(X(RADAR_CX - COVER_W / 2 - 0.2), y0, Z(0), X(RADAR_CX + COVER_W / 2 + 0.2), Y(COVER_SLOT), Z(IH) + 1))
    # aperture through the holder in front of the antenna
    ap = RADAR_W / 2 + 0.5
    cuts.append(box(X(RADAR_CX - ap), Y(COVER_SLOT) - 0.1, Z(RADAR_CZ - ap), X(RADAR_CX + ap), Y(HOLDER_T) + 0.1, Z(RADAR_CZ + ap)))
    # radar pocket (module drops in from the top)
    rp = RADAR_W / 2 + RADAR_CLR
    cuts.append(box(X(RADAR_CX - rp), Y(HOLDER_T) - 0.01, Z(RADAR_LEDGE), X(RADAR_CX + rp), Y(HOLDER_T + RADAR_DEPTH), Z(IH) + 1))
    # back opening of the pocket for the connector / wires (leaves 3 mm lips each side)
    cuts.append(box(X(RADAR_CX - rp + 3), Y(HOLDER_T + RADAR_DEPTH) - 0.1, Z(RADAR_LEDGE), X(RADAR_CX + rp - 3), Y(HOLDER_T + RADAR_DEPTH + 2.0), Z(IH) + 1))
    # right wall: Teensy USB.  rear wall: battery charge port, switch slot
    cuts.append(box(X(IW) - 1, Y(TEENSY_IY - USB_W / 2), Z(TEENSY_USB_Z - USB_H / 2 - USB_EXTRA_DOWN), OW + 1, Y(TEENSY_IY + USB_W / 2), Z(TEENSY_USB_Z + USB_H / 2)))
    cuts.append(box(X(CHG_IX - CHG_W / 2), Y(ID) - 1, Z(CHG_Z0), X(CHG_IX + CHG_W / 2), OD + 1, Z(CHG_Z1)))
    cuts.append(box(X(SW_IX - SW_W / 2), Y(ID) - 1, Z(SW_Z - SW_H / 2), X(SW_IX + SW_W / 2), OD + 1, Z(SW_Z + SW_H / 2)))
    # tripod insert hole from below
    cuts.append(cyl_z(X(TRIPOD_IX), Y(TRIPOD_IY), TRIPOD_HOLE_D / 2, -1, Z(TRIPOD_INNER_H) - 0.5, SEG))

    t = time.time()
    s = s.subtract(union_all(cuts))
    print("  base cuts", round(time.time() - t, 1), "s", len(s.polys), "polys")
    return s


def name_cuts(cx, cy, ztop):
    """NAME_TEXT ('BLIPR') in rounded block letters, cut NAME_DEPTH into the lid's top face, centred on (cx, cy).
    It reads from behind the case (like the OLED): the tops of the letters point to the front."""
    H, sw = NAME_H, NAME_STROKE
    k = H / 12.0                     # the letter shapes were drawn 12 mm tall
    r = 3.0 * k
    def bowl(u0, v0, u1, v1):
        return [("ring", u0, v0, u1, v1, r)]
    stem = ("box", 0, 0, sw, H, 0)
    G = {
        "B": (8.4 * k, [stem] + bowl(0, H / 2 - sw / 2, 7.6 * k, H) + bowl(0, 0, 8.4 * k, H / 2 + sw / 2)),
        "L": (7.0 * k, [stem, ("box", 0, 0, 7.0 * k, sw, 0)]),
        "I": (sw, [stem]),
        "P": (8.0 * k, [stem] + bowl(0, H * 0.42 - sw / 2, 8.0 * k, H)),
        "R": (8.4 * k, [stem] + bowl(0, H * 0.42 - sw / 2, 8.0 * k, H) +
              [("leg", 3.2 * k, H * 0.42, 8.4 * k, 0, 0)]),
    }
    gap = 2.6 * k
    glyphs = [G[ch] for ch in NAME_TEXT]
    total = sum(w for w, _ in glyphs) + gap * (len(glyphs) - 1)
    z0, z1 = ztop - NAME_DEPTH, ztop + 1
    def pt(u, v):                    # local -> lid coords, turned 180 degrees so it reads from the back
        return (cx + total / 2 - u, cy + H / 2 - v)
    out, u = [], 0.0
    for w, shapes in glyphs:
        for kind, a0, b0, a1, b1, rr in shapes:
            if kind == "leg":        # the R's leg: a slanted bar from the bowl down to the baseline
                lw = sw * 1.15
                q = [pt(u + a0, b0), pt(u + a0 + lw, b0), pt(u + a1, b1), pt(u + a1 - lw, b1)]
                area = sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4))
                out.append(prism(q if area > 0 else q[::-1], z0, z1))
                continue
            (xa, ya), (xb, yb) = pt(u + a1, b1), pt(u + a0, b0)
            if kind == "box":
                out.append(box(xa, ya, z0, xb, yb, z1))
            else:
                out.append(rbox(xa, ya, z0, xb, yb, z1, rr).subtract(
                    rbox(xa + sw, ya + sw, z0 - 1, xb - sw, yb - sw, z1 + 1, max(rr - sw, 0.4))))
        u += w + gap
    return out


def site_cuts(ztop):
    """SITE_TEXT ('rangebook.org') in small lower-case letters in the lid corner at your bottom right as you sit
    behind it (back edge, far side from the gun), reading the same way as the name."""
    if not SITE_TEXT:
        return []
    from textcut import text_outline, text_solid
    cs, (u0, v0, u1, v1) = text_outline(SITE_TEXT, SITE_FONT, SITE_SIZE)
    right = X(SITE_END_IX)               # the end of the text (the 'g') is this far along X
    bottom = Y(ID) + WALL - SITE_EDGE    # the bottom of the letters, this far in from the back edge
    place = lambda u, v: (right + (u1 - u), bottom - (v - v0))
    return text_solid(cs, place, ztop - NAME_DEPTH, ztop + 1)


def lid(with_oled, sensors=False):
    s = rbox(0, 0, 0, OW, OD, LID_T, R_OUT)
    if sensors:   # risers under the pod's two screws, so the inserts have 8.4 mm of plastic to grip
        s = s.union(union_all([cyl_z(X(POD_IX), Y(POD_IY + dy), POD_RISER_D / 2, -POD_RISER_H, 0.3, SEG)
                               for dy in (-POD_SCREW_DY, POD_SCREW_DY)]))
    cuts = []
    if sensors:
        for dy in (-POD_SCREW_DY, POD_SCREW_DY):   # M3 heat-set inserts, pressed in from the top, into the risers
            cuts.append(cyl_z(X(POD_IX), Y(POD_IY + dy), INSERT_D / 2, LID_T - INSERT_DEPTH, LID_T + 1, SEG))
        cx, cy = POD_IX + POD_CABLE_X, POD_IY + POD_CABLE_Y
        cuts.append(box(X(cx - POD_CABLE_W / 2), Y(cy - POD_CABLE_D / 2), -1, X(cx + POD_CABLE_W / 2), Y(cy + POD_CABLE_D / 2), LID_T + 1))
    for cx, cy in [(0, 0), (IW - COL, 0), (0, ID - COL), (IW - COL, ID - COL)]:
        cuts.append(cyl_z(X(cx + COL / 2), Y(cy + COL / 2), SCREW_CLEAR / 2, -1, LID_T + 1, SEG))
    cuts += name_cuts(X(NAME_IX), Y(NAME_IY), LID_T)
    cuts += site_cuts(LID_T)
    if with_oled:
        wy = OLED_IY + OLED_WIN_OFFSET
        cuts.append(box(X(OLED_IX - OLED_WIN_W / 2), Y(wy - OLED_WIN_H / 2), -1, X(OLED_IX + OLED_WIN_W / 2), Y(wy + OLED_WIN_H / 2), LID_T + 1))
        cuts.append(box(X(OLED_IX - OLED_POCKET / 2), Y(OLED_IY - OLED_POCKET / 2), -1, X(OLED_IX + OLED_POCKET / 2), Y(OLED_IY + OLED_POCKET / 2), OLED_POCKET_D))
    s = s.subtract(union_all(cuts))
    adds, holes = [], []
    if with_oled:                                 # screw pads in the screen pocket's four corners
        h = OLED_POCKET / 2
        for sx in (-1, 1):
            for sy in (-1, 1):
                xa, xb = sorted((OLED_IX + sx * h, OLED_IX + sx * (h - OLED_PAD_W)))
                ya, yb = sorted((OLED_IY + sy * h, OLED_IY + sy * (h - OLED_PAD_D)))
                adds.append(box(X(xa), Y(ya), -OLED_PAD_DROP, X(xb), Y(yb), OLED_POCKET_D + 0.01))
        for dx, dy in OLED_HOLES:
            holes.append(cyl_z(X(OLED_IX + dx), Y(OLED_IY + dy), OLED_PILOT / 2, -OLED_PAD_DROP - 1, OLED_POCKET_D, 20))
    # radar hold-down rib: with the lid on, it stops RADAR_FOAM - RADAR_SQUEEZE above the radar's top edge
    rib_bottom = (RADAR_LEDGE + RADAR_W + RADAR_FOAM - RADAR_SQUEEZE) - IH      # lid coords: the underside is z = 0
    ry = HOLDER_T + 3.0                                                          # over the middle of the module's 6 mm edge
    adds.append(box(X(RADAR_CX - RADAR_RIB_LEN / 2), Y(ry - RADAR_RIB_T / 2), rib_bottom, X(RADAR_CX + RADAR_RIB_LEN / 2), Y(ry + RADAR_RIB_T / 2), 0.3))
    s = s.union(union_all(adds))
    if holes:
        s = s.subtract(union_all(holes))
    return s


def sensor_pod():
    """Vented pod for the SHT45, BMP390 and IMU boards; sits on the lid. Printed upright, as it sits."""
    hw, hd = POD_W / 2, POD_D / 2
    s = rbox(-hw, -hd, 0, hw, hd, POD_H, 3.0)
    s = s.subtract(rbox(-hw + POD_WALL, -hd + POD_WALL, POD_FLOOR, hw - POD_WALL, hd - POD_WALL, POD_H + 1, 1.6))
    cuts = []
    # louvre slots, 2 mm tall, all four walls. Each slot is split by 2 mm uprights (2 on the long walls,
    # 1 on the short walls) so the printer never has to bridge more than about 17 mm.
    def spans(a0, a1, n_posts, post=POD_POST_W):
        step = (a1 - a0) / (n_posts + 1)
        edges = [a0] + [a0 + step * (k + 1) + sgn * post / 2 for k in range(n_posts) for sgn in (-1, 1)] + [a1]
        return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]
    for z in (4.5, 8.0, 11.5, 15.0):
        for x0, x1 in spans(-27, 27, 2):
            cuts.append(box(x0, -hd - 1, z, x1, -hd + POD_WALL + 0.4, z + 2))
            cuts.append(box(x0, hd - POD_WALL - 0.4, z, x1, hd + 1, z + 2))
        for y0, y1 in spans(-17, 17, 1):
            cuts.append(box(-hw - 1, y0, z, -hw + POD_WALL + 0.4, y1, z + 2))
            cuts.append(box(hw - POD_WALL - 0.4, y0, z, hw + 1, y1, z + 2))
    for dy in (-POD_SCREW_DY, POD_SCREW_DY):
        cuts.append(cyl_z(0, dy, SCREW_CLEAR / 2, -1, POD_FLOOR + 1, SEG))
    cuts.append(box(POD_CABLE_X - POD_CABLE_W / 2, POD_CABLE_Y - POD_CABLE_D / 2, -1, POD_CABLE_X + POD_CABLE_W / 2, POD_CABLE_Y + POD_CABLE_D / 2, POD_FLOOR + 1))
    s = s.subtract(union_all(cuts))
    # three sets of screw standoffs, long sides front-to-back, air underneath: SHT45 left, BMP390 middle,
    # IMU right (the end farthest from the battery), with an arrow in front of the IMU pointing to the front
    parts, holes = [], []
    for dx in (-POD_BOARD_DX, 0.0, POD_BOARD_DX):
        p, h = stemma_mount(dx, 0.0, POD_FLOOR, along_y=True)
        parts += p; holes += h
    parts.append(front_arrow(POD_BOARD_DX, -19.0, POD_FLOOR, 0.6, 4.0))
    # corner columns for the roof screws: a block in each inside corner, full height, with a pilot hole.
    # Its exposed edge is rounded and it blends into both walls with small fillets.
    b, R, F = POD_ROOF_BOSS / 2, POD_COL_R, POD_COL_FILLET
    z0, z1 = POD_FLOOR - 0.3, POD_H
    wx, wy = hw - POD_WALL, hd - POD_WALL          # inside faces of the walls
    def sbox(ax, ay, bx, by):                       # box from corners given in either order
        return box(min(ax, bx), min(ay, by), z0, max(ax, bx), max(ay, by), z1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * POD_ROOF_SX, sy * POD_ROOF_SY
            xi, yi = cx - sx * b, cy - sy * b       # the column's exposed corner
            xo, yo = sx * (wx + 0.5), sy * (wy + 0.5)
            parts.append(sbox(xi + sx * R, yi, xo, yo))
            parts.append(sbox(xi, yi + sy * R, xo, yo))
            parts.append(cyl_z(xi + sx * R, yi + sy * R, R, z0, z1, 24))
            # fillet against the long wall, and against the short wall
            parts.append(sbox(xi - sx * F, sy * wy, xi + sx * 0.01, sy * wy - sy * F)
                         .subtract(cyl_z(xi - sx * F, sy * wy - sy * F, F, z0 - 1, z1 + 1, 24)))
            parts.append(sbox(sx * wx, yi - sy * F, sx * wx - sx * F, yi + sy * 0.01)
                         .subtract(cyl_z(sx * wx - sx * F, yi - sy * F, F, z0 - 1, z1 + 1, 24)))
            holes.append(cyl_z(cx, cy, POD_ROOF_PILOT / 2, POD_H - 10.0, POD_H + 1, 24))
    # keep the cable slot through the floor clear of the front-left column's fillet
    holes.append(box(POD_CABLE_X - POD_CABLE_W / 2, POD_CABLE_Y - POD_CABLE_D / 2, -1, POD_CABLE_X + POD_CABLE_W / 2, POD_CABLE_Y + POD_CABLE_D / 2, POD_FLOOR + 0.6))
    return s.union(union_all(parts)).subtract(union_all(holes))


def sensor_pod_roof():
    """Shade roof for the pod: printed upside down (flat face on the bed); its lip drops inside the pod walls."""
    hw, hd = POD_W / 2, POD_D / 2
    s = rbox(-hw - 3, -hd - 3, 0, hw + 3, hd + 3, 2.0, 4.0)
    li = POD_WALL + 0.3
    lip = rbox(-hw + li, -hd + li, 1.9, hw - li, hd - li, 5.0, 1.3).subtract(rbox(-hw + li + 1.6, -hd + li + 1.6, 1.5, hw - li - 1.6, hd - li - 1.6, 6.0, 0.8))
    # the lip stops short of the corners, where the pod's screw columns are
    gx = POD_ROOF_SX - POD_ROOF_BOSS / 2 - POD_COL_FILLET - 0.6
    gy = POD_ROOF_SY - POD_ROOF_BOSS / 2 - POD_COL_FILLET - 0.6
    notch = union_all([box(gx if sx > 0 else -hw - 1, gy if sy > 0 else -hd - 1, 1.0,
                           hw + 1 if sx > 0 else -gx, hd + 1 if sy > 0 else -gy, 6.0) for sx in (-1, 1) for sy in (-1, 1)])
    s = s.union(lip.subtract(notch))
    return s.subtract(union_all([cyl_z(sx * POD_ROOF_SX, sy * POD_ROOF_SY, POD_ROOF_CLEAR / 2, -1, 3, 24)
                                 for sx in (-1, 1) for sy in (-1, 1)]))


def front_cover(window_t=None):
    """Printed flat, outside face down on the bed. Lies in XY; thickness along Z."""
    s = rbox(0, 0, 0, COVER_W, COVER_H, COVER_T, 1.0)
    # window: centred on the radar. Radar centre is RADAR_CZ above the floor; cover bottom sits on the floor.
    wc = RADAR_CZ
    win = box(COVER_W / 2 - WINDOW_W / 2, wc - WINDOW_H / 2, WINDOW_T if window_t is None else window_t, COVER_W / 2 + WINDOW_W / 2, wc + WINDOW_H / 2, COVER_T + 1)
    return s.subtract(win)


def export(solid, name, outdir):
    pts, faces, planes = clean_mesh(solid)
    bad, total = edge_report(faces)
    stl = os.path.join(outdir, name + ".stl")
    stp = os.path.join(outdir, name + ".step")
    ntri = write_stl(stl, pts, faces, planes, name)
    nf = write_step(stp, pts, faces, planes, name) if bad == 0 else None
    print("  %s: %d triangles, %d faces, unpaired edges=%d/%d %s" % (name, ntri, len(faces), bad, total,
          "" if bad == 0 else "(STEP skipped)"))
    return bad


# ---------------- the base now comes from Sean's CAD ----------------
# From case v0.8 the base is Sean's own model (user_edits/base_from_sean_2026-10-22.stl): battery-holder mounting
# points, USB-C charge and power-button holes in the far-side wall, the old back-wall charge and switch slots filled,
# the Teensy USB hole trimmed at the top. base() above is the older script version, kept for reference. Small changes
# on top of his model are listed in BASE_EDITS and made with mesh booleans (needs: pip install trimesh manifold3d).
BASE_SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_edits", "base_from_sean_2026-10-22.stl")
BASE_EDITS = [
    # (what, "cut" or "add", box from inside coords: x0, y0, z0, x1, y1, z1)
    ("radar pocket 0.2 mm wider each side and 0.2 mm deeper, for 1 mm foam tape on its sides and back",
     "cut", (RADAR_CX - 13.3, HOLDER_T, RADAR_LEDGE, RADAR_CX + 13.3, HOLDER_T + 6.8, IH + 5)),
]


def base_mesh():
    import numpy as np, trimesh, manifold3d as mf
    t = trimesh.load(BASE_SOURCE, force="mesh")
    m = mf.Manifold(mf.Mesh64(vert_properties=np.asarray(t.vertices, np.float64), tri_verts=np.asarray(t.faces, np.uint64)))
    for what, op, (a, b, c, d, e, f) in BASE_EDITS:
        blk = mf.Manifold.cube([d - a, e - b, f - c]).translate([X(a), Y(b), Z(c)])
        m = m - blk if op == "cut" else m + blk
    mm = m.to_mesh64()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts))


def export_mesh(t, name, outdir):
    """STL straight from the mesh; STEP through OpenCascade (pip install cadquery-ocp), flat areas merged into faces."""
    t.export(os.path.join(outdir, name + ".stl"))
    try:
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
        from OCP.gp import gp_Pnt
        from OCP.TopoDS import TopoDS
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_SHELL
        from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
        from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
        sew = BRepBuilderAPI_Sewing(1e-3)
        V_ = t.vertices
        for a, b, c in t.faces:
            poly = BRepBuilderAPI_MakePolygon(gp_Pnt(*V_[a]), gp_Pnt(*V_[b]), gp_Pnt(*V_[c]), True)
            f = BRepBuilderAPI_MakeFace(poly.Wire(), True)
            if f.IsDone():
                sew.Add(f.Face())
        sew.Perform()
        ex = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL)
        mk = BRepBuilderAPI_MakeSolid()
        while ex.More():
            mk.Add(TopoDS.Shell(ex.Current()))
            ex.Next()
        u = ShapeUpgrade_UnifySameDomain(mk.Solid(), True, True, True)
        u.Build()
        w = STEPControl_Writer()
        w.Transfer(u.Shape(), STEPControl_AsIs)
        w.Write(os.path.join(outdir, name + ".step"))
        step = "STEP written"
    except Exception as ex_:
        step = "STEP skipped (%s)" % ex_
    print("  %s: %d triangles, watertight %s, %d body, %s" % (name, len(t.faces), t.is_watertight, t.body_count, step))


def main():
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(outdir, exist_ok=True)
    print("Outside size: %.1f x %.1f x %.1f mm (+%.1f mm lid)" % (OW, OD, FLOOR + IH, LID_T))
    parts = {"front_cover": front_cover, "front_cover_thin": lambda: front_cover(WINDOW_T_THIN), "lid_plain": lambda: lid(False), "lid_oled": lambda: lid(True), "base": base,
             "lid_sensors": lambda: lid(True, True), "sensor_pod": sensor_pod, "sensor_pod_roof": sensor_pod_roof}
    only = sys.argv[1:]
    for name, fn in parts.items():
        if only and name not in only:
            continue
        if name == "base":                      # Sean's CAD model plus BASE_EDITS
            t = time.time()
            export_mesh(base_mesh(), "base", outdir)
            print("base built in %.1f s" % (time.time() - t))
            continue
        t = time.time()
        s = run_big_stack(fn)
        print("%s built in %.1f s" % (name, time.time() - t))
        export(s, name, outdir)


if __name__ == "__main__":
    main()
