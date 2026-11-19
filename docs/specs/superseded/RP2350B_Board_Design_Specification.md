# RP2350B Museum/Maker Development Board
## Complete Design Specification

**Designer:** Clark Planetarium  
**Date:** 2026-02-04  
**MCU:** RP2350B (QFN-80, 48 GPIO, 8 ADC)  
**Board Size:** 120mm Ã— 90mm  
**PCB:** 2-layer FR-4, 1.6mm, ENIG finish

---

## POWER ARCHITECTURE

### Power Input (Auto-Sensing OR-ing)
```
USB-C PD (5-20V, up to 3A) â”€â”€[D1: SS54]â”€â”€â”
                                          â”‚
Barrel Jack (6-28V, 5A) â”€â”€â”€â”€[D2: SS54]â”€â”€â”€â”œâ”€â”€â†’ V_INPUT
                                          â”‚    â”œâ”€â†’ TPS54531 Buck
Screw Terminal (6-28V, 5A) â”€[D3: SS54]â”€â”€â”€â”˜    â””â”€â†’ J8 output
```

**Protection:**
- D1-D3: SS54 Schottky diodes (OR-ing, 5A, 40V)
- D4: SMAJ28CA TVS diode (transient protection)
- F1: 1206L500/33WR polyfuse (5A overcurrent)

### Power Conversion
```
V_INPUT (5-28V)
    â†“
[TPS54531 Buck] â†’ 5V @ 5A
    â”œâ”€â†’ [AP2112K #1] â†’ 3.3V_AUX @ 100mA (STUSB4500 always-on)
    â”œâ”€â†’ [AP2112K #2] â†’ 3.3V_MAIN @ 600mA (RP2350B + peripherals)
    â”œâ”€â†’ [RP2350B VREG_VIN] â†’ Internal regulator â†’ 1.1V DVDD
    â”œâ”€â†’ [J7 MOSFET] â†’ 5V @ 3A (GPIO8 switched)
    â””â”€â†’ [GPIO24 MOSFET] â†’ 5V_SW @ 3A (motors/servos)
```

### Smart Outputs with Monitoring

**J7: 5V Smart Output**
```
5V rail â†’ [INA219 @ 0x40] â†’ [P-MOSFET] â†’ [Polyfuse 3A] â†’ J7 connector
                               â†‘                             â†“
                             GPIO8 enable              [SS54 flyback]
                                                             â†“
                                                       [10kÎ© bleeder]
                                                             â†“
                                                            GND
```
- Voltage: 5V (from buck)
- Current: 3A max
- Monitoring: Voltage + current via I2C
- Control: GPIO8 (software on/off)
- Protection: Flyback diode + bleeder resistor for motor/inductive loads

**J8: Variable Voltage Smart Output**
```
V_INPUT â†’ [INA219 @ 0x41] â†’ [P-MOSFET] â†’ [Polyfuse 3A] â†’ J8 connector
                               â†‘                             â†“
                             GPIO9 enable              [SS54 flyback]
                                                             â†“
                                                       [10kÎ© bleeder]
                                                             â†“
                                                            GND
```
- Voltage: 5-28V (matches input source)
- Current: 3A max
- Monitoring: Voltage + current via I2C
- Control: GPIO9 (software on/off)
- Use: Motors, solenoids requiring input voltage
- Protection: Flyback diode + bleeder resistor for inductive kickback

---

## COMPLETE GPIO ALLOCATION

### Reserved/Internal (8 signals)
| GPIO | Function | Description |
|------|----------|-------------|
| GPIO20 | I2C0 SDA | STUSB4500 + INA219s + Arduino I2C |
| GPIO21 | I2C0 SCL | Shared I2C bus |
| GPIO23 | WS2812B | Status RGB LED |
| GPIO24 | 5V_SW Enable | MOSFET gate for servo power |
| GPIO25 | User LED | Pico-compatible onboard LED |
| GPIO8 | J7 Enable | 5V output MOSFET control |
| GPIO9 | J8 Enable | Variable voltage output control |
| SWCLK | SWD Clock | Debug interface |
| SWDIO | SWD Data | Debug interface |
| RUN | Reset | Reset button |

### EdgeLock Connectors (J1-J4: Joystick Ready)

**J1: 6-pin Molex 502598-0603**
```
Pin 1: GPIO0
Pin 2: GPIO40 (ADC0)
Pin 3: GND
Pin 4: 3.3V
Pin 5: GPIO1
Pin 6: GPIO41 (ADC1)
```
*Typical use: 2-axis joystick (X/Y) + 2 buttons*

**J2: 6-pin Molex 502598-0603**
```
Pin 1: GPIO2
Pin 2: GPIO42 (ADC2)
Pin 3: GND
Pin 4: 3.3V
Pin 5: GPIO3
Pin 6: GPIO43 (ADC3)
```
*Typical use: 2-axis joystick (X/Y) + 2 buttons*

**J3: 6-pin Molex 502598-0603**
```
Pin 1: GPIO4
Pin 2: GPIO44 (ADC4)
Pin 3: GND
Pin 4: 3.3V
Pin 5: GPIO5
Pin 6: GPIO45 (ADC5)
```
*Typical use: 2-axis joystick (X/Y) + 2 buttons*

**J4: 6-pin Molex 502598-0603**
```
Pin 1: GPIO6
Pin 2: GPIO46 (ADC6)
Pin 3: GND
Pin 4: 3.3V
Pin 5: GPIO7
Pin 6: GPIO47 (ADC7)
```
*Typical use: 2-axis joystick (X/Y) + 2 buttons*

### Additional EdgeLock Connectors

**J5: SPI0 (4-pin) - Shared with Arduino**
```
Pin 1: GPIO16 (SPI0 MISO)
Pin 2: GPIO17 (SPI0 CS)
Pin 3: GPIO18 (SPI0 SCK)
Pin 4: GPIO19 (SPI0 MOSI)
```

**J6: UART1 (6-pin)**
```
Pin 1: GPIO10 (UART1 TX)
Pin 2: GPIO11 (UART1 RX)
Pin 3: GPIO26 (Enable/Reset)
Pin 4: GPIO27 (Status/IRQ)
Pin 5: 3.3V
Pin 6: GND
```
*Use: Serial modules, Zigbee, GPS*

**J9: PWM/Motor (6-pin)**
```
Pin 1: 5V_SW
Pin 2: GPIO28 (PWM)
Pin 3: GPIO29 (PWM)
Pin 4: GPIO30 (PWM)
Pin 5: GPIO31 (PWM)
Pin 6: GND
```
*Use: Servo motors, DC motors via drivers*

**J10: SWD Debug (3-pin JST-SH)**
```
Pin 1: SWCLK
Pin 2: GND
Pin 3: SWDIO
```

### Smart Power Outputs

**J7: 5V @ 3A (2-pin screw terminal or barrel jack)**
```
Pin 1: +5V (INA219 monitored, GPIO8 switched)
Pin 2: GND
```

**J8: V_INPUT @ 3A (2-pin screw terminal or barrel jack)**
```
Pin 1: +V_INPUT (INA219 monitored, GPIO9 switched)
Pin 2: GND
```

### SD Card (SPI1)
| Signal | GPIO | Pin |
|--------|------|-----|
| MISO | GPIO12 | DAT0 |
| CS | GPIO13 | DAT3/CD |
| SCK | GPIO14 | CLK |
| MOSI | GPIO15 | CMD |
| Card Detect | GPIO22 | CD (optional) |

**Support:** 10kÎ© pullups on all DAT + CMD lines (SD spec)  
**Socket:** Molex 503398-1892 or GCT MEM2061-01-188-00-A

### Arduino Shield Headers (Dual SMD+THT Footprint)

**Power Header (1Ã—8 pin)**
```
Pin 1: NC
Pin 2: IOREF (3.3V)
Pin 3: RESET (RUN)
Pin 4: 3.3V
Pin 5: 5V
Pin 6: GND
Pin 7: GND
Pin 8: VIN (5V)
```

**Analog Header (1Ã—6 pin)**
```
Pin 1: A0 â†’ GPIO40 (ADC0) [shared with J1]
Pin 2: A1 â†’ GPIO41 (ADC1) [shared with J1]
Pin 3: A2 â†’ GPIO42 (ADC2) [shared with J2]
Pin 4: A3 â†’ GPIO43 (ADC3) [shared with J2]
Pin 5: A4/SDA â†’ GPIO20 (I2C)
Pin 6: A5/SCL â†’ GPIO21 (I2C)
```

**Digital 0-7 (1Ã—8 pin)**
```
Pin 1: D0/RX â†’ GPIO0 (UART0) [shared with J1]
Pin 2: D1/TX â†’ GPIO1 (UART0) [shared with J1]
Pin 3: D2 â†’ GPIO2 [shared with J2]
Pin 4: D3 (PWM) â†’ GPIO3 [shared with J2]
Pin 5: D4 â†’ GPIO4 [shared with J3]
Pin 6: D5 (PWM) â†’ GPIO5 [shared with J3]
Pin 7: D6 (PWM) â†’ GPIO6 [shared with J4]
Pin 8: D7 â†’ GPIO7 [shared with J4]
```

**Digital 8-13 (1Ã—10 pin)**
```
Pin 1: D8 â†’ GPIO32
Pin 2: D9 (PWM) â†’ GPIO33
Pin 3: D10/SS (PWM) â†’ GPIO17 (SPI0 CS)
Pin 4: D11/MOSI (PWM) â†’ GPIO19 (SPI0 MOSI)
Pin 5: D12/MISO â†’ GPIO16 (SPI0 MISO)
Pin 6: D13/SCK â†’ GPIO18 (SPI0 SCK)
Pin 7: GND
Pin 8: AREF (3.3V via jumper)
Pin 9: SDA â†’ GPIO20
Pin 10: SCL â†’ GPIO21
```

**âš ï¸ Arduino Sharing Conflicts:**
- GPIO0-7: EdgeLock J1-J4 OR Arduino D0-D7
- GPIO16-19: EdgeLock J5 OR Arduino SPI (can share same bus)
- GPIO32-33: Expansion OR Arduino D8-D9
- GPIO40-43: EdgeLock J1-J2 OR Arduino A0-A3

### Raspberry Pi HAT Header (40-pin, footprint only)
- **Not populated by default**
- Footprint present for future daughter boards
- All GPIO accessible via EdgeLock + expansion
- Mount holes compatible with Pi HAT spacing

### Expansion GPIO Available
- GPIO34-39 (6 pins)
- Available for test points or expansion header

---

## PER-GPIO LED INDICATORS

**Circuit per GPIO:**
```
GPIO â†’ [330Î©] â†’ [LED] â†’ [100Î©] â†’ Connector pin
```

**Specifications:**
- Total resistance: 430Î©
- LED current: ~5mA @ 3.3V
- Total count: 48Ã— LEDs

**Color Coding:**
| Color | Function |
|-------|----------|
| Green | Digital GPIO |
| Yellow | ADC inputs |
| Blue | I2C (SDA, SCL) |
| Cyan | SPI signals |
| Orange | UART signals |
| Red | Power control |

**Optional:** Solder jumpers on ADC pins (GPIO40-47) to bypass resistors for precision analog measurements.

---

## CRITICAL COMPONENTS

### Microcontroller
- **Part:** RP2350B
- **Package:** QFN-80 (10mm Ã— 10mm)
- **CPU:** Dual ARM Cortex-M33 @ 150MHz (or RISC-V Hazard3)
- **RAM:** 520KB SRAM
- **GPIO:** 48 pins (3.3V logic)
- **ADC:** 8Ã— 12-bit (GPIO40-47)

### Flash Memory
- **Part:** W25Q512JVSSIQ (Winbond)
- **Size:** 64MB
- **Interface:** Quad SPI
- **Speed:** 133MHz max
- **Package:** SOIC-8 or WSON-8

**Flash Partitioning:**
```
0-2MB:    Firmware (XIP execute-in-place)
2-8MB:    USB Mass Storage (user-accessible)
8-64MB:   Data storage / assets / logs
```

### Crystal Oscillator (CRITICAL - Follow Exactly)
- **Part:** Abracon ABM8-272-T3 (required)
- **Frequency:** 12MHz
- **Load capacitance:** 18pF
- **Load caps:** 15pF (C3, C4)
- **Series resistor:** 1kÎ© (R2)
- **Critical:** Must use this exact part for stability

### USB-C Power Delivery
- **IC:** STUSB4500AQTR
- **Programmable:** Via I2C (GPIO20/21)
- **Voltages:** 5V, 9V, 12V, 15V, 20V
- **Default:** 12V @ 3A (software configurable)
- **Fallback:** 5V @ 3A if PD unavailable

### Power ICs
- **Buck:** TPS54531DDAR (5V @ 5A, 570kHz)
- **LDO #1:** AP2112K-3.3 (always-on for STUSB4500)
- **LDO #2:** AP2112K-3.3 (main 3.3V rail)
- **Current sensors:** 2Ã— INA219 (I2C 0x40, 0x41)

### Power Connectors
- **USB-C:** GCT USB4105 (data + PD)
- **Barrel:** PJ-102AH (5.5mm/2.1mm, center +, with switch)
- **Screw:** 2-position 5.08mm pitch

---

## CRITICAL LAYOUT REQUIREMENTS

### RP2350B Internal Regulator (MUST FOLLOW)
**Components:**
- L1: 3.3ÂµH Abracon AOTA-B201610S3R3-101-T (with polarity dot!)
- C6, C7, C9: 4.7ÂµF 0402
- R3: 33Î© 0402

**Layout rules:**
- Keep all within 10mm of RP2350B
- Star ground for VREG_PGND
- VREG_LX trace: short, wide, minimal inductance
- **Inductor orientation critical:** Magnetic field interference if wrong
- Follow reference layout exactly

### Crystal Oscillator (MUST FOLLOW)
- XIN/XOUT traces < 10mm total
- Ground plane directly underneath (layer 2)
- Guard ring around crystal (grounded)
- Keep-out zone: 5mm radius, no other signals
- Load caps: 15pF (accounts for ~3pF parasitic)

### RP2350B Decoupling
- 100nF ceramic per IOVDD/DVDD pin (within 5mm)
- Vias directly to ground plane
- Shared cap on pins 68-69 acceptable (space constraint)
- 4.7ÂµF bulk caps on opposite corners

### USB Differential Pair
- 90Î© differential impedance
- Trace width: 0.8mm, spacing: 0.15mm (1.6mm FR-4)
- Length matched within 5mm
- Solid ground plane underneath
- 27Î© series termination near RP2350B

### Power Supply Layout
- Large ground plane (layer 2)
- Wide power traces (20mil min for 5A)
- Buck SW node: short, thick
- Star ground at buck converter
- Input/output caps close to ICs

---

## PCB LAYOUT BEST PRACTICES

### General Principles

**Layer Stack (2-layer):**
```
Top Layer (Layer 1):    Components + Signal routing
Bottom Layer (Layer 2): Ground plane (mostly solid) + Power routing
```

**Ground plane coverage:** Aim for >80% copper on bottom layer. Only break for through-hole pads and vias.

---

### Power Supply Layout (CRITICAL - Do First)

**1. Buck Converter (TPS54531) - Highest Priority**

**Component placement order:**
```
1. U4 (TPS54531) - central position
2. Input cap (C_IN: 22ÂµF) - within 5mm of VIN pin
3. Output cap (C_OUT: 47ÂµF) - within 5mm of SW pin  
4. Inductor (L2: 22ÂµH) - within 10mm of SW pin
5. Bootstrap cap (C_BOOT: 100nF) - within 3mm of BOOT pin
6. Feedback resistors - within 10mm of FB pin
```

**Trace width requirements:**
- **VIN trace:** 40mil (1mm) minimum - carries input current
- **SW node:** 60mil (1.5mm) minimum, KEEP AS SHORT AS POSSIBLE (< 20mm)
- **VOUT (5V rail):** 40mil (1mm) minimum - distributes to entire board
- **GND return:** Wide pour, star ground at input cap

**Critical SW node routing:**
```
TPS54531 SW pin â†’ [short, thick, straight trace] â†’ L2 inductor
                                                    
âš ï¸ SW node is high-frequency switching (570kHz)
   - Radiates EMI if too long
   - Creates voltage spikes if high inductance
   - Route on TOP layer only (no vias)
   - Keep away from sensitive signals (USB, crystal, ADC)
```

**Ground strategy (star grounding):**
```
                [Input Cap GND]
                       â†“
                [TPS54531 PGND] â† Star point
                       â†“
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â†“              â†“              â†“
   [Output Cap]   [Inductor]   [Bottom GND plane]
```

**Layout checklist:**
- [ ] Input cap within 5mm of VIN/PGND
- [ ] Output cap within 5mm of SW/PGND  
- [ ] SW trace < 20mm, no vias, thick (60mil)
- [ ] Feedback network away from SW node
- [ ] Thermal pad soldered and viaed to GND (9 vias minimum)

---

**2. LDO Regulators (AP2112K) - Simple**

**Placement:**
- Close to loads they power
- LDO #1 near STUSB4500
- LDO #2 near RP2350B

**Decoupling:**
- Input: 10ÂµF within 5mm of VIN pin
- Output: 10ÂµF within 5mm of VOUT pin
- Both caps to GND via short, wide traces

**Trace width:**
- VIN: 20mil minimum
- VOUT: 20mil minimum (fan out to loads)

---

**3. Power Distribution**

**3.3V rail routing:**
```
LDO #2 output â†’ [wide trace, 30mil] â†’ Fan out to:
                                       â”œâ”€ RP2350B IOVDD pins
                                       â”œâ”€ Decoupling caps
                                       â”œâ”€ Flash memory
                                       â””â”€ Peripheral connectors
```

**Power plane strategy (bottom layer):**
- 3.3V pour in RP2350B area (don't mix with GND)
- 5V pour in connector area
- GND fills remaining space (majority of layer)

**Via stitching:**
- Place GND vias every 10-15mm around board perimeter
- Purpose: Tie top GND to bottom GND plane
- Reduces EMI, improves return paths

---

### RP2350B Core Layout (CRITICAL - Do Second)

**1. Internal Regulator (MUST FOLLOW EXACTLY)**

Reference the official layout in Hardware Design with RP2350 datasheet.

**Component placement (measured from RP2350B edge):**
```
     [RP2350B QFN-80]
            â†“
   Pin 63 (VREG_LX)
            â†“ (5mm max)
        [L1: 3.3ÂµH]
            â†“
   Pin 64 (VREG_VIN) â† (2mm) [C6: 4.7ÂµF]
            â†“
   Pin 65 (VREG_FB) â† (3mm) [R3: 33Î©] â†’ [C9: 4.7ÂµF] â†’ GND
            â†“
   Pin 62 (VREG_PGND) â† Star ground
            â†“
        [C7: 4.7ÂµF]
            â†“
          GND
```

**CRITICAL: L1 inductor orientation**
```
Correct orientation: Dot marking toward VREG_LX pin
  [RP2350B] â†’ [â—L1] â†’ [C7]
  
Wrong orientation: Creates magnetic interference with C7
  [RP2350B] â†’ [L1â—] â†’ [C7]  â† Don't do this!
```

**Layout rules:**
- All components within 10mm radius of RP2350B
- VREG_LX trace: 40mil wide, < 10mm long, no vias
- VREG_PGND: Star ground directly under regulator area
- C7 placement: Directly adjacent to L1 output, shortest path to GND
- R3 filtering: Creates RC network with C9, keep both close to FB pin
- Ground plane: Solid underneath entire regulator area

**Inductor footprint:**
- Use recommended footprint for AOTA-B201610S3R3-101-T
- Include polarity marking on silkscreen (dot = pin 1)
- Add note: "Inductor orientation critical - see datasheet"

---

**2. Crystal Oscillator (MUST FOLLOW EXACTLY)**

**Component placement:**
```
        [Y1: 12MHz Crystal]
              /        \
    [C3: 15pF]        [C4: 15pF]
         |                 |
         GND              GND
         
Distance from RP2350B: 5-10mm (close but not touching)
```

**Trace routing:**
```
RP2350B Pin XIN â†’ [R2: 1kÎ©] â†’ Crystal Pad 1
                               
RP2350B Pin XOUT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â†’ Crystal Pad 3

Total trace length XIN + XOUT: < 10mm combined
Trace width: 10-15mil (narrow is OK, they're low current)
Trace style: Straight, direct, no right angles
```

**Ground plane management:**
```
Bottom layer under crystal:
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚   GND PLANE     â”‚  â† Solid ground directly underneath
  â”‚    (no gaps)    â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Top layer around crystal:
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘ â”‚  â† Ground guard ring (grounded via)
  â”‚ â–‘             â–‘ â”‚
  â”‚ â–‘  [CRYSTAL]  â–‘ â”‚  â† 5mm keep-out zone
  â”‚ â–‘             â–‘ â”‚
  â”‚ â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘ â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Keep-out zone:**
- Radius: 5mm from crystal center
- No signals routed through this area
- No components (except C3, C4, R2)
- No vias (except for guard ring GND)

**Load capacitors:**
- C3, C4: Placed symmetrically on opposite sides of crystal
- Traces to GND: Short (< 5mm), wide (20mil), direct
- GND connection: Via to bottom plane (one via per cap is fine)

**Guard ring:**
- Trace: 20mil wide, surrounds crystal at 5mm distance
- Connected to GND via multiple vias (4-6 vias around perimeter)
- Purpose: Shields crystal from external noise

---

**3. Decoupling Capacitors (100nF ceramic)**

**Placement rules:**
```
For each IOVDD or DVDD pin:
  Pin â†’ [via] â†’ [100nF cap] â†’ [via] â†’ GND plane
         â†‘                      â†‘
    Keep < 5mm           Keep < 3mm
```

**Pin-by-pin strategy:**
```
RP2350B power pins (QFN-80):
  IOVDD: Pins 5, 15, 24, 29, 41, 50, 60, 76
  DVDD:  Pins 10, 32, 51
  
Each pin gets dedicated 100nF cap EXCEPT:
  Pins 68-69: Share one 100nF (space constrained)
```

**Via placement:**
- Power via (pin to cap): Place immediately next to pin
- GND via (cap to plane): Place immediately at cap GND pad
- Via size: 0.3mm drill, 0.6mm pad (standard)
- Multiple vias OK if space allows (lowers inductance)

**Bulk capacitors (4.7ÂµF):**
```
Place at opposite corners of RP2350B:
  
    [4.7ÂµF]              [4.7ÂµF]
        â†“                    â†“
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚                             â”‚
  â”‚        RP2350B              â”‚
  â”‚                             â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â†‘                    â†‘
    [4.7ÂµF]              [4.7ÂµF]
```

Purpose: Provides bulk charge storage, different frequency response than 100nF

---

### Flash Memory Layout

**Placement:**
- Within 20mm of RP2350B
- Adjacent to QSPI pins (right side of chip)
- Oriented to minimize trace crossings

**QSPI signal routing:**
```
RP2350B â†’ W25Q512JVS
  
Signals: QSPI_SS, QSPI_SCLK, QSPI_SD0-3
  
Routing strategy:
  - Keep traces short (< 30mm)
  - Route as a group (similar lengths)
  - Avoid crossing high-frequency signals
  - No need for impedance control (not differential)
  - Trace width: 10-15mil is fine
```

**Length matching:**
- QSPI is not high-speed enough to require strict matching
- Keep within 10mm of each other (rough matching)
- SD0-SD3 should be similar length (within 5mm)
- SCLK can be slightly different

**Decoupling:**
- 100nF cap within 5mm of flash VCC pin
- Via directly to GND plane

---

### USB Differential Pair (CRITICAL)

**Impedance requirements:**
- Differential impedance: 90Î© Â±10%
- Single-ended impedance: 45Î© per trace

**Trace geometry (for 1.6mm FR-4):**
```
         8mil (0.2mm) spacing
         â†â†’
    ___________    ___________
   |  USB D+  |  |  USB D-  |   â† 31mil (0.8mm) width each
   â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾    â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾â€¾
        â†•
   GND plane (solid, no gaps)
```

**Routing rules:**
- Route on TOP layer only (no layer changes)
- Keep parallel - constant spacing throughout
- Length match within 5mm (preferably 2mm)
- No vias if possible (if required, use both traces)
- No 90Â° angles - use 45Â° or curved
- Avoid crossing other signals (especially clocks)
- Keep 20mil clearance from other traces

**Termination:**
```
RP2350B USB_DP (Pin 67) â†’ [27Î©] â†’ USB-C D+ pin
RP2350B USB_DM (Pin 66) â†’ [27Î©] â†’ USB-C D- pin

Resistor placement: Within 5mm of RP2350B pins
Package: 0402 (keeps trace length short)
```

**Ground plane:**
- Solid pour directly under USB traces (no gaps)
- Extend 3Ã— trace width on each side
- No other signals in GND plane cutout area

**Keep away from:**
- Crystal oscillator (15mm minimum)
- Buck converter SW node (20mm minimum)  
- High-frequency clocks (10mm minimum)

---

### SD Card Interface (SPI1)

**Not critical** - SPI is relatively low speed

**Routing:**
- Keep traces < 50mm
- Rough length matching (within 10mm)
- Group signals together
- Trace width: 10-15mil

**Pullup resistors:**
- 10kÎ© on all DAT lines and CMD
- Place close to SD socket (within 10mm)
- Purpose: Required by SD card specification

---

### EdgeLock Connectors

**Placement:**
- Distribute around board edges
- Group by function (all joystick connectors together)
- Leave 5mm clearance from corners
- Allow space for cable bend radius

**Trace routing:**
- GPIO traces: 10-15mil width (not critical)
- 3.3V power: 20mil width (higher current)
- GND: 20mil width or connect to plane

**Per-GPIO LED circuits:**
```
GPIO â†’ [330Î©] â†’ [LED] â†’ [100Î©] â†’ Connector pin
         â†‘                â†‘
    SMD 0402         SMD 0603
    
Placement: Near connector (makes routing easier)
```

**Bypass jumpers (ADC pins):**
```
For GPIO40-47 (ADC inputs):

         [330Î©]     [100Î©]
GPIO â†’ â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”¬â”€â”€â†’ Connector
            â”‚    â”‚      â”‚
          [Jumper pads] â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            
If jumpered: Bypasses series resistors for precision ADC
```

---

### I2C Bus Layout

**Devices on bus:**
- STUSB4500 (0x28)
- INA219 #1 (0x40)
- INA219 #2 (0x41)
- Arduino I2C header
- Optional external sensors

**Routing:**
- Trace width: 10-15mil
- Length not critical (I2C is slow, 400kHz max)
- Route together (easier to follow)
- Pull-up resistors: 4.7kÎ© to 3.3V
  - Place centrally on bus (near RP2350B)
  - One set for entire bus (don't duplicate)

**Bus topology:**
```
                 [4.7kÎ©]  [4.7kÎ©]
                    â†“        â†“
                  SDA      SCL
                    â”‚        â”‚
    RP2350B â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€ STUSB4500
                    â”‚        â”‚
                    â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”¤â”€â”€â”€â”€ INA219 #1
                    â”‚        â”‚
                    â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”¤â”€â”€â”€â”€ INA219 #2
                    â”‚        â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€ Arduino header

Star topology (all branches from center) preferred over daisy-chain
```

---

### Thermal Management

**RP2350B:**
- Center thermal pad MUST be soldered
- Minimum 9 vias (0.3mm drill) in thermal pad
- Vias connect to bottom GND plane (acts as heatsink)
- Optional: Bottom side copper pour under chip

**TPS54531 Buck Converter:**
- Thermal pad to GND plane via 9+ vias
- Large copper pour on bottom under IC
- Consider: Top-side copper pour around IC (tied to GND)

**MOSFETs (Q1, Q2 for J7/J8):**
- Connect drain pad to output trace (wide copper)
- SOT-23 has good thermal performance if pad is soldered

---

### High-Current Trace Width Guidelines

**Current capacity for 1oz copper, 10Â°C rise:**
```
10mil (0.25mm):  0.5A
20mil (0.50mm):  1.0A
40mil (1.00mm):  2.0A
60mil (1.50mm):  3.0A
80mil (2.00mm):  4.0A
100mil (2.50mm): 5.0A
```

**Recommended trace widths for your design:**
```
Signal Type           Current    Trace Width
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
USB VBUS              2-3A       40mil
Buck input (V_INPUT)  3-5A       40-60mil
Buck output (5V)      5A         60-80mil
Buck SW node          5A peak    60mil (keep short!)
3.3V rail             1A         30mil
GPIO signals          < 20mA     10mil
I2C/SPI/UART          < 10mA     10mil
J7/J8 outputs         3A         40mil
```

**Thermal vias for high current:**
- Use thermal vias to connect top traces to bottom plane
- Spacing: Every 5-10mm along trace
- Lowers resistance and improves heat spreading

---

### Design Rule Recommendations

**PCB manufacturer capabilities (standard 2-layer):**
```
Minimum trace width:      6mil (0.15mm)
Minimum trace spacing:    6mil (0.15mm)
Minimum drill size:       0.3mm (12mil)
Minimum annular ring:     4mil (0.1mm)
Copper weight:            1oz (35Âµm)
```

**Your design targets:**
```
Default trace width:      10mil (general signals)
Default trace spacing:    10mil (general clearance)
Power trace width:        40mil (3A+)
Critical spacing:         15mil (USB, crystal)
Via size:                 0.3mm drill / 0.6mm pad
```

---

### EMI/EMC Best Practices

**1. Ground plane integrity**
- Keep bottom GND plane >80% solid
- Don't split plane (creates return path issues)
- Use GND vias liberally (every 10-15mm)

**2. High-frequency signal containment**
- Buck SW node: Keep short, thick, no loops
- USB D+/D-: Solid GND underneath, no gaps
- Crystal: Guard ring + solid GND underneath

**3. Signal return paths**
```
Every signal has a return current:
  
    â”€â”€â”€â”€â†’ Signal trace â”€â”€â”€â”€â†’
       â†‘                 â†“
    â†â”€â”€ GND plane return â†â”€â”€
    
If GND plane is broken, return current takes long path
â†’ Creates loop antenna â†’ Radiates EMI
```

**4. Decoupling strategy**
- Place caps as close as possible (minimizes loop area)
- Via to GND immediately at cap (short return path)
- Multiple capacitors of different values (0.1ÂµF, 4.7ÂµF, 10ÂµF)
  - Different values resonate at different frequencies
  - Covers wider frequency range

**5. Keep-out zones**
```
Crystal:          5mm radius, no signals
Buck SW node:     10mm radius, no sensitive signals  
USB traces:       3mm on each side, no other signals
```

---

### Component Placement Strategy

**Order of placement:**
```
1. RP2350B (center of board)
2. Buck converter (away from sensitive areas)
3. Crystal (near RP2350B, quiet area)
4. Flash memory (near RP2350B QSPI pins)
5. USB-C connector (board edge)
6. Power input connectors (board edge, away from USB)
7. LDO regulators (near their loads)
8. INA219 sensors (near J7/J8 outputs)
9. EdgeLock connectors (around perimeter)
10. Arduino headers (one side of board)
11. Decoupling caps (last, squeezed around ICs)
```

**Zones:**
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  NOISY: Buck converter, MOSFETs     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  DIGITAL: RP2350B, Flash, Logic     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  SENSITIVE: Crystal, USB, ADC refs  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  I/O: Connectors around perimeter   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Keep zones separated physically on board
```

---

### Silkscreen Best Practices

**Component labels:**
- Place reference designators near components (R1, C1, U1)
- Make readable from 2 directions (top and side)
- Use consistent size (1mm height minimum)

**Polarity markings:**
- Diodes: Add cathode bar
- LEDs: Add anode (+) marker
- Polarized caps: Add (+) marker
- Connectors: Pin 1 marker (square pad + "1")
- Inductor L1: Add dot for pin 1 orientation

**Functional labels:**
```
Power inputs:  "USB-C 5-20V" / "DC IN 6-28V"
Outputs:       "J7: 5V @ 3A" / "J8: Variable"
Connectors:    "SPI" / "UART" / "I2C" / "PWM"
LEDs:          "Power" / "User" / "Status"
Buttons:       "BOOTSEL" / "RESET"
```

**Warnings:**
- "âš  3.3V LOGIC ONLY"
- "âš  Observe polarity: + left, - right"
- "âš¡ Max 28V input"

**Test points:**
- Label critical voltages: "3.3V" / "5V" / "V_IN"
- Label critical signals: "SDA" / "SCL" / "USB_D+"

---

### Design Verification Checklist

**Power:**
- [ ] Buck converter layout matches reference design
- [ ] SW node < 20mm, thick trace, no vias
- [ ] Input cap within 5mm of VIN
- [ ] Output cap within 5mm of SW
- [ ] Star ground at buck converter
- [ ] All power traces adequately sized for current

**RP2350B:**
- [ ] Internal regulator layout follows datasheet exactly
- [ ] L1 inductor oriented correctly (dot marking documented)
- [ ] All components within 10mm of chip
- [ ] 100nF decoupling on every power pin (except 68-69)
- [ ] 4.7ÂµF bulk caps at corners
- [ ] Thermal pad has 9+ vias to GND plane

**Crystal:**
- [ ] Total trace length < 10mm
- [ ] Ground plane solid underneath
- [ ] Guard ring present and grounded
- [ ] 5mm keep-out zone maintained
- [ ] Load caps (15pF) placed symmetrically
- [ ] Series resistor (1kÎ©) present

**USB:**
- [ ] Differential pair 90Î© impedance (0.8mm width, 0.15mm spacing)
- [ ] Length matched within 5mm
- [ ] Solid GND plane underneath
- [ ] 27Î© termination resistors within 5mm of RP2350B
- [ ] No vias in differential pair
- [ ] Keep 20mm from buck SW node

**Flash:**
- [ ] Within 20mm of RP2350B
- [ ] QSPI traces < 30mm
- [ ] 100nF decoupling cap present
- [ ] Pull-up on SS line (if required by design)

**General:**
- [ ] Ground plane >80% coverage on bottom layer
- [ ] GND stitching vias every 10-15mm
- [ ] High-current traces adequately sized
- [ ] All ICs have thermal pad vias (if applicable)
- [ ] Silkscreen labels present and readable
- [ ] Polarity markings on all polarized components
- [ ] Pin 1 markers on all connectors

---

## DESIGN FOR MANUFACTURABILITY (DFM)

**Assembly considerations:**

**1. Component orientation:**
- Orient similar parts same direction when possible
- Makes pick-and-place faster
- Reduces errors

**2. Fiducial markers:**
- Add 3Ã— fiducial markers (circles, 1mm diameter, bare copper)
- Placement: Opposite corners + center of board
- Purpose: Pick-and-place machine alignment

**3. Panelization:**
- Add mouse bites or V-score lines if ordering panels
- Leave 5mm border around board edge
- Add tooling holes if required by manufacturer

**4. Paste stencil:**
- Use default 1:1 ratio for most pads
- Reduce paste for thermal pads (80%) to avoid bridging
- QFN thermal pad: Use cross-hatch pattern (not solid)

**5. Test points:**
```
Add test points for critical signals:
  - 3.3V rail
  - 5V rail
  - V_INPUT
  - GND (multiple locations)
  - I2C (SDA, SCL)
  - USB D+, D-
  
Test point style: Via with no soldermask opening (exposed copper)
Diameter: 0.8-1.0mm
```

---

## DESIGN FOR TESTING (DFT)

**Bring-up procedure:**

**1. Visual inspection (before power):**
- Check component orientation (especially L1 inductor)
- Check for solder bridges (especially QFN, USB-C)
- Check polarity of diodes, LEDs, caps

**2. Power supply test (multimeter):**
```
Step 1: Connect 12V to barrel jack (NO USB YET)
  - Measure V_INPUT: Should be ~12V
  - Measure 5V rail: Should be 4.9-5.1V
  - Measure 3.3V rail: Should be 3.2-3.4V
  
Step 2: Connect USB-C (WITHOUT barrel)
  - Measure V_INPUT: Should be ~5V (or PD voltage)
  - Measure 5V rail: Should be 4.9-5.1V
  - Measure 3.3V rail: Should be 3.2-3.4V
```

**3. Current consumption (before programming):**
```
Expected current at 12V input (no load):
  - Buck converter quiescent: ~10mA
  - RP2350B (no code): ~50mA
  - Total: <100mA
  
If >200mA: Something is wrong (short circuit)
```

**4. Programming test:**
- Hold BOOTSEL button
- Press RESET button
- Release RESET
- Release BOOTSEL
- RP2350B should appear as USB mass storage device
- If not: Check USB D+/D- traces, check 3.3V rail

**5. Blink LED test:**
- Upload simple blink program to GPIO25 (user LED)
- Verifies: Flash programming, RP2350B execution, GPIO function

**6. Peripheral tests:**
- I2C scan (should find STUSB4500, 2Ã— INA219)
- SD card detection
- GPIO input/output tests
- ADC reading test

---

**General:**
- Layers: 2-layer FR-4
- Thickness: 1.6mm
- Finish: ENIG (gold)
- Soldermask: Green or black
- Silkscreen: White (top and bottom)
- Min trace/space: 6mil/6mil (0.15mm)

**Dimensions:**
- Size: 120mm Ã— 90mm
- Mount holes: 4Ã— M3 (3.2mm diameter)
- Corner radius: 3mm
- Connector clearance: 5mm from edges

---

## HIERARCHICAL SCHEMATIC ORGANIZATION

### Sheet 1: Root/Cover Page
- Title block
- Revision history
- Block diagram
- Power flow diagram

### Sheet 2: USB-C PD & Protection
- USB-C connector (J1)
- STUSB4500 PD controller
- ESD protection (USBLC6-2SC6)
- USB data routing to RP2350B

### Sheet 3: Power Conversion
- Barrel jack input (J_BARREL)
- Screw terminal input (J_SCREW)
- Schottky OR-ing diodes (D1-D3)
- TVS protection (D4)
- TPS54531 buck converter
- 2Ã— AP2112K LDOs
- 5V_SW MOSFET circuit

### Sheet 4: Power Monitoring
- 2Ã— INA219 current sensors
- J7 5V output MOSFET + polyfuse
- J8 V_INPUT output MOSFET + polyfuse
- Shunt resistors (0.05Î©, 2W)
- Flyback diodes (SS54) for motor protection
- Bleeder resistors (10kÎ©) for discharge

### Sheet 5: RP2350B Core
- RP2350B IC (all pins)
- Internal regulator circuit (L1, C6, C7, C9, R3)
- Crystal oscillator (Y1, C3, C4, R2)
- Decoupling capacitors
- USB data lines (27Î© termination)
- BOOTSEL/RESET buttons

### Sheet 6: Flash & Debug
- W25Q512JVS 64MB flash
- QSPI connections
- Decoupling
- SWD debug connector (J10)

### Sheet 7: EdgeLock Connectors (Part 1)
- J1-J4: Joystick connectors
- Per-GPIO LED circuits
- Series resistors (330Î© + 100Î©)

### Sheet 8: EdgeLock Connectors (Part 2)
- J5: SPI0 connector
- J6: UART1 connector
- J9: PWM connector
- All LED indicators

### Sheet 9: Arduino Headers
- Power header (1Ã—8)
- Analog header (1Ã—6)
- Digital headers (1Ã—8, 1Ã—10)
- Dual SMD+THT footprints
- IOREF, AREF connections

### Sheet 10: SD Card & Status
- SD card socket (SPI1)
- 10kÎ© pullup resistors
- Card detect circuit
- WS2812B RGB LED (GPIO23)
- User LED (GPIO25)
- Power LED
- 5V_SW indicator LED

---

## STATUS INDICATORS

**Onboard LEDs:**
- **Power LED (Green):** Always on when 3.3V present
- **User LED (Yellow):** GPIO25, Pico-compatible
- **WS2812B RGB:** GPIO23, multi-color status
  - Green: Running normally
  - Blue: Booting
  - Red: Error
  - Purple: Bootloader
  - Cyan: USB Mass Storage active
- **5V_SW LED (Red):** Shows servo rail enabled
- **Per-GPIO LEDs (48Ã—):** Color-coded by function

**Buttons:**
- **SW1 (BOOTSEL):** 6Ã—6mm tactile, USB bootloader mode
- **SW2 (RESET):** 6Ã—6mm tactile, hard reset

---

## USB MASS STORAGE FEATURE

**Filesystem:** LittleFS on flash (2-8MB partition)

**Exposed Files:**
```
RP2350_EXHIBIT/
â”œâ”€â”€ CONFIG.TXT (user-editable settings)
â”œâ”€â”€ VERSION.TXT (firmware version, read-only)
â”œâ”€â”€ README.TXT (instructions)
â”œâ”€â”€ ERROR_LOG.TXT (last 100 errors)
â”œâ”€â”€ DATA_LOG.CSV (usage data)
â””â”€â”€ firmware/UPDATE.UF2 (drag-drop updates)
```

**Example CONFIG.TXT:**
```ini
EXHIBIT_NAME=Asteroid Miner Station 3
LED_BRIGHTNESS=80
BUTTON_DEBOUNCE_MS=50
ENABLE_SERIAL_DEBUG=true
LOG_LEVEL=INFO
J8_DEFAULT_VOLTAGE=12
```

---

## BILL OF MATERIALS SUMMARY

**Core Components (Always Populated):**
- RP2350B: $1.50
- W25Q512JVS 64MB: $2.50
- STUSB4500: $2.50
- TPS54531 buck: $1.50
- 2Ã— AP2112K LDO: $0.60
- 2Ã— INA219: $2.00
- 2Ã— Shunt resistor (0.05Î©, 2W): $0.60
- 2Ã— SS54 flyback diode: $0.30
- 2Ã— 10kÎ© bleeder resistor: $0.02
- 8Ã— EdgeLock connectors: $6.40
- USB-C connector: $0.80
- Barrel jack: $0.60
- Screw terminal: $0.50
- SD card socket: $0.70
- Protection (3Ã— SS54, TVS, polyfuses): $0.95
- Inductors, MOSFETs, passives: $3.00
- 52Ã— LEDs: $2.60
- Switches, headers: $0.50

**Total (Basic Board):** ~$29-31

**Optional:**
- Arduino headers (SMD): Included in base
- Pi HAT headers: Footprint only
- LoRa module: N/A (removed from design)

---

## FIRMWARE EXAMPLES

### Reading INA219 Sensors
```cpp
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219_J7(0x40);  // 5V output
Adafruit_INA219 ina219_J8(0x41);  // Variable output

void setup() {
    ina219_J7.begin();
    ina219_J8.begin();
}

void loop() {
    float voltage_J7 = ina219_J7.getBusVoltage_V();
    float current_J7 = ina219_J7.getCurrent_mA();
    
    float voltage_J8 = ina219_J8.getBusVoltage_V();
    float current_J8 = ina219_J8.getCurrent_mA();
    
    Serial.printf("J7: %.2fV @ %.0fmA\n", voltage_J7, current_J7);
    Serial.printf("J8: %.2fV @ %.0fmA\n", voltage_J8, current_J8);
}
```

### Controlling Smart Outputs
```cpp
// GPIO definitions
#define J7_ENABLE 8   // 5V output
#define J8_ENABLE 9   // Variable voltage output

void enableMotor(float requiredVoltage) {
    float vbus = ina219_J8.getBusVoltage_V();
    
    if (vbus < requiredVoltage - 1.0) {
        Serial.println("Error: Insufficient voltage");
        return;
    }
    
    digitalWrite(J8_ENABLE, HIGH);  // Turn on motor
    Serial.printf("Motor enabled at %.1fV\n", vbus);
}

void disableMotor() {
    digitalWrite(J8_ENABLE, LOW);
    Serial.println("Motor disabled");
}
```

### USB PD Voltage Request
```cpp
// Request higher voltage from USB-C PD
void requestPDVoltage(float voltage) {
    // Use STUSB4500 library to request specific voltage
    // This changes what the PD charger provides
    stusb4500.setPDO(voltage, 3.0);
    delay(500);  // Wait for renegotiation
    
    float actual = ina219_J8.getBusVoltage_V();
    Serial.printf("Requested %.0fV, got %.1fV\n", voltage, actual);
}

// Example usage
void setup() {
    requestPDVoltage(20.0);  // Request max voltage for motor
}
```

---

## DESIGN PHILOSOPHY

**Key Principles:**
1. **Field Serviceability:** Museum staff can configure without programming
2. **Visual Debugging:** Per-GPIO LEDs show pin states
3. **Power Flexibility:** USB-C PD, barrel, or screw terminals
4. **Smart Monitoring:** INA219 current/voltage sensing
5. **Modular Expansion:** Arduino shields, daughter boards
6. **Robust Installation:** Polyfuse protection, screw-down connections

**Target Applications:**
- Interactive museum exhibits
- Maker projects with multiple input devices
- Educational demonstrations
- Prototyping platforms
- Industrial control panels

---

## ENCLOSURE DESIGN

**3D Printed Base:**
- Material: PLA or PETG
- Dimensions: 130mm Ã— 100mm Ã— 30mm
- Wall thickness: 2.5mm
- Mounting: M3 brass threaded inserts

**Vacuum-Formed Acrylic Lid:**
1. Vacuum form 3mm clear acrylic
2. Magnifying lens dome over RP2350B
3. Laser etch labels, logos, QR codes
4. Paint fill engraved areas
5. Sand to frost (320-400 grit)
6. Mask lens during sanding

**Features:**
- Frosted hides internals
- Clear lens shows chip
- "Clark Inside" logo
- QR code to docs
- EdgeLock port holes

---

## DESIGN STATUS

**Ready for:** Schematic entry in KiCad 7.0+

**Next Steps:**
1. Create hierarchical schematic sheets
2. Place components following critical layout rules
3. Route power traces (wide, short)
4. Route USB differential pair (90Î© impedance)
5. Place decoupling caps (within 5mm of pins)
6. Add per-GPIO LED indicators
7. Design enclosure in CAD
8. Generate BOM and assembly files

---

*Document created: 2026-02-04*  
*Revision: 1.0*  
*Status: Final - Ready for Implementation*
