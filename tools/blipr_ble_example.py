#!/usr/bin/env python3
"""Minimal BLIPR Bluetooth client: finds BLIPR, prints each shot and its status, and can send a command.

A starting point for your own app or script. The interface is described in firmware/PROTOCOL.md.

    pip install bleak
    python blipr_ble_example.py                 # print shots until Ctrl+C
    python blipr_ble_example.py --cmd TEST      # also send a command (TEST sends a made-up shot)

Only one app can be connected to BLIPR at a time: close Range Book (or disconnect it) first.
"""
import argparse
import asyncio
import json
import time

from bleak import BleakClient, BleakScanner

SERVICE = "239d0001-5192-4fb5-95ad-180af63137b3"
SHOT = "239d0002-5192-4fb5-95ad-180af63137b3"
STATUS = "239d0003-5192-4fb5-95ad-180af63137b3"
COMMAND = "239d0004-5192-4fb5-95ad-180af63137b3"
CONFIG = "239d0005-5192-4fb5-95ad-180af63137b3"


def parse(data: bytearray):
    """Values are UTF-8 JSON. A long one can arrive cut short in a notification: then read it instead."""
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


async def main(cmd: str | None, last_shot: int):
    print("Looking for BLIPR...")
    dev = await BleakScanner.find_device_by_filter(
        lambda d, adv: SERVICE in [u.lower() for u in adv.service_uuids] or (d.name or "").startswith("RB BLIPR"),
        timeout=15)
    if dev is None:
        print("BLIPR not found. Is it switched on, and not connected to another app?")
        return
    print(f"Found {dev.name} ({dev.address}), connecting...")

    seen = set()   # shots are unique by (boot id b, shot number n)

    async with BleakClient(dev) as client:
        def on_shot(_, data):
            s = parse(data)
            if s is None or (s.get("b"), s.get("n")) in seen:
                return
            seen.add((s.get("b"), s.get("n")))
            tag = " (test)" if s.get("test") else ""
            if s.get("ok"):
                print(f"Shot {s['n']}: {s['v']:.1f} fps{tag}")
            else:
                print(f"Shot {s['n']}: no read ({s.get('why', '?')}){tag}")

        def on_status(_, data):
            st = parse(data)
            if st:
                print(f"  status: battery {st.get('bat')}%, {'armed' if st.get('arm') else 'not armed'}, "
                      f"firmware Teensy {st.get('fw')} / ESP32 {st.get('efw')}", end="\r")

        await client.start_notify(SHOT, on_shot)
        await client.start_notify(STATUS, on_status)

        async def send(text: str):
            await client.write_gatt_char(COMMAND, text.encode("utf-8"), response=True)

        await send(f"TIME {int(time.time())}")   # so stored shots get the right time
        await send(f"SYNC {last_shot}")          # shots fired while nothing was connected
        config = parse(await client.read_gatt_char(CONFIG))   # a read always returns the whole value
        if config:
            print(f"Speed window {config.get('vmin')}-{config.get('vmax')} fps")
        if cmd:
            await send(cmd)
            print(f"Sent: {cmd}")

        print("Listening for shots (Ctrl+C to stop)")
        while client.is_connected:
            await asyncio.sleep(1)
        print("\nDisconnected")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", help='a command to send after connecting, e.g. "TEST" or "SET vmin=950 vmax=1200"')
    ap.add_argument("--since", type=int, default=0, help="re-send stored shots newer than this shot number")
    args = ap.parse_args()
    try:
        asyncio.run(main(args.cmd, args.since))
    except KeyboardInterrupt:
        pass
