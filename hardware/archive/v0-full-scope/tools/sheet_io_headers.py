"""Arduino Uno R3 shield sockets and Pico-compatible sockets.

Both header sets share the GPIO nets with the EdgeLock connectors; use one accessory class at a
time. On the PCB the Pico sockets sit inside the Arduino pin pattern so the two cannot be
plugged in together.

Arduino UART convention (resolves the old open question): D0 is RX = GPIO1, D1 is TX = GPIO0.
VIN on the Arduino power header is the board's +5V, not the raw input voltage.
"""
FP_SOCKET = "Connector_PinSocket_2.54mm:PinSocket_1x{n:02d}_P2.54mm_Vertical"
CONN = "Connector_Generic:Conn_01x{n:02d}"

ARDUINO = [
    ("Arduino power", 8, {1: None, 2: "+3V3", 3: "RUN", 4: "+3V3", 5: "+5V", 6: "GND", 7: "GND", 8: "+5V"},
     "Power header 1x8: NC, IOREF (3.3 V logic level), RESET (RUN), 3.3 V, 5 V, GND, GND, VIN (+5V)."),
    ("Arduino analog", 6, {1: "GPIO40", 2: "GPIO41", 3: "GPIO42", 4: "GPIO43", 5: "GPIO20", 6: "GPIO21"},
     "Analog header 1x6: A0-A3 = GPIO40-43 (ADC0-3), A4 = SDA (GPIO20), A5 = SCL (GPIO21)."),
    ("Arduino digital 0-7", 8, {1: "GPIO1", 2: "GPIO0", 3: "GPIO2", 4: "GPIO3", 5: "GPIO4", 6: "GPIO5",
                                7: "GPIO6", 8: "GPIO7"},
     "Digital 1x8: D0 (RX) = GPIO1, D1 (TX) = GPIO0, D2-D7 = GPIO2-7."),
    ("Arduino digital 8-13", 10, {1: "GPIO32", 2: "GPIO33", 3: "GPIO17", 4: "GPIO19", 5: "GPIO16",
                                  6: "GPIO18", 7: "GND", 8: "AREF", 9: "GPIO20", 10: "GPIO21"},
     "Digital 1x10: D8, D9 = GPIO32, 33; D10 SS = GPIO17; D11 MOSI = GPIO19; D12 MISO = GPIO16;\n"
     "D13 SCK = GPIO18; GND; AREF (joined to +3V3 only if the solder jumper is bridged); SDA, SCL."),
]

PICO_LEFT = {1: "GPIO0", 2: "GPIO1", 3: "GND", 4: "GPIO2", 5: "GPIO3", 6: "GPIO4", 7: "GPIO5", 8: "GND",
             9: "GPIO6", 10: "GPIO7", 11: "GPIO8", 12: "GPIO9", 13: "GND", 14: "GPIO10", 15: "GPIO11",
             16: "GPIO12", 17: "GPIO13", 18: "GND", 19: "GPIO14", 20: "GPIO15"}
# right row listed from Pico pin 40 down to pin 21
PICO_RIGHT = {1: "+5V", 2: "+5V", 3: "GND", 4: "+3V3", 5: "+3V3", 6: "+3V3", 7: "GPIO28", 8: "GND",
              9: "GPIO27", 10: "GPIO26", 11: "RUN", 12: "GPIO22", 13: "GND", 14: "GPIO21", 15: "GPIO20",
              16: "GPIO19", 17: "GPIO18", 18: "GND", 19: "GPIO17", 20: "GPIO16"}


def socket(s, refs, name, n, pins, x, y, mpn="", extra=None):
    c = s.add(CONN.format(n=n), refs.next("J"), name, FP_SOCKET.format(n=n), x, y,
              extra=dict(extra or {}, MPN=mpn) if mpn else extra)
    for pin, net in pins.items():
        if net is None:
            s.no_connect(c.pin(pin))
        else:
            s.attach(c.pin(pin), net, length=7.62)
    return c


def build(s, refs):
    s.note("ARDUINO UNO R3 SHIELD SOCKETS (female). Pin 1 of each header is at the D0 / A0 / NC / D8 end in this\n"
           "numbering; place them on the Uno R3 hole pattern (KiCad footprint Module:Arduino_UNO_R3 has the exact positions).",
           25.4, 25.4)
    x, y = 63.5, 76.2
    for name, n, pins, desc in ARDUINO:
        s.note(desc, x - 25.4, y - 17.78)
        c = socket(s, refs, name, n, pins, x, y, mpn="1x%d 2.54 mm female header" % n)
        if name.endswith("8-13"):
            # AREF to +3V3 through an open solder jumper (bridge to connect)
            aref = s.add("Jumper:SolderJumper_2_Open", refs.next("JP"), "AREF to 3V3",
                         "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", x + 55.88, y - 7.62)
            s.attach(aref.pin(1), "AREF", length=5.08)
            s.attach(aref.pin(2), "+3V3", length=5.08)
        x += 88.9
        if x > 400:
            x, y = 63.5, y + 76.2
    s.note("PICO-COMPATIBLE SOCKETS: two 1x20 female headers, 17.78 mm (700 mil) apart, in the Pico pinout.\n"
           "GP0 = TX, GP1 = RX (Pico convention). GP8/GP9 are also the J7/J8 output enables and GP12-15/GP22 the\n"
           "microSD pins: a Pico accessory must not drive them. VBUS / VSYS are the board's +5V.",
           25.4, 177.8)
    socket(s, refs, "Pico left (pins 1-20)", 20, PICO_LEFT, 63.5, 254.0, mpn="B-2200S20P-A120 (1x20 female)",
           extra={"LCSC": "C124410"})
    socket(s, refs, "Pico right (pins 40-21)", 20, PICO_RIGHT, 152.4, 254.0, mpn="B-2200S20P-A120 (1x20 female)",
           extra={"LCSC": "C124410"})
