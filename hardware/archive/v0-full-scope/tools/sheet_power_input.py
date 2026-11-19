"""Power inputs: USB-C VBUS, barrel jack and push-in terminal, joined by a Schottky diode-OR,
then a resettable fuse and a TVS to make V_INPUT.

  VBUS  --|>|--+
  BARREL --|>|--+-- V_RAW --[fuse]-- V_INPUT --+-- TVS --- GND
  TERM  --|>|--+

Diodes block reverse polarity on any input and stop one source back-feeding another.
The fuse sits before the TVS so a failed (shorted) TVS opens the fuse.
See kicad/docs/power_input.md.
"""
from cells import FP_C0402

J_BARREL = "lcsc:PJ-102AH_C3096093"
J_TERM = "lcsc:2060-452_998-404"
D_SCHOTTKY = "lcsc:SS54F-HF"
F_PTC = "lcsc:2920L500_30GR"
D_TVS = "lcsc:SMBJ28A-C178227"

FP_BARREL = "lcsc:DC-IN-TH_PJ-102AH"
FP_TERM = "lcsc:CONN-SMD_2060-452"
FP_SS54F = "lcsc:DO-214AD_L4.0-W2.5-LS4.8-FD"
FP_FUSE = "lcsc:F2920"
FP_TVS = "lcsc:SMB_L4.6-W3.6-LS5.3-RD"


def diode(s, refs, x, y, anode, cathode, mpn="SS54F-HF"):
    """Schottky diode drawn left to right: anode on the left, cathode on the right."""
    d = s.add(D_SCHOTTKY, refs.next("D"), "SS54F-HF 5A 40V", FP_SS54F, x, y, rot=180,
              extra={"MPN": mpn, "LCSC": "C5142774"})
    s.attach(d.pin(2), anode, length=7.62)      # pin 2 = anode (left after rotation)
    s.attach(d.pin(1), cathode, length=7.62)    # pin 1 = cathode
    return d


def build(s, refs):
    s.note("POWER INPUTS (any one, or several at once; the highest voltage wins through its diode)\n"
           "USB-C: VBUS comes from the USB-C / PD sheet.  Barrel jack: 5.5 x 2.1 mm, centre positive.\n"
           "Push-in terminal: pin 1 is positive, pin 2 is ground (mark on silkscreen).\n"
           "Range: about 5 V to 28 V. The barrel jack is rated 24 V (CUI PJ-102AH), the rest 28 V.",
           25.4, 25.4)

    # ------------------------------------------------------------------ connectors
    j1 = s.add(J_BARREL, refs.next("J"), "Barrel 5.5x2.1", FP_BARREL, 50.8, 76.2,
               extra={"MPN": "PJ-102AH", "LCSC": "C3096093"})
    s.attach(j1.pin(1), "BARREL_IN", length=7.62)      # centre pin (tip), positive
    s.attach(j1.pin(2), "GND", length=7.62)            # sleeve / switch contacts, both to ground:
    s.attach(j1.pin(3), "GND", length=7.62)            # whichever is the sleeve ends up grounded
    s.note("Pin 1 is the centre pin (CUI datasheet). Pins 2 and 3 are the sleeve and the switch contact;\n"
           "tying both to ground is safe for either assignment. Verify with a plug and a meter on the\n"
           "first board.", 25.4, 99.06)
    j2 = s.add(J_TERM, refs.next("J"), "Terminal 2P", FP_TERM, 50.8, 139.7,
               extra={"MPN": "2060-452/998-404", "LCSC": "C2765055"})
    s.attach(j2.pin(1), "TERM_IN", length=7.62)        # +
    s.attach(j2.pin(2), "GND", length=7.62)            # -

    # ------------------------------------------------------------------ diode-OR
    diode(s, refs, 127.0, 63.5, "VBUS", "V_RAW")
    diode(s, refs, 127.0, 76.2, "BARREL_IN", "V_RAW")
    diode(s, refs, 127.0, 139.7, "TERM_IN", "V_RAW")
    s.note("Schottky diodes: about 0.4 V drop at 1 A, up to about 0.55 V at 5 A (2.7 W worst case at 5 A).\n"
           "A 5 V USB source therefore reaches the converter at about 4.6 V; the buck-boost\n"
           "handles that.", 101.6, 38.1)

    # ------------------------------------------------------------------ fuse and TVS
    f1 = s.add(F_PTC, refs.next("F"), "5A hold 30V", FP_FUSE, 203.2, 101.6,
               extra={"MPN": "2920L500/30GR", "LCSC": "C19078763"})
    s.attach(f1.pin(1), "V_RAW", length=7.62)
    s.attach(f1.pin(2), "V_INPUT", length=7.62)
    s.note("Resettable fuse: 5 A hold, rated 30 V. Sits before the TVS so a shorted TVS opens it.\n"
           "TVS: SMBJ28A, one-way (reverse polarity is already blocked by the diodes), working voltage 28 V.\n"
           "It clamps near 38 V for a modest surge (about 45 V at 13 A), and the converter's absolute maximum\n"
           "is 40 V: acceptable indoors, add an over-voltage cut-off stage if surges are expected.",
           127.0, 165.1)
    tvs = s.add(D_TVS, refs.next("D"), "SMBJ28A", FP_TVS, 254.0, 114.3, rot=270,
                extra={"MPN": "SMBJ28A", "LCSC": "C178227"})
    s.attach(tvs.pin(1), "V_INPUT", length=7.62)       # cathode toward the supply
    s.attach(tvs.pin(2), "GND", length=7.62)
