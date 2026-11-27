Range Book BLIPR main board v1.2 - getting an assembled-board (PCBA) quote from PCBWay

WHAT'S IN THIS FOLDER
  RBBLIPR_PCB_v1.2_gerbers.zip         the board itself (the same files as the bare-board order)
  RBBLIPR_v1.2_PCBA_BOM.xlsx           parts list: what goes where, with manufacturer part numbers
  RBBLIPR_v1.2_PCBA_positions.csv      where each part sits (mm from the board's front-left corner, top side)
  RBBLIPR_v1.2_assembly_drawing.png    picture of the board with every part's place, value and polarity

WHAT THEY FIT, WHAT YOU FIT
  They fit (61 parts per board, all through-hole, top side): all 24 resistors, all 25 capacitors, L1, L2, D1, U3,
  the two DIP-8 sockets with the MCP6022 op-amps pushed into them, and the female socket strips for the
  Teensy (2 x 24) and the ESP32 (2 x 8).
  Left empty on purpose (DNP): J1-J5, the wire headers. You solder wires or headers there, as the build
  guide says (J2, the radar, gets wires soldered straight in, so nothing there can be plugged in backwards).
  Off the board: R25 (at the battery holder), the Teensy, the ESP32 and all wiring.

STEP BY STEP ON PCBWAY
  1. pcbway.com > PCB Assembly (or Quote Now > PCB Assembly).
  2. Assembly type: Turnkey (PCBWay buys the parts).
  3. Fill in the quote form:
       Quantity (pcs) ....................... 5 (or however many you want; see "PRICE" below)
       Number of unique parts ............... 22
       Number of SMT parts .................. 0
       Number of BGA/QFP parts .............. 0
       Number of through-hole parts ......... 61
       Sensitive components ................. No
       Alternatives/substitutes allowed ..... Yes (the BOM says which parts must not be swapped)
       Board type ........................... Single pieces
       Assembly side(s) ..................... Top side
       Detailed assembly information:
         "All through-hole, top side only. Do not fit J1-J5 (DNP). U1/U2: solder the DIP-8 sockets, then push
          the MCP6022 op-amps in with pin 1 at the square pad (do not solder the op-amps). U4/U5: solder the
          female header strips straight and square (rows 15.24 mm apart); do not fit any module. Polarised
          parts (C3, C4, C7, C10, D1, U3) as marked on the silkscreen and the assembly drawing."
  4. Add the PCB itself: same settings as the bare-board order -
       2 layers, FR-4, 1.6 mm, 6/6 mil, 0.3 mm min hole, any solder mask colour, white silkscreen,
       HASL lead-free, 1 oz copper. Upload RBBLIPR_PCB_v1.2_gerbers.zip.
  5. Upload RBBLIPR_v1.2_PCBA_BOM.xlsx as the BOM and RBBLIPR_v1.2_PCBA_positions.csv as the centroid /
     pick-and-place file (for through-hole parts they mostly go by the drawing, but they ask for it).
     Attach RBBLIPR_v1.2_assembly_drawing.png wherever it asks for other files or an assembly drawing.
  6. Submit. The online price is a first estimate; PCBWay's engineers check the files and the parts list
     (usually within a day or two), price the parts, and email you a final quote to accept or not.
     Nothing is charged until you pay that.

PRICE
  Most of the cost is fixed (setup and parts handling), so it barely changes between a few boards and a
  dozen. Asking for two quotes, 5 and 20 boards, shows what a batch for other builders would cost per board.
  The parts themselves are about $8-20 a board at their prices.

IF THEY ASK
  - A part is out of stock: any equivalent with the same value, the same lead spacing (it's in the BOM) and
    an equal or higher voltage is fine, except U1/U2 (MCP6022-E/P) and U3 (MCP1700-3302E/TO): those
    stay exactly as listed.
  - Through-hole parts are soldered by hand or wave; either is fine.
  - The DIP sockets' notch: as printed on the board (pointing right).
