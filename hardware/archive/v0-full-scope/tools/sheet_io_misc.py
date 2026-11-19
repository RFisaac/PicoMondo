"""Board support: microSD, WS2812B status LED, power and user LEDs, I2C pull-ups, test points,
mounting holes and fiducials.

microSD uses SPI mode on SPI1: GPIO12 = DAT0 (MISO), GPIO13 = CS (DAT3), GPIO14 = CLK,
GPIO15 = CMD (MOSI), GPIO22 = card detect.
"""
from cells import FP_C0402, FP_C0805, FP_R0402, cap, res

SD = "lcsc:503398-1892"
FP_SD = "lcsc:TF-SMD_503398-1892"
WS = "lcsc:WS2812B-V5_C2846931"
FP_WS = "lcsc:LED-SMD_4P-L5.0-W5.0-LS5.4-TL-1"
LED = "lcsc:LWQH8G-Q2OO-3K5L-1"
FP_LED = "lcsc:LED-SMD_L1.0-W0.5-RD_WHITE"
D_SCHOTTKY = "lcsc:1N5819HW-7-F"
FP_D = "lcsc:SOD-123_L2.7-W1.6-LS3.7-RD"

TEST_POINTS = ["+5V", "+3V3", "V_INPUT", "GND", "GND", "+1V1", "+3V3_AUX", "+5V_SW", "VBUS",
               "GPIO20", "GPIO21", "USB_D+", "USB_D-", "GPIO36", "GPIO37", "GPIO38", "GPIO39"]


def build(s, refs):
    # ------------------------------------------------------------------ microSD
    s.note("MICROSD (Molex 5033981892, push-push), SPI mode. 10 kohm pull-ups on CMD, DAT0, CS and the unused\n"
           "DAT1/DAT2 as the SD specification asks. Card detect: the two switch contacts (pins 9, 10) close when\n"
           "a card is inserted, pulling GPIO22 low. Verify pins 9/10 against Molex's drawing (not reachable here).",
           25.4, 25.4)
    u = s.add(SD, refs.next("U"), "microSD", FP_SD, 88.9, 76.2,
              extra={"MPN": "5033981892", "LCSC": "C428492"})
    for pin, net in {1: "SD_DAT2", 2: "GPIO13", 3: "GPIO15", 5: "GPIO14", 7: "GPIO12", 8: "SD_DAT1",
                     9: "GPIO22"}.items():
        s.attach(u.pin(pin), net, length=7.62)
    s.attach(u.pin(4), "+3V3", length=7.62)
    for pin in (6, 10, 11):
        s.attach(u.pin(pin), "GND", length=7.62)
    x = 152.4
    for net in ("SD_DAT2", "GPIO13", "GPIO15", "GPIO12", "SD_DAT1", "GPIO22"):
        res(s, refs, x, 63.5, "10k", "+3V3", net)
        x += 15.24
    cap(s, refs, x, 63.5, "100n", FP_C0402, "+3V3", "GND")
    cap(s, refs, x + 15.24, 63.5, "10u 10V", FP_C0805, "+3V3", "GND")

    # ------------------------------------------------------------------ WS2812B
    s.note("WS2812B-V5 STATUS LED on GPIO23. The LED needs a logic high of 0.63 x VDD (3.15 V at 5 V), which a 3.3 V GPIO\n"
           "barely reaches. A series Schottky diode drops VDD to about 4.6 V, so the threshold falls to about 2.9 V.\n"
           "100 ohm in the data line; DOUT is unused.", 25.4, 139.7)
    d = s.add(D_SCHOTTKY, refs.next("D"), "1N5819HW", FP_D, 63.5, 177.8, rot=180,
              extra={"MPN": "1N5819HW-7-F", "LCSC": "C82544"})
    s.attach(d.pin(2), "+5V", length=7.62)                # anode toward +5V
    s.attach(d.pin(1), "WS_VDD", length=7.62)
    w = s.add(WS, refs.next("D"), "WS2812B-V5", FP_WS, 139.7, 177.8,
              extra={"MPN": "WS2812B-V5", "LCSC": "C2846931"})
    s.attach(w.pin(1), "WS_VDD", length=7.62)
    s.attach(w.pin(3), "GND", length=7.62)
    s.no_connect(w.pin(2))
    r = s.add("Device:R", refs.next("R"), "100", FP_R0402, 177.8, 177.8, rot=90)
    s.attach(r.pin(1), "GPIO23", length=7.62)
    s.wire(r.pin(2).pos, w.pin(4).pos)
    cap(s, refs, 101.6, 190.5, "100n", FP_C0402, "WS_VDD", "GND")

    # ------------------------------------------------------------------ status LEDs
    s.note("STATUS LEDS: power (always on with +3V3) and user LED on GPIO25 (Pico convention). 470 ohm, about 1 mA.",
           25.4, 228.6)
    for i, (src, label) in enumerate((("+3V3", "power"), ("GPIO25", "user"))):
        x0 = 63.5 + i * 38.1
        rr = s.add("Device:R", refs.next("R"), "470", FP_R0402, x0, 254.0)
        s.attach(rr.pin(1), src, length=0 if src in ("+3V3",) else 5.08)
        led = s.add(LED, refs.next("D"), label, FP_LED, x0 + 2.54, 262.89, rot=90,
                    extra={"MPN": "LW QH8G-Q2OO-3K5L-1", "LCSC": "C7220928"}, show_value=True)
        s.wire(rr.pin(2).pos, led.pin(2).pos)
        s.attach(led.pin(1), "GND", length=0)

    # ------------------------------------------------------------------ I2C pull-ups
    s.note("I2C0 pull-ups (one set for the whole bus: STUSB4500, two INA226 and the Arduino header): 4.7 kohm to +3V3.",
           190.5, 228.6)
    res(s, refs, 203.2, 254.0, "4.7k", "+3V3", "GPIO20")
    res(s, refs, 218.44, 254.0, "4.7k", "+3V3", "GPIO21")

    # ------------------------------------------------------------------ test points
    s.note("TEST POINTS (1.5 mm pads): rails, ground, I2C, USB, and the spare GPIO36-39 for expansion.", 25.4, 292.1)
    for i, net in enumerate(TEST_POINTS):
        tp = s.add("Connector:TestPoint", refs.next("TP"), net, "TestPoint:TestPoint_Pad_D1.5mm",
                   38.1 + i * 20.32, 317.5, rot=0, show_value=True)
        s.attach(tp.pin(1), net, length=5.08)

    # ------------------------------------------------------------------ mechanical
    s.note("MECHANICAL: 4 x M3 mounting holes (Pi HAT hole spacing if practical) and 3 fiducials.", 25.4, 355.6)
    for i in range(4):
        s.add("Mechanical:MountingHole", refs.next("H"), "M3", "MountingHole:MountingHole_3.2mm_M3",
              38.1 + i * 25.4, 374.65, show_ref=True)
    for i in range(3):
        s.add("Mechanical:Fiducial", refs.next("FID"), "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm",
              165.1 + i * 25.4, 374.65, show_ref=True)
