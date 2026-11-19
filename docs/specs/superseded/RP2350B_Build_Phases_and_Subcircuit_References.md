# RP2350B Dev Board — Phased Build Guide & Subcircuit References

The goal: build each hierarchical sheet as a self-contained, proven subcircuit. Validate the power supply before touching the MCU. Validate the MCU core before adding peripherals. You won't be designing from scratch — every subcircuit here has a reference design you can follow closely.

---

## Phase 1: Power Supply (Do This First — Validate Independently)

**Why first:** The power supply is the foundation everything else depends on. Getting it right before designing the MCU circuitry means one less variable when boards come back.

### 1A — Input Protection (Sheet 3 partial)
**Circuit:** 3× SS54 Schottky OR-ing diodes, SMAJ28CA TVS, 1206L500 polyfuse

This is simple enough to draw from the datasheet alone. No reference design needed — just follow the OR-ing diode topology in your spec. Place D1–D3 with cathodes tied together to form V_INPUT.

---

### 1B — TPS54531 Buck Converter (Sheet 3)
**Circuit:** 5V @ 5A from V_INPUT (5–28V)

**Best reference: TI WEBENCH Power Designer**
- Go to: https://webench.ti.com/power-designer/
- Select the TPS54531
- Enter: Vin = 5–28V, Vout = 5V, Iout = 5A
- WEBENCH will calculate exact component values, suggest part numbers, and show efficiency curves
- **Download the schematic** — it gives you a ready-to-use design

**Also check:**
- TPS54531 datasheet "Typical Application" section (page 2) — matches your spec almost exactly
- TI application note SLVA932 — explains the feedback resistor calculation

**Key things WEBENCH will confirm:**
- L2 inductance (likely 22µH — matches your spec)
- C_IN (22µF), C_OUT (47µF) values
- Feedback resistors for 5V output

---

### 1C — AP2112K LDOs (Sheet 3)
**Circuit:** Two instances — 3.3V_AUX (always-on) and 3.3V_MAIN

The AP2112K is a simple 3-pin LDO. The typical application in the datasheet is exactly what you need: 10µF in, 10µF out, done.

**Reference:** AP2112K datasheet Figure 1 (Diodes Inc) — it's a single-page application circuit.

---

## Phase 2: RP2350B Core (The Heart)

Don't start this phase until Phase 1 is validated.

### 2A — RP2350B + Decoupling (Sheet 5)
**The definitive reference: "Hardware Design with RP2350"**
- Download from: https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- Section 2 covers every IOVDD/DVDD pin with exact decoupling requirements
- This document was written specifically so people don't have to guess

**Also invaluable: Raspberry Pi Pico 2 reference schematic**
- Download from: https://datasheets.raspberrypi.com/pico/pico-2-r4-schematics.pdf
- This is the official RP2350B reference board — completely open source
- Every decoupling cap, every power pin, every pull-up is shown
- KiCad source files available at: https://datasheets.raspberrypi.com/pico/RPi-PicoW-PUBLIC-20220607.zip (check raspberrypi.com for RP2350 version)

---

### 2B — Internal VREG Circuit (Sheet 5, critical)
**Same reference:** Hardware Design with RP2350, Section 2.2

The exact circuit (L1, C6, C7, C9, R3) is shown in the official doc with placement guidance. Your spec already captures the critical details — the inductor orientation note is correct and important.

**Do not improvise this circuit.** Copy the reference layout exactly.

---

### 2C — Crystal Oscillator (Sheet 5, critical)
**Reference:** Hardware Design with RP2350, Section 2.3

The Abracon ABM8-272-T3 at 12MHz with 15pF load caps and 1kΩ series resistor is already specified. The hardware design guide shows the exact schematic and layout rules.

---

### 2D — W25Q512 Flash Memory (Sheet 6)
**Reference:**
- Winbond W25Q512JV datasheet — "Standard Application" shows the QSPI connection
- Pico 2 schematic (above) uses the same flash family — check their hookup

Simple circuit: VCC decoupling (100nF close), QSPI_SS pull-up (10kΩ to 3.3V), /HOLD and /WP tied high via 10kΩ if not used.

---

### 2E — USB Differential Pair + Termination (Sheet 2/5)
**Reference:** Hardware Design with RP2350, Section 2.4

27Ω series resistors on D+ and D− near the RP2350B pins. Impedance-controlled traces (90Ω differential) on the PCB — your spec already has the exact geometry (0.8mm wide, 0.15mm spacing on 1.6mm FR-4).

---

## Phase 3: System Peripherals

### 3A — STUSB4500 USB-C PD Controller (Sheet 2)
**Reference:**
- ST application note AN5410: "STUSB4500 software programming guide"
- STEVAL-ISC005V1 evaluation board schematic (free from ST's website — search "STEVAL-ISC005V1")
- SparkFun STUSB4500 breakout board: https://github.com/sparkfun/SparkFun_STUSB4500 — open source KiCad schematic, excellent reference

**Key hookup points:**
- I2C address: 0x28 (hardwired)
- ATTACH pin → connect to VBUS detect
- FLT_N → GPIO for fault detection (optional but useful)
- RESET via RC circuit on power-on

**Important:** The STUSB4500 has NVM (non-volatile memory) that stores the PDO profile. You configure it via I2C once and it remembers. SparkFun's Arduino library makes this straightforward.

---

### 3B — INA219 Current Sensors (Sheet 4)
**Reference:**
- TI INA219 datasheet "Typical Application" — it's a 4-page hookup
- Adafruit INA219 breakout (open source): https://github.com/adafruit/Adafruit-INA219-Current-Sensor-PCB

**Your config:**
- R_SHUNT = 0.05Ω (0.1% tolerance, 2W rated)
- INA219 @ 0x40 monitors J7 (5V output)
- INA219 @ 0x41 monitors J8 (variable output)
- Address set by A0/A1 pins: 0x40 = both low, 0x41 = A0 high

---

### 3C — Smart Output MOSFETs + Polyfuses (Sheet 4)
P-channel MOSFET switch controlled by GPIO. Use the Si2305 or similar P-MOSFET in SOT-23.

**Reference:** Any "high-side P-MOSFET switch" application note. TI's SLVA598 is a good one. The key is the gate drive: GPIO → NPN transistor (or N-MOSFET) → P-MOSFET gate for logic-level control.

---

### 3D — SD Card SPI Interface (Sheet 10)
**Reference:**
- Adafruit SD breakout (open source KiCad): https://github.com/adafruit/Adafruit-SD-Card-PCB
- The key details: 10kΩ pull-ups on all DAT + CMD lines (SD card spec requirement)

---

### 3E — WS2812B RGB LED (Sheet 10)
Single NeoPixel. 100Ω series resistor on data line, 100nF bypass cap on power. Standard hookup — any Adafruit NeoPixel schematic works.

---

## Phase 4: Expansion Headers

### 4A — EdgeLock Connectors + GPIO LEDs (Sheets 7–8)
Draw one connector with its LED circuit (330Ω → LED → 100Ω → pin), then copy it 47 more times. Time-consuming but not technically complex.

**Tip:** In KiCad, build one LED indicator as a hierarchical sub-sheet or a reusable block, then instantiate it. Saves a lot of repetitive work.

---

### 4B — Arduino Shield Headers (Sheet 9)
The KiCad connector library includes standard Arduino Uno R3 shield footprints. Search for `Connector_Arduino_Uno_R3` in KiCad's symbol library — it already exists as a matched set.

**Pin mapping is already solved** in your spec. The firmware side uses Earle Philhower's arduino-pico core, which supports custom board variants. You'll define a `pins_arduino.h` file mapping your GPIOs to Arduino pin numbers — this is a ~50-line text file, not a complex task.

**Compatible shields to watch out for:**
- Shields requiring 5V logic (most modern shields are 3.3V tolerant, but some older ones aren't — RP2350B is 3.3V only)
- Shields using Timer1/Timer2 (AVR-specific, won't work) — most modern shields avoid this

---

### 4C — SWD Debug Connector (Sheet 6)
3-pin JST-SH: SWCLK, GND, SWDIO. Dead simple — just connect to the RP2350B's dedicated SWD pins.

---

## Recommended KiCad Workflow

1. **Start with hierarchical sheets** — your 10-sheet plan is correct. Create all sheet stubs first so the structure is in place.
2. **Sheet 3 first** (power) → validate on breadboard or with a quick test board if possible
3. **Sheet 5 next** (RP2350B core) → the Pico 2 schematic is your cheat sheet
4. **Fill in the rest** in any order once core is solid
5. **Symbols/footprints:** Most components exist in KiCad's built-in library. For anything missing, check SnapEDA (snapeda.com) or Ultra Librarian (ultralibrarian.com) — both offer free KiCad exports.

---

## Key Downloads to Have Open While Working

| Resource | URL |
|----------|-----|
| Hardware Design with RP2350 | https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf |
| Pico 2 Reference Schematic | https://datasheets.raspberrypi.com/pico/pico-2-r4-schematics.pdf |
| TI WEBENCH | https://webench.ti.com/power-designer/ |
| STUSB4500 App Note AN5410 | Search "AN5410" on st.com |
| SparkFun STUSB4500 KiCad | https://github.com/sparkfun/SparkFun_STUSB4500 |
| Adafruit INA219 KiCad | https://github.com/adafruit/Adafruit-INA219-Current-Sensor-PCB |
| SnapEDA (symbols/footprints) | https://www.snapeda.com |

---

*Added: 2026-03-19*
