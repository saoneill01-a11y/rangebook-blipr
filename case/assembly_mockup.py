"""Assembled / exploded mockup of the case.  python3 assembly_mockup.py <explode_mm> <lid name> <out.png> [title]"""
import os, sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blip_case as c
from render import load_stl, zbuffer
O = os.path.join(HERE, "out") + os.sep
def boxtris(x0,y0,z0,x1,y1,z1):
    v=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]])
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return np.array([[v[a],v[b],v[d]] for a,b,d in f])
def cylz(cx,cy,r,z0,z1,n=24):
    out=[]
    for i in range(n):
        a,b=2*np.pi*i/n,2*np.pi*(i+1)/n
        p,q=(cx+r*np.cos(a),cy+r*np.sin(a)),(cx+r*np.cos(b),cy+r*np.sin(b))
        out+= [[(cx,cy,z0),q+(z0,),p+(z0,)],[(cx,cy,z1),p+(z1,),q+(z1,)],[p+(z0,),q+(z0,),q+(z1,)],[p+(z0,),q+(z1,),p+(z1,)]]
    return np.array(out)
explode = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
lidfile = sys.argv[2] if len(sys.argv) > 2 else "lid_sensors"
top = c.FLOOR + c.IH
parts, cols = [], []
def add(t, col): parts.append(t); cols.append(col)
add(load_stl(O+"base.stl"), (0.55,0.6,0.68))
# front cover standing in its slot
cv = load_stl(O+"front_cover.stl")
x = c.X(c.RADAR_CX) - c.COVER_W/2 + cv[:,:,0]; y = c.y0 + 0.1 + cv[:,:,2]; z = c.Z(0) + cv[:,:,1]
add(np.stack([x,y,z],-1), (0.85,0.55,0.3))
# insides (simple blocks)
X, Y, Z = c.X, c.Y, c.Z
add(boxtris(X(c.BOARD_IX),Y(c.BOARD_IY),Z(c.POST_H),X(c.BOARD_IX+c.BOARD_W),Y(c.BOARD_IY+c.BOARD_D),Z(c.POST_H+1.6)), (0.15,0.5,0.25))
add(boxtris(X(c.BOARD_IX+3),Y(c.TEENSY_IY-9),Z(c.POST_H+1.6+8.5),X(c.BOARD_IX+3+61),Y(c.TEENSY_IY+9),Z(c.POST_H+1.6+8.5+1.6)), (0.1,0.35,0.15))
add(boxtris(X(c.RADAR_CX-12.5),Y(c.HOLDER_T),Z(c.RADAR_LEDGE),X(c.RADAR_CX+12.5),Y(c.HOLDER_T+6),Z(c.RADAR_LEDGE+25)), (0.85,0.75,0.2))
add(boxtris(X(2),Y(c.BAY_IY0+2),Z(0.5),X(c.BAY_W-2),Y(c.BAY_IY0+100),Z(22)), (0.25,0.35,0.6))
add(boxtris(X(c.OLED_IX-13.5),Y(c.OLED_IY-14),Z(c.IH-4),X(c.OLED_IX+13.5),Y(c.OLED_IY+14),Z(c.IH-1)), (0.2,0.2,0.25))
# lid (raised when exploded)
L = load_stl(O+lidfile+".stl") + np.array([0,0,top+explode])
add(L, (0.62,0.68,0.78))
if lidfile == "lid_sensors":
    pz = top + c.LID_T + explode*1.8
    pod = load_stl(O+"sensor_pod.stl") + np.array([X(c.POD_IX), Y(c.POD_IY), pz])
    add(pod, (0.72,0.74,0.78))
    rf = load_stl(O+"sensor_pod_roof.stl")
    rz = pz + c.POD_H + 2.0 + explode*0.8
    rf = np.stack([rf[:,:,0]+X(c.POD_IX), -rf[:,:,1]+Y(c.POD_IY), rz - rf[:,:,2]], -1)
    add(rf, (0.92,0.92,0.88))
out = sys.argv[3]
views = [(28, -58, "From the front (radar window), right side"), (32, 125, "From behind, over your right shoulder")]
fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=110)
for ax, (e, a, lab) in zip(axs, views):
    ax.imshow(zbuffer(parts, e, a, W=1100, H=850, colors=cols)); ax.set_title(lab); ax.axis("off")
plt.suptitle(sys.argv[4] if len(sys.argv) > 4 else "", fontsize=13)
plt.tight_layout(); plt.savefig(out)
