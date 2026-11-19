# RP2350B Exhibit Control Board — Spec Packet

Designer: Clark Planetarium. Purpose: museum exhibit / maker controller with flexible power input, monitored switchable power outputs, and a visible indicator LED on every GPIO.

This is a spec, not an implementation. Where a part is listed under "Must-use," use that exact MPN. Everywhere else, the electrical requirement is what matters; pick a real part from the library (prefer JLCPCB basic parts) or leave it as "TBD part" with the requirement attached. If anything below is electrically wrong or conflicts with a datasheet, flag it rather than silently fixing it.

Implementation request: ato v2 idioms, one module per block with public interfaces (`ElectricPower`, `USB2_0`, `I2C`, `SPI`, `UART`, `ElectricLogic`), files split as `power/`, `mcu/`, `io/`, composed in `main.ato:App`.

---

## 1. System architecture

```
USB-C (PD sink, 5–20V) ─┐
Barrel jack (6–28V) ────┼─ Diode-OR + TVS + polyfuse ─> V_INPUT (5–28V)
Push-in terminal (6–28V)┘                                 │
                                                          ├─> Buck-boost ─> +5V (5A)
                                                          │                  ├─> LDO ─> +3V3_AUX (always-on, PD controller)
                                                          │                  ├─> LDO ─> +3V3 (MCU + peripherals)
                                                          │                  ├─> Switched ─> +5V_SW (servo rail, J9)
                                                          │                  └─> Monitored + switched ─> J7 (5V out)
                                                          └─> Monitored + switched ─> J8 (V_INPUT out)

RP2350B ── QSPI flash (64MB)
        ── USB 2.0 device (to USB-C)
        ── I2C0: PD controller, 2× current monitors, Arduino header
        ── SPI0: EdgeLock J5 + Arduino SPI
        ── SPI1: microSD
        ── 48 GPIO → EdgeLock connectors / Arduino headers, each with indicator LED
```

Form factor: custom, 120 × 90 mm, 3 mm corner radius, 4× M3 holes (Pi HAT–compatible spacing for one set if practical).
Stackup: 2-layer FR-4, 1.6 mm, 1 oz, ENIG. Top = components + signals, bottom = mostly solid GND (>80%).
Assembly: SMD parts by assembler; connectors and headers may be hand-soldered through-hole.

## 2. MCU core

| Item | Spec |
|---|---|
| MCU | RP2350B (QFN-80, 48 GPIO, ADC on GPIO40–47), A4 stepping |
| Core supply | Internal switching regulator (VREG), per Raspberry Pi "Hardware Design with RP2350" reference, copied exactly |
| Flash | 64MB QSPI, W25Q512JVBIQ (24-TFBGA) |
| Boot mode | BOOTSEL button pulls QSPI_SS low through 1kΩ, per reference |
| Reset | RESET button pulls RUN to GND; pull-up per reference |
| Clock | 12 MHz crystal, Abracon ABM8-272-T3, 1kΩ series on XOUT, load caps per reference |
| USB | Device only (no host/OTG). 27Ω series on DP/DM near MCU. Type-C CC handled by PD controller (see §4) |
| Debug | SWD, 3-pin JST-SH |
| Decoupling | 100nF per IOVDD/DVDD pin as in reference, plus 4.7µF bulk; follow reference pin grouping |

## 3. Pin / interface map

### RP2350B dedicated pins

| Net | RP2350B pin | External | Notes |
|---|---|---|---|
| USB_DP / USB_DM | USB_DP / USB_DM | USB-C D+/D− via 27Ω, ESD array | 90Ω diff, length-matched |
| XIN / XOUT | XIN / XOUT | 12 MHz crystal + load caps, 1kΩ on XOUT | Short traces, guard ring |
| RUN | RUN | RESET button to GND, Arduino RESET pin | Pull-up per reference |
| SWCLK / SWDIO | SWCLK / SWDIO | J10 pins 1 / 3 | J10 pin 2 = GND |
| QSPI_SS | QSPI_SS | Flash /CS, BOOTSEL button via 1kΩ | Pull-up per reference |
| QSPI_SCLK, QSPI_SD0–3 | QSPI_* | Flash CLK, IO0–IO3 | |
| VREG_VIN, VREG_LX, VREG_FB, VREG_PGND, VREG_AVDD | VREG_* | 3.3µH inductor, 4.7µF caps, 33Ω filter | Exact reference circuit |
| IOVDD, QSPI_IOVDD, USB_OTP_VDD, ADC_AVDD | — | +3V3 | ADC_AVDD per reference filtering |
| DVDD | DVDD | VREG output | Per reference |

### GPIO (all 48)

| GPIO | Function | External | Notes |
|---|---|---|---|
| 0 | UART0 TX / digital | J1.1, Arduino D0 | Indicator LED |
| 1 | UART0 RX / digital | J1.5, Arduino D1 | Indicator LED |
| 2 | Digital | J2.1, Arduino D2 | Indicator LED |
| 3 | Digital / PWM | J2.5, Arduino D3 | Indicator LED |
| 4 | Digital | J3.1, Arduino D4 | Indicator LED |
| 5 | Digital / PWM | J3.5, Arduino D5 | Indicator LED |
| 6 | Digital / PWM | J4.1, Arduino D6 | Indicator LED |
| 7 | Digital | J4.5, Arduino D7 | Indicator LED |
| 8 | J7_EN | J7 output switch gate driver | Active high = output on |
| 9 | J8_EN | J8 output switch gate driver | Active high = output on |
| 10 | UART1 TX | J6.1 | Indicator LED |
| 11 | UART1 RX | J6.2 | Indicator LED |
| 12 | SPI1 RX | microSD DAT0 | 10k pull-up |
| 13 | SPI1 CSn | microSD DAT3/CS | 10k pull-up |
| 14 | SPI1 SCK | microSD CLK | |
| 15 | SPI1 TX | microSD CMD | 10k pull-up |
| 16 | SPI0 RX | J5.1, Arduino D12 | Indicator LED |
| 17 | SPI0 CSn | J5.2, Arduino D10 | Indicator LED |
| 18 | SPI0 SCK | J5.3, Arduino D13 | Indicator LED |
| 19 | SPI0 TX | J5.4, Arduino D11 | Indicator LED |
| 20 | I2C0 SDA | PD ctrl, INA219 ×2, Arduino A4 + SDA | 4.7k pull-up to +3V3 (one set) |
| 21 | I2C0 SCL | Same as above, Arduino A5 + SCL | 4.7k pull-up to +3V3 (one set) |
| 22 | SD_CD | microSD card-detect switch | Pull-up |
| 23 | WS2812_DIN | WS2812B via 100Ω | LED powered from +5V |
| 24 | 5V_SW_EN | +5V_SW switch gate driver | Active high = rail on |
| 25 | USER_LED | LED + resistor to GND | Active high, Pico-compatible |
| 26 | UART1_EN | J6.3 | Indicator LED |
| 27 | UART1_IRQ | J6.4 | Indicator LED |
| 28–31 | PWM | J9.2–J9.5 | Indicator LEDs |
| 32 | Digital | Arduino D8 | Indicator LED |
| 33 | Digital / PWM | Arduino D9 | Indicator LED |
| 34 | PD_ALERT | PD controller ALERT (open-drain) | 4.7k pull-up, active low |
| 35–39 | Expansion | Test points | |
| 40–47 | ADC0–7 | J1–J4 ADC pins; 40–43 also Arduino A0–A3 | Indicator LED with bypass jumper |

### Connectors

| Ref | Part | Pinout |
|---|---|---|
| J1 | Molex EdgeLock 502598-0603 | 1 GPIO0, 2 GPIO40, 3 GND, 4 +3V3, 5 GPIO1, 6 GPIO41 |
| J2 | Molex EdgeLock 502598-0603 | 1 GPIO2, 2 GPIO42, 3 GND, 4 +3V3, 5 GPIO3, 6 GPIO43 |
| J3 | Molex EdgeLock 502598-0603 | 1 GPIO4, 2 GPIO44, 3 GND, 4 +3V3, 5 GPIO5, 6 GPIO45 |
| J4 | Molex EdgeLock 502598-0603 | 1 GPIO6, 2 GPIO46, 3 GND, 4 +3V3, 5 GPIO7, 6 GPIO47 |
| J5 | Molex EdgeLock, 4-pin | 1 GPIO16, 2 GPIO17, 3 GPIO18, 4 GPIO19 |
| J6 | Molex EdgeLock, 6-pin | 1 GPIO10, 2 GPIO11, 3 GPIO26, 4 GPIO27, 5 +3V3, 6 GND |
| J7 | 2-pos screw terminal | 1 J7_OUT (switched +5V), 2 GND |
| J8 | 2-pos screw terminal | 1 J8_OUT (switched V_INPUT), 2 GND |
| J9 | Molex EdgeLock, 6-pin | 1 +5V_SW, 2 GPIO28, 3 GPIO29, 4 GPIO30, 5 GPIO31, 6 GND |
| J10 | JST-SH 3-pin | 1 SWCLK, 2 GND, 3 SWDIO |
| Arduino power | 1×8 TH | NC, IOREF(+3V3), RESET(RUN), +3V3, +5V, GND, GND, VIN(+5V) |
| Arduino analog | 1×6 TH | A0–A3 = GPIO40–43, A4 = GPIO20, A5 = GPIO21 |
| Arduino D0–7 | 1×8 TH | GPIO0–7 |
| Arduino D8–13 | 1×10 TH | GPIO32, GPIO33, GPIO17, GPIO19, GPIO16, GPIO18, GND, AREF (+3V3 via jumper), GPIO20, GPIO21 |
| Pi HAT | 2×20 footprint | DNP, footprint only |

### Per-GPIO indicator LED (reusable module, as currently specified)

GPIO → 330Ω (0402) → LED (OSRAM LW QH8G, white 0402, Vf 2.8V) → 100Ω (0603) → connector pin.
ADC pins (GPIO40–47): solder jumper bypassing the chain.

## 4. Power tree

| Rail | Source | Target | Load / notes |
|---|---|---|---|
| V_INPUT | Diode-OR of VBUS, barrel, terminal | 5–28V | Feeds buck-boost and J8 |
| +5V | Buck-boost from V_INPUT | 5.0V, 5A | Buck-boost so 5V in still regulates to 5V |
| +3V3_AUX | LDO from +5V | 3.3V, ≥100mA | Always on; powers PD controller |
| +3V3 | LDO from +5V | 3.3V, ≥600mA | MCU, flash, SD, LEDs, connectors |
| +5V_SW | Switched +5V | 5V, 3A | GPIO24 enable, feeds J9 |
| J7_OUT | Monitored + switched +5V | 5V, 3A | GPIO8 enable, INA219 @ 0x40 |
| J8_OUT | Monitored + switched V_INPUT | 5–28V, 3A | GPIO9 enable, INA219 @ 0x41 |

**Input protection:** Schottky diode per input (5A, 40V) forming the OR. Bidirectional TVS on V_INPUT (28V standoff). 5A-hold polyfuse in series.

**USB-C PD:** STUSB4500 sink controller at I2C 0x28, powered from +3V3_AUX. Dead-battery mode enabled per ST reference (STEVAL-ISC005V1). CC1/CC2 direct from connector. DISCH: 100Ω to VBUS, 100nF to GND. RESET: 10k pull-down. ALERT → GPIO34. POWER_OK pins and external VBUS path MOSFETs not used. Default PDO 12V @ 3A, fallback 5V @ 3A, stored in NVM. ESD array on D+/D−.

**Smart outputs (J7, J8, and +5V_SW):** rail → 0.05Ω shunt (0.1%, 2W) → P-MOSFET high-side switch → 3A polyfuse → connector. Gate drive: GPIO → NPN (MMBT3904) pulls P-FET gate low; gate-to-source pull-up keeps it off by default. Output side: Schottky flyback diode (cathode to output) and 10k bleeder to GND. INA219 address set by A0/A1 (0x40 both GND, 0x41 A0 = VS). +5V_SW uses the same switch topology without a monitor.

**Sequencing:** none required. Outputs default off at power-up.

**Decoupling budget:** 10µF in / 10µF out per LDO. Buck-boost input/output bulk per datasheet typical application. 100nF at every IC supply pin. MCU per reference.

## 5. Connectors, buttons, LEDs

- USB-C: GCT USB4105, USB 2.0 data + power
- Barrel: 5.5 × 2.1 mm, center positive
- Input terminal: WAGO push-in, 2-pos, 4 mm pitch
- Buttons: 2× Omron B3FS-4005P (BOOTSEL, RESET)
- Status: power LED on +3V3, user LED on GPIO25, WS2812B on GPIO23, indicator LED on +5V_SW
- microSD: Molex 5033981892

## 6. BOM preferences

**Must-use (already selected/purchased):**
RP2350B, W25Q512JVBIQ, ABM8-272-T3, Abracon AOTA-B201610S3R3-101-T (VREG inductor), TPS55288RPMR, AP2112K-3.3 ×2, STUSB4500QTR, SI2305A (J7 and +5V_SW switches only), MMBT3904, USBLC6-2SC6, SS54-HF (Comchip), GCT USB4105, Molex 5033981892, Molex EdgeLock 502598 series, OSRAM LW QH8G, WS2812B, Omron B3FS-4005P.

**Selected but open to replacement (see Known issues, §9):**
INA219AIDR ×2 (bus voltage limit), SI2305A on J8 (voltage rating), Littelfuse 2920L500/24SLDR (voltage rating), SMAJ28CA-E3/61 (clamp margin).

**Flexible (use requirement, prefer JLCPCB basic parts):**
All generic resistors and capacitors (0402 default, 0603 where noted), shunt resistors (0.05Ω, 0.1%, ≥2W), output polyfuses (3A hold), barrel jack, screw terminals, headers, JST-SH.

**Do not invent MPNs or LCSC IDs.** Leave "TBD part" with the requirement if nothing real matches.

## 7. Layout intent

- VREG components within 10mm of RP2350B; VREG_LX short, wide, no vias; inductor polarity dot toward VREG_LX
- Buck-boost switch nodes short and wide, top layer only, away from crystal/USB/ADC
- USB D+/D− 90Ω differential, length-matched within 5mm, solid GND underneath, no vias
- Crystal traces <10mm, 5mm keep-out, grounded guard ring
- Decoupling within 5mm of pins; thermal pads with ≥9 vias
- Zones: noisy (power) / digital (MCU, flash) / sensitive (crystal, USB, ADC) / I/O around the perimeter
- GND stitching vias every 10–15mm

## 8. Assumptions

- USB is device-only; the board never sources VBUS
- No battery; no power-path or charging circuitry
- All GPIO are 3.3V logic
- Arduino shields and EdgeLock connectors share GPIO; only one is used at a time per pin

## 9. Open questions

1. TPS55288RPMR: my TI WEBENCH design lists external MOSFETs CSD18543Q3A and CSD18514Q5A. Confirm from the datasheet whether external switching FETs are needed; omit them if not.
2. Crystal load capacitors: my notes conflict (10pF vs 15pF). Use the value from the RP2350 reference design.
3. GPIO10/11 as UART1 TX/RX: confirm the RP2350 function mux allows this (UART aux function); if not, propose the nearest valid pins.
4. Arduino D0 is conventionally RX and D1 TX, but GPIO0 is UART0 TX and GPIO1 is UART0 RX. Confirm whether to swap for shield compatibility.

### Known issues (please fix, not just flag)

These are problems I'm already aware of in the spec above. The intent of each block is fixed; the specific parts are open to replacement. Suggestions are starting points, not requirements.

5. **J8 P-MOSFET voltage ratings.** J8 switches V_INPUT, which can reach 28V (and briefly the TVS clamp voltage during transients). The SI2305A is rated 20V V_DS and ±8V V_GS, so it can't be used on J8. With the NPN pulling the gate to GND, V_GS would equal the full rail voltage. J8 needs a P-FET rated ≥40V V_DS with ≥3A capability, plus gate-voltage limiting (for example, a zener clamp or a resistor divider from source to NPN collector) so V_GS stays within rating across 5–28V. SI2305A is fine for J7 and +5V_SW, which only switch 5V.
6. **INA219 bus voltage limit on J8.** INA219's bus/shunt inputs are rated to 26V, below the 28V maximum on J8. Replace the J8 monitor (and J7's too, for consistency, if a single part is simpler) with a pin-compatible or near-drop-in I2C monitor rated for ≥36V, such as INA226 (36V) or INA228/INA237 (85V). Keep I2C addresses 0x40 (J7) and 0x41 (J8).
7. **Input polyfuse voltage rating.** The 2920L500/24SLDR is rated 24V, but V_INPUT can reach 28V. Needs a ≥30V-rated overcurrent device with ~5A hold. If no suitable polyfuse exists in that size, an eFuse / hot-swap controller is an acceptable alternative.
8. **Per-GPIO indicator LED topology.** As specified, the LED sits in series between the GPIO and the connector pin. That blocks inputs from driving the GPIO correctly, drops ~2.8V on outputs, and makes ADC readings meaningless without the bypass jumper. The intent is simply "an LED that lights when the pin is high," without affecting the signal. Redesign as a shunt indicator that doesn't sit in the signal path: either GPIO/connector net → resistor → LED → GND directly (target ~1mA to limit loading), or a buffered driver (e.g., a small MOSFET or buffer IC per LED) so the indicator draws negligible current from the pin. Keep the ADC-pin option to disconnect the indicator entirely (jumper or DNP) for precision analog. Keep a small series resistor between GPIO and connector for protection if you think it's useful.
9. **Transient margin on V_INPUT.** The SMAJ28CA clamps well above 28V during a transient (roughly mid-40s V). Check that everything connected directly to V_INPUT (TPS55288 VIN, J8 switch, J8 monitor, OR-ing diodes) survives the clamp voltage, and adjust the TVS or add margin where needed.

## 10. Pico deltas

Not Pico-shaped. Keeps Pico conventions for: GPIO25 user LED, BOOTSEL on QSPI_SS, 12 MHz crystal, SWD, and the reference VREG/decoupling. Differs in: RP2350B (48 GPIO) instead of RP2350A, 64MB flash, USB-C PD input, multi-source power, and no Pico-footprint castellations.
