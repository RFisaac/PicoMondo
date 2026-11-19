"""Generate the PicoMondo README graphics as standalone SVGs."""
import math, os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
FONT = "Inter, 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif"

BG = "#0e1a14"
PANEL = "#15281f"
PANEL_LINE = "#2a4a3a"
TEXT = "#eef4f0"
MUTED = "#9db5a8"
GOLD = "#e3b341"
BLUE = "#5cc8ff"
ORANGE = "#ff9f43"
PURPLE = "#b79cff"
RED = "#ff6b6b"
GREEN = "#4cd087"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_open(w, h, title):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="{FONT}" role="img" aria-label="{esc(title)}">',
        f"<title>{esc(title)}</title>",
        "<defs>"
        f'<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>'
        f'<marker id="arrg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{GOLD}"/></marker>'
        f'<marker id="arrb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker>'
        "</defs>",
        f'<rect width="{w}" height="{h}" rx="18" fill="{BG}"/>',
    ]


def text(x, y, s, size=15, fill=TEXT, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" {extra}>{esc(s)}</text>')


def box(x, y, w, h, title, lines=(), accent=GOLD, dashed=False, title_size=16):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL}" stroke="{PANEL_LINE}" stroke-width="1.5"{dash}/>',
           f'<rect x="{x}" y="{y + 10}" width="4" height="{h - 20}" rx="2" fill="{accent}"/>']
    ty = y + 25
    out.append(text(x + 18, ty, title, title_size, TEXT, 600))
    for i, ln in enumerate(lines):
        out.append(text(x + 18, ty + 20 + i * 18, ln, 13.5, MUTED))
    return out


def line(x1, y1, x2, y2, color=MUTED, marker="arr", dashed=False, width=1.8):
    dash = ' stroke-dasharray="5 5"' if dashed else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{width}" fill="none"{dash}{m}/>'


def path(d, color=MUTED, marker="arr", dashed=False, width=1.8):
    dash = ' stroke-dasharray="5 5"' if dashed else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none"{dash}{m}/>'


# ---------------------------------------------------------------- architecture
def architecture():
    W, H = 1200, 640
    o = svg_open(W, H, "PicoMondo system architecture")
    o.append(text(40, 54, "System architecture", 26, TEXT, 700))
    o.append(text(40, 80, "One board that takes exhibit power, protects itself, and gives the RP2350B's GPIO robust connectors.", 15, MUTED))
    for x, lbl, c in ((40, "POWER", ORANGE), (450, "CORE", GOLD), (860, "EXHIBIT I/O", BLUE)):
        o.append(text(x, 122, lbl, 12.5, c, 700, extra='letter-spacing="2"'))

    # power column
    o += box(40, 136, 300, 54, "Barrel jack, 12–24 V", (), ORANGE)
    o += box(40, 214, 300, 76, "Input protection", ("Reverse + overvoltage cut-off (LM74502)", "5 A PTC fuse, TVS, trips near 28 V"), ORANGE)
    o += box(40, 314, 300, 58, "5 V buck, 3 A", ("LMR33630B, 1.4 MHz",), ORANGE)
    o += box(40, 396, 300, 58, "+5 V rail → 3.3 V LDO", ("Diode-OR, never back-feeds USB host",), ORANGE)
    o += box(40, 478, 300, 58, "USB-C", ("5 V power, data and programming",), BLUE)
    o += box(40, 560, 300, 58, "Switched output, 3 A", ("Barrel voltage, GPIO enable, INA226",), GOLD)
    o.append(line(190, 190, 190, 212))
    o.append(line(190, 290, 190, 312))
    o.append(line(190, 372, 190, 394))
    o.append(line(190, 478, 190, 456))
    o.append(path("M40,252 L22,252 L22,589 L38,589", color=GOLD, marker="arrg"))
    o.append(text(16, 420, "V_BARREL", 11.5, GOLD, 600, "middle", 'transform="rotate(-90 16 420)"'))
    o.append(path("M342,425 L372,425 L372,300 L448,300"))
    o.append(text(410, 293, "3.3 V", 11.5, MUTED, 600, "middle"))
    o.append(path("M342,507 L400,507 L400,340 L448,340", color=BLUE, marker="arrb"))
    o.append(text(424, 333, "USB", 11.5, BLUE, 600, "middle"))

    # core
    o.append(f'<rect x="450" y="136" width="300" height="236" rx="12" fill="#183a2a" stroke="{GOLD}" stroke-width="2"/>')
    cx, cy = 600, 220
    o.append(f'<g transform="rotate(45 {cx} {cy})"><rect x="{cx-34}" y="{cy-34}" width="68" height="68" rx="4" fill="#111" stroke="#666"/>'
             + "".join(f'<rect x="{cx-30+i*7.5}" y="{cy-40}" width="3" height="6" fill="{GOLD}"/>'
                       f'<rect x="{cx-30+i*7.5}" y="{cy+34}" width="3" height="6" fill="{GOLD}"/>'
                       f'<rect x="{cx-40}" y="{cy-30+i*7.5}" width="6" height="3" fill="{GOLD}"/>'
                       f'<rect x="{cx+34}" y="{cy-30+i*7.5}" width="6" height="3" fill="{GOLD}"/>' for i in range(9))
             + "</g>")
    for k in range(40):
        a = math.radians(100 + k * (280 / 39))
        o.append(f'<circle cx="{cx + 64*math.cos(a):.1f}" cy="{cy - 64*math.sin(a):.1f}" r="3" fill="#fffbe6" opacity="0.9"/>')
    o.append(text(600, 318, "RP2350B", 22, TEXT, 700, "middle"))
    o.append(text(600, 340, "Dual Arm Cortex-M33 / RISC-V, 150 MHz", 13.5, MUTED, 400, "middle"))
    o.append(text(600, 358, "QFN-80, 48 GPIO, 8 ADC", 13.5, MUTED, 400, "middle"))
    o += box(450, 396, 300, 58, "16 MB QSPI flash", ("W25Q128, copied from the Pi reference",), GOLD)
    o += box(450, 478, 300, 58, "microSD", ("SPI1 with card detect",), GOLD)
    o += box(450, 560, 300, 58, "PSRAM (in progress)", ("APS6404L on the second chip select",), GOLD, dashed=True)
    o.append(line(600, 372, 600, 394, marker=None))

    # I/O
    io = [
        ("7 × Molex EdgeLock, 8-circuit", ("38 GPIO, 100 Ω in series on every pin", "Header holes behind each one"), BLUE, 76),
        ("Indicator LED ring", ("40 white LEDs, one per GPIO, ~1 mA",), GOLD, 58),
        ("Qwiic / STEMMA QT", ("I2C sensors, shared with the INA226",), PURPLE, 58),
        ("NeoPixel connector", ("Data buffered to 5 V, fused 5 V supply",), ORANGE, 58),
        ("Status and debug", ("WS2812 LED, BOOTSEL, RESET, SWD",), GREEN, 58),
    ]
    y = 136
    for title, lines_, c, h in io:
        o += box(860, y, 300, h, title, lines_, c)
        o.append(path(f"M752,254 C800,254 810,{y + h/2} 858,{y + h/2}", color=c, marker=None, width=1.6))
        y += h + 24
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- board map
def board_map():
    W, H = 1200, 700
    S = 5.0
    BX, BY = 70, 120

    def P(x, y):
        return BX + (x - 50) * S, BY + (y - 50) * S

    o = svg_open(W, H, "PicoMondo connector map")
    o.append(text(40, 54, "Connector map", 26, TEXT, 700))
    o.append(text(40, 80, "120 × 90 mm, 4-layer. Each connector takes its pins from the side of the chip that faces it.", 15, MUTED))

    bw, bh = 120 * S, 90 * S
    o.append(f'<rect x="{BX}" y="{BY}" width="{bw}" height="{bh}" rx="15" fill="#1c5a3b" stroke="#3d8a5f" stroke-width="2"/>')
    # power zone
    zx, zy = P(124, 72)
    o.append(f'<rect x="{zx}" y="{zy}" width="{30*S}" height="{38*S}" rx="10" fill="{ORANGE}" opacity="0.10" stroke="{ORANGE}" stroke-opacity="0.5" stroke-dasharray="5 4"/>')
    o.append(text(zx + 15 * S, zy + 38 * S - 10, "power stage", 12.5, ORANGE, 600, "middle"))
    # holes
    for hx, hy in ((54, 54), (166, 54), (54, 136), (166, 136)):
        x, y = P(hx, hy)
        o.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{BG}" stroke="{GOLD}" stroke-width="3"/>')

    roles = {"EL1": ORANGE, "EL4": ORANGE, "EL2": BLUE, "EL3": BLUE, "EL5": BLUE, "EL6": BLUE, "EL7": PURPLE}

    def edgelock(name, cxmm, side, n=8, width=27.1, color=None):
        color = color or roles[name]
        d = 7.0 * S
        w = width * S
        if side in ("top", "bottom"):
            x0 = BX + (cxmm - 50) * S - w / 2
            y0 = BY if side == "top" else BY + bh - d
            o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{d}" rx="3" fill="{color}" opacity="0.22" stroke="{color}" stroke-width="1.5"/>')
            pitch = 2.0 * S
            grp = n // 2
            for g, gx in enumerate((x0 + 3.5 * S, x0 + w - 3.5 * S - (grp - 1) * pitch - 1.0 * S)):
                for i in range(grp):
                    o.append(f'<rect x="{gx + i*pitch:.1f}" y="{y0 + (2 if side=="top" else d-26)}" width="{1.0*S}" height="24" rx="1" fill="{GOLD}"/>')
            ly = y0 + d + 18 if side == "top" else y0 - 8
            o.append(text(x0 + w / 2, ly, name, 14, color, 700, "middle"))
        else:
            cy = BY + (cxmm - 50) * S
            y0 = cy - w / 2
            x0 = BX if side == "left" else BX + bw - d
            o.append(f'<rect x="{x0}" y="{y0}" width="{d}" height="{w}" rx="3" fill="{color}" opacity="0.22" stroke="{color}" stroke-width="1.5"/>')
            pitch = 2.0 * S
            grp = n // 2
            for gy in (y0 + 3.5 * S, y0 + w - 3.5 * S - (grp - 1) * pitch - 1.0 * S):
                for i in range(grp):
                    o.append(f'<rect x="{x0 + (2 if side=="left" else d-26)}" y="{gy + i*pitch:.1f}" width="24" height="{1.0*S}" rx="1" fill="{GOLD}"/>')
            lx = x0 + d + 10 if side == "left" else x0 - 10
            o.append(text(lx, cy + 5, name, 14, color, 700, "start" if side == "left" else "end"))

    edgelock("EL1", 73.5, "top"); edgelock("EL2", 110, "top"); edgelock("EL3", 146.5, "top")
    edgelock("EL4", 73.5, "bottom"); edgelock("EL5", 108.75, "bottom"); edgelock("EL6", 144, "bottom")
    edgelock("EL7", 94.2, "left")
    edgelock("OUT", 104, "right", n=4, width=19.1, color=GOLD)

    def small(xmm, ymm, wmm, hmm, label, color, side, over=0):
        x, y = P(xmm, ymm)
        w, h = wmm * S, hmm * S
        rx = x - w / 2 + (over * S if side == "right" else -over * S if side == "left" else 0)
        o.append(f'<rect x="{rx}" y="{y - h/2}" width="{w}" height="{h}" rx="3" fill="#cfd6d2" stroke="#7d8a84"/>')
        if side == "right":
            o.append(text(BX + bw + 2 * S + over * S + 10, y + 5, label, 13.5, color, 600))
        elif side == "left":
            o.append(text(rx + w + 8, y + 5, label, 13, color, 600))
        else:
            o.append(text(x, y + h / 2 + 16, label, 12.5, color, 600, "middle"))

    small(165.3, 67.9, 7.5, 9.0, "USB-C", BLUE, "right", 1.5)
    small(159.6, 84.9, 14, 9.0, "12–24 V in", ORANGE, "right", 6.5)
    small(164.1, 122, 6, 10, "NeoPixel", ORANGE, "right", 1.5)
    small(53.4, 65.6, 4.2, 6, "Qwiic", PURPLE, "left")
    small(53.2, 74.5, 4.2, 5, "SWD", GREEN, "left")
    small(59.5, 117.1, 12, 13, "", GOLD, "left")
    mx, my = P(59.5, 117.1)
    o.append(text(mx, my + 13 * S / 2 + 16, "microSD", 12.5, GOLD, 600, "middle"))
    for yy, lbl in ((90, "BOOT"), (101, "RESET")):
        x, y = P(75.65, yy)
        o.append(f'<rect x="{x-12}" y="{y-12}" width="24" height="24" rx="3" fill="#cfd6d2" stroke="#7d8a84"/><circle cx="{x}" cy="{y}" r="6" fill="#e8c27a"/>')
        o.append(text(x - 18, y + 4, lbl, 11, TEXT, 600, "end"))
    o.append(text(BX + bw + 2 * S + 10, P(0, 104)[1] + 5 + 22, "3 A switched", 12.5, GOLD, 600))

    # MCU + ring
    cx, cy = P(104, 95)
    r = 19 * S
    for k in range(40):
        a = math.radians(100 + k * (280 / 39))
        o.append(f'<circle cx="{cx + r*math.cos(a):.1f}" cy="{cy - r*math.sin(a):.1f}" r="4" fill="#fffbe6"/>')
    o.append(f'<g transform="rotate(45 {cx} {cy})"><rect x="{cx-25}" y="{cy-25}" width="50" height="50" rx="3" fill="#111" stroke="#777"/></g>')
    o.append(text(cx, cy + 5, "RP2350B", 12, TEXT, 700, "middle"))
    fx, fy = P(108.1, 81)
    o.append(f'<g transform="rotate(-45 {fx} {fy})"><rect x="{fx-13}" y="{fy-13}" width="26" height="26" rx="2" fill="#111" stroke="#777"/></g>')
    o.append(text(fx + 20, fy - 8, "flash", 12, MUTED, 600))
    o.append(text(fx + 20, fy + 8, "(USB exits here too)", 11, MUTED, 400))
    o.append(text(cx, cy + r + 26, "40 indicator LEDs", 12.5, TEXT, 600, "middle"))

    # legend / pin table
    LX = 820
    o.append(text(LX, 130, "PIN MAP", 12.5, MUTED, 700, extra='letter-spacing="2"'))
    rows = [
        ("EL1", ORANGE, "Servo / LED strip", "+5V · GND · GP4–7 · +5V · GND"),
        ("EL4", ORANGE, "Servo / LED strip", "+5V · GND · GP18–21 · +5V · GND"),
        ("EL2", BLUE, "Joystick", "3V3 · ADC46–47 · GP0–3 · GND"),
        ("EL3", BLUE, "Joystick", "3V3 · ADC44–45 · GP36–39 · GND"),
        ("EL5", BLUE, "Joystick", "3V3 · ADC40–41 · GP26–29 · GND"),
        ("EL6", BLUE, "Joystick", "3V3 · ADC42–43 · GP30–33 · GND"),
        ("EL7", PURPLE, "I2C + GPIO", "3V3 · GP8–11 · SDA · SCL · GND"),
        ("OUT", GOLD, "Switched power", "OUT+ ×2 · GND ×2, barrel voltage"),
    ]
    y = 162
    for name, c, role, pins in rows:
        o.append(f'<rect x="{LX}" y="{y - 16}" width="340" height="50" rx="8" fill="{PANEL}" stroke="{PANEL_LINE}"/>')
        o.append(f'<rect x="{LX + 12}" y="{y - 6}" width="44" height="26" rx="5" fill="{c}" opacity="0.22" stroke="{c}"/>')
        o.append(text(LX + 34, y + 12, name, 13.5, c, 700, "middle"))
        o.append(text(LX + 70, y + 2, role, 14, TEXT, 600))
        o.append(text(LX + 70, y + 22, pins, 12.5, MUTED))
        y += 58
    o.append(text(LX, y + 6, "Joystick connectors: 2 axes + up to 4 buttons each.", 12.5, MUTED))
    o.append(text(LX, y + 24, "ADC pins aren't 5 V tolerant, so they get 3V3.", 12.5, MUTED))
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- journey
def journey():
    W, H = 1200, 600
    o = svg_open(W, H, "PicoMondo project timeline")
    o.append(text(40, 54, "From feature creep to a board on the bench", 26, TEXT, 700))
    o.append(text(40, 80, "One year, two designs, one hard scope cut.", 15, MUTED))

    ms = [
        ("Nov 2025", "The problem", ["Pico exhibits run out", "of GPIO; shift", "registers everywhere."], BLUE),
        ("Feb–Jun 2026", "Everything board", ["10 sheets: USB-PD,", "5 A buck-boost, power", "monitors, Arduino and", "Pico sockets."], MUTED),
        ("Oct 2026", "It won't route", ["Scope reset, one rule:", "a feature is in v1 only", "if an exhibit is blocked", "without it."], RED),
        ("Late Oct 2026", "v1 ordered", ["Rebuilt on the", "Raspberry Pi reference", "core. 4-layer, sent", "to JLCPCB."], GOLD),
        ("Nov 2026", "Arrives bare", ["No assembly: laser-cut", "a paste stencil and", "hand-solder the", "0.4 mm QFN-80."], ORANGE),
        ("Next", "Bring-up + v2", ["Test in real exhibits;", "PSRAM, USB-PD and", "buck-boost return", "in v2."], GREEN),
    ]
    x0, x1, ly = 110, 1090, 150
    o.append(f'<path d="M{x0},{ly} L{x1},{ly}" stroke="{PANEL_LINE}" stroke-width="4" stroke-linecap="round"/>')
    step = (x1 - x0) / (len(ms) - 1)
    for i, (date, title, desc, c) in enumerate(ms):
        x = x0 + i * step
        o.append(f'<circle cx="{x}" cy="{ly}" r="11" fill="{BG}" stroke="{c}" stroke-width="4"/>')
        if i == 4:
            o.append(f'<circle cx="{x}" cy="{ly}" r="19" fill="none" stroke="{c}" stroke-width="1.5" opacity="0.6"/>')
            o.append(text(x, ly - 30, "NOW", 11.5, c, 700, "middle", 'letter-spacing="2"'))
        bx = x - 85
        o.append(f'<rect x="{bx}" y="{ly + 34}" width="170" height="164" rx="10" fill="{PANEL}" stroke="{PANEL_LINE}"/>')
        o.append(f'<rect x="{bx}" y="{ly + 34}" width="170" height="4" rx="2" fill="{c}"/>')
        o.append(text(bx + 14, ly + 62, date, 12.5, c, 700))
        o.append(text(bx + 14, ly + 86, title, 16, TEXT, 700))
        for j, dl in enumerate(desc):
            o.append(text(bx + 14, ly + 112 + j * 19, dl, 13, MUTED))

    # stats strip
    sy = 420
    o.append(text(40, sy, "WHAT THE SCOPE CUT BOUGHT", 12.5, MUTED, 700, extra='letter-spacing="2"'))
    bars = [("Raspberry Pi Pico", 26, "26 GPIO on 0.1\" pins", MUTED),
            ("Full-scope design", 28, "28 GPIO on EdgeLock", MUTED),
            ("PicoMondo v1", 38, "38 on EdgeLock + 2 on solder holes", GOLD)]
    bx, maxw = 250, 560
    for i, (lbl, v, note, c) in enumerate(bars):
        y = sy + 26 + i * 44
        o.append(text(40, y + 19, lbl, 15, TEXT, 600))
        o.append(f'<rect x="{bx}" y="{y}" width="{maxw}" height="26" rx="6" fill="{PANEL}"/>')
        o.append(f'<rect x="{bx}" y="{y}" width="{maxw * v / 40:.0f}" height="26" rx="6" fill="{c}" opacity="{1 if c == GOLD else 0.55}"/>')
        o.append(text(bx + maxw * v / 40 - 10, y + 18, str(v), 14, BG, 700, "end"))
        o.append(text(bx + maxw + 16, y + 18, note, 13.5, MUTED))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("architecture", architecture), ("connector_map", board_map), ("timeline", journey)):
        with open(os.path.join(OUT, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", name)
