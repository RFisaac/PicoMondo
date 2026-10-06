# 3.3 V regulators

Sheet: `power_ldo.kicad_sch`. Two AP2112K-3.3 (Diodes Inc, LCSC C51118) from the +5V rail:
`+3V3_AUX` (PD controller) and `+3V3` (everything else). EN is tied to the input, so both are
always on. 10 uF in and out on each (datasheet minimum 1 uF; X5R or X7R).

## The thermal limit (important)

The AP2112K is rated 600 mA, but a linear regulator turns the whole voltage drop into heat:
(5 V - 3.3 V) x current. The SOT-23-5 package is 184 C/W with no heatsink (datasheet), and the
chip's maximum junction temperature is 150 C.

| Load | Heat | Temperature rise | Allowed at 40 C ambient? |
|------|------|------------------|-------------------------|
| 100 mA | 0.17 W | 31 C | yes |
| 200 mA | 0.34 W | 63 C | yes |
| 350 mA | 0.60 W | 109 C | borderline (150 C junction) |
| 600 mA | 1.02 W | 188 C | no, thermal shutdown |

Real boards do better than 184 C/W when the pad is tied to a copper pour (assume about 100 C/W,
roughly 600 mA possible), but plan for 350 mA unless the layout proves otherwise. The chip has
thermal shutdown, so overload makes the 3.3 V rail drop out, not fail permanently.

Expected load on `+3V3`: RP2350B about 100 mA, flash 20 mA, microSD up to 100 mA, the 3.3 V pins on
the EdgeLock and Arduino connectors, and the indicator LEDs (about 1 mA each). That is already
close to the limit once external modules are attached.

Options if the budget is exceeded:
1. Keep the AP2112K and limit what hangs on `+3V3` (document the budget for users).
2. Replace the main 3.3 V LDO with a small buck converter (more parts, much cooler).
3. Feed the LDO from a lower input than 5 V (not available here).

`+3V3_AUX` only powers the PD controller (about 5 mA), so it has plenty of margin.
