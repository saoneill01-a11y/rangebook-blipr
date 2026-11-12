#!/usr/bin/env python3
"""List the steady tones in BLIPR raw recordings (interference hunting).

    python tools/tones.py recordings/<folder> [first file number]

For each s*.bin: the strongest lines (frequency, the speed it would read as, dB over the median) in the averaged
spectrum, and a row showing in which 6.8-8 ms frames the strongest line is present (# = present).
A line that stays at the same frequency when the sample rate (set fs=) changes is a real signal below Nyquist;
one that moves is an alias of something faster.
"""
import json, sys, glob, os, numpy as np
d = sys.argv[1]; files = sorted(glob.glob(os.path.join(d, "s*.bin")))
first = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for fn in files:
    num = int(os.path.basename(fn)[1:6])
    if num < first: continue
    raw = open(fn, "rb").read()
    h = json.loads(raw[:512].split(b"\0")[0]); n = int(h["n"]); fs = h["fs"]
    a = np.frombuffer(raw[512:512 + 4 * n], dtype="<u2").astype(float)
    I, Q = a[:n], a[n:2 * n]
    x = (I - I.mean()) + 1j * (Q - Q.mean())
    # averaged spectrum over 4096-sample frames (Welch), plus per-frame presence of the top line
    N = 4096; fr = [x[i:i + N] * np.hanning(N) for i in range(0, n - N, N)]
    S = np.array([np.abs(np.fft.fftshift(np.fft.fft(f))) ** 2 for f in fr])
    f = np.fft.fftshift(np.fft.fftfreq(N, 1 / fs))
    P = 10 * np.log10(S.mean(0) + 1e-9); med = np.median(P)
    mask = np.abs(f) > 3000
    idx = np.argsort(np.where(mask, P, -1e9))[::-1]
    peaks = []
    for k in idx:
        if P[k] - med < 8: break
        if all(abs(f[k] - p[0]) > 3000 for p in peaks): peaks.append((f[k], P[k] - med))
        if len(peaks) >= 6: break
    # how many frames contain the top peak at >8 dB above that frame's median
    pres = ""
    if peaks:
        k0 = np.argmin(np.abs(f - peaks[0][0]))
        Pf = 10 * np.log10(S + 1e-9); fm = np.median(Pf, 1)
        on = (Pf[:, max(0, k0 - 2):k0 + 3].max(1) - fm) > 10
        pres = "".join("#" if o else "." for o in on)
    fps = lambda hz: abs(hz) * 0.0124141 / 2 / 0.3048
    pk = "  ".join(f"{p[0]/1e3:+7.1f}k({fps(p[0]):4.0f}fps) {p[1]:4.1f}dB" for p in peaks)
    print(f"s{num:05d} fs={fs/1e3:.0f}k v0={h.get('v0',0):7.1f}  {pk}\n         top line over time: {pres}")
