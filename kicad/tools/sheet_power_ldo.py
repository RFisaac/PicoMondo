"""3.3 V rails: two AP2112K-3.3 linear regulators from +5V.

  +3V3_AUX  always-on supply for the USB-C PD controller (STUSB4500), separate from the MCU rail
  +3V3      MCU, flash, microSD, indicators and the 3.3 V pins on the connectors

Both regulators are always enabled (EN tied to the input). See kicad/docs/power_ldo.md for the
thermal limit: at 5 V in and 3.3 V out the SOT-23-5 package supports about 350 mA, not 600 mA.
"""
from cells import FP_C0805, cap

FP_SOT235 = "Package_TO_SOT_SMD:SOT-23-5"


def ldo(s, refs, x, y, out_net, label):
    u = s.add("Regulator_Linear:AP2112K-3.3", refs.next("U"), "AP2112K-3.3", FP_SOT235, x, y,
              extra={"MPN": "AP2112K-3.3TRG1", "LCSC": "C51118"})
    s.attach(u.pin(1), "+5V", length=10.16)        # input
    s.attach(u.pin(3), "+5V", length=10.16)        # enable tied to input: always on
    s.attach(u.pin(2), "GND")
    s.attach(u.pin(5), out_net, length=10.16)
    cap(s, refs, x - 25.4, y + 7.62, "10u 10V", FP_C0805, "+5V", "GND",
        extra={"LCSC": "C91158"})                   # input capacitor
    cap(s, refs, x + 25.4, y + 7.62, "10u 10V", FP_C0805, out_net, "GND",
        extra={"LCSC": "C91158"})                   # output capacitor
    s.note(label, x - 38.1, y - 25.4)
    return u


def build(s, refs):
    ldo(s, refs, 88.9, 76.2, "+3V3_AUX",
        "+3V3_AUX: always-on supply for the PD controller (needs about 5 mA).\n"
        "Input and output capacitors: 10 uF X5R/X7R, within 5 mm of the regulator pins.")
    ldo(s, refs, 88.9, 152.4, "+3V3",
        "+3V3: MCU, flash, microSD, indicators, connector 3.3 V pins.\n"
        "THERMAL LIMIT: 1.7 V x load current is dissipated here (SOT-23-5, 184 C/W in the datasheet).\n"
        "At 40 C ambient that allows about 350 mA unless the pad is tied to a large copper area.\n"
        "Budget: MCU about 100 mA, flash 20 mA, microSD up to 100 mA, connector loads on top.")
