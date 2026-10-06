# 5 V rail: TPS55288 buck-boost

Sheet: `power_buck.kicad_sch`. Source: TI TPS55288 datasheet SLVSF01B
(`resources/datasheets/tps55288.pdf`), section 8.2 and figure 8-1, plus the calculations below.
Everything here should be checked on the bench: the datasheet says its application section is not
part of the TI specification.

## What the chip does here

V_INPUT (about 4.6 V to 28 V) goes in; a fixed 5 V comes out, whether the input is below
(boost), near (buck-boost) or above (buck) 5 V. The buck side uses two **external** N-channel FETs
(DR1H/DR1L gate drivers); the boost side switches are inside the chip. So the external FETs from
the web design were required, which resolves open question 1 in the spec packet.

Power-up default (no I2C needed): internal feedback, reference 0.282 V, ratio 0.0564, so the
output starts at 5.0 V. The I2C interface (address 0x74) can change voltage, current limit and mode
later. The chip's own datasheet limits: VIN and SW1 absolute maximum 40 V, recommended 36 V;
VOUT up to 22 V.

## Component values

| Part | Value | Why |
|------|-------|-----|
| Switching frequency | R_FSW 49.9 kohm = 400 kHz | TI reference. Below 500 kHz is recommended for thermal reasons at 5 A. |
| Inductor | 4.7 uH, Isat 12 A or more, DCR 12 mohm or less | TI reference value (range 1 to 10 uH). See ripple numbers below. |
| Input capacitors | 4 x 10 uF 50 V + 100 nF | 36 V parts derate heavily with DC bias; TI wants about 20 uF effective |
| Output capacitors | 4 x 22 uF 16 V at VOUT, 2 x 22 uF after the sense resistor | Datasheet range 10 to 1000 uF effective |
| Sense resistor | 10 mohm 1% 1 W | 50 mV default limit / 10 mohm = 5 A. Dissipates 0.25 W at 5 A. |
| R_ILIM | 33.2 kohm | Average inductor limit = 330000 / R = about 10 A (TI's 20 kohm gives 16.5 A) |
| MODE | 0 ohm to AGND | Internal VCC, I2C 0x74, forced PWM (no audible light-load buzz). 6.19 kohm gives PFM. |
| EN/UVLO divider | 220 kohm / 88.7 kohm | Turn-on about 4.3 V, turn-off about 3.2 V; at 28 V the pin sees 8 V (limit 20 V) |
| VCC capacitor | 10 uF | Datasheet requires more than 4.7 uF |
| Bootstrap | 2 x 100 nF | Datasheet requirement |
| Dither | 10 nF on DITH/SYNC | Spread spectrum for EMI, as in the reference |
| CDC | 100 kohm | Cable droop compensation not used (reference value) |
| Compensation | R 7.5 kohm + C 3.3 nF in series, 10 pF in parallel (DNP) | Calculated below |
| FB/INT | 10 kohm pull-up to +3V3, to GPIO35 | Fault indicator when internal feedback is used |

### Ripple and inductor current (checks the 4.7 uH choice)

- Boost, worst case (V_IN 4.65 V, 5 V at 5 A, efficiency 0.95): I_L(DC) = 5 x 5 / (4.65 x 0.95) =
  5.7 A. Ripple = V_IN (V_OUT - V_IN) / (L f V_OUT) = 0.17 A p-p. Negligible.
- Buck, worst case (V_IN 28 V, 5 V at 5 A): ripple = (28 - 5) x 5 / (4.7 uH x 400 kHz x 28) = 2.2 A
  p-p, peak 6.1 A, about 44% ripple. TI advises under 40% for the maximum output current, so this is
  at the edge but acceptable (the datasheet reference uses the same inductor with up to 20 V in).
  A 6.8 uH inductor would cut ripple to 30% if the exact part allows it.
- So a 12 A saturation rating covers the 5.7 A boost current, the 6.1 A buck peak and the 10 A
  ILIM clamp.

### Compensation (boost mode is the restrictive case)

Using the datasheet equations with: C_OUT effective about 50 uF (4 x 22 uF at 5 V bias), R_load 1 ohm
(5 V, 5 A), V_IN 4.65 V so D = 0.07, L 4.7 uH, R_sense 0.055 ohm, G_EA 190 uA/V, V_REF 0.282 V:

- f_RHPZ = R_load (1 - D)^2 / (2 pi L) = 29 kHz, so the crossover f_C is limited to f_RHPZ / 5 = about 5 kHz
- R_C = 2 pi V_OUT R_sense C_OUT f_C / ((1 - D) V_REF G_EA) = about 7.5 kohm
- C_C = R_load C_OUT / (2 R_C) = about 3.3 nF
- C_P = ESR x C_OUT / R_C, under 10 pF, so left unfitted (footprint kept)

These are starting values. Confirm with a load-step test on the first board, and adjust R_C and C_C.

## Things that need your attention

1. **Input transient margin (known issue 9).** The chip's VIN and SW1 pins stop at 40 V absolute. A
   28 V TVS (for example SMBJ28A) clamps at roughly 38 V at 5 A of surge current (my interpolation) and 45 V at its 13 A
   rating, so a large surge would exceed 40 V. For an indoor exhibit this is a reasonable risk;
   if surges are likely, an input over-voltage protection stage is the fix. The TVS and input
   protection are on the input sheet (not drawn yet).
2. **Low-side FET.** The web design used a 40 V CSD18514Q5A on the low side. With a 28 V input plus
   switching ringing that is marginal, so both FETs here are the 60 V CSD18543Q3A (also one part
   fewer on the BOM). It is a 3.3 x 3.3 mm package with a drain pad that carries heat: needs copper.
3. **Input power limit.** From a plain 5 V USB source (3 A, 15 W) the converter cannot deliver 25 W.
   The PD controller negotiates 12 V for normal use; with a 5 V-only source expect the output
   to be limited by the source. Firmware can read the PD status and the INA226 monitors.
4. **Total 5 V load.** 5 A at the converter, but J7 (3 A) + 5V_SW (3 A) + the 3.3 V LDOs can add up to
   more. Either limit the outputs in firmware or revisit the current rating.
5. **Inductor part is still open.** The previous pick (Magsonder CMKD-1350A-4R7M, LCSC C373345) is
   no longer listed by LCSC. Candidates from the datasheet: Coilcraft XAL1010-472ME, Vishay
   IHLP5050EZER4R7, Sumida 125CDMCCDS-4R7MC. Placeholder footprint: Coilcraft XAL1010.

## Layout notes (from TI's layout example)

- 4-layer board: first inner layer is the PGND plane; AGND island joins PGND at the VCC capacitor.
- Input capacitors, buck FETs and the inductor together in a tight loop; SW1/SW2 on the top layer,
  short and wide, no vias.
- ISP/ISN are Kelvin sense lines to the two ends of the sense resistor.
- Output capacitors next to the VOUT pins, before the sense resistor.
- The chip's thermal performance in TI's EVM is 25.8 C/W on a 4-layer, 2 oz board. On 1 oz copper
  expect worse; use plenty of copper and vias around the chip and FETs.
