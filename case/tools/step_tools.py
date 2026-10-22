"""Read a STEP file with OpenCascade (OCP): size, volume, and an STL for rendering / comparing.
   python3 step_tools.py info part.step
   python3 step_tools.py stl part.step out.stl [tolerance_mm]"""
import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer


def load(path):
    r = STEPControl_Reader()
    if r.ReadFile(path) != IFSelect_RetDone:
        raise SystemExit("couldn't read " + path)
    r.TransferRoots()
    return r.OneShape()


def info(shape):
    b = Bnd_Box(); BRepBndLib.Add_s(shape, b)
    p0, p1 = b.CornerMin(), b.CornerMax()
    x0, y0, z0, x1, y1, z1 = p0.X(), p0.Y(), p0.Z(), p1.X(), p1.Y(), p1.Z()
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(shape, g)
    return dict(size=(x1 - x0, y1 - y0, z1 - z0), min=(x0, y0, z0), volume=g.Mass())


def to_stl(shape, out, tol=0.05):
    BRepMesh_IncrementalMesh(shape, tol, False, 0.3, True)
    w = StlAPI_Writer(); w.ASCIIMode = False
    w.Write(shape, out)


if __name__ == "__main__" and sys.argv[1] != "diff":
    cmd, path = sys.argv[1], sys.argv[2]
    s = load(path)
    if cmd == "info":
        i = info(s)
        print("size %.2f x %.2f x %.2f mm, min corner (%.2f, %.2f, %.2f), volume %.1f mm3" % (*i["size"], *i["min"], i["volume"]))
    elif cmd == "stl":
        to_stl(s, sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 0.05)
        print("wrote", sys.argv[3])


def diff(a_path, b_path):
    """What changed from part A to part B: the pieces of material added and removed, each with its box and volume."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SOLID
    a, b = load(a_path), load(b_path)
    out = {}
    for name, (x, y) in (("added", (b, a)), ("removed", (a, b))):
        cut = BRepAlgoAPI_Cut(x, y); cut.Build()
        pieces = []
        e = TopExp_Explorer(cut.Shape(), TopAbs_SOLID)
        while e.More():
            i = info(e.Current())
            if i["volume"] > 0.5:
                pieces.append(i)
            e.Next()
        out[name] = sorted(pieces, key=lambda p: -p["volume"])
    return out


if __name__ == "__main__" and sys.argv[1] == "diff":
    d = diff(sys.argv[2], sys.argv[3])
    for name in ("added", "removed"):
        print("%s: %d piece(s)" % (name, len(d[name])))
        for p in d[name][:20]:
            x0, y0, z0 = p["min"]; sx, sy, sz = p["size"]
            print("  %8.1f mm3  x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" % (p["volume"], x0, x0 + sx, y0, y0 + sy, z0, z0 + sz))
