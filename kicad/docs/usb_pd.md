# USB-C and Power Delivery

Sheet: `usb_pd.kicad_sch`. USB-C receptacle (GCT USB4105-GF-A, USB 2.0 data, rated 20 V),
STUSB4500 PD sink controller, and the protection around them. Source for the hookup: ST's STUSB4500
datasheet (DS12499 rev 5, section 6 and figure 10) in `resources/datasheets/`.

## What each part does

| Part | Role |
|------|------|
| STUSB4500 (U) | Negotiates the VBUS voltage with the charger over the CC wires. I2C address 0x28 (ADDR0/1 low). |
| ESDA25P35-1U1M | One-way TVS on VBUS (22 V stand-off, 23-26 V breakdown), pin 1 = cathode on VBUS. ST's reference part. |
| ESDA25W | Dual TVS on CC1 and CC2 (cathodes to the CC lines, common anode to GND). ST's reference part. |
| USBLC6-2SC6 | ESD for D+/D-. Connector side `USB_DP_CON` / `USB_DN_CON`, MCU side `USB_D+` / `USB_D-`. |
| 4.7 uF 25 V | Bulk capacitor on VBUS at the connector. |

## Hookup (follows ST's reference, with the choices below)

- **Dead-battery mode:** CC1DB tied to CC1, CC2DB to CC2. A PD charger always supplies VBUS, even
  with no other power on the board.
- **Supplies:** VDD (pin 24) from VBUS (4.1-22 V); VSYS (pin 22) from `+3V3_AUX` (3.0-5.5 V). ST says VDD
  is required for VBUS monitoring; VSYS keeps the chip, and its I2C pins, alive when only the barrel jack
  powers the board.
- **VBUS sense and discharge:** `VBUS_VS_DISCH` (pin 18) and `DISCH` (pin 9) each through 1 kohm to VBUS (ST
  uses 1 kohm; it limits the discharge current, maximum 50 mA on pin 18).
- **Internal regulators:** 1 uF on `VREG_2V7` and `VREG_1V2`.
- **I2C:** SCL/SDA on GPIO21/GPIO20 (shared bus; pull-ups still to be placed). ALERT on GPIO34 with a 4.7 kohm
  pull-up to +3V3. RESET (active high) pulled low with 10 kohm.
- **Not used:** VBUS_EN_SNK, POWER_OK2/3, GPIO, A_B_SIDE, ATTACH (all open-drain outputs, left floating),
  and the SBU pins. There is no VBUS power-path switch: the board is powered as soon as the charger
  provides 5 V, then the voltage steps to the negotiated one (the buck-boost accepts 4.6 V to 28 V).

## Power profile (firmware task)

The chip's factory profile, from its datasheet: 5 V at 1.5 A, 15 V at 1.5 A, 20 V at 1.0 A. That works
as is (22 W at 15 V), but the board wants more. Program the NVM once over I2C, for example
PDO1 5 V 3 A, PDO2 12 V 3 A, PDO3 20 V 2 A, or whatever the exhibit needs, using ST's STUSB4500 library.
The converter's usable output power is whatever the charger can supply at the negotiated voltage,
minus about 10% conversion loss and the diode drop.

## Things to know

1. **VBUS surge.** VDD's absolute maximum is 28 V; the TVS clamps near 29-31 V at 10 A (ST's own choice). A large
   hot-plug surge could exceed that; this is ST's reference and is normal practice.
2. **Plain 5 V sources** (a USB-A to USB-C cable) give a 5 V default current of 0.5-1.5 A, so the 5 V
   converter cannot reach 5 A. Expect brown-outs under load; firmware can read the PD state from the
   STUSB4500 over I2C.
3. **Connector footprint** was checked against GCT's recommended PCB layout (pad widths, 0.5 mm pitch, shell slots 8.64 mm apart,
   positioning holes). The shield is tied directly to GND. Reflow the connector first: the 16 signal pads are fine pitch.
4. **TVS polarity.** The ESDA25P35 is polarised (DFN1610): JLCPCB places it from the polarity data in the
   footprint; check the pin-1 mark after assembly.
