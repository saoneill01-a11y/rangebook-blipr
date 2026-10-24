"""3D frames of the v0.8 case from the real STL files (numpy z-buffer from case/render.py)."""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
import os, sys, numpy as np
CASE = REPO + "/case"
sys.path.insert(0, CASE)
import blipr_case as c
from render import load_stl
O = CASE + "/out/"

def boxtris(x0,y0,z0,x1,y1,z1):
    v=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]])
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return np.array([[v[a],v[b],v[d]] for a,b,d in f], float)

_cache = {}
def stl(name):
    if name not in _cache:
        _cache[name] = load_stl(O + name)
    return _cache[name]

COL = {"base": (0.50, 0.55, 0.63), "cover": (0.93, 0.92, 0.86), "board": (0.13, 0.42, 0.24), "teensy": (0.11, 0.43, 0.24),
       "radar": (0.85, 0.72, 0.30), "holder": (0.20, 0.34, 0.62), "cell": (0.24, 0.55, 0.28), "oled": (0.15, 0.16, 0.20),
       "lid": (0.60, 0.66, 0.76), "pod": (0.70, 0.72, 0.76), "roof": (0.93, 0.93, 0.90), "esp": (0.10, 0.10, 0.12)}

def assembly(ex=None, include=None):
    """ex: dict of part -> lift in mm (z offset). include: set of part names to draw."""
    ex = ex or {}
    X, Y, Z = c.X, c.Y, c.Z
    top = c.FLOOR + c.IH
    parts = []
    def add(name, tris):
        if include is None or name in include:
            d = ex.get(name, 0.0)
            off = np.array(d, float) if isinstance(d, (tuple, list)) else np.array([0, 0, d], float)
            parts.append((name, tris + off))
    add("base", stl("base.stl"))
    cv = stl("front_cover.stl")
    x = X(c.RADAR_CX) - c.COVER_W / 2 + cv[:, :, 0]; y = c.y0 + 0.1 + cv[:, :, 2]; z = Z(0) + cv[:, :, 1]
    add("cover", np.stack([x, y, z], -1))
    add("board", boxtris(X(c.BOARD_IX), Y(c.BOARD_IY), Z(c.POST_H), X(c.BOARD_IX + c.BOARD_W), Y(c.BOARD_IY + c.BOARD_D), Z(c.POST_H + 1.6)))
    add("teensy", boxtris(X(c.BOARD_IX + 3), Y(c.TEENSY_IY - 9), Z(c.POST_H + 1.6 + 8.5), X(c.BOARD_IX + 3 + 61), Y(c.TEENSY_IY + 9), Z(c.POST_H + 1.6 + 8.5 + 1.6)))
    add("radar", boxtris(X(c.RADAR_CX - 12.5), Y(c.HOLDER_T), Z(c.RADAR_LEDGE), X(c.RADAR_CX + 12.5), Y(c.HOLDER_T + 6), Z(c.RADAR_LEDGE + 25)))
    add("holder", boxtris(X(2), Y(c.BAY_IY0 + 2), Z(0.5), X(c.BAY_W - 2), Y(c.BAY_IY0 + 100), Z(22)))
    add("oled", boxtris(X(c.OLED_IX - 13.5), Y(c.OLED_IY - 14), Z(c.IH - 4), X(c.OLED_IX + 13.5), Y(c.OLED_IY + 14), Z(c.IH - 1)))
    add("lid", stl("lid_sensors.stl") + np.array([0, 0, top]))
    pz = top + c.LID_T
    add("pod", stl("sensor_pod.stl") + np.array([X(c.POD_IX), Y(c.POD_IY), pz]))
    rf = stl("sensor_pod_roof.stl")
    rz = pz + c.POD_H + 2.0
    add("roof", np.stack([rf[:, :, 0] + X(c.POD_IX), -rf[:, :, 1] + Y(c.POD_IY), rz - rf[:, :, 2]], -1))
    return parts

import math
def rotm(elev, azim):
    a, e = math.radians(azim), math.radians(-(90 - elev))
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Rz

CENTER = np.array([59.4, 65.4, 30.0])   # roughly the closed case centre (mm)

def render(parts, elev, azim, W=1240, H=880, scale=6.0, center=None, colors=None, light=(0.35, 0.45, 0.82)):
    """Fixed-camera z-buffer. Returns RGBA float image (alpha 0 = background)."""
    R = rotm(elev, azim)
    ctr = (np.array(center) if center is not None else CENTER) @ R.T
    img = np.zeros((H, W, 4))
    zb = np.full((H, W), -np.inf)
    L = np.array(light, float); L /= np.linalg.norm(L)
    for k, (name, tris) in enumerate(parts):
        base_col = np.array(colors[k] if colors else COL.get(name, (0.6, 0.65, 0.75)))
        P = tris @ R.T
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        ln = np.linalg.norm(n, axis=1); ok = ln > 1e-9
        P, n = P[ok], n[ok] / ln[ok][:, None]
        shade = 0.38 + 0.62 * np.abs(n @ L)
        sx = (P[:, :, 0] - ctr[0]) * scale + W / 2
        sy = H / 2 - (P[:, :, 1] - ctr[1]) * scale
        sz = P[:, :, 2]
        for i in range(len(P)):
            x, y, z = sx[i], sy[i], sz[i]
            x0, x1 = int(max(0, math.floor(x.min()))), int(min(W - 1, math.ceil(x.max())))
            y0, y1 = int(max(0, math.floor(y.min()))), int(min(H - 1, math.ceil(y.max())))
            if x1 < x0 or y1 < y0:
                continue
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-12:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not inside.any():
                continue
            zz = l0 * z[0] + l1 * z[1] + l2 * z[2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (zz > sub)
            sub[upd] = zz[upd]
            img[y0:y1 + 1, x0:x1 + 1][upd] = np.append(base_col * shade[i], 1.0)
    return img

def project(pt, elev, azim, W=1240, H=880, scale=6.0, center=None):
    R = rotm(elev, azim)
    ctr = (np.array(center) if center is not None else CENTER) @ R.T
    p = np.array(pt) @ R.T
    return (p[0] - ctr[0]) * scale + W / 2, H / 2 - (p[1] - ctr[1]) * scale
