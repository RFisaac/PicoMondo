# PCB

File: `picomondo.kicad_pcb`, created by `tools/make_pcb.py` (run it with KiCad's Python, see below). It holds all
289 footprints with their nets and schematic paths, so KiCad's **Update PCB from Schematic (F8)** updates them in place
rather than duplicating. **Do not re-run `make_pcb.py --force` once you have placed parts**: it rebuilds the board from scratch.

## What is already done

- **Outline:** 120 x 90 mm, 3 mm corner radius, with the EdgeLock notches cut into the edge (they come from the footprints).
- **EdgeLock connectors:** J1-J4 on the top edge, J9, J6 and J5 on the bottom edge, spaced clear of the corner holes. The footprint
  carries the board notches and latch windows; the outline is joined to them. The bottom edge has about 35 mm free to its right
  for J7/J8 or other connectors.
- **Mounting:** four M3 holes, 4 mm in from each corner. (No Pi HAT spacing: there is no HAT header.)
- **Arduino Uno R3 and Pico sockets** on their exact patterns (the Uno positions are from KiCad's `Module:Arduino_UNO_R3`
  footprint: header rows 48.26 mm apart), centred on the board and **grouped** ("Arduino + Pico sockets") so you can move them
  as one. The Pico sockets run along the same axis between the two Uno rows. Pin 1 of each header is at the D0 / A0 / NC / D8 end.
- **Everything else** is laid out in labelled rows to the right of the board, grouped by schematic sheet.
- **GND plane** zone on In1.Cu (layer 2). It connects through-hole pads automatically; SMD ground pads need vias.

## Stackup (JLC04161H-3313, 1.6 mm, ENIG)

| Layer | Use (suggested) | Thickness |
|-------|-----------------|-----------|
| F.Cu | components, signals | 35 um |
| prepreg 3313 | | 0.0994 mm, er 4.05 |
| In1.Cu | **solid GND** (zone drawn) | 15 um |
| core | | 1.265 mm, er 4.6 |
| In2.Cu | power pours (+3V3, +5V, V_INPUT), some signals | 15 um |
| prepreg 3313 | | 0.0994 mm |
| B.Cu | signals, GND fill | 35 um |

The inner layers are 0.5 oz. Do not rely on them for the 5 A paths: carry V_INPUT, +5V, J7/J8 and the SW nodes on the outer
layers with wide copper or pours.

## Design rules (`project_settings.py` writes them into `picomondo.kicad_pro`)

JLCPCB 4-layer capability: tracks and spacing from 0.09 mm, vias 0.45 mm pad / 0.2 mm drill, copper at least 0.3 mm from
the board edge. Used here: minimum track and clearance 0.127 mm (5 mil), minimum via 0.45 / 0.2.

| Net class | Track | Via (pad / drill) | Nets |
|-----------|-------|-------------------|------|
| Default | 0.2 mm | 0.6 / 0.3 | everything else |
| Power | 0.5 mm | 0.8 / 0.4 | +3V3, +3V3_AUX, +1V1, WS2812 supply |
| PowerHigh | 1.0 mm | 0.8 / 0.4 | V_INPUT, +5V, +5V_SW, VBUS, converter output and SW nodes, V_RAW, input nets, J7/J8 output chain |
| USB | 0.15 mm, pair gap 0.16 mm | 0.6 / 0.3 | USB_D+, USB_D- and the nets through the ESD array and resistors |

Wide classes are routing defaults only: fine-pitch ICs (TPS55288, INA226, the RP2350) must neck down at their pins. For
currents of 3-5 A use pours rather than 1 mm tracks (a 1 oz outer track of 1 mm carries only about 2.5 A at a 10 C rise).

### USB geometry for this stackup

90 ohm differential, microstrip on F.Cu over the In1 ground plane, h = 0.0994 mm, er = 4.05, copper 35 um:
single-ended Z0 = 87 / sqrt(er + 1.41) x ln(5.98 h / (0.8 w + t)) gives 50 ohm at **w = 0.15 mm**; Zdiff = 2 Z0 (1 - 0.48 e^(-0.96 s/h))
gives 90 ohm at **s = 0.16 mm**. These approximations are good to about 10%; check with JLCPCB's impedance calculator before ordering.
(The old spec's 0.8 mm / 0.15 mm was Raspberry Pi's figure for a 1 mm two-layer board and does not apply.) Keep the pair on one layer over
unbroken ground, length-matched, no vias if possible; USB full speed is forgiving.

## Things to check before ordering

1. **EdgeLock notches:** the narrow notches are 0.85 mm wide. JLCPCB's stated minimum routed slot is 1.0 mm. Run the Gerbers through their DFM check early.
2. **Impedance:** confirm the USB numbers with JLCPCB's tool (above).
3. **EdgeLock 3D models** are attached (`lib/3dmodels/edgelock`, rotated -90 degrees about X): checked in a side render, housing straddles the board correctly.
4. **Tall parts** (inductor, any electrolytic) collide with an Arduino shield above the header area.
5. **Layout rules from the datasheets** are in notes on each schematic sheet (RP2350 regulator, crystal, buck-boost loop, USB-C).

## Tools

| Script | Purpose |
|--------|---------|
| `tools/make_pcb.py` | Create the board once. Run: `"C:\Program Files\KiCad\10.0\bin\python.exe" tools\make_pcb.py [--force]` |
| `tools/drc_report.py` | KiCad DRC summary incl. schematic parity (`--type X`, `--refill`) |
| `tools/project_settings.py` | Design rules, net classes, severities (re-applies after any pcbnew save) |
| `tools/make_edgelock_fp.py`, `tools/fix_lcsc_footprints.py` | Regenerate / correct library footprints |

Current DRC: only the 499 unrouted connections (expected). Parity notes (custom fields, BOM-exclude flags) clear on your first F8.

## Placement suggestions (from the datasheets and your old spec)

Power stage first (input caps, FETs, inductor, output caps in a tight loop; SW nodes short, top layer, no vias), then the RP2350 with
its regulator parts within 10 mm (inductor polarity dot toward VREG_LX), crystal close with ground under it, flash near the QSPI pins, USB
resistors and connector with the pair straight and short, then connectors and the indicator LEDs near their pins. The area between the
two Uno rows is a good home for the MCU core (low parts only under a shield).
