#!/usr/bin/env python3
"""Log a BLIPR shooting session from the Teensy's USB serial port (and optionally the ESP32's).

Everything the boards print is saved with a timestamp, every shot is parsed into shots.csv, and a
running string summary (count, average, SD, extreme spread) is printed as you shoot.

    pip install pyserial
    python tools/blipr_log.py                      find the Teensy, arm it, log until Ctrl-C
    python tools/blipr_log.py --live               also turn on the twice-a-second radar readout (noise floor)
    python tools/blipr_log.py --cmd "set save=1" --cmd stat
    python tools/blipr_log.py --minutes 20 --esp   stop after 20 minutes; log the ESP32 too
    python tools/blipr_log.py --list               show the serial ports it can see

Plugging the Teensy into a computer puts it in USB drive mode, which pauses shots. This script sends
'arm' when it starts (unless --no-arm), which turns drive mode off so shots are measured while it logs.

While it runs, any line added to <session>/commands.txt is sent to the Teensy, so another program
(Claude Code, for one) can send commands without stopping the logger, e.g.:
    echo "set snr=10" >> sessions/2026-10-25_1012/commands.txt
Lines starting with "esp:" go to the ESP32 instead (with --esp).

Output: sessions/<date_time>/teensy.log, esp.log, shots.csv, commands.txt
"""
import argparse, csv, datetime, math, os, re, sys, threading, time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial is missing: run  pip install pyserial")

TEENSY_VID = 0x16C0   # PJRC
ESP_VIDS = (0x303A,)  # Espressif USB (the ESP32-C3's own USB port)

SHOT_HEAD = re.compile(r"^(Shot|Recording) #(\d+): (.+?)(?:\s+([\d.]+) fps \(([\d.]+) m/s\))?\s*$")
SHOT_BODY = re.compile(r"points (\d+), span ([\d.]+) ms, SNR ([-\d.]+) dB, scatter ([\d.]+) m/s, accel ([-\d.]+) m/s\^2, "
                       r"tracked ([-\d.]+)-([-\d.]+) m, (\d+) ms to process")
SAVED = re.compile(r"saved as (s\d+\.bin)")


def find_port(vids, want=None):
    if want:
        return want
    for p in list_ports.comports():
        if p.vid in vids:
            return p.device
    return None


class String:
    """Running stats for the shots in this session."""
    def __init__(self):
        self.v = []

    def add(self, fps):
        self.v.append(fps)

    def summary(self):
        n = len(self.v)
        if not n:
            return "no shots yet"
        avg = sum(self.v) / n
        sd = math.sqrt(sum((x - avg) ** 2 for x in self.v) / (n - 1)) if n > 1 else 0.0
        return f"{n} shots, avg {avg:.1f} fps, SD {sd:.1f}, ES {max(self.v) - min(self.v):.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="Teensy serial port (found by itself if not given)")
    ap.add_argument("--esp", nargs="?", const="auto", help="also log the ESP32 (port, or found by itself)")
    ap.add_argument("--cmd", action="append", default=[], help="command to send at the start (repeatable)")
    ap.add_argument("--no-arm", action="store_true", help="don't send 'arm' at the start")
    ap.add_argument("--live", action="store_true", help="turn on the radar readout ('live') for noise checks")
    ap.add_argument("--minutes", type=float, help="stop after this many minutes")
    ap.add_argument("--out", default="sessions", help="folder for session folders (default: sessions)")
    ap.add_argument("--note", default="", help="a note saved with the session (ammo, distance, setup)")
    ap.add_argument("--list", action="store_true", help="list serial ports and exit")
    a = ap.parse_args()

    if a.list:
        for p in list_ports.comports():
            kind = "Teensy" if p.vid == TEENSY_VID else ("ESP32" if p.vid in ESP_VIDS else "")
            print(f"{p.device:24s} {kind:7s} {p.description}")
        return

    tport = find_port((TEENSY_VID,), a.port)
    if not tport:
        sys.exit("No Teensy found. Is it plugged in with a data cable? Try --list, then --port <name>.")
    eport = find_port(ESP_VIDS, None if a.esp in (None, "auto") else a.esp) if a.esp else None
    if a.esp and not eport:
        print("ESP32 not found; logging the Teensy only.")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    sess = os.path.join(a.out, stamp)
    os.makedirs(sess, exist_ok=True)
    cmdfile = os.path.join(sess, "commands.txt")
    open(cmdfile, "a").close()
    if a.note:
        with open(os.path.join(sess, "note.txt"), "w") as f:
            f.write(a.note + "\n")

    tser = serial.Serial(tport, 115200, timeout=0.2)
    eser = serial.Serial(eport, 115200, timeout=0.2) if eport else None
    tlog = open(os.path.join(sess, "teensy.log"), "a", buffering=1)
    elog = open(os.path.join(sess, "esp.log"), "a", buffering=1) if eser else None
    shots_path = os.path.join(sess, "shots.csv")
    new = not os.path.exists(shots_path)
    shots_f = open(shots_path, "a", newline="", buffering=1)
    shots = csv.writer(shots_f)
    if new:
        shots.writerow(["time", "kind", "shot", "result", "fps", "mps", "points", "span_ms", "snr_db", "scatter_mps",
                        "accel", "from_m", "to_m", "process_ms", "file"])
    stop = threading.Event()
    lock = threading.Lock()
    string = String()

    def send(ser, log, text):
        with lock:
            ser.write((text.strip() + "\n").encode())
            log.write(f"{datetime.datetime.now().isoformat(timespec='milliseconds')} >> {text.strip()}\n")
        print(f">> {text.strip()}")

    def reader(ser, log, name, parse):
        cur = None
        buf = b""
        while not stop.is_set():
            try:
                chunk = ser.read(512)
            except serial.SerialException as e:
                print(f"[{name}] port closed: {e}")
                stop.set()
                return
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode(errors="replace").rstrip("\r")
                now = datetime.datetime.now().isoformat(timespec="milliseconds")
                log.write(f"{now} {line}\n")
                if not parse:
                    print(f"[{name}] {line}")
                    continue
                m = SAVED.search(line)
                if m and pending[0] is not None:
                    pending[0]["file"] = m.group(1)
                    flush_pending()
                    print(line)
                    continue
                flush_pending()
                m = SHOT_HEAD.match(line.strip())
                if m:
                    cur = {"time": now, "kind": m.group(1).lower(), "shot": m.group(2), "result": m.group(3).strip(),
                           "fps": m.group(4) or "", "mps": m.group(5) or ""}
                    print(line)
                    continue
                m = SHOT_BODY.search(line)
                if m and cur is not None:
                    cur.update(points=m.group(1), span=m.group(2), snr=m.group(3), scatter=m.group(4), accel=m.group(5),
                               d0=m.group(6), d1=m.group(7), proc=m.group(8), file="")
                    print(line)
                    pending[0] = cur          # a "saved as" line may follow with the recording's file name
                    pending_t[0] = time.time()
                    cur = None
                    continue
                print(f"[{name}] {line}" if name != "teensy" else line)
            if pending[0] is not None and time.time() - pending_t[0] > 1.0:
                flush_pending()

    pending, pending_t = [None], [0.0]

    def flush_pending():
        if pending[0] is not None:
            write_shot(pending[0])
            pending[0] = None

    def write_shot(s):
        shots.writerow([s["time"], s["kind"], s["shot"], s["result"], s["fps"], s["mps"], s["points"], s["span"], s["snr"],
                        s["scatter"], s["accel"], s["d0"], s["d1"], s["proc"], s.get("file", "")])
        if s["kind"] == "shot" and s["fps"]:
            string.add(float(s["fps"]))
            print(f"   string: {string.summary()}")

    def watch_commands():
        pos = os.path.getsize(cmdfile)
        while not stop.is_set():
            time.sleep(0.3)
            size = os.path.getsize(cmdfile)
            if size < pos:
                pos = 0
            if size > pos:
                with open(cmdfile) as f:
                    f.seek(pos)
                    lines = f.read().splitlines()
                    pos = f.tell()
                for ln in lines:
                    if not ln.strip():
                        continue
                    if ln.lower().startswith("esp:"):
                        if eser:
                            send(eser, elog, ln[4:])
                    else:
                        send(tser, tlog, ln)

    threads = [threading.Thread(target=reader, args=(tser, tlog, "teensy", True), daemon=True),
               threading.Thread(target=watch_commands, daemon=True)]
    if eser:
        threads.append(threading.Thread(target=reader, args=(eser, elog, "esp", False), daemon=True))
    for t in threads:
        t.start()

    print(f"Logging {tport}{' and ' + eport if eser else ''} to {sess}/  (Ctrl-C to stop)")
    time.sleep(0.5)
    send(tser, tlog, f"time {int(time.time())}")
    if not a.no_arm:
        send(tser, tlog, "arm")
    for c in a.cmd:
        send(tser, tlog, c)
    send(tser, tlog, "stat")
    if a.live:
        send(tser, tlog, "live")

    end = time.time() + a.minutes * 60 if a.minutes else None
    try:
        while not stop.is_set() and (end is None or time.time() < end):
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    if a.live and not stop.is_set():
        send(tser, tlog, "live")   # it's a toggle: turn the readout back off
    stop.set()
    time.sleep(0.4)
    flush_pending()
    print(f"\nSession {sess}: {string.summary()}")
    with open(os.path.join(sess, "summary.txt"), "w") as f:
        f.write(string.summary() + "\n")


if __name__ == "__main__":
    main()
