# IO sheets

Four sheets: `io_edgelock` (connectors), `io_indicators` (LEDs), `io_headers` (Arduino and Pico),
`io_misc` (microSD, WS2812, status LEDs, pull-ups, test points, mechanical).

## EdgeLock connectors J1-J6 and J9 (important)

The spec says "Molex EdgeLock 502598-0603". That part number is a 0.3 mm flat-cable connector, not
EdgeLock. The EdgeLock you supplied a product spec for (series **200890**, 2.0 mm pitch) is a
**wire housing that clips over the board edge** and touches contact pads on the PCB (1.2 or 1.6 mm board,
2, 4, 6 or 8 circuits, 3 A, 125 V). So J1-J6 and J9 are rows of pads at the board edge:

| Connector | Circuits | Housing to order (mate) | Pins |
|-----------|----------|-------------------------|------|
| J1-J4 | 6 | Molex 2008900106 | GPIOa, ADC, GND, +3V3, GPIOb, ADC (joystick ready) |
| J5 | 4 | Molex 2008900104 | GPIO16-19, SPI0 |
| J6 | 6 | Molex 2008900106 | GPIO10, 11 (UART1), GPIO26, 27, +3V3, GND |
| J9 | 6 | Molex 2008900106 | +5V_SW, GPIO28-31 (PWM), GND |

(Housings need Molex 200449 crimp terminals and a crimp tool; documents are in `resources/edgelock/docs/`.)

**Footprints are now the real geometry.** They come from Molex's own KiCad footprints (kept under
`resources/edgelock/kicad-vendor/`), checked against Molex's sales drawing 2008900206 sheet 2 ("PCB layout, contact
side", in `resources/edgelock/docs/drawings/`): contact pads 1.10 x 6.2 mm at 2.0 mm pitch, 0.9 mm in from the board
edge, outer notches 7.1 mm deep and 2.2 mm wide, two narrow notches 4.2 mm deep and 0.85 mm wide, and a 2.8 x 3.05 mm
latch window. `kicad/tools/make_edgelock_fp.py` regenerates `EdgeLock_<n>ckt_Molex20089001nn` for 2, 4, 6 and 8 circuits.
I removed solder paste from the pads (they are bare gold contact fingers) and marked the footprint board-only.

Things the footprint means for the board:
- **The footprint contains the board-edge cut-outs** (Edge.Cuts). Place it on the board edge and join the board outline to
  its end points. All seven connectors need straight edge, clear of corners and mounting holes. The drawing says the
  tie-bars of any traces should stay out of the contact zone.
- **Pads must be plated for repeated mating:** Molex "strongly recommends" a tin or equivalent plating process; ENIG
  (your spec) is a good choice. The mating zone on the PCB must be smooth and free of flux.
- **Board thickness 1.6 mm (housing 2008900106 / 2008900104), tolerance +/-0.16 mm including pads.** The 1.2 mm boards use the
  2008900206 family instead.
- **Manufacturability check needed.** JLCPCB's published minimum routed slot width is 1.0 mm and minimum inner-corner radius 0.5 mm;
  Molex's narrow notches are 0.85 mm wide. Run the Gerbers through JLCPCB's DFM check early. If they cannot cut 0.85 mm, the notches
  may need widening to 1.0 mm (the housing ribs they accept are not documented), or another fabricator is needed.
- **3D model:** STEP files are in `resources/edgelock/3d/`. They are centered on the same origin as the footprint but I have not
  confirmed their orientation; I will check with a render once the board exists.
- The mating housings (2008900106 / 2008900104) need Molex 200449 crimp terminals; they are not BOM parts on the board.

Each signal pin has a **100 ohm series resistor** from the GPIO net to the pad (protects the MCU from user wiring);
use 0 ohm to bypass. Power pins (+3V3, +5V_SW) are unfused: a shorted cable is limited only by the supply
(the +3V3 LDO and +5V_SW fuse).

## GPIO indicator LEDs (30)

470 ohm + white LED (OSRAM LW QH8G, 0402, Vf about 2.6 V) from the GPIO net to ground, about 1 mA. A white LED
suits 3.3 V logic: it does not conduct below about 2.4 V, so an input held by a weak pull-up still reads high
(a red or green LED would pull it down). Listed pins: GPIO0-7, 10, 11, 16-19, 26-33 and the ADC pins.

**ADC pins (GPIO40-47):** the LED is on like the others, but when routing, leave a narrow neck (0.15 mm) in the trace
between the GPIO net and that pin's 470 ohm resistor, with a small silkscreen "cut" mark across it. A knife cut there
disconnects the LED so the pin carries no extra load for precision analog readings. (There is no jumper part; the eight
solder jumpers JP1-JP8 were removed, `tools/remove_led_jumpers.py`.)

Pins without an indicator: GPIO8, 9, 24 (output enables), 12-15 and 22 (microSD), 20 and 21 (I2C), 23 (WS2812),
25 (user LED), 34 and 35 (PD alert, converter fault) and 36-39 (spare, on test points).

## Arduino and Pico sockets

- **Arduino Uno R3:** power 1x8, analog 1x6, digital 0-7 1x8, digital 8-13 1x10. D0 (RX) is GPIO1 and D1
  (TX) is GPIO0, the shield convention (resolves the old open question about the UART mapping). A0-A3 are the
  ADC pins GPIO40-43, A4/A5 are I2C. IOREF is +3V3 (tells shields this is a 3.3 V board). VIN is the board's +5V,
  not the raw input. AREF is joined to +3V3 only through an open solder jumper.
- **Pico:** two 1x20 sockets, 17.78 mm apart, in the Pico pinout. VBUS and VSYS are +5V; 3V3_EN and ADC_VREF are +3V3.
  GP26-28 are digital here (the RP2350B's ADC pins are GPIO40-47).
- The Pico sockets sit inside the Arduino pin pattern on the PCB so the two cannot be plugged in together. KiCad's
  `Module:Arduino_UNO_R3` footprint has the exact Uno pin positions; I can place the headers precisely when we do the PCB.
- The 1x10 Sullins socket is out of stock at JLCPCB (hence the old 8+6 workaround); these are normally hand-soldered
  through-hole parts, so any 1x10 2.54 mm female header will do.

## Board support

- **microSD** (Molex 5033981892) in SPI mode: GPIO12 DAT0, GPIO13 CS, GPIO14 CLK, GPIO15 CMD, GPIO22 card detect;
  10 kohm pull-ups on CMD, DAT0, CS and the unused DAT1/DAT2; 100 nF and 10 uF at the socket. The card-detect switch
  is on socket pins 9 and 10 (a plain switch, so polarity does not matter); the Molex drawing was unreachable, so confirm on the first board.
- **WS2812B-V5 on GPIO23** (100 ohm data resistor). The LED needs a logic high of 0.63 x VDD, which is 3.15 V at 5 V: a 3.3 V
  GPIO barely reaches it, with no margin. A series Schottky (1N5819HW) drops VDD to about 4.6 V, so the threshold
  falls to about 2.9 V. The earlier design had none of this.
- **Power LED and user LED** (GPIO25), 470 ohm white, about 1 mA each. The +5V_SW LED is on the outputs sheet.
- **I2C pull-ups:** 4.7 kohm to +3V3 on GPIO20 and GPIO21, one set for the whole bus.
- **Test points** (1.5 mm pads): +5V, +3V3, V_INPUT, 2x GND, +1V1, +3V3_AUX, +5V_SW, VBUS, SDA, SCL, USB D+/D-, and the spare GPIO36-39.
- **Mechanical:** 4 x M3 holes and 3 fiducials, positions to be set on the PCB (Pi HAT hole spacing if practical).

## Questions from the spec that are now answered

- GPIO10/11 as UART1 TX/RX: valid. The RP2350 datasheet lists UART1 TX/RX on GPIO10/11 as function 11
  (use `GPIO_FUNC_UART_AUX` in the SDK). GPIO26/27 offer the same.
- Arduino D0/D1: D0 = RX = GPIO1, D1 = TX = GPIO0.
