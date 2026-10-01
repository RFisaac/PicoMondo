# Switched outputs (J7, J8, +5V_SW)

Sheet: `power_outputs.kicad_sch`. One channel function builds all three, so they are identical in
structure.

```
rail --[20 mohm shunt]-- SRC --(source) P-FET (drain)-- DRAIN --[3 A fuse]-- OUT --+-- terminal
                          |  R_gs (47k, plus a 12 V zener on J8) source to gate     |-- flyback diode to GND
                          +-- INA226 (IN+ rail, IN- and VBUS on SRC)                +-- bleeder to GND
GPIO -- 10k -- NPN base (100k pull-down); NPN collector -- R_g -- gate. GPIO high = output on.
```

Floating or low GPIO: the NPN is off, R_gs holds the gate at the source, and the output is off
(so outputs are off at power-up and during reset).

| Channel | Rail | Enable | FET | Monitor | Output |
|---------|------|--------|-----|---------|--------|
| J7 | +5V | GPIO8 | SI2305A (20 V, Vgs +/-12 V, 4.2 A, 40 mohm at 4.5 V) | INA226 at 0x40 | terminal J7 |
| J8 | V_INPUT (about 5 to 28 V) | GPIO9 | DMP4015SSS-13 (40 V, Vgs +/-25 V, 9 to 15 mohm) | INA226 at 0x41 | terminal J8 |
| +5V_SW | +5V | GPIO24 | SI2305A | none | `+5V_SW` net for J9, plus a red LED |

## Why it is built this way

- **Shunt: 20 mohm, not 50 mohm.** The INA226's shunt input range is only +/-81.92 mV (the INA219 it
  replaced handled +/-320 mV). 50 mohm would saturate at 1.64 A. 20 mohm reads up to 4.1 A with
  125 uA per step after calibration, and dissipates 0.18 W at 3 A.
- **J8 gate protection (known issue 5).** With the NPN pulling the gate to ground, Vgs would equal
  the whole rail (28 V). The 12 V zener from gate to source limits Vgs to -12 V, inside the
  FET's +/-25 V rating, and still turns the FET fully on from a 5 V rail (Vgs about -4.4 V; threshold at most
  -2.5 V; 15 mohm at 4.5 V). R_g is 22 kohm so the zener and NPN currents stay under 1 mA.
- **INA226 range (known issue 6).** The INA226 handles 36 V common-mode and VBUS; absolute maximum
  on its inputs is 40 V.
- **J7 / +5V_SW FET.** At 3 A the SI2305A dissipates 0.36 W (40 mohm), about 32 C rise at the
  datasheet's 90 C/W. Gate drive is only -5 V, inside its +/-12 V rating.
- **Bleeders.** 10 kohm at 5 V; 22 kohm on J8 because 10 kohm would dissipate 78 mW at 28 V, more than a
  0402 resistor can take.
- **Flyback diodes** (SS54-HF, cathode to the output) clamp the negative spike when an inductive load
  (motor, solenoid, relay) is switched off. They do nothing for positive spikes.

## Things to know

1. **Fuse hold current drops with temperature.** The 1812L300/33GR is 3 A hold at room temperature;
   inside a warm enclosure (say 50 C) it can trip near 2 A. If J7/J8 must deliver a full 3 A
   continuously, choose a fuse with more headroom or accept the derating.
2. **Surge margin.** J8 rides on V_INPUT, so the TVS clamp (about 38 V at 5 A) is close to the 40 V ratings of
   the FET and the INA226. Same residual risk as the converter input.
3. **Shared GPIOs.** GPIO8, 9 and 24 are also on the Pico header (and GPIO8/9 are the first digital
   pins of that header). A Pico accessory plugged into the header that drives those pins would
   switch the outputs: another reason only one accessory class is used at a time.
4. **No current limit in hardware** beyond the fuse and the INA226 readings (firmware can read the INA226 and
   turn an output off). A real electronic current limit would need an e-fuse or load-switch IC.
5. **I2C bus loading.** Both INA226s, the PD controller and the Arduino header share GPIO20/21; the 4.7 kohm
   pull-ups are still to be placed (planned on the IO sheet).
