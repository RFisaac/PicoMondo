"""Per-GPIO indicator LEDs: a 470 ohm resistor and a white LED from the GPIO net to ground.

About 1 mA when the pin is high (white LED, Vf about 2.6 V): bright enough to see, and the LED
does not conduct below about 2.4 V, so inputs, I2C-style pull-ups and button lines still work.
The ADC pins (GPIO40-47) have an open solder jumper in series: bridge it to enable that LED;
left open, the pin sees no extra load (precision analog readings).
Pins without an indicator: GPIO8, 9 (output enables), 12-15, 22 (microSD), 20, 21 (I2C),
23 (WS2812), 24 (+5V_SW enable), 25 (user LED has its own), 34 (PD alert), 35-39 (spare).
"""
from cells import FP_R0402, res

LED = "lcsc:LWQH8G-Q2OO-3K5L-1"
FP_LED = "lcsc:LED-SMD_L1.0-W0.5-RD_WHITE"
JUMPER = "Jumper:SolderJumper_2_Open"
FP_JUMPER = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"

DIGITAL = list(range(0, 8)) + [10, 11] + list(range(16, 20)) + [26, 27] + list(range(28, 32)) + [32, 33]
ADC = list(range(40, 48))


def indicator(s, refs, x, y, gpio, jumper=False):
    """One LED cell: GPIO net -> [open solder jumper] -> 470 ohm -> white LED -> GND."""
    net = f"GPIO{gpio}"
    top = net
    if jumper:
        top = f"LED{gpio}_J"
        j = s.add(JUMPER, refs.next("JP"), "LED enable", FP_JUMPER, x, y - 25.4, rot=90,
                  show_value=False)
        s.attach(j.pin(2), net, length=5.08)       # top contact: the GPIO net
        s.attach(j.pin(1), top, length=5.08)       # bottom contact: to the resistor
    r = s.add("Device:R", refs.next("R"), "470", FP_R0402, x, y)
    s.attach(r.pin(1), top, length=5.08)
    led = s.add(LED, refs.next("D"), "white", FP_LED, x + 2.54, y + 8.89, rot=90,
                extra={"MPN": "LW QH8G-Q2OO-3K5L-1", "LCSC": "C7220928"}, show_value=False)
    s.wire(r.pin(2).pos, led.pin(2).pos)            # resistor bottom to LED anode
    s.attach(led.pin(1), "GND", length=0)           # LED cathode to ground
    s.note(net, x - 5.08, y - (35.56 if jumper else 12.7), size=1.4)


def build(s, refs):
    s.note("GPIO INDICATOR LEDS: 470 ohm + white LED from each listed GPIO net to ground (about 1 mA).\n"
           "GPIO40-47 (ADC pins): LED is disconnected by an open solder jumper; bridge it to turn the LED on.\n"
           "Every pin here is also on a connector or header, so the LED lights for any accessory.",
           25.4, 25.4)
    col = 0
    row = 0
    for g in DIGITAL:
        indicator(s, refs, 38.1 + col * 25.4, 76.2 + row * 55.88, g)
        col += 1
        if col == 10:
            col, row = 0, row + 1
    row += 1
    col = 0
    for g in ADC:
        indicator(s, refs, 38.1 + col * 25.4, 76.2 + row * 55.88 + 12.7, g, jumper=True)
        col += 1
