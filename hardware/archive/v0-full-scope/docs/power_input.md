# Power input sheet

Sheet: `power_input.kicad_sch`. Three inputs share one rail through Schottky diodes:
USB-C VBUS (from the PD sheet), a 5.5 x 2.1 mm barrel jack, and a WAGO push-in terminal.

```
VBUS   -|>|-+
BARREL -|>|-+- V_RAW -[F1 fuse]- V_INPUT -+- TVS - GND
TERM   -|>|-+
```

| Part | Choice | Notes |
|------|--------|-------|
| Diodes | SS54F-HF (Comchip, 5 A 40 V, LCSC C5142774) x3 | About 0.4 V at 1 A. They block reverse polarity and stop sources back-feeding each other. |
| Fuse | Lute 2920L500/30GR (5 A hold, 30 V, C19078763) | Before the TVS, so a shorted TVS opens the fuse. Datasheet in `resources/datasheets/`. |
| TVS | Littelfuse SMBJ28A, one-way (C178227) | Working voltage 28 V. One-way because the diodes already block reverse polarity. |
| Barrel jack | CUI PJ-102AH (C3096093) | **Rated 24 V**, not 28 V. 5 A. |
| Terminal | WAGO 2060-452/998-404 (C2765055) | 28 V. Pin 1 positive, pin 2 ground. |

## Things to know

- **Barrel jack pins.** Pin 1 is the centre pin (positive) per the CUI datasheet and KiCad's library.
  Pins 2 and 3 are the sleeve and a switch contact; I tied both to ground, which is safe whichever is
  the sleeve. The old atopile design had pin 3 as positive and pin 1 as ground, which contradicts the
  datasheet. Check with a plug and a meter on the first board. If I have the centre pin wrong, the
  diode blocks the jack and nothing is damaged; the barrel input just would not power the board.
- **Voltage limit.** The jack is rated 24 V but the design range is 28 V. Either tell users to use a 24 V
  supply at the jack, or choose a jack with a higher rating (CUI PJ-102AH alternatives, DigiKey
  Tensility 54-00164 was the earlier preference).
- **TVS margin.** The converter's VIN and SW1 pins stop at 40 V absolute. The SMBJ28A clamps near
  38 V at about 5 A of surge and 45 V at its 13 A rating. OK indoors; add an over-voltage cut-off
  stage if surges are expected.
- **Diode loss.** Up to about 2.7 W at 5 A through one diode (0.55 V x 5 A). At 12 V in, input
  current for 25 W out is about 2.3 A, so about 1 W. A 5 V USB source gives about 4.6 V at the
  converter.
- **USB-C VBUS** is a global net `VBUS`, to be driven by the PD sheet.
