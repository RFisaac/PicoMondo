# PicoMondo v1 — RP2350B Exhibit Controller Specification

**Status:** v1 scope, agreed 2026-10-25. Supersedes `superseded/RP2350B_Board_Design_Specification.md` (Feb 2026) and the scope parts of `hardware/archive/v0-full-scope/DECISIONS.md`. Verified engineering findings in that `DECISIONS.md` (crystal caps, flash limit, VREG values, EdgeLock geometry) still apply.

**KiCad project:** first build of `picomondo_reduced` generated 2026-10-26 (Pi core + reused sheets + placeholders; see `docs/history/2026-10-26_v1_first_build_notes.md`).

---

## 1. Purpose

A Pico replacement for museum exhibits that has **more usable GPIO on robust EdgeLock connectors**. Typical loads: arcade buttons with LEDs, addressable LED strips, a few servos, an occasional 12 V solenoid or other load on the switched output. Volume about 20 boards a year. Should be easy for beginners to use and hard to damage.

**v1 test:** a feature belongs in v1 only if a v1 exhibit would be blocked without it. Unfitted (DNP) footprints still take space and routing, so they follow the same rule.

---

## 2. Scope

### In v1
- RP2350B core copied from the Raspberry Pi "RP2350B Minimal Board" layout: regulator, crystal, decoupling, flash and USB resistors.
- W25Q128JVS 16 MB QSPI flash (the RP2350 can address at most 16 MB per chip select).
- USB-C, **5 V only** (5.1 kΩ CC pull-downs, USBLC6-2SC6 ESD). Used for data and programming, and powers the board when no barrel supply is present.
- **12–24 V barrel jack**, protected against reverse polarity, overvoltage and overcurrent. Runs a 5 V buck and feeds the switched output directly.
- **One switched high-side output** carrying the full barrel voltage, with an indicator LED, fuse, flyback diode and bleeder.
- **INA226 current/voltage monitor** on the switched output (I2C on GPIO16/17, address 0x41 on the schematic): reads barrel voltage and output current, so firmware knows whether the output can work and can catch stalls or overloads. Uses no GPIO.
- microSD (SPI1) with card detect.
- EdgeLock board-edge connectors with 100 Ω series resistors on every signal. Notches widened to **1.0 mm** to meet JLCPCB's minimum slot.
- A 2.54 mm through-hole header row behind each EdgeLock, not fitted by default (§5.1).
- Per-GPIO indicator LEDs, **arranged in a ring around the MCU** (see §6).
- WS2812B status LED, user LED (GPIO25), power LED, BOOTSEL and RESET buttons, SWD header.
- I2C bus with pull-ups, brought out to an EdgeLock connector **and a Qwiic/STEMMA QT connector** (JST-SH 4-pin) for external sensors.
- **NeoPixel connector** (3-pin: 5V, DATA, GND) beside the OUT connector, for addressable LED strips (§5.2).
- 4-layer, 1.6 mm, **lead-free HASL** (tin, per Molex's EdgeLock recommendation; see §7). MCU rotated 45° to the board.

### Cut from v1 (candidates for v2)
| Feature | Why it was cut |
|---|---|
| USB-PD (STUSB4500, its ESD, the 3.3 V aux LDO) | The barrel jack covers higher voltages; PD added parts and a second I2C device. |
| TPS55288 5 A buck-boost and its external FETs | The biggest layout risk on the old board; replaced by a simple 3 A buck. |
| WAGO push-in / screw-terminal power input | The barrel jack is enough. |
| Second switched output (J7 / +5V_SW split) | Merged into one output. |
| Second INA226 (the old 5 V output monitor) | Only one output remains; its INA226 is kept (§3.4). |
| Arduino Uno and Pico sockets | They took the board centre, capped part height, and pulled each GPIO three ways. A v2 "maker" variant could add them. |
| Spare flash footprint | Never going to be fitted. |
| Spare-GPIO test points | Those pins go to EdgeLock instead. |

---

## 3. Power architecture

```
Barrel jack (12–24 V, centre +)
   │
   ▼
[Reverse-polarity + overvoltage cut-off]   blocks reversed input and anything over ~26 V
   │
[F1 fuse, 5 A hold, ≥30 V]
   │
[TVS, transient clamp]
   │
 V_BARREL ──┬──► [5 V buck, 3 A] ──► [priority / OR] ──┐
            │                                         ├──► +5V ──► AP2112K-3.3 ──► +3V3
            │        USB-C VBUS ──► [priority / OR] ──┘           (RP2350 VREG ──► +1V1)
            │
            └──► [20 mΩ shunt + INA226] ──► [high-side P-FET, GPIO enable] ──► [3 A fuse] ──► OUT (4-ckt EdgeLock)
                     (I2C: V_BARREL, current)                                  ├─ indicator LED (at the connector)
                                                    ├─ flyback diode
                                                    └─ bleeder resistor
```

### 3.1 Barrel input protection
- **Reverse polarity.** Recommended: a P-FET (or N-FET in the ground return) reverse-protection stage, with a Vgs clamp zener because the input can reach 24 V. It adds almost no loss. A reversed plug simply does nothing.
- **Why not make it polarity-agnostic?** That needs a bridge rectifier. A plain diode bridge drops about 1 V and wastes about 3 W at 3 A on the output, too much heat for small parts. It also means the jack sleeve is no longer board ground. An ideal-diode bridge controller (LT4320 type) solves the loss but costs several dollars and adds 4 FETs. **Deferred to v2**; v1 is centre-positive, silkscreened clearly.
- **Overvoltage.** A TVS only clamps short spikes. A 36 V or 48 V supply plugged in for real would destroy it and then blow the fuse. v1 uses a **real cut-off**: an OV/reverse-protection controller driving back-to-back FETs (the LTC4365 is the textbook part: it survives about +60/−40 V and handles both faults in one chip). A discrete version (zener plus transistor pulling the series FET off) is the cheap alternative. **Pick the part by JLCPCB stock and cost at schematic time.**
  - Trip point about 26 V: above the 24 V jack rating and below the 30 V+ ratings of the buck, output FET and fuse.
- **F1:** the existing 5 A hold / 30 V part (C19078763) fits. Worst case at 12 V is about 1.4 A buck input plus 3 A output.
- **TVS** stays for transients, sized for a 24 V working voltage.
- **Barrel jack:** CUI PJ-102AH (5.5 × 2.1 mm, rated 24 V / 5 A). Check pin 1 = centre on the first board.

### 3.2 5 V rail
- **Buck:** 3 A class, switches built into the chip (no external FETs), input rated 30 V or more, around 400 kHz–1 MHz. Candidates to check: TI TPS62933 family or a Diodes AP643xx part; confirm at JLCPCB. Place the switching loop well away from the MCU, crystal and USB.
- **Priority / OR between USB and buck.** The barrel supply should win when it is present, and the board must **never back-feed 5 V into a USB host**. Two options, decided at schematic time:
  - (a) Schottky diodes on both, with the buck set slightly high (~5.2 V) so it carries the load.
  - (b) A Pico-style P-FET that disconnects VBUS while the buck is running, plus a diode on the buck side.
- USB data keeps working whichever source powers the board.
- **5 V budget:** buck 3 A. USB without PD gives whatever the charger advertises (usually 1.5–3 A). Document limits for users.

### 3.3 3.3 V rail
- Single AP2112K-3.3 from +5V. It is thermally limited to about 350 mA in SOT-23-5 (see `hardware/archive/v0-full-scope/docs/power_ldo.md`); give its pad a copper pour.
- Loads: MCU ~100 mA, flash ~20 mA, microSD up to ~100 mA, LEDs ~1 mA each, plus the 3.3 V pins on the EdgeLock connectors. **Document the budget.** If v1 testing shows it is too tight, swap in a small 3.3 V buck in v2.

### 3.4 Switched output (OUT)
- Carries **V_BARREL** (full barrel voltage). Works whenever the barrel supply is present, **even if USB is also connected**. Dead when running on USB only; firmware reads the INA226 and can warn.
- Circuit as before (old J8 channel): GPIO → 10 kΩ → NPN (100 kΩ base pull-down) → R_g → P-FET gate; R_gs plus a **12 V gate zener** from source to gate; P-FET rated 40 V (DMP4015SSS-13). GPIO floating or low means the output is off, so it stays off at power-up and during reset.
- **3 A output fuse** (1812L300/33GR; derates to about 2 A in a warm enclosure).
- **Flyback diode** (SS54) and **bleeder** (22 kΩ).
- **Indicator LED at the output terminal**, driven from the switched side, so it shows that voltage is actually present on OUT, not just that the GPIO is high. Pick its resistor for about 1 mA at 12 V (about 2 mA at 24 V).
- **Monitor:** INA226 (I2C 0x40, shared GPIO20/21 bus), 20 mΩ shunt **ahead of the FET** so it reads barrel voltage even with the output off (bus-voltage input on the shunt's low side; INA226 handles 36 V). Reads up to ~4 A. ALERT pin left unconnected (or to a test point); firmware polls it.
- **Connector: 4-circuit EdgeLock (2008900104), contacts paralleled 2 + 2.** The latch window already splits it into two pairs: pins 1–2 = OUT+, pins 3–4 = GND.
  - Why not 2-circuit: Molex rates each contact **3.0 A max with 22–24 AWG wire** (product spec 2008900001 §4.2), and the edge pad geometry is fixed by Molex, so the pads can't be made heavier. Paralleling halves the current per contact (1.5 A at 3 A out) and lets the harness use two 22 AWG wires per side. The footprint is only 4 mm wider (19.1 mm vs 15.1 mm).
  - Copper behind the contacts: pours on F.Cu and B.Cu, stitched with vias, not tracks.
  - **Heavy through-hole pads behind it:** one hole per net (OUT+, GND) at **5.08 mm pitch, ~1.3 mm drill / ~2.6 mm pad**. These take 18–20 AWG wire soldered directly, or a standard 2-pin 5.08 mm screw terminal if an exhibit wants one. Square pad on OUT+.
  - Silkscreen: "OUT = barrel V, 3 A max", polarity on both the contacts and the holes.

---

## 4. Core (unchanged from the verified design)
- RP2350B QFN-80. Copy the Pi minimal board's layout for the regulator (L1 3.3 µH AOTA-B201610S3R3, **pad 1 / polarity dot on +1V1, pad 2 on VREG_LX**, as on the Pi board. The Feb spec and old schematic had this reversed; fixed in the v1 build; C6/C7/C10 4.7 µF; R3 33 Ω + C9), the crystal (ABM8-272-T3, 15 pF caps, 1 kΩ on XOUT), decoupling and the USB 27 Ω resistors.
- **45° rotation:** group the whole copied core block and rotate it 45°. Do not re-place the parts on a diagonal one by one.
- Flash W25Q128JVS (SOIC-8), next to the QSPI pins.
- BOOTSEL and RESET: TS-1187A switches (C318884), set in from the right edge (~x 86–98) so they aren't in a valley between the USB-C and the taller barrel jack.
- SWD: J10, JST-SH 3-pin SM03B-SRSS-TB (LCSC C160403), Pi Debug Probe pinout 1 SWCLK / 2 GND / 3 SWDIO, fitted, on the **left edge, below the Qwiic**, so it can be reached in the enclosure. SWD is slow enough that the ~5–6 cm trace run is fine; keep SWCLK/SWDIO away from the buck and the USB pair.

---

## 5. GPIO allocation (by function)

| Function | GPIO | Count |
|---|---|---|
| microSD (SPI1 + card detect) | 12–15, 22 | 5 |
| WS2812B status LED | 23 | 1 |
| User LED | 25 | 1 |
| Switched output enable | 24 | 1 |
| NeoPixel data (buffered) + one spare, both on solder holes | 2 GPIO, picked at placement | 2 |
| **EdgeLock signals** | all others | **38** |

- **38 GPIO on EdgeLock** (40 user GPIO in total), against 28 on the old board and 26 on a Pico. This includes all 8 ADC pins (GPIO40–47), I2C0 (20/21, with 4.7 kΩ pull-ups; also shared with the on-board INA226), SPI0 (16–19) and UART pairs.
- **One connector size:** all seven signal EdgeLocks are 8-circuit (one housing part to stock). 42 slots for 38 GPIO; the 4 left over become extra GND (or 3V3) contacts, placed where a harness benefits most (e.g. button-bank connectors).
- **Four joystick-capable connectors:** each of four 8-circuit connectors gets 2 ADC pins plus 3V3 (two joystick axes + up to 4 buttons). The ADC pins all come off one side of the chip, so these four sit on the edges nearest that side.
- Connector logic (from the Nov 2025 planning): one connector per wiring harness; size for the busiest single exhibit (two 5-button banks, or two joysticks + a 4-button bank); every connector carries GND, analog ones carry 3V3.
- **The connector pin map is decided after placement, not before** (§6.2). Each connector should take pins from the side of the MCU that faces its board edge.
- **Connector standard (to settle at placement):** one pinout used everywhere, for example 8-circuit EdgeLock = 6 GPIO + 3V3 + GND (7 connectors = 42 signals), or 6-circuit joystick style = 4 GPIO + 3V3 + GND. One or two connectors should carry **+5V instead of 3V3** for servos and LED strips (fused).
- The RP2350B A4 is 5 V tolerant on GPIO, but the logic is still 3.3 V. Silkscreen: "3.3 V LOGIC".

### 5.0 Small connectors
- **Qwiic / STEMMA QT:** JST-SH 1.0 mm 4-pin, right-angle (SM04B-SRSS-TB or equivalent), on the left edge above EL7. Pinout per the Qwiic standard: GND, 3V3, SDA (GPIO16), SCL (GPIO17). Shares the I2C bus with EL7 and the INA226, so it costs no GPIO. The INA226 is at 0x40; avoid sensors that are fixed at that address.

### 5.2 NeoPixel connector
- **JST-XH 2.5 mm, 3-pin, right-angle** (S3B-XH-A or equivalent), next to OUT on the right edge. Chosen over JST-PH (2.0 mm) because it is the larger, sturdier one and is rated 3 A per contact against PH's 2 A. Strips usually ship with JST-SM pigtails, so an SM-to-XH adapter lead is needed either way. Silkscreen 5V / DIN / GND.
- **Power is +5V, not the OUT voltage.** WS2812-type pixels are 5 V parts, and OUT carries 12–24 V, which would destroy a 5 V strip. OUT is right next door for 12 V pixel strips (WS2815 and similar), or a 5 V strip with its own supply injected at the far end.
  - The on-board 5 V rail is a 3 A buck shared with everything else, so budget roughly 1–2 A for pixels (about 30–50 LEDs at full white). Past that, inject power separately. Document this.
  - Fuse the connector's 5 V (about 2 A) and put a bulk capacitor (about 220–470 µF, low ESR) plus 100 nF at the connector. Add a ~330 Ω series resistor on DATA.
- **Data source (decided 2026-10-25): a dedicated GPIO through a 5 V buffer** (74AHCT1G125 powered from +5V), independent of the status LED. Buffer output → ~330 Ω → DIN.
- **Three solder holes** (1×3, 2.54 mm pitch: NeoPixel GPIO, spare GPIO, GND) near the NeoPixel connector. The NeoPixel GPIO hole taps the raw 3.3 V side, before the buffer. Each GPIO goes GPIO → 100 Ω → hole, the same protection as the EdgeLocks. Both GPIO get ring LEDs and silkscreen labels. If no strip is fitted, the NeoPixel GPIO is just another pin on its hole.
- Pick both GPIO at placement, from the side of the chip facing the right edge.
- Every EdgeLock gets a matching **1×N row of 2.54 mm plated through-holes** just behind it: one hole per contact, power and GND included, in the same order. Not fitted by default. Male or female headers can be soldered in when an exhibit needs them, and the holes double as probe points.
- Each contact trace runs **through its hole** (pad → hole → 100 Ω → GPIO), so the hole is on the connector side of the 100 Ω resistor. Header users get the same protection as EdgeLock users.
- Hole size: about 1.0 mm drill / 1.7 mm pad (standard header pins). Square pad and "1" on pin 1. Silkscreen the same labels as the EdgeLock contacts.
- **Pitch mismatch:** EdgeLock is 2.0 mm and headers are 2.54 mm, and the contacts are split into two groups (4+4 on the 8-circuit, 3+3 on the 6-circuit) with a ~9.3 mm latch window between them. Footprint widths: 8-circuit 27.1 mm, 6-circuit 23.1 mm (from the Molex footprint). Each header row sits behind one contact group:
  - **Tilted row:** a single row at an angle. At about 38° it spans the same width as the connector; at **45° it spans about 12.6 mm** and matches the rotated MCU. Takes a standard single-row header, same pin order.
  - **Two rows on the 2.54 mm grid (2×N/2):** about 7.6 mm wide for 8 circuits. Takes a standard dual-row header or IDC/ribbon. Pin order becomes odd/even (zig-zag), so silkscreen every hole.
  - **Two rows offset by half a pitch:** packs tightest, but no standard header fits. Use it only if the holes are for wires or probes.
  Pick one style and use it on every connector, so the look and the pin numbering stay consistent.
- **Chosen direction (2026-10-25): tilted rows, probably split.** For example, an 8-circuit connector becomes two tilted 1×4 rows (a 6-circuit one becomes two 1×3 rows).
  - At 45°, each 1×4 row spans about 5.4 mm along the edge, about the same as its 6 mm contact group, so each row sits directly behind its group.
  - Arrange the two rows either **parallel** (same angle) or as a **chevron** (mirrored ±45°, which can point toward the MCU).
  - Keep pins sequential: row A = contacts 1–4, row B = contacts 5–8. Square pad on each row's first hole, and a GPIO label on every hole.
  - Takes two standard 1×4 single-row headers (snapped from breakaway strip). A one-piece 1×8 or a 2×4 IDC won't fit.
  - Lay out one connector + resistors + header pattern, check it routes cleanly, then reuse that block for every connector.
- **Housing clearance:** confirmed OK: the header holes sit clear of the clipped-on EdgeLock housing.
- **Planes:** a row of holes slots the In1 GND plane. At 2.54 mm pitch with 1.7 mm pads the plane web between holes is thin, so keep the plane continuous around the ends of each row and stitch GND nearby.
- Enclosure is custom-designed around the board, so header height and board size are not constraints.

---

## 6. Indicator LED ring and layout plan

### 6.1 LED ring
- Each indicator is a shunt LED: GPIO net → 470 Ω → white LED (OSRAM LW QH8G 0402) → GND, about 1 mA. White LEDs don't conduct below about 2.4 V, so inputs on weak pull-ups still read high.
- LEDs sit in a **radial ring around the 45° MCU**: a circle about 38 mm across (radius ~19 mm from the chip centre), each LED and its 470 Ω pointing along the radius. 40 LEDs over ~300° gives about 2.5 mm spacing. The ring sits outside the core keep-out.
- **The ring has a ~60° gap** on the side of the package where the QSPI, USB, crystal and regulator pins are. The flash sits in the gap and the USB pair exits through it.
  - Measured on the copied Pi core block: the flash and its resistors span about 55°–100° above the right-hand horizontal and reach r ≈ 22 mm; the USB pair leaves the chip at about 25°. So the gap runs from about **20° to 100° up and to the right** (80°, centred near 60°), and the 40 LEDs share the other 280° (~2.4 mm pitch). The route-art board (`hardware/route-art/picomondo_art.kicad_pcb`) uses exactly this.
- **Ring order follows the chip's pin order**, so traces fan out without crossing. Do not reorder for looks.
- ADC pins: keep the cuttable trace neck (0.15 mm, silkscreen "cut" mark) between the GPIO and the 470 Ω, so the LED can be removed from precision analog inputs.
- The LED taps off on the MCU side; the 100 Ω series resistor sits at the connector.

### 6.2 Placement order
1. Board outline, mounting holes, EdgeLock positions (1.0 mm notches) with their header-hole rows behind them (§5.1).
2. The power corner: barrel jack, protection, buck, priority/OR, output stage. Keep it away from the core.
3. The RP2350B core block from the Pi layout, rotated 45°.
4. The LED ring, in pin order.
5. **Then** assign GPIO to connector pins so each side of the chip feeds its nearest edge.
6. USB-C close to the ring gap: pair on F.Cu over the In1 ground plane, 0.15 mm / 0.16 mm gap (90 Ω, check with JLCPCB's calculator), short and with no vias.
7. microSD near the SPI1 pins.
8. Route the critical nets by hand: power loops, USB, crystal, QSPI. Autoroute only the leftover GPIO, if at all.

### 6.3 Silkscreen
- GPIO number next to **every ring LED** and next to **every EdgeLock contact**.
- Connector names and functions, the barrel polarity symbol plus "12–24 V", "OUT = barrel V, 3 A", "3.3 V LOGIC", and a mark on the joystick-capable connectors.
- Polarity marks on L1, diodes and LEDs; pin-1 marks on everything.

### 6.4 Route art (decorative silkscreen)
- Concept: "circuit" lines from the chip, through each ring LED, out to its EdgeLock contact, coloured or patterned by function, with a legend on the board. Decorative only: it does not follow the real copper.
- Workflow: a separate art copy of the placed board (chip, LED ring, connectors only; no passives) with direct chip → LED → contact nets; route it on **one layer only** (Freerouting or KiCad's router; no vias) with wide tracks and clearance for a clean look; export the copper as SVG; finish in Illustrator; import back onto F.Silkscreen (File › Import › Graphics) or hand the image to the fab's colour-print process.
- Single-layer routing only works without crossings if connector pins are assigned in ring order (§6.2), which the real layout needs anyway.
- Fab rules: silkscreen is clipped off pads and holes, so lines visibly "enter" each LED and contact. Keep lines ≥ 0.2 mm; check the fab's minimum width and clearance. Start the lines outside the core keep-out (~11 mm radius) rather than at the 0.4 mm-pitch chip pins.
- Colour: standard silkscreen is one colour. Options: full-colour silkscreen (check the fab's process and limits), line patterns (solid/dashed/dotted), exposed (tinned) copper for one category, or colour on the acrylic lid.

---

## 7. Board
- 4-layer JLC04161H-3313, 1.6 mm, **lead-free HASL** (decided 2026-10-26, was ENIG). Molex's EdgeLock product spec (2008900001 §10) strongly recommends tin-plated mating areas for the rated durability and contact resistance: the EdgeLock terminals are tin, ENIG's thin gold wears through to nickel, and tin-on-gold is a poor contact pair. Keep solder mask and flux off the contact areas, and keep the entry edge smooth and burr-free. Check that JLCPCB assembles the 0.4 mm-pitch QFN-80 cleanly on HASL.
- In1 solid GND, In2 power pours. Carry high current on the outer layers or in pours.
- Rules: 0.10 mm minimum track and space (target 0.127 mm), vias 0.45 / 0.2 mm.
- Size: 120 × 90 mm, 3 mm corners, 4 × M3 holes 4 mm in from the corners. It could shrink, but space makes routing easier; size it to the enclosure.
- 3 fiducials. Test points: V_BARREL, +5V, +3V3, +1V1, VBUS, GND ×2, SDA/SCL, USB D+/D−, INA226 ALERT.

---

## 8. Open items
1. ~~OV/reverse protection~~ decided: LM74502 + AO4882 (see §10).
2. ~~Buck part~~ decided: LMR33630B (see §10).
3. ~~Priority/OR~~ decided: Schottky OR, option (a) (see §10).
4. EdgeLock plan (draft in the layout mockup): EL1–EL7 all 8-circuit (6 signals + power + GND; EL5/EL6 carry +5V; EL7 carries SDA/SCL + 4 GPIO; four connectors joystick-capable), OUT 4-circuit (2 + 2 paralleled). 42 slots for 38 GPIO; 4 become extra GND/3V3. Depth from edge: contacts 0.9–7.1 mm, housing to 8.7 mm, header rows ~10.9–16.3 mm, 100 Ω row ~18–19 mm.
4a. Header-hole style: tilted rows chosen; still to decide one row vs split 1×4 pairs, and parallel vs chevron (§5.1).
5. microSD socket card-detect pins 9/10: confirm on the Molex drawing.
6. Confirm CPL rotations in JLCPCB's preview (the 45° MCU especially).
7. Check the Molex 200449 terminal / housing: confirm two 22 AWG wires per side is how the OUT harness gets built.
8. INA226 address: the reused schematic straps it to 0x41, this spec says 0x40. Pick one.
9. J8 in the schematic is still the KF301 screw terminal; swap to the 4-circuit EdgeLock (§3.4).
10. Future (v2): polarity-agnostic input, USB-PD, Arduino/Pico variant, 3.3 V buck.


---

## 9. Pin map and EdgeLock sheet (decided 2026-10-26)

Drawn in `edgelock.kicad_sch` and placed on the board. Contact -> header hole -> 100R -> GPIO on every signal.
EdgeLock pin 1 is on the counter-clockwise end of each connector (top edge: right end; bottom: left end; left edge: top end), so pin order runs the same way round the board as the LED ring.

| Connector | Edge | Role | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|---|
| EL1 | top-left | servo / strip | +5V (PTC) | GND | 4 | 5 | 6 | 7 | +5V (PTC) | GND |
| EL2 | top-middle | joystick | 3V3 | 46 (ADC) | 47 (ADC) | 0 | 1 | 2 | 3 | GND |
| EL3 | top-right | joystick | 3V3 | 44 (ADC) | 45 (ADC) | 36 | 37 | 38 | 39 | GND |
| EL4 | bottom-left | servo / strip | +5V (PTC) | GND | 18 | 19 | 20 | 21 | +5V (PTC) | GND |
| EL5 | bottom-middle | joystick | 3V3 | 40 (ADC) | 41 (ADC) | 26 | 27 | 28 | 29 | GND |
| EL6 | bottom-right | joystick | 3V3 | 42 (ADC) | 43 (ADC) | 30 | 31 | 32 | 33 | GND |
| EL7 | left | I2C | 3V3 | 8 | 9 | 10 | 11 | 16 (SDA) | 17 (SCL) | GND |

- NeoPixel holes: GPIO34 (NeoPixel data, buffered) and GPIO35 (spare).
- **+5V moved from EL5/EL6 to EL1/EL4.** The ADC-capable pins (GPIO40-47) are not 5 V tolerant, so the four joystick connectors carry 3V3; the two +5V connectors are the ones furthest from the ADC side. Each has a 2 A-hold 1812 PTC (part number to pick).
- **I2C moved to GPIO16/17** (I2C0). The Qwiic connector, INA226, 4.7k pull-ups and test points follow. The Qwiic connector previously used *local* labels and was not connected to the bus at all; it is now. GPIO20/21 are ordinary GPIO on EL4; the indicator LEDs DNP moved from GPIO20/21 to GPIO16/17.
- Joystick ADC pairs cross other lines in the route art (the ADC pins all leave the chip on the right): accepted, drawn as bridges.
- EdgeLock footprints: latch notches widened to 1.0 mm. New footprint `EdgeLock_8ckt_HeaderHoles_Chevron` shares the EdgeLock origin.
- R37 (OUT indicator) is 10k: LCSC changed to C25744 to match (was the 470R part).
- OUT done (2026-10-26): J8 is now the 4-circuit EdgeLock on the right edge (board y 104), pins 1-2 OUT+, 3-4 GND; J9 = two heavy holes behind it (1.3 mm drill / 2.6 mm pad, 5.08 mm pitch, square = OUT+), new footprint `EdgeLock_4ckt_HeavyHoles`. Pin 1 is the lower end. Copper pours behind the contacts still to add.
- NeoPixel sheet done (2026-10-26): U12 74AHCT1G125GW (C12495, +5V, OE tied low) buffers GPIO34 -> R161 330R -> DIN on J11 JST-XH S3B-XH-A (C157928; pins 5V / DIN / GND), right edge below OUT, opening outward. Strip 5 V through F6 PTC 2 A hold (SMD1812P200TF/16, C20812), C54 220 uF 10 V (C487024) + C55 100 nF at the connector. R162 100k pulls GPIO34 low during reset. J12 solder holes: GPIO34 via R163 100R, GPIO35 via R164 100R, GND (not fitted).
- F4/F5 (EL1/EL4 +5V PTCs) can use the same C20812 part.
- EL6 moved 2.5 mm left (board-relative centre x 94.0) to make room for J11.


## 10. Power sheets (drawn and placed 2026-10-26)

**Barrel input (`barrel_input.kicad_sch`).** J13 PJ-102AH (C3096093) -> F1 2920 PTC 5 A hold / 30 V (C19078763) -> D55 SMBJ28CA bidirectional TVS (C8836) -> U13 LM74502DDFR (C3236215) driving Q7 AO4882 dual N-FET (C477943) back-to-back -> V_INPUT.
- EN tied to VS (always on). VCAP 220 nF to VS. OV divider 100k / 4.7k: cutoff 27.9 V nominal (26.0-29.7 V over the OV threshold tolerance), so a 24 V supply always passes and nothing downstream (36 V buck, 40 V FETs, 36 V INA226) sees more than ~30 V.
- A reversed plug: the bidirectional TVS doesn't conduct and Q7 stays off, so the board simply stays dead (no fuse trip).
- V_INPUT bulk: 2 x 10 uF 50 V 1206 (C13585) + 100 uF 35 V electrolytic (C294520) to damp hot-plug ringing.
- J13 pin 1 = centre (CUI drawing): verify on the first board.

**5 V (`power_5v.kicad_sch`).** U14 LMR33630BDDA (1.4 MHz, 36 V, 3 A, C544370), L2 3.3 uH Sunlord SWPA6045S3R3NT (Isat 6.2 A, C279943), Cin 2 x 10 uF 50 V + 100 nF, Cout 3 x 22 uF 25 V 1206 (C12891), feedback 100k / 23.2k -> 5.31 V. PG left open.
- Priority: D56 SS54 (buck -> +5V) and D57 SS54 (VBUS -> +5V). With the barrel present +5V ~ 4.85 V and the VBUS diode is reverse-biased; on USB alone +5V ~ 4.55 V. The board never back-feeds a USB host. PWR_FLAGs on +5V, VIN_F and V_INPUT.

**USB-C (`usb_c.kicad_sch`).** J14 GCT USB4105-GF-A (C3020560), 5.1k on CC1 and CC2, U15 USBLC6-2SC6 (C7519) on D+/D- with VBUS reference, 4.7 uF on VBUS. SBU unused. D+/D- connect straight to USB_D+/USB_D- (27R on the MCU sheet).

**Placement.** Barrel and USB-C on the right edge at the mockup positions (openings outward); protection, buck and 5 V OR in the power zone left of the barrel/OUT; 3V3 LDO next to the 5 V output. First pass only: the buck loop (Cin - U14 - L2 - Cout) needs hand-tuning to the TI layout guide.

**Part numbers still to pick:** C57 220 nF 25 V 0402, R168 23.2k 1 % 0402, C70 4.7 uF 25 V 0805.

**Switched-output stage placed (2026-10-26)** after BOOT/RESET moved to the lower left (board x 72 / 80.5, y 113) and the OUT heavy holes shifted down: shunt R27 and INA226 U8 directly above the protection output, P-FET Q5 beside them, fuse F3 between USB-C and the barrel jack, flyback D7 between the barrel jack and OUT, bleeder/indicator (R32, R37, D8) next to the heavy holes. First pass; J8_DRAIN and J8_OUT are long-ish 3 A runs to tidy when routing.

## 11. Changes, 2026-10-26 afternoon
- **Board finish:** lead-free HASL instead of ENIG (§7).
- **J11 NeoPixel connector** is now the SMD JST-XH **S3B-XH-SM4-TB(LF)(SN)** (KiCad footprint `JST_XH_S3B-XH-SM4-TB_1x03-1MP_P2.50mm_Horizontal`), same position and pin order (1 5V / 2 DIN / 3 GND), same mating plug as the S3B-XH-A. **LCSC number still to fill in** (the 4-pin S4B-XH-SM4-TB is C161861), and it needs a 3D model (not in the stock KiCad library).
- **J13 barrel jack** (PJ-102AH, 24 V / 5 A): stays through-hole, marked **DNP** and left out of the placement file; hand-soldered. Still on the BOM.
- **Indicator ring LEDs stay white.** Amber was considered but rejected: amber's ~1.9 V forward voltage would pull weak-pull-up inputs to around the RP2350's logic threshold. Colour comes from a gel/diffuser in the enclosure instead.
- **USB-C J14:** confirmed C3020560 is the USB4105-GF-A in LCSC's own library (the generic footprint name is LCSC's), so the BOM is right.
- **Routing:** net classes set (Power5A 1.6 mm, PowerHigh 1.2 mm, Power 0.5 mm, Ground 0.4 mm, USB 0.2 / 0.25 mm gap; all 0.15 mm clearance). In1 = GND plane, In2 = +3V3 plane with a +1V1 island under the core. Power routed and locked, with 2-3 parallel vias on every high-current layer change. USB pair coupled on F.Cu (~51 mm), entering the ring through the gap, and locked. Signals autorouted by Isaac; DRC clean with no unconnected items.
- **3D models:** the LCSC and project models were copied from `picomondo_creep/lib` into `picomondo_reduced/lib`; U14 repointed to the stock `HTSOP-8-1EP_3.9x4.9mm_P1.27mm.step`. Do not import LMR33630**A**DDAR (400 kHz) for U14; the design needs the B part (C544370).
