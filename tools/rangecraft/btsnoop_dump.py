#!/usr/bin/env python3
"""Read an Android Bluetooth HCI snoop log and print the BLE (GATT/ATT) traffic in plain lines.

Used to work out how the Rangecraft chronograph talks to its phone app, so Range Book can read it too.
No Wireshark needed. Works on:
  - btsnoop_hci.log (from the phone, or pulled with adb)
  - an Android bug report .zip (it finds the snoop log inside)

  python3 btsnoop_dump.py bugreport.zip                 # every GATT packet, with the UUID of each handle
  python3 btsnoop_dump.py log --only notify             # just what the chronograph sends by itself
  python3 btsnoop_dump.py log --find 1067 1071 1063     # which bytes hold these velocities (fps or m/s)
  python3 btsnoop_dump.py log --addr AA:BB              # only one device (the end of its address is enough)

Lines show: time, direction (phone > dev / dev > phone), ATT operation, handle and its UUID, hex, and text.
"""
import argparse
import struct
import sys
import zipfile
from datetime import datetime, timedelta

# ---------- reading the file ----------

EPOCH_DELTA = 0x00DCDDB30F2F8000  # btsnoop counts microseconds from year 0; this moves it to 1970


def load(path):
    """Return the raw bytes of a btsnoop log, from a log file or a bug report zip."""
    if zipfile.is_zipfile(path):
        z = zipfile.ZipFile(path)
        names = [n for n in z.namelist() if "btsnoop" in n.lower() and not n.endswith("/")]
        if not names:
            sys.exit("No btsnoop log in this zip. Is 'Bluetooth HCI snoop log' set to Enabled (not Filtered)?")
        # the current log first, then the older ".last" one
        names.sort(key=lambda n: (n.endswith(".last"), -z.getinfo(n).file_size))
        print(f"# using {names[0]} from the zip" + (f" (also there: {', '.join(names[1:])})" if names[1:] else ""))
        data = z.read(names[0])
        # some phones nest the log in another zip/cfa wrapper; most give it plain
        if zipfile.is_zipfile(__import__("io").BytesIO(data)):
            return load_bytes_zip(data)
        return data
    with open(path, "rb") as f:
        return f.read()


def load_bytes_zip(data):
    import io
    z = zipfile.ZipFile(io.BytesIO(data))
    n = [x for x in z.namelist() if "btsnoop" in x.lower()][0]
    return z.read(n)


def records(data):
    """Yield (time, received, h4_type, payload) for every packet."""
    if data[:8] != b"btsnoop\0":
        sys.exit("This isn't a btsnoop log (wrong header).")
    _ver, link = struct.unpack(">II", data[8:16])
    off = 16
    while off + 24 <= len(data):
        orig, incl, flags, _drops, ts = struct.unpack(">IIIIq", data[off:off + 24])
        off += 24
        pkt = data[off:off + incl]
        off += incl
        if len(pkt) < incl:
            break
        t = datetime(1970, 1, 1) + timedelta(microseconds=ts - EPOCH_DELTA) if ts > EPOCH_DELTA else None  # phone local time
        received = bool(flags & 1)
        if link == 1002:  # H4: first byte says what it is
            if not pkt:
                continue
            yield t, received, pkt[0], pkt[1:]
        elif link == 1001:  # unencapsulated: bit 1 = command/event, else data
            yield t, received, (0x04 if received else 0x01) if flags & 2 else 0x02, pkt
        else:
            sys.exit(f"Unknown btsnoop link type {link}.")


# ---------- HCI events (to learn device addresses) and ACL reassembly ----------

def addr_str(b):
    return ":".join(f"{x:02X}" for x in reversed(b))


def connections(data):
    """Map ACL handle -> device address from LE Connection Complete events."""
    out = {}
    for _t, _rx, typ, p in records(data):
        if typ != 0x04 or len(p) < 2:
            continue
        ev = p[0]
        if ev == 0x3E and len(p) > 3:  # LE meta
            sub = p[2]
            if sub in (0x01, 0x0A) and p[3] == 0:  # (enhanced) connection complete, success
                h = struct.unpack("<H", p[4:6])[0] & 0x0FFF
                out[h] = addr_str(p[8:14])
        elif ev == 0x03 and len(p) > 11 and p[2] == 0:  # classic connection complete
            h = struct.unpack("<H", p[3:5])[0] & 0x0FFF
            out[h] = addr_str(p[5:11])
    return out


def att_packets(data):
    """Yield (time, received, acl_handle, att_bytes) with L2CAP fragments joined."""
    partial = {}
    for t, rx, typ, p in records(data):
        if typ != 0x02 or len(p) < 4:
            continue
        hf, ln = struct.unpack("<HH", p[:4])
        h, pb = hf & 0x0FFF, (hf >> 12) & 3
        body = p[4:4 + ln]
        key = (h, rx)
        if pb == 1:  # continuation
            if key not in partial:
                continue
            partial[key][2] += body
        else:
            partial[key] = [t, rx, bytearray(body)]
        t0, rx0, buf = partial[key]
        if len(buf) < 4:
            continue
        l2len, cid = struct.unpack("<HH", buf[:4])
        if len(buf) - 4 < l2len:
            continue
        del partial[key]
        if cid == 0x0004:
            yield t0, rx0, h, bytes(buf[4:4 + l2len])


# ---------- ATT ----------

OPS = {
    0x01: "error", 0x02: "mtu req", 0x03: "mtu rsp", 0x04: "find info req", 0x05: "find info rsp",
    0x06: "find by type req", 0x07: "find by type rsp", 0x08: "read by type req", 0x09: "read by type rsp",
    0x0A: "read req", 0x0B: "read rsp", 0x0C: "read blob req", 0x0D: "read blob rsp",
    0x10: "read group req", 0x11: "read group rsp", 0x12: "write req", 0x13: "write rsp",
    0x16: "prep write req", 0x17: "prep write rsp", 0x18: "exec write req", 0x19: "exec write rsp",
    0x1B: "notify", 0x1D: "indicate", 0x1E: "confirm", 0x52: "write cmd", 0xD2: "signed write",
}
SHORT = {  # a few well-known 16-bit UUIDs
    0x1800: "GAP", 0x1801: "GATT", 0x180A: "Device Info", 0x180F: "Battery", 0x2902: "CCCD (notify on/off)",
    0x2901: "description", 0x2A00: "device name", 0x2A19: "battery level", 0x2A29: "maker", 0x2A24: "model",
    0x2A26: "firmware", 0x2A27: "hardware rev", 0x2A28: "software rev", 0x2A25: "serial", 0x2A05: "service changed",
    0x2800: "primary service", 0x2803: "characteristic",
}
PROPS = [(0x02, "read"), (0x04, "write-no-rsp"), (0x08, "write"), (0x10, "notify"), (0x20, "indicate")]


def uuid_str(b):
    if len(b) == 2:
        u = struct.unpack("<H", b)[0]
        return f"0x{u:04X}" + (f" {SHORT[u]}" if u in SHORT else "")
    h = b[::-1].hex()
    s = f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"
    if s.endswith("-0000-1000-8000-00805f9b34fb"):
        return uuid_str(bytes.fromhex(s[4:8])[::-1])
    return s


class Gatt:
    """What we learn about each device's GATT table from the discovery packets in the log."""

    def __init__(self):
        self.names = {}     # (acl, handle) -> label
        self.services = {}  # acl -> [(start, end, uuid)]
        self.chars = {}     # acl -> [(value_handle, props, uuid)]
        self.pending = {}   # acl -> last request (opcode, type uuid)

    def label(self, acl, h):
        n = self.names.get((acl, h))
        if n:
            return n
        # a CCCD sits right after its characteristic's value
        prev = self.names.get((acl, h - 1))
        return f"(next to {prev})" if prev else "?"

    def learn(self, acl, rx, a):
        op = a[0]
        if not rx and op in (0x08, 0x10) and len(a) >= 7:
            self.pending[acl] = (op, a[5:])
        elif rx and op == 0x11 and len(a) > 2:  # services
            n = a[1]
            for i in range(2, len(a) - n + 1, n):
                s, e = struct.unpack("<HH", a[i:i + 4])
                u = uuid_str(a[i + 4:i + n])
                self.services.setdefault(acl, []).append((s, e, u))
                self.names[(acl, s)] = "service " + u
        elif rx and op == 0x09 and len(a) > 2:
            req = self.pending.get(acl)
            n = a[1]
            if req and req[1] == b"\x03\x28":  # characteristic declarations
                for i in range(2, len(a) - n + 1, n):
                    _decl, props, vh = struct.unpack("<HBH", a[i:i + 5])
                    u = uuid_str(a[i + 5:i + n])
                    self.chars.setdefault(acl, []).append((vh, props, u))
                    self.names[(acl, vh)] = u
        elif rx and op == 0x05 and len(a) > 2:  # descriptors
            fmt = a[1]
            n = 4 if fmt == 1 else 18
            for i in range(2, len(a) - n + 1, n):
                h = struct.unpack("<H", a[i:i + 2])[0]
                u = uuid_str(a[i + 2:i + n])
                if (acl, h) not in self.names or u.startswith("0x29"):
                    self.names.setdefault((acl, h), u)

    def table(self, acl):
        lines = []
        for s, e, u in sorted(self.services.get(acl, [])):
            lines.append(f"  service {u}  (handles {s}-{e})")
            for vh, props, cu in sorted(self.chars.get(acl, [])):
                if s <= vh <= e:
                    p = ",".join(n for b, n in PROPS if props & b)
                    lines.append(f"    handle {vh:3d}  {cu}  [{p}]")
        return "\n".join(lines)


def show(b, n=48):
    h = b.hex(" ")
    txt = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    if len(b) > n:
        h = b[:n].hex(" ") + " ..."
        txt = txt[:n] + "..."
    return f"{h}  |{txt}|"


def describe(gatt, acl, rx, a):
    op = a[0]
    name = OPS.get(op, f"op 0x{op:02X}")
    who = "dev > phone" if rx else "phone > dev"
    handle = None
    val = b""
    if op in (0x1B, 0x1D, 0x12, 0x52, 0x0A, 0x0C, 0x16) and len(a) >= 3:
        handle = struct.unpack("<H", a[1:3])[0]
        val = a[3:] if op != 0x16 else a[5:]
    elif op in (0x0B, 0x0D):
        val = a[1:]
    elif op == 0x01 and len(a) >= 5:
        handle = struct.unpack("<H", a[2:4])[0]
        val = a[1:]
        name = f"error (for {OPS.get(a[1], hex(a[1]))}, code 0x{a[4]:02X})"
    elif op in (0x02, 0x03) and len(a) >= 3:
        val = a[1:]
        name += f" {struct.unpack('<H', a[1:3])[0]}"
    else:
        val = a[1:]
    hs = f"h{handle:<3d} {gatt.label(acl, handle)}" if handle is not None else ""
    if handle is not None and op in (0x12, 0x52) and gatt.label(acl, handle).startswith("0x2902") or \
            (handle is not None and op == 0x12 and val in (b"\x01\x00", b"\x02\x00", b"\x00\x00") and "CCCD" in gatt.label(acl, handle)):
        hs += {b"\x01\x00": "  -> notify ON", b"\x02\x00": "  -> indicate ON", b"\x00\x00": "  -> OFF"}.get(val, "")
    return who, name, handle, hs, val


# ---------- finding known velocities in the bytes ----------

def candidates(b):
    """Every number these bytes could hold at each offset: (offset, encoding, value)."""
    out = []
    for i in range(len(b)):
        for size, fmts in ((2, ("<H", ">H", "<h")), (4, ("<I", ">I", "<f", ">f")), (8, ("<d",))):
            if i + size > len(b):
                continue
            for f in fmts:
                v = struct.unpack(f, b[i:i + size])[0]
                if v != v or abs(v) > 1e9:
                    continue
                out.append((i, f, v))
    # numbers written as text, e.g. "1067.4"
    import re
    s = b.decode("latin-1")
    for m in re.finditer(r"\d{2,5}(?:\.\d+)?", s):
        out.append((m.start(), "text", float(m.group())))
    return out


SCALES = [(1, False, "fps"), (10, False, "fps x10"), (100, False, "fps x100"),
          (1, True, "m/s"), (10, True, "m/s x10"), (100, True, "m/s x100"), (1000, True, "m/s x1000")]


def find(payloads, targets, tol):
    """payloads: list of (index, bytes). Look for each target velocity (fps) in each payload."""
    hits = {}
    for idx, b in payloads:
        for off, f, v in candidates(b):
            for div, mps, sname in SCALES:
                fps = v / div / 0.3048 if mps else v / div
                for t in targets:
                    if abs(fps - t) <= tol:
                        hits.setdefault((off, f, sname), []).append((idx, t, round(fps, 2)))
    return hits


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="btsnoop_hci.log or an Android bug report .zip")
    ap.add_argument("--addr", help="only this device (any part of its address)")
    ap.add_argument("--only", choices=["notify", "write", "read"], help="only notifications, only writes, or only reads")
    ap.add_argument("--find", nargs="+", type=float, metavar="FPS",
                    help="velocities the app showed (fps), in order; reports where in the packets they sit")
    ap.add_argument("--tol", type=float, default=0.6, help="how close a match must be, fps (default 0.6)")
    args = ap.parse_args()

    data = load(args.log)
    conns = connections(data)
    gatt = Gatt()
    rows = []
    for t, rx, acl, a in att_packets(data):
        if not a:
            continue
        addr = conns.get(acl, f"link {acl}")
        if args.addr and args.addr.upper() not in addr.upper():
            continue
        gatt.learn(acl, rx, a)
        rows.append((t, rx, acl, addr, a))

    if not rows:
        sys.exit("No GATT traffic found" + (" for that address" if args.addr else "") +
                 ". Check the snoop log was set to Enabled (not Filtered) before turning Bluetooth on.")

    print("# devices seen:", ", ".join(sorted(set(r[3] for r in rows))))
    for acl in sorted(set(r[2] for r in rows)):
        tab = gatt.table(acl)
        print(f"\n# GATT table for {conns.get(acl, acl)}:")
        print(tab or "  (no discovery in this log: the phone had it cached. Forget the device or toggle Bluetooth, then capture again.)")
    print()

    payloads = []
    for t, rx, acl, addr, a in rows:
        who, name, handle, hs, val = describe(gatt, acl, rx, a)
        if args.only == "notify" and a[0] not in (0x1B, 0x1D):
            continue
        if args.only == "write" and a[0] not in (0x12, 0x52, 0x16):
            continue
        if args.only == "read" and a[0] not in (0x0A, 0x0B, 0x0C, 0x0D):
            continue
        ts = t.strftime("%H:%M:%S.%f")[:-3] if t else "--"
        print(f"{ts}  {addr[-8:]}  {who}  {name:<15} {hs}")
        if val:
            print(f"{'':28}{show(val)}")
        if a[0] in (0x1B, 0x1D, 0x0B, 0x0D):
            payloads.append((len(payloads), (ts, hs), val))

    if args.find:
        print(f"\n# looking for {args.find} (fps, +/-{args.tol}) in {len(payloads)} packets from the device")
        hits = find([(i, v) for i, _m, v in payloads], args.find, args.tol)
        meta = {i: m for i, m, _v in payloads}
        ranked = sorted(hits.items(), key=lambda kv: -len(set(t for _i, t, _f in kv[1])))
        if not ranked:
            print("  nothing matched. Try --tol 2, or check the app was showing fps.")
        for (off, f, sname), hl in ranked[:8]:
            found = sorted(set(t for _i, t, _f in hl))
            print(f"  byte {off}, {f} as {sname}: matches {len(found)}/{len(args.find)} -> " +
                  ", ".join(f"{fps} ({meta[i][0]} {meta[i][1].split()[0] if meta[i][1] else ''})" for i, _t, fps in hl[:6]))


if __name__ == "__main__":
    main()
