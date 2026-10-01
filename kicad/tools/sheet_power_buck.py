"""5 V rail: TPS55288 buck-boost converter (V_INPUT -> +5V, up to 5 A).

Follows TI's reference circuit (TPS55288 datasheet SLVSF01B, figure 8-1) with these choices:
  * output fixed at 5 V by the chip's power-up default (internal feedback, no divider needed)
  * 400 kHz switching (RFSW 49.9k), forced-PWM at light load (MODE shorted to AGND via 0R)
  * 10 mohm output sense resistor: default current limit of 50 mV / 10 mohm = 5 A
  * both external buck-side MOSFETs are 60 V CSD18543Q3A (the 40 V low-side part in the web
    design was marginal against the 40 V absolute maximum on VIN/SW1)
  * ILIM resistor 33.2k (about 10 A average inductor limit; 330000 / R from the datasheet)
See kicad/docs/power_buck_boost.md for the design calculations.
"""
from cells import (FP_C0402, FP_C0603, FP_C0805, FP_C1206, FP_R0402, FP_R2512, cap, res)

U = "lcsc:TPS55288RPMR"
Q = "lcsc:CSD18543Q3A"
FP_TPS = "lcsc:VQFN-HR-26_L4.0-W3.5_TPS55288RPMR"
FP_Q = "lcsc:VSONP-8_L3.1-W3.1-P0.65-LS3.5-BL"
FP_L = "Inductor_SMD:L_Coilcraft_XAL1010-XXX"
FP_CP = "Capacitor_SMD:CP_Elec_8x10"


def build(s, refs):
    # ------------------------------------------------------------------ controller
    u = s.add(U, refs.next("U"), "TPS55288", FP_TPS, 299.72, 152.4,
              extra={"MPN": "TPS55288RPMR", "LCSC": "C2864583"})
    left = {1: "DR1L", 2: "DR1H", 3: "V_INPUT", 4: "EN_UVLO", 5: "GPIO21", 6: "GPIO20",
            7: "DITH", 8: "FSW", 9: "GND", 10: "AGND", 11: "VOUT_PRE", 12: "VOUT_PRE"}
    right = {13: "+5V", 14: "GPIO35", 15: "MODE", 16: "CDC", 17: "ILIM", 18: "COMP",
             19: "VCC_TPS", 20: "BOOT2", 21: "SW2", 22: "BOOT1", 23: "SW1"}
    for n, net in left.items():
        s.attach(u.pin(n), net, length=12.7)
    for n, net in right.items():
        s.attach(u.pin(n), net, length=12.7)
    s.attach(u.pin(24), "GND")
    s.attach(u.pin(25), "SW2")
    s.attach(u.pin(26), "VOUT_PRE")

    # ------------------------------------------------------------------ input capacitors
    x, y = 38.1, 63.5
    s.note("INPUT: 4 x 10 uF 50 V ceramic (about 20 uF effective after DC-bias derating, TI recommends at least\n"
           "4.7 uF effective), 100 nF close to the VIN pin. Optional 100 uF bulk (DNP) for long supply leads.\n"
           "Place the ceramics right at the buck-side FET drain and PGND (shortest loop).", x - 12.7, y - 25.4)
    for i in range(4):
        cap(s, refs, x + 12.7 * i, y, "10u 50V", FP_C1206, "V_INPUT", "GND",
            extra={"LCSC": "C7432782"})
    cap(s, refs, x + 12.7 * 4, y, "100n 50V", FP_C0402, "V_INPUT", "GND")
    bulk = s.add("Device:C_Polarized", refs.next("C"), "100u 50V", FP_CP, x + 12.7 * 5, y, dnp=True)
    s.attach(bulk.pin(1), "V_INPUT", length=5.08)
    s.attach(bulk.pin(2), "GND", length=0)

    # ------------------------------------------------------------------ buck-side FETs + inductor
    s.note("POWER STAGE: keep V_INPUT -> Q1 -> Q2 -> GND -> input caps loop tiny; SW1/SW2 traces short and wide,\n"
           "top layer, no vias. Inductor: 4.7 uH, saturation current 12 A or more, DCR 12 mohm or less\n"
           "(Coilcraft XAL1010-472 or equivalent). 0.1 uF bootstrap caps right at BOOT/SW pins.", 114.3, 160.0)
    q1 = s.add(Q, refs.next("Q"), "CSD18543Q3A", FP_Q, 152.4, 88.9,
               extra={"MPN": "CSD18543Q3A", "LCSC": "C840100"})
    s.bus([q1.pin(1), q1.pin(2), q1.pin(3)], "SW1")            # source -> switch node
    s.attach(q1.pin(4), "DR1H", length=7.62)
    s.bus([q1.pin(n) for n in (5, 6, 7, 8, 9)], "V_INPUT")      # drain -> input
    q2 = s.add(Q, refs.next("Q"), "CSD18543Q3A", FP_Q, 152.4, 127.0,
               extra={"MPN": "CSD18543Q3A", "LCSC": "C840100"})
    s.bus([q2.pin(1), q2.pin(2), q2.pin(3)], "GND")            # source -> ground
    s.attach(q2.pin(4), "DR1L", length=7.62)
    s.bus([q2.pin(n) for n in (5, 6, 7, 8, 9)], "SW1")          # drain -> switch node

    l1 = s.add("Device:L", refs.next("L"), "4.7u", FP_L, 215.9, 109.22, rot=90,
               extra={"MPN": "XAL1010-472MED", "LCSC": "C19271849",
                      "NOTE": "4.7uH, Isat 25A, DCR 10 mohm (TI reference inductor)"})
    s.attach(l1.pin(1), "SW1", length=5.08)
    s.attach(l1.pin(2), "SW2", length=5.08)
    cap(s, refs, 190.5, 63.5, "100n 25V", FP_C0402, "BOOT1", "SW1")
    cap(s, refs, 215.9, 63.5, "100n 25V", FP_C0402, "BOOT2", "SW2")

    # ------------------------------------------------------------------ output and current sense
    x, y = 400.05, 63.5
    s.note("OUTPUT: 4 x 22 uF 16 V ceramic on the converter side of the sense resistor (the loop is compensated\n"
           "for 10 uF minimum effective capacitance), plus 2 x 22 uF after it. ISP/ISN are Kelvin\n"
           "connections to the two ends of R_SNS: route them as a pair, separate from the power copper.",
           x - 25.4, y - 25.4)
    for i in range(4):
        cap(s, refs, x + 12.7 * i, y + 38.1, "22u 16V", FP_C1206, "VOUT_PRE", "GND",
            extra={"LCSC": "C2985039"})
    cap(s, refs, x + 12.7 * 4, y + 38.1, "100n 25V", FP_C0402, "VOUT_PRE", "GND")
    sns = s.add("Device:R", refs.next("R"), "10m 1% 1W", FP_R2512, x - 12.7, y + 12.7, rot=90,
                extra={"MPN": "GX2512-2W-10mR-1%", "LCSC": "C500718"})
    s.attach(sns.pin(1), "VOUT_PRE", length=7.62)
    s.attach(sns.pin(2), "+5V", length=7.62)
    for i in range(2):
        cap(s, refs, x + 12.7 * i, y + 83.82, "22u 16V", FP_C1206, "+5V", "GND",
            extra={"LCSC": "C2985039"})
    s.flag("+5V", (x + 12.7 * 3, y + 76.2))

    # ------------------------------------------------------------------ control network
    x, y = 63.5, 215.9
    s.note("CONTROL NETWORK (all AGND returns go to the AGND island, which joins GND only at the net tie\n"
           "next to the VCC capacitor, as in TI's layout example).", x - 12.7, y - 25.4)
    cap(s, refs, x, y, "10u 16V", FP_C0805, "VCC_TPS", "AGND")                      # VCC bypass
    s.flag("AGND", (x - 12.7, y + 12.7))
    res(s, refs, x + 25.4, y, "49.9k 1%", "FSW", "AGND")                              # 400 kHz
    cap(s, refs, x + 50.8, y, "10n", FP_C0402, "DITH", "AGND")                        # spread spectrum
    res(s, refs, x + 76.2, y, "33.2k 1%", "ILIM", "AGND")                             # ~10 A avg limit
    res(s, refs, x + 101.6, y, "100k", "CDC", "AGND")                                 # cable comp unused
    res(s, refs, x + 127.0, y, "0", "MODE", "AGND",
        extra={"NOTE": "0R = internal VCC, I2C 0x74, forced PWM. 6.19k = PFM at light load"})
    # loop compensation: COMP -> R_c + C_c to AGND, optional C_p in parallel
    rc = s.add("Device:R", refs.next("R"), "7.5k", FP_R0402, x + 152.4, y)
    cc = s.add("Device:C", refs.next("C"), "3.3n", FP_C0402, x + 152.4, y + 7.62)
    s.attach(rc.pin(1), "COMP", length=5.08)
    s.attach(cc.pin(2), "AGND", length=0)
    cap(s, refs, x + 165.1, y, "10p", FP_C0402, "COMP", "AGND", dnp=True)
    # EN/UVLO divider on V_INPUT: turn-on about 4.3 V, turn-off about 3.2 V
    ra = s.add("Device:R", refs.next("R"), "220k 1%", FP_R0402, x + 190.5, y)
    rb = s.add("Device:R", refs.next("R"), "88.7k 1%", FP_R0402, x + 190.5, y + 7.62)
    s.attach(ra.pin(1), "V_INPUT", length=5.08)
    s.attach(rb.pin(2), "AGND", length=0)
    node = ra.pin(2).pos
    end = (node[0] + 10.16, node[1])
    s.wire(node, end)
    s.label("EN_UVLO", end, 0)
    # fault output pull-up (FB/INT is a fault indicator with internal feedback)
    res(s, refs, x + 215.9, y, "10k", "+3V3", "GPIO35")
    # AGND <-> GND tie
    nt = s.add("Device:NetTie_2", refs.next("NT"), "AGND-GND", "NetTie:NetTie-2_SMD_Pad0.5mm",
               x + 241.3, y + 5.08, show_value=False)
    s.attach(nt.pin(1), "AGND", length=5.08)
    s.attach(nt.pin(2), "GND", length=5.08)
