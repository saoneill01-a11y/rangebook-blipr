#!/usr/bin/env python3
"""Make fake BLIPR recordings (same file format as the Teensy's s00001.bin) for testing the replay tool
and the signal processing without the hardware. Uses the same shot model as firmware/test/sim_test.cpp:
a bullet slowing at a fixed rate, the radar beside and behind the muzzle, a 1/R^2 echo, noise and a
muzzle-blast burst.

    pip install numpy
    python tools/make_test_recordings.py                      5 shots near 2700 fps into recordings/fake/
    python tools/make_test_recordings.py --fps 2650 2655 2648 --amp 250 --blast 3000 --into recordings/fake_weak
"""
import argparse, json, os
import numpy as np


def make(path, fps, shot, acc=-320.0, lat=0.12, behind=0.15, amp=800.0, noise=14.0, blast=1500.0,
         fs=600000.0, f0=24.150e9, seed=1):
    rng = np.random.default_rng(seed)
    n = 78 * 1024
    t0s = 12 * 1024 + 300                       # muzzle exit, samples from the capture start
    v0 = fps * 0.3048
    t = (np.arange(n) - t0s) / fs
    lam = 299792458.0 / f0
    I = 2048 + noise * rng.standard_normal(n)
    Q = 2048 + noise * rng.standard_normal(n)
    m = t >= 0
    tt = t[m]
    X = v0 * tt + 0.5 * acc * tt * tt + behind
    R = np.sqrt(X * X + lat * lat)
    ph = 4 * np.pi * R / lam
    a = amp / np.maximum(R * R, 0.04)
    a = np.where(R < 0.2, a * R / 0.2, a)
    env = blast * np.exp(-tt / 0.002)
    I[m] += a * np.cos(ph) + env * 0.6 * rng.standard_normal(len(tt))
    Q[m] += a * np.sin(ph) + env * 0.6 * rng.standard_normal(len(tt))
    I = np.clip(np.round(I), 0, 4095).astype("<u2")
    Q = np.clip(np.round(Q), 0, 4095).astype("<u2")
    hdr = {"fmt": "rchrono1", "fw": "fake", "boot": "00000000", "shot": shot, "fs": fs, "n": n, "t0": t0s / fs,
           "pre": 0, "f0": f0, "cal": 0, "lat": lat, "behind": behind, "vmin": 300 * 0.3048, "vmax": 4500 * 0.3048,
           "snr": 12, "trig": 0, "code": 0, "v0": v0, "acc": acc, "pts": 0, "rms": 0, "ovr": 0, "ms": 0, "unix": 0}
    h = json.dumps(hdr, separators=(",", ":")).encode().ljust(510, b" ") + b"\r\n"
    with open(path, "wb") as f:
        f.write(h + I.tobytes() + Q.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fps", type=float, nargs="+", default=[2700, 2706, 2695, 2702, 2698])
    ap.add_argument("--amp", type=float, default=800, help="echo strength (counts at 1 m); 250 is weak, 90 very weak")
    ap.add_argument("--noise", type=float, default=14, help="noise per channel (counts rms)")
    ap.add_argument("--blast", type=float, default=1500, help="muzzle blast strength (counts)")
    ap.add_argument("--lat", type=float, default=0.12, help="radar beside the bore line (m)")
    ap.add_argument("--behind", type=float, default=0.15, help="radar behind the muzzle (m)")
    ap.add_argument("--into", default="recordings/fake")
    a = ap.parse_args()
    os.makedirs(a.into, exist_ok=True)
    for i, fps in enumerate(a.fps):
        make(os.path.join(a.into, f"s{i + 1:05d}.bin"), fps, i + 1, amp=a.amp, noise=a.noise, blast=a.blast,
             lat=a.lat, behind=a.behind, seed=i + 1)
    print(f"{len(a.fps)} fake recordings in {a.into}")


if __name__ == "__main__":
    main()
