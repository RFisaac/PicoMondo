# Design decisions

Decisions made in conversation. These overrule anything in `../resources/` (old docs may be stale).

## Tooling
- Design in **KiCad 10** directly (schematic + PCB files). atopile is not used: its parts/registry
  services (`components.atopileapi.com`, `packages.atopileapi.com`) no longer resolve.
- Parts: LCSC IDs from the BOM, converted with `easyeda2kicad` (to be tested).
- Placement by hand, routing with an autorouter (Freerouting or KiCad's router).
- Baseline for the RP2350B core: Raspberry Pi "RP2350B Minimal Board" KiCad project
  (`../resources/pi-reference/kicad/`).

## Board (decided 2026-10-01)
| Item | Decision |
|------|----------|
| Layers | 4-layer, 1.6 mm (JLCPCB-style stackup) |
| 5 V converter | TPS55288 buck-boost (verify from datasheet whether external switching FETs are needed) |
| Current monitors (J7, J8) | INA226, addresses 0x40 (J7) / 0x41 (J8) |
| GPIO indicator LEDs | Shunt LED, about 1 mA to GND, outside the signal path; on the ADC pins (GPIO40-47) a trace neck you cut with a knife disconnects the LED |
| Flash | W25Q128JVS (16 MB, SOIC-8) as primary, as in the Pi reference. Plus Pi's optional second-memory footprint (DNP): extra chip select on GPIO0, so GPIO0 stays free for EdgeLock/Arduino unless that part is fitted. Bulk data goes on the microSD. |
| Size | 120 x 90 mm, 3 mm corners, 4x M3 |

## Carried over from the newest spec (not re-discussed)
- J8 switch: P-FET rated 40 V or more, with a Vgs clamp. SI2305A only on J7 and +5V_SW.
- Input overcurrent protection rated for 30 V or more.
- Check V_INPUT TVS clamp margin against everything on V_INPUT.
- Must-use parts: see `../resources/board-spec/rp2350b_exhibit_board_spec_packet.md` section 6.

## Findings verified against Raspberry Pi documents (2026-10-01)
- **Flash size:** RP2350 supports at most 16 MB per QSPI chip select (24-bit addressing only;
  two chip selects, 32 MB total). The W25Q512JVBIQ (64 MB) would only expose its first 16 MB.
  RP2350 datasheet section 12.14 (QMI), and "Hardware design with RP2350" section 3.1.
- **Crystal:** ABM8-272-T3 has a 10 pF load. Use 15 pF caps (7.5 pF series + about 3 pF parasitic)
  and a 1 kohm series resistor on XOUT. The old "18 pF load" note is wrong.
- **VREG:** L1 3.3 uH from VREG_LX to +1V1; C6 4.7 uF on VREG_VIN; C7 and C10 4.7 uF plus C8/C11
  100 nF on +1V1; R3 33 ohm from +3V3 to VREG_AVDD with C9 4.7 uF. Copy from the Pi project.
- **USB trace geometry:** the Pi 0.8 mm / 0.15 mm figure is for a 1 mm 2-layer board. On a
  4-layer stackup the width depends on the prepreg thickness to the ground plane, so it must
  be recomputed for the actual JLCPCB stackup.

## 5 V rail design (2026-10-01, see docs/power_buck_boost.md)
- TPS55288 needs **external buck-side FETs** (resolves the old open question). Both are 60 V CSD18543Q3A.
- 400 kHz, forced PWM, output fixed at 5 V by the chip default, I2C address 0x74, 10 mohm sense resistor
  (5 A limit), ILIM about 10 A.
- GPIO35 is the TPS55288 fault input (FB/INT, 10k pull-up). Pins 35-39 were expansion/test points.
- Library parts: symbols/footprints/3D models for LCSC parts are generated with easyeda2kicad into
  `lib/lcsc/` (`lcsc` library). Datasheets: `resources/datasheets/` (run `tools/fetch_datasheets.py`).

## Power input and 3.3 V rails (2026-10-01, see docs/power_input.md and docs/power_ldo.md)
- Decided by Claude per "go with your recommendation": simple TVS (SMBJ28A) rather than an OVP stage;
  inductor Coilcraft XAL1010-472MED (TI's reference part, in stock at JLCPCB); 5 V budget handled by
  documenting limits (firmware or user), not by a larger converter.
- WAGO terminal (C2765055) is orderable at JLCPCB; the LCSC lookup just fails for it.
- Barrel jack: pin 1 positive, pins 2 and 3 grounded; verify with a plug on the first board.
- Main 3.3 V LDO is thermally limited to about 350 mA (see docs/power_ldo.md).

## Switched outputs (2026-10-01, see docs/power_outputs.md)
- INA226 shunt is 20 mohm (the INA226 range is +/-81.92 mV, so the old 50 mohm part would saturate at 1.64 A).
- J8: DMP4015SSS-13 (40 V) with a 12 V gate zener. J7 and +5V_SW: SI2305A. 3 A fuses (1812L300/33GR).
- Parts for this sheet generated into `lib/lcsc/` (GX2512 shunts, SS54-HF, fuse, KF301 terminal).
- Still to do: I2C pull-ups (4.7k to +3V3 on GPIO20/GPIO21) - planned on the IO sheet.

## USB-C and PD (2026-10-01, see docs/usb_pd.md)
- STUSB4500 powered from both VBUS (VDD) and +3V3_AUX (VSYS), dead-battery mode, address 0x28, no VBUS power switch.
- ESD per ST's reference: ESDA25P35-1U1M on VBUS, ESDA25W on CC1/CC2 (the old BOM had neither), USBLC6-2SC6 on D+/D-.
- PD profile must be programmed into the STUSB4500 NVM by firmware (factory profile is 5 V / 15 V / 20 V at 1.5 / 1.5 / 1.0 A).
- Connector footprint verified against GCT's drawing.

## IO (2026-10-01, see docs/io.md)
- EdgeLock J1-J6, J9 are Molex 200890 board-edge contact pads (not SMD parts); the spec's 502598-0603 is the wrong series.
  Footprints come from Molex's KiCad footprints (pads and edge notches) and match Molex's sales drawing; mating housings 2008900106 (J1-4, J6, J9) and 2008900104 (J5).
- Connector references follow the spec: J1-J6 and J9 EdgeLock, J7 and J8 output terminals, J10 SWD.
- Indicator LEDs: 30 shunt LEDs (470 ohm + white LED); the 8 ADC pins' LEDs are on by default and are disconnected by cutting a trace neck (no jumper parts; JP1-JP8 removed 2026-10-04). 100 ohm series
  resistors on every EdgeLock signal pin.
- Arduino D0 = RX = GPIO1, D1 = TX = GPIO0. GPIO10/11 as UART1 TX/RX is valid (RP2350 function 11).
- WS2812B powered through a series Schottky so a 3.3 V GPIO meets its logic-high threshold.
- microSD in SPI mode on GPIO12-15, card detect GPIO22. GPIO36-39 on test points.

## PCB (2026-10-01, see docs/pcb.md)
- 120 x 90 mm, 3 mm corners, 4 x M3 holes 4 mm in from the corners; JLC04161H-3313 stackup (In1 = GND plane, In2 = power).
- EdgeLock: J1-J4 on the top edge, J9/J6/J5 on the bottom edge, notches built into the outline. Arduino and Pico sockets grouped at the
  exact Uno R3 pattern, centred on the board. All other parts staged beside the board by sheet.
- Rules: 0.127 mm track/clearance, via 0.45/0.2 minimum; classes Default, Power, PowerHigh, USB (0.15 mm track, 0.16 mm gap for 90 ohm).
- The PCB is generated through KiCad's own pcbnew API (not kiutils) so footprints are exactly KiCad's; do not re-run make_pcb --force after placing parts.

## Parts and JLCPCB assembly (2026-10-04, see bom/)
- `bom/parts.csv` is the source of truth for LCSC numbers and MPNs, keyed by (Value, Footprint). `tools/apply_parts.py` writes them into the
  schematic, `tools/sync_board_parts.py` onto the board, `tools/bom.py` makes `bom/jlcpcb_bom.csv`, `jlcpcb_cpl.csv` and `BOM_REPORT.md`
  with a live JLCPCB stock check. Re-run `bom.py` after placement and before ordering.
- Passives are JLCPCB basic parts where one exists (0402 resistors, most caps). 21 of 67 line items are basic; the rest are extended.
- Changed for availability or fit: BOOTSEL/RESET now the 5.1 mm TS-1187A-B-A-B switch (basic, C318884; the old footprint was a 3 mm Wurth part
  that did not match the listed Omron B3FS, a 12 mm switch; pins go to the diagonal pads); SWD header A1002WR-S-3P (SH-compatible, JST was 2 in stock);
  D5/D7 SS54 (SS54-HF out of stock); WS2812B-V5/W; C40-C43 10u caps now X5R 25 V (C91158 was Y5V and out of stock).
- Through-hole parts (J7, J8, J11, Arduino and Pico sockets) are in the BOM but not the SMD placement file; check whether to hand-fit them.
- Not assembled: EdgeLock connectors (contact fingers on the board), DNP parts (U3 spare flash, C26, C39), test points, fiducials, jumpers.

## Routing review (2026-10-05)
- JLCPCB 4-layer limits, from their capabilities page: tracks and spacing 0.10 / 0.10 mm on 1 oz copper (outer layers here), copper to routed
  edge at least 0.2 mm, vias 0.2 mm hole / 0.45 mm pad at standard price; vias down to 0.15 / 0.25 mm are possible but cost more.
- The first routing pass (outside plugin) used 0.0889 mm tracks (61 on F.Cu/B.Cu: CDC, QSPI_SS, GPIO39, ILIM) and 7 vias smaller than 0.45 / 0.2.
  Widening them to 0.10 mm makes 30 clearance errors, so they were left; re-route with 0.10 / 0.10 and 0.45 / 0.2 rules to remove the surcharge risk.
- USB D+/D- were routed about 111 / 122 mm long on the inner layers (straight distance about 45 mm): re-route by hand on F.Cu.
- Fixed by hand: fiducials moved to three spread corners, J12 moved 0.25 mm in from the edge, three In2 +3V3 tracks moved off the EdgeLock notch corners,
  GND pin 8 of J18/J19 connected solid to the plane.
- Left open: 7 unrouted connections (U11 GND pin 6, U1 pin 64 +3V3, U4 pin 13 +5V, U4 pin 26 VOUT_PRE, U10 pin 22 +3V3_AUX, GPIO9 at U1 pin 7, one +1V1 gap).

## Open
- Barrel jack rated 24 V vs the 28 V design range (see docs/power_input.md).
- Output fuse hold current derates with temperature (3 A hold at room temperature).
- Main 3.3 V rail load budget vs the LDO's 350 mA thermal limit.
- 5 V load budget: converter is 5 A; J7 + 5V_SW + LDOs can exceed it.
- EdgeLock notches are 0.85 mm wide; JLCPCB's stated minimum routed slot is 1.0 mm: check with their DFM tool (docs/io.md).
- microSD socket pins 9/10 (card-detect switch): confirm against the Molex drawing.
- Mounting hole and fiducial positions, header placement: PCB stage.
- Confirm CPL rotations in JLCPCB's preview before ordering (SOT-23, QFN, polarised parts often need a correction).
