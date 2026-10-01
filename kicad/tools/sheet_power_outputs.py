"""Switched power outputs: J7 (5 V), J8 (V_INPUT) and +5V_SW (for the J9 servo/motor connector).

Each channel is a high-side P-channel switch driven by a GPIO through an NPN transistor:

  rail --[shunt]-- SRC --(source) P-FET (drain)-- DRAIN --[fuse]-- OUT --+-- terminal
                    |  R_gs (and, for J8, a 12 V zener) to the gate      |-- flyback diode to GND
                    +-- INA226 monitors voltage and current             +-- 10k bleeder to GND

  GPIO -- 10k -- NPN base; NPN collector -- R_g -- gate. GPIO high = output on.
  With the GPIO low or floating, R_gs holds the gate at the source, so the output is off at power-up.

J7 and J8 are monitored by INA226 current/voltage monitors (I2C 0x40 and 0x41). +5V_SW has no monitor.
J8 can switch up to 28 V, so its P-FET is a 40 V part and a zener limits the gate-source voltage to 12 V.
See kicad/docs/power_outputs.md.
"""
from cells import FP_C0402, FP_C0603, FP_R0402, FP_R0603, cap, res

PFET_SMALL = "Transistor_FET:Q_PMOS_GSD"
PFET_BIG = "lcsc:DMP4015SSS-13"
NPN = "Transistor_BJT:MMBT3904"
INA = "Sensor_Energy:INA226"
D_SS54 = "lcsc:SS54-HF"
FUSE = "lcsc:1812L300_33GR"
TERM = "lcsc:KF301-5.0-2P"
SHUNT = "lcsc:GX2512-2W-20MR-1%"

FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SO8 = "lcsc:SO-8_L4.9-W3.9-P1.27-LS5.9-BL"
FP_VSSOP10 = "Package_SO:MSOP-10_3x3mm_P0.5mm"   # TI DGS (VSSOP-10), same 3x3 mm / 0.5 mm outline
FP_SMA = "lcsc:SMA_L4.3-W2.5-LS5.0-RD"
FP_FUSE = "lcsc:F1812"
FP_TERM = "lcsc:CONN-TH_P5.00_KF301-5.0-2P"
FP_SHUNT = "lcsc:R2512"
FP_SOD123 = "Diode_SMD:D_SOD-123"
FP_LED = "LED_SMD:LED_0603_1608Metric"


def channel(s, refs, x, y, name, rail, enable, out_net, big_fet=False, ina_a0=None, terminal=None,
            term_ref=None, led=False, desc=""):
    """One switched output. (x, y) is the centre of the shunt; the chain runs left to right."""
    n = name.replace("+", "").replace("5V_SW", "SW")
    src, drain, gate, gcol, base = f"{n}_SRC", f"{n}_DRAIN", f"{n}_GATE", f"{n}_GCOL", f"{n}_BASE"
    s.note(desc, x - 25.4, y - 40.64)

    # ---- shunt (monitored channels only) and power P-FET
    if ina_a0 is not None:
        res_ = s.add(SHUNT, refs.next("R"), "20m 1% 2W",
                     FP_SHUNT, x, y, rot=90, extra={"MPN": "GX2512-2W-20mR-1%", "LCSC": "C500720"})
        s.attach(res_.pin(1), rail, length=7.62)
        s.attach(res_.pin(2), src, length=7.62)
        src_net = src
    else:
        src_net = rail                       # no monitor: the FET source is the rail itself
    qx = x + 50.8
    if big_fet:
        q = s.add(PFET_BIG, refs.next("Q"), "DMP4015SSS-13", FP_SO8, qx, y + 12.7,
                  extra={"MPN": "DMP4015SSS-13", "LCSC": "C508210"})
        s.bus([q.pin(1), q.pin(2), q.pin(3)], src_net)          # source pins
        s.bus([q.pin(n_) for n_ in (5, 6, 7, 8)], drain)         # drain pins
        gate_pin = q.pin(4)
        s.attach(gate_pin, gate, length=7.62)
    else:
        q = s.add(PFET_SMALL, refs.next("Q"), "SI2305A", FP_SOT23, qx, y + 12.7, rot=180,
                  extra={"MPN": "SI2305A", "LCSC": "C347488"})
        s.attach(q.pin(2), src_net, length=5.08)               # source toward the supply
        s.attach(q.pin(3), drain, length=5.08)
        s.attach(q.pin(1), gate, length=7.62)

    # ---- gate network: R_gs (and zener for J8) from source to gate, series R_g, NPN, base resistors
    gx = x + 101.6
    res(s, refs, gx, y + 12.7, "47k", src_net, gate)
    if big_fet:
        z = s.add("Device:D_Zener", refs.next("D"), "BZT52C12 12V", FP_SOD123, gx + 15.24, y + 12.7,
                  rot=270, extra={"MPN": "BZT52C12-13-F", "LCSC": "C177013"})
        s.attach(z.pin(1), src_net, length=5.08)                # cathode to source
        s.attach(z.pin(2), gate, length=5.08)                   # anode to gate: Vgs limited to -12 V
    res(s, refs, gx + 30.48, y + 12.7, "22k" if big_fet else "10k", gate, gcol,
        fp=FP_R0603 if big_fet else FP_R0402)
    nq = s.add(NPN, refs.next("Q"), "MMBT3904", FP_SOT23, gx + 55.88, y + 25.4,
               extra={"MPN": "MMBT3904LT1G", "LCSC": "C81464"})
    s.attach(nq.pin(3), gcol, length=5.08)
    s.attach(nq.pin(2), "GND", length=5.08)
    s.attach(nq.pin(1), base, length=5.08)
    res(s, refs, gx + 55.88 - 20.32, y + 38.1, "10k", enable, base, rot=90)
    res(s, refs, gx + 55.88 - 10.16, y + 50.8, "100k", base, "GND")

    # ---- output: fuse, flyback diode, bleeder, terminal
    ox = gx + 101.6
    f = s.add(FUSE, refs.next("F"), "3A hold 33V", FP_FUSE, ox, y + 12.7,
              extra={"MPN": "1812L300/33GR", "LCSC": "C54300298"})
    s.attach(f.pin(1), drain, length=7.62)
    s.attach(f.pin(2), out_net, length=7.62)
    if terminal:
        d = s.add(D_SS54, refs.next("D"), "SS54-HF", FP_SMA, ox + 25.4, y + 30.48, rot=270,
                  extra={"MPN": "SS54-HF", "LCSC": "C3757794"})
        s.attach(d.pin(1), out_net, length=5.08)               # cathode to the output
        s.attach(d.pin(2), "GND", length=5.08)
        # bleeder: 10k at 5 V; 22k on J8 so it stays within a 0402 resistor at 28 V (36 mW)
        res(s, refs, ox + 40.64, y + 30.48, "22k" if big_fet else "10k", out_net, "GND")
        j = s.add(TERM, term_ref, terminal, FP_TERM, ox + 66.04, y + 12.7,
                  extra={"MPN": "KF301-5.0-2P", "LCSC": "C474881"})
        s.attach(j.pin(1), out_net, length=7.62)
        s.attach(j.pin(2), "GND", length=7.62)
    if led:
        # indicator on the switched rail (red 0603, about 6 mA)
        res(s, refs, ox + 25.4, y + 30.48, "470", out_net, f"{n}_LED")
        ld = s.add("Device:LED", refs.next("D"), "red", FP_LED, ox + 25.4, y + 48.26, rot=90,
                   extra={"MPN": "KT-0603R", "LCSC": "C2286"})
        s.attach(ld.pin(2), f"{n}_LED", length=5.08)
        s.attach(ld.pin(1), "GND", length=5.08)

    # ---- INA226 monitor
    if ina_a0 is not None:
        ix = x + 25.4
        iy = y - 20.32
        u = s.add(INA, refs.next("U"), f"INA226 ({'0x40' if ina_a0 == 'GND' else '0x41'})", FP_VSSOP10,
                  ix + 101.6, iy, extra={"MPN": "INA226AIDGSR", "LCSC": "C49851"})
        s.attach(u.pin(10), rail, length=10.16)                # IN+ : supply side of the shunt
        s.attach(u.pin(9), src, length=10.16)                  # IN- : load side
        s.attach(u.pin(8), src, length=10.16)                  # VBUS: measure the switched side
        s.attach(u.pin(6), "+3V3", length=5.08)
        s.attach(u.pin(7), "GND", length=5.08)
        s.attach(u.pin(1), "GND", length=7.62)                 # A1 = GND
        s.attach(u.pin(2), ina_a0, length=7.62)                # A0: GND = 0x40, +3V3 = 0x41
        s.attach(u.pin(4), "GPIO20", length=7.62)
        s.attach(u.pin(5), "GPIO21", length=7.62)
        s.no_connect(u.pin(3))                                 # ALERT not used
        cap(s, refs, ix + 127.0, iy - 15.24, "100n", FP_C0402, "+3V3", "GND")


def build(s, refs):
    channel(s, refs, 63.5, 76.2, "J7", "+5V", "GPIO8", "J7_OUT", terminal="J7 5V out", term_ref=refs.fixed("J", 7),
            ina_a0="GND",
            desc="J7: switched 5 V output, up to 3 A. GPIO8 high = on. INA226 at I2C 0x40.\n"
                 "Shunt 20 mohm: the INA226 input range is only +/-81.92 mV, so 3 A needs 27 mohm or less.")
    channel(s, refs, 63.5, 203.2, "J8", "V_INPUT", "GPIO9", "J8_OUT", big_fet=True, terminal="J8 V_INPUT out", term_ref=refs.fixed("J", 8),
            ina_a0="+3V3",
            desc="J8: switched V_INPUT output (about 5 V to 28 V), up to 3 A. GPIO9 high = on. INA226 at 0x41.\n"
                 "40 V P-FET with a 12 V zener limiting the gate-source voltage; INA226 is rated 36 V.")
    channel(s, refs, 63.5, 330.2, "+5V_SW", "+5V", "GPIO24", "+5V_SW", led=True,
            desc="+5V_SW: switched 5 V for the J9 servo/motor connector, up to 3 A. GPIO24 high = on.\n"
                 "No current monitor. The red LED shows the rail is on.")
    s.flag("+5V_SW", (63.5, 393.7))      # the switched rail is driven by the FET (ERC)
