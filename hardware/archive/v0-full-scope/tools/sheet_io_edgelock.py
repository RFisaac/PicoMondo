"""EdgeLock connectors J1-J6 and J9, and the per-GPIO indicator LEDs.

The Molex Edge Lock system (series 200890, 2.0 mm pitch) is a wire housing that clips over the
board EDGE and contacts pads on the PCB, so J1-J6 and J9 are rows of edge pads, not SMD parts.
The footprints come from Molex's own KiCad footprints, checked against Molex's sales drawing
2008900206: pads plus the board-edge cut-outs (see kicad/docs/io.md and make_edgelock_fp.py).
(Your spec's "502598-0603" is a different Molex series, a 0.3 mm flat-cable connector.)

Each signal pin has a 100 ohm series resistor between the GPIO net and the connector pad (limits
fault and ESD current from user wiring). The indicator LEDs hang on the GPIO net (shunt, about
1 mA to ground) and do not sit in the signal path.
"""
from cells import FP_R0402, res

CONN = {6: "Connector_Generic:Conn_01x06", 4: "Connector_Generic:Conn_01x04"}
FP = {6: "picomondo:EdgeLock_6ckt_Molex2008900106", 4: "picomondo:EdgeLock_4ckt_Molex2008900104"}
HOUSING = {6: "2008900106", 4: "2008900104"}

# (number, circuits, {pin: net}, description)
CONNECTORS = [
    (1, 6, {1: "GPIO0", 2: "GPIO40", 3: "GND", 4: "+3V3", 5: "GPIO1", 6: "GPIO41"},
     "J1: joystick-ready. GPIO0 and GPIO1 are also UART0 TX / RX; GPIO40/41 are ADC0 / ADC1."),
    (2, 6, {1: "GPIO2", 2: "GPIO42", 3: "GND", 4: "+3V3", 5: "GPIO3", 6: "GPIO43"},
     "J2: joystick-ready. GPIO42/43 are ADC2 / ADC3."),
    (3, 6, {1: "GPIO4", 2: "GPIO44", 3: "GND", 4: "+3V3", 5: "GPIO5", 6: "GPIO45"},
     "J3: joystick-ready. GPIO44/45 are ADC4 / ADC5."),
    (4, 6, {1: "GPIO6", 2: "GPIO46", 3: "GND", 4: "+3V3", 5: "GPIO7", 6: "GPIO47"},
     "J4: joystick-ready. GPIO46/47 are ADC6 / ADC7."),
    (5, 4, {1: "GPIO16", 2: "GPIO17", 3: "GPIO18", 4: "GPIO19"},
     "J5: SPI0 (MISO, CS, SCK, MOSI), shared with the Arduino header."),
    (6, 6, {1: "GPIO10", 2: "GPIO11", 3: "GPIO26", 4: "GPIO27", 5: "+3V3", 6: "GND"},
     "J6: UART1 (TX, RX) plus enable and IRQ lines, for serial modules."),
    (9, 6, {1: "+5V_SW", 2: "GPIO28", 3: "GPIO29", 4: "GPIO30", 5: "GPIO31", 6: "GND"},
     "J9: servo / motor connector: switched 5 V (GPIO24), four PWM-capable GPIOs."),
]

POSITIONS = {1: (88.9, 63.5), 2: (88.9, 114.3), 3: (88.9, 165.1), 4: (88.9, 215.9),
             5: (88.9, 266.7), 6: (254.0, 63.5), 9: (254.0, 114.3)}


def build(s, refs):
    s.note("Pins 1-2 and 5-6 of the 6-pin connectors carry signals; the 100 ohm series resistors protect the MCU\n"
           "from user wiring. Indicator LEDs are on the next sheet. These connectors share GPIOs with the Arduino\n"
           "and Pico headers: use one accessory class at a time.", 25.4, 25.4)
    for num, n, pins, desc in CONNECTORS:
        cx, cy = POSITIONS[num]
        c = s.add(CONN[n], refs.fixed("J", num), f"EdgeLock J{num}", FP[n], cx, cy, in_bom=False,
                  extra={"MPN": f"Molex {HOUSING[n]} (mating housing, bought separately)",
                         "NOTE": "board-edge pads and board cut-outs; no part on the board"})
        s.note(desc, cx - 38.1, cy - 17.78)
        for pin, net in pins.items():
            p = c.pin(pin)
            if net.startswith("GPIO"):
                # 100 ohm in series between the GPIO net and the connector pad
                r = s.add("Device:R", refs.next("R"), "100", FP_R0402, p.x - 5.08 - 3.81, p.y,
                          rot=90)
                s.wire(r.pin(2).pos, p.pos)
                s.attach(r.pin(1), net, length=7.62)
            else:
                s.attach(p, net, length=7.62)
