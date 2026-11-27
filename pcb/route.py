"""Write a Specctra DSN from design.py, route it with Freerouting (headless under Xvfb), read the SES back."""
import os, re, subprocess, json, sys, shutil
import design as D

U = 1000  # um per mm

def um(v):
    return int(round(v * U))

def padstack_name(sh, w, h, dr):
    return "PS_%s_%d_%d_%d" % (sh, um(w), um(h), um(dr))

def write_dsn(path):
    D.check_netlist()
    pw = D.pads_world()
    stacks = {}
    lines = []
    A = lines.append
    A('(pcb rbblipr')
    A('  (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "rbblipr-py") (host_version "1"))')
    A('  (resolution um 1)')
    A('  (unit um)')
    A('  (structure')
    A('    (layer F.Cu (type signal) (property (index 0)))')
    A('    (layer B.Cu (type signal) (property (index 1)))')
    e = 0.3
    A('    (boundary (path pcb 0 %d %d %d %d %d %d %d %d %d %d))' % (0, 0, um(D.BOARD_W), 0, um(D.BOARD_W), um(D.BOARD_H), 0, um(D.BOARD_H), 0, 0))
    # mounting holes: keepouts on both layers
    for hx, hy in D.HOLES:
        A('    (keepout "" (circle signal %d %d %d))' % (um(D.HOLE_KEEPOUT * 2), um(hx), um(hy)))
    # ESP32-C3 antenna end: no wires or vias between the module's two pin rows
    ax0, ay0, ax1, ay1 = D.ANTENNA_KEEPOUT
    A('    (keepout "" (rect signal %d %d %d %d))' % (um(ax0 + 3.2), um(ay0), um(ax1 - 3.2), um(ay1 + 0.5)))
    A('    (via "Via600")')
    A('    (rule (width %d) (clearance %d) (clearance %d (type smd_smd)))' % (um(D.SIGNAL_W), um(D.CLEARANCE), um(D.CLEARANCE)))
    A('  )')
    # each part gets its own image (footprint with its rotation applied by placement)
    A('  (placement')
    for ref, p in D.P.items():
        A('    (component IMG_%s (place %s %d %d front %d))' % (ref, ref, um(p["x"]), um(p["y"]), int(p["rot"]) % 360))
    A('  )')
    A('  (library')
    for ref, p in D.P.items():
        A('    (image IMG_%s' % ref)
        for (nm, dx, dy, sh, w, h, dr) in p["fp"]["pads"]:
            st = padstack_name(sh, w, h, dr)
            stacks[st] = (sh, w, h, dr)
            A('      (pin %s "%s" %d %d)' % (st, nm, um(dx), um(dy)))
        A('    )')
    for st, (sh, w, h, dr) in stacks.items():
        A('    (padstack %s' % st)
        for L in ("F.Cu", "B.Cu"):
            if sh == "rect":
                A('      (shape (rect %s %d %d %d %d))' % (L, -um(w / 2), -um(h / 2), um(w / 2), um(h / 2)))
            else:
                A('      (shape (circle %s %d))' % (L, um(max(w, h))))
        A('      (attach off)')
        A('    )')
    A('    (padstack Via600 (shape (circle F.Cu 600)) (shape (circle B.Cu 600)) (attach off))')
    A('  )')
    A('  (network')
    for n, pins in D.NETS.items():
        A('    (net "%s" (pins %s))' % (n, " ".join('%s-"%s"' % tuple(p.split("-", 1)) if False else p for p in pins)))
    groups = {}
    for n in D.NETS:
        groups.setdefault(D.POWER_NETS.get(n, D.SIGNAL_W), []).append(n)
    for i, (w, ns) in enumerate(sorted(groups.items())):
        A('    (class C%d %s (circuit (use_via Via600)) (rule (width %d) (clearance %d)))' % (i, " ".join('"%s"' % n for n in ns), um(w), um(D.CLEARANCE)))
    A('  )')
    A('  (wiring)')
    A(')')
    open(path, "w").write("\n".join(lines) + "\n")

def run_freerouting(dsn, ses, passes=40):
    jar = os.environ.get("FREEROUTING_JAR", "")
    for cand in (jar, os.path.expanduser("~/tools/freerouting-1.9.0.jar"),
                 os.path.expanduser("~/Library/Caches/blipr-tools/freerouting/freerouting-1.9.0.jar")):
        if cand and os.path.exists(cand):
            jar = cand
            break
    java = shutil.which("java")
    if sys.platform == "darwin" and os.path.exists("/opt/homebrew/opt/openjdk/bin/java"):
        java = "/opt/homebrew/opt/openjdk/bin/java"   # Homebrew's Java (macOS has only a stub)
    # Linux: run it under a virtual display; macOS: Freerouting opens its window briefly
    cmd = ([] if sys.platform == "darwin" or not shutil.which("xvfb-run") else ["xvfb-run", "-a"]) + \
          [java, "-Djava.awt.headless=false", "-jar", jar, "-de", dsn, "-do", ses, "-mp", str(passes), "-dct", "0"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    log = (r.stdout + r.stderr)
    open(ses + ".log", "w").write(log)
    return os.path.exists(ses)

def parse_ses(path):
    """-> {"wires": [(net, layer, width_mm, [(x,y),...])], "vias": [(net, x, y)]}"""
    s = open(path).read()
    res = re.search(r"\(resolution um (\d+)\)", s)
    scale = int(res.group(1)) * U if res else U
    out = {"wires": [], "vias": []}
    i = s.find("(network_out")
    body = s[i:]
    for m in re.finditer(r'\(net\s+("?)([^"\s)]+)\1(.*?)(?=\(net\s|\Z)', body, re.S):
        net, chunk = m.group(2), m.group(3)
        for w in re.finditer(r"\(path\s+(\S+)\s+(\d+)\s+([-\d\s]+)\)", chunk):
            layer, width = w.group(1), int(w.group(2)) / scale
            nums = [int(v) for v in w.group(3).split()]
            pts = [(nums[k] / scale, nums[k + 1] / scale) for k in range(0, len(nums) - 1, 2)]
            out["wires"].append((net, layer, width, pts))
        for v in re.finditer(r'\(via\s+"?[^"\s]+"?\s+(-?\d+)\s+(-?\d+)', chunk):
            out["vias"].append((net, int(v.group(1)) / scale, int(v.group(2)) / scale))
    return out

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    write_dsn("out/rbblipr.dsn")
    print("dsn written")
    if "--route" in sys.argv:
        ok = run_freerouting(os.path.abspath("out/rbblipr.dsn"), os.path.abspath("out/rbblipr.ses"), int(sys.argv[sys.argv.index("--route") + 1]) if len(sys.argv) > sys.argv.index("--route") + 1 else 40)
        print("routed" if ok else "routing failed; see log")
    if os.path.exists("out/rbblipr.ses"):
        r = parse_ses("out/rbblipr.ses")
        json.dump(r, open("out/routes.json", "w"))
        print(len(r["wires"]), "wires", len(r["vias"]), "vias")
