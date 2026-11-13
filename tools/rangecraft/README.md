# Rangecraft over Bluetooth

Goal: Range Book reads shots from Sean's Rangecraft chronograph live, the same way it reads BLIPR
(Chrome on Android, Bluefy on iPhone). First we learn how the Rangecraft talks to its own app.

`btsnoop_dump.py` reads an Android Bluetooth log (or a whole bug report .zip) and prints every
Bluetooth message in plain lines. With `--find`, it looks for velocities you saw in the app and says
which bytes hold them. No Wireshark needed.

## What we know (nRF Connect, Nov 12)

- Name `AthlonVPR1_020418` (address FB:7D:C4:EB:9A:A0), maker "Athlon", model "Athlon_V3".
  Zephyr / Nordic nRF chip. It bonded with the phone when notifications were turned on.
- **Data service** `6e40ff01-b5a3-f393-e0a9-4174686c6f6e`, a Nordic-UART-style serial pipe (the
  last part is "Athlon" in ASCII):
  - `6e40ff02-…` WRITE / WRITE NO RESPONSE: phone -> chronograph (commands)
  - `6e40ff03-…` NOTIFY: chronograph -> phone (shots, replies)
- Battery `0x180F` / `0x2A19` (notify, %), Device Info `0x180A`.
- **Don't write to the SMP service** `8d53dc1d-…` / `da2e7828-…`: that's the firmware-update port.
- Web Bluetooth needs: `filters: [{namePrefix: "AthlonVPR"}]`,
  `optionalServices: ["6e40ff01-b5a3-f393-e0a9-4174686c6f6e", "battery_service"]`.
- Still unknown: the live shot message (fire with the snoop log on).

## Protocol so far (snoop log, Nov 12 20:18-20:29, no shots fired)

Capture: `recordings/rangecraft/bugreport-a25xtfn-…-2026-11-12-20-41-22.zip` (log at
`FS/data/log/bt/btsnoop_hci.log` on this Samsung A25), notes in `rangecraft_debug_times.txt`.

Every message on ff02/ff03 is `[type] [length] [code] [data…]`, length = code + data bytes.
Types: `80` = a command (phone -> unit) or an event the unit sends by itself; `90` = the unit's reply;
`91` / `92` / `93` = a long reply in pieces (first / middle / last). Times and dates are **BCD**
(`26 11 12 20 18 30` = 2026-11-12 20:18:30).

What the Athlon app does on connect (Range Book should copy it):
1. Notifications on for ff03 (handle 29) and battery (handle 19); Service Changed indications on.
2. `80 07 66 YY MM DD hh mm ss`: set the clock. Reply `90 04 66 4F 4B 00` ("OK").
3. `80 01 65`: firmware version. Reply `90 0a 65` + text `1.40.87.1`.
4. `80 01 81`: unknown (status?). Reply `90 02 81 00`.
   (The app sends 65 and 81 twice.)

`80 01 77` = **list of sessions on the unit** (what "Sync data" sends). Reply is 3 pieces (91/92/93),
mostly zero padding. Entries are 11 bytes: 6 BCD date-time + 3 unknown bytes + bullet weight
(little-endian, grains x10: `90 01` = 40.0 gr, `be 05` = 147.0 gr). Nov 12 list: 7 sessions
(Oct 11 x3 at 147 gr, Oct 17 x3, Nov 11 20:34:07 at 40 gr). The shots themselves were **not**
sent: the app showed them from its own (cloud) copy. The command to download a session's shots is unknown.

Events the unit sends by itself:
- `80 0d 21` + `08` + BCD start time + `03 26 01` + weight `90 01`: a session started (20:27:52).
- `80 0b 24` + `08` + the same start time + `03 26 01`: that session ended (20:29:04).
- Expected tomorrow: a shot event between those two (probably code 22 or 23).

Changing fps <-> m/s in the app sent nothing to the unit (display only). The battery
characteristic notifies about once a second.

## Tonight (no shooting): Android phone

**A. Map the chronograph (nRF Connect, ~10 min)**
1. Install **nRF Connect for Mobile** (Nordic, free). Close the Rangecraft app completely.
2. Rangecraft on. In nRF Connect: Scan, find it (write down its name), Connect.
3. Screenshot every service with its characteristics expanded (the long UUIDs and the
   READ / WRITE / NOTIFY labels).
4. Tap the "subscribe" arrows on everything marked NOTIFY or INDICATE. Wait 30 s, press its buttons,
   change a setting on the unit. Screenshot anything that shows up.
5. Disconnect.

**B. Record the Rangecraft app (~15 min)**
1. Settings → About phone → tap Build number 7 times (turns on Developer options).
2. Settings → System → Developer options → **Bluetooth HCI snoop log → Enabled** (*not* "Filtered":
   filtered cuts the data out).
3. Turn Bluetooth **off and on** (logging starts from here).
4. Open the Rangecraft app, connect, and do everything you can without firing:
   - download or open any shots stored on the unit (the Nov 11 .22 string, if it's still there),
     and **write down every velocity the app shows, in order**
   - change units fps -> m/s -> fps, and any other setting it has
   - start and end a session or string, if the app has that
   - disconnect from the app
5. Note the time of each step (rough is fine).
6. Developer options → **Take bug report** → Full report. When it's ready (a few minutes), tap the
   notification and share the .zip to Google Drive or email it to yourself, then save it on the Mac
   into `recordings/rangecraft/` in this repo. (It holds phone logs, so don't post it anywhere.)
7. Leave the snoop log on for tomorrow, or turn it off: either is fine.

Then Claude runs:

```bash
python3 tools/rangecraft/btsnoop_dump.py recordings/rangecraft/<bugreport>.zip --find <velocities>
```

## Tomorrow at the range

Same as B, with the snoop log on: connect the app, fire a string, write down each velocity the app
shows, take a bug report. That shows the live "new shot" message and confirms the byte layout.

## What we're looking for

- The service and characteristic UUIDs (Range Book needs them to ask the browser for permission).
- Whether the app has to **write** something first (a handshake or "start") before shots arrive.
  If so, Range Book sends the same bytes.
- Which bytes hold the velocity, and how (fps or m/s, whole number or x10, byte order).

Then a small test page here in `tools/rangecraft/` connects to the Rangecraft and shows shots live
(Chrome on the Mac via localhost, or a phone over https). All Rangecraft testing stays in this repo;
Range Book (the `chrono` branch only) gets it later, and only when Sean says so.
