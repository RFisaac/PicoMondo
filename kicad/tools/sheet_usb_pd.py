"""USB-C input with USB Power Delivery sink controller (STUSB4500).

  USB-C receptacle (USB 2.0 only) --> VBUS (to the power input sheet's diode-OR)
                                  --> D+/D- through an ESD array to the MCU (USB_D+/USB_D-)
                                  --> CC1/CC2 to the STUSB4500, which negotiates the voltage

The STUSB4500 runs in dead-battery mode (CC1DB/CC2DB tied to CC1/CC2) so a PD source always
provides VBUS. It is powered from VBUS (VDD) and from +3V3_AUX (VSYS), and configured over I2C
(address 0x28, GPIO20/GPIO21). There is no VBUS power switch: the 5 V default voltage reaches the
converter first, then the negotiated voltage. See kicad/docs/usb_pd.md.
"""
from cells import FP_C0402, FP_C0603, FP_R0402, cap, res

CONN = "lcsc:USB4105-GF-A"
PD = "Interface_USB:STUSB4500QTR"
ESD_CC = "lcsc:ESDA25W"
TVS_VBUS = "lcsc:ESDA25P35-1U1M"
ESD_USB = "Power_Protection:USBLC6-2SC6"

FP_CONN = "lcsc:TYPE-C-SMD_SBC-160S1A-20-S412"
FP_PD = "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm"
FP_ESD_CC = "lcsc:SOT-323-3_L2.1-W1.3-P1.32-LS2.1-BR"
FP_TVS_VBUS = "lcsc:DFN1610-2_L1.6-W1.0-P1.05-RD"
FP_ESD_USB = "Package_TO_SOT_SMD:SOT-23-6"


def build(s, refs):
    s.note("USB-C RECEPTACLE (USB 2.0 data, power and PD). GCT USB4105-GF-A.\n"
           "Both A and B row contacts of VBUS, GND, D+ and D- are tied together so the plug can go in either way.\n"
           "SBU1/SBU2 are not used.", 25.4, 25.4)
    # ------------------------------------------------------------------ receptacle
    j = s.add(CONN, refs.next("J"), "USB-C", FP_CONN, 88.9, 114.3,
              extra={"MPN": "USB4105-GF-A", "LCSC": "C3020560"})
    for n in ("A4", "A9", "B4", "B9"):
        vbus_end = s.attach(j.pin(n), "VBUS", length=7.62)
    s.flag_net(vbus_end, direction=270)               # VBUS comes from the cable: mark it driven (ERC)
    for n in ("A1", "A12", "B1", "B12"):
        s.attach(j.pin(n), "GND", length=7.62)
    for n in ("1", "2", "3", "4"):                       # shield / mounting contacts
        s.attach(j.pin(n), "GND", length=5.08)
    s.attach(j.pin("A5"), "CC1", length=7.62)
    s.attach(j.pin("B5"), "CC2", length=7.62)
    for n in ("A6", "B6"):
        s.attach(j.pin(n), "USB_DP_CON", length=7.62)
    for n in ("A7", "B7"):
        s.attach(j.pin(n), "USB_DN_CON", length=7.62)
    s.no_connect(j.pin("A8"))
    s.no_connect(j.pin("B8"))

    # ------------------------------------------------------------------ VBUS protection and bulk
    s.note("VBUS: 4.7 uF at the connector, and a one-way 22 V TVS (ESDA25P35-1U1M, ST's reference part;\n"
           "cathode on VBUS). 20 V is the highest PD voltage requested.", 25.4, 160.02)
    cap(s, refs, 63.5, 190.5, "4.7u 25V", "Capacitor_SMD:C_0805_2012Metric", "VBUS", "GND")
    tv = s.add(TVS_VBUS, refs.next("D"), "ESDA25P35-1U1M", FP_TVS_VBUS, 88.9, 190.5, rot=270,
               extra={"MPN": "ESDA25P35-1U1M", "LCSC": "C1974707", "NOTE": "pin 1 = cathode on VBUS"})
    s.attach(tv.pin(1), "VBUS", length=5.08)
    s.attach(tv.pin(2), "GND", length=5.08)

    # ------------------------------------------------------------------ CC line ESD
    s.note("CC1 / CC2 ESD: ESDA25W dual TVS (25 V breakdown; the CC pins tolerate up to 22 V).",
           25.4, 223.52)
    esd = s.add(ESD_CC, refs.next("D"), "ESDA25W", FP_ESD_CC, 63.5, 248.92,
                extra={"MPN": "ESDA25W", "LCSC": "C2935152"})
    s.attach(esd.pin(1), "CC1", length=7.62)
    s.attach(esd.pin(2), "CC2", length=7.62)
    s.attach(esd.pin(3), "GND", length=7.62)

    # ------------------------------------------------------------------ USB 2.0 data ESD
    s.note("USB data ESD: USBLC6-2SC6. Connector side is the _CON nets; the MCU side is USB_D+/USB_D-\n"
           "(the 27 ohm series resistors are on the MCU sheet). Keep the pair 90 ohm differential.",
           165.1, 25.4)
    u2 = s.add(ESD_USB, refs.next("U"), "USBLC6-2SC6", FP_ESD_USB, 190.5, 63.5,
               extra={"MPN": "USBLC6-2SC6", "LCSC": "C7519"})
    s.attach(u2.pin(1), "USB_DP_CON", length=7.62)
    s.attach(u2.pin(6), "USB_D+", length=7.62)
    s.attach(u2.pin(3), "USB_DN_CON", length=7.62)
    s.attach(u2.pin(4), "USB_D-", length=7.62)
    s.attach(u2.pin(5), "VBUS", length=7.62)
    s.attach(u2.pin(2), "GND", length=5.08)

    # ------------------------------------------------------------------ STUSB4500
    s.note("STUSB4500 USB PD SINK CONTROLLER (I2C address 0x28). Dead-battery mode: CC1DB/CC2DB tied to CC1/CC2.\n"
           "Powered from VBUS (VDD) and +3V3_AUX (VSYS). Default contract set in its NVM (5 V 1.5 A / 15 V 1.5 A /\n"
           "20 V 1.0 A); firmware should program the wanted profile once over I2C.", 165.1, 101.6)
    u = s.add(PD, refs.next("U"), "STUSB4500", FP_PD, 254.0, 190.5,
              extra={"MPN": "STUSB4500QTR", "LCSC": "C2678061"})
    s.attach(u.pin(1), "CC1", length=7.62)       # CC1DB
    s.attach(u.pin(2), "CC1", length=7.62)       # CC1
    s.attach(u.pin(4), "CC2", length=7.62)       # CC2
    s.attach(u.pin(5), "CC2", length=7.62)       # CC2DB
    s.attach(u.pin(6), "PD_RESET", length=7.62)  # active-high reset, held low
    s.attach(u.pin(7), "GPIO21", length=7.62)    # SCL
    s.attach(u.pin(8), "GPIO20", length=7.62)    # SDA
    s.attach(u.pin(12), "PD_ADDR0", length=7.62)
    s.attach(u.pin(13), "PD_ADDR1", length=7.62)
    s.attach(u.pin(19), "GPIO34", length=7.62)   # ALERT (open drain, active low)
    s.attach(u.pin(9), "PD_DISCH", length=7.62)
    s.attach(u.pin(18), "PD_VSENSE", length=7.62)
    s.attach(u.pin(24), "VBUS", length=5.08)     # VDD
    s.attach(u.pin(22), "+3V3_AUX", length=5.08)  # VSYS
    s.attach(u.pin(23), "PD_V27", length=5.08)
    s.attach(u.pin(21), "PD_V12", length=5.08)
    s.attach(u.pin(10), "GND", length=5.08)
    s.attach(u.pin(25), "GND", length=5.08)
    for n in (3, 11, 14, 15, 16, 17, 20):        # unused (open-drain outputs and NC)
        s.no_connect(u.pin(n))

    # supporting parts
    x, y = 330.2, 114.3
    cap(s, refs, x, y, "1u 10V", FP_C0402, "PD_V27", "GND")               # VREG_2V7
    cap(s, refs, x + 15.24, y, "1u 10V", FP_C0402, "PD_V12", "GND")       # VREG_1V2
    cap(s, refs, x + 30.48, y, "1u 25V", FP_C0603, "VBUS", "GND")         # VDD decoupling
    res(s, refs, x, y + 38.1, "1k", "VBUS", "PD_VSENSE")                  # limits VBUS discharge current
    res(s, refs, x + 15.24, y + 38.1, "1k", "VBUS", "PD_DISCH")
    res(s, refs, x + 30.48, y + 38.1, "10k", "PD_RESET", "GND")
    res(s, refs, x + 45.72, y + 38.1, "100k", "PD_ADDR0", "GND")          # address 0x28
    res(s, refs, x + 60.96, y + 38.1, "100k", "PD_ADDR1", "GND")
    res(s, refs, x + 76.2, y + 38.1, "4.7k", "+3V3", "GPIO34")            # ALERT pull-up
