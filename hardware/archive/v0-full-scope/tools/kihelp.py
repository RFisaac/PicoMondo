"""Helpers for generating KiCad schematic sheets with kiutils.

Design style: every part is placed explicitly and every connection is a pin stub that ends in a
net label or a power symbol. Labels give nets their names, so the netlist is exactly what the
generator scripts say, and nothing depends on wires being routed visually.

Once a sheet has been opened and edited in KiCad, the .kicad_sch file is the source of truth.
Do not regenerate it; add new sheets or edit with kiutils read-modify-write instead.
"""
import copy
import math
import uuid
from pathlib import Path

from kiutils.items.common import (Effects, Font, Justify, PageSettings, Position,
                                  Property, Stroke, TitleBlock)
from kiutils.items.schitems import (Connection, GlobalLabel, HierarchicalSheet,
                                    HierarchicalSheetProjectInstance,
                                    HierarchicalSheetProjectPath, Junction, LocalLabel,
                                    NoConnect, SchematicSymbol, SymbolProjectInstance,
                                    SymbolProjectPath, Text)
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib

PROJECT = "picomondo"
KICAD_SYMBOLS = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
PROJECT_LIBS = {"MCU_RaspberryPi_RP2350": LIB_DIR / "MCU_RaspberryPi_RP2350.kicad_sym",
                "lcsc": LIB_DIR / "lcsc" / "lcsc.kicad_sym"}

# Nets drawn as power symbols (KiCad power:* library). Value = default direction of the symbol.
POWER_SYMBOLS = {"GND": "down", "AGND": "down", "+3V3": "up", "+3V3_AUX": "up", "+1V1": "up", "+5V": "up", "+5V_SW": "up"}

# Non-power nets that cross sheet boundaries (GPIOn nets are handled by name).
# Net name -> KiCad power library symbol, where they differ (the net name is the instance value).
POWER_LIB = {"AGND": "GNDA", "+3V3_AUX": "+3.3VA", "+5V_SW": "+5V"}

GLOBAL_NETS = {"RUN", "USB_D+", "USB_D-", "V_INPUT", "VBUS"}

G = 1.27  # schematic grid, mm


def uid():
    return str(uuid.uuid4())


def r(v):
    return round(v + 0.0, 4)


# --------------------------------------------------------------------------- symbol libraries
_libs = {}


def _lib(nick):
    if nick not in _libs:
        path = PROJECT_LIBS.get(nick) or KICAD_SYMBOLS / f"{nick}.kicad_sym"
        _libs[nick] = SymbolLib.from_file(str(path))
    return _libs[nick]


def lib_symbol(libid):
    """Return a flattened (no 'extends') copy of a library symbol, ready to embed."""
    nick, name = libid.split(":")
    lib = _lib(nick)
    by_name = {s.entryName: s for s in lib.symbols}
    sym = by_name[name]
    if sym.extends:
        parent = copy.deepcopy(by_name[sym.extends])
        old = parent.entryName
        parent.entryName = name
        for u in parent.units:
            u.entryName = u.entryName.replace(old, name, 1)
        child_props = {p.key: p for p in sym.properties}
        for p in parent.properties:
            if p.key in child_props:
                p.value = child_props[p.key].value
        parent.extends = None
        sym = parent
    else:
        sym = copy.deepcopy(sym)
    sym.libraryNickname = nick
    if nick == "lcsc":
        # EasyEDA symbols leave every pin 'unspecified', which only produces ERC noise.
        for u in sym.units:
            for pin in u.pins:
                if pin.electricalType == "unspecified":
                    pin.electricalType = "passive"
    return sym


def _all_pins(sym):
    pins = list(sym.pins)
    for u in sym.units:
        pins.extend(u.pins)
    return pins


# --------------------------------------------------------------------------- geometry
def _rot(px, py, rot):
    th = math.radians(rot)
    return (px * math.cos(th) - py * math.sin(th), px * math.sin(th) + py * math.cos(th))


class Pin:
    def __init__(self, number, x, y, out_angle):
        self.number, self.x, self.y, self.out = number, x, y, out_angle % 360

    @property
    def pos(self):
        return (self.x, self.y)


def _dir(angle):
    """Unit vector in schematic coordinates (y down) for a CCW angle in degrees."""
    a = math.radians(angle)
    return (round(math.cos(a), 6), -round(math.sin(a), 6))


class Part:
    def __init__(self, sheet, schsym, libsym, x, y, rot):
        self.sheet, self.sym, self.x, self.y, self.rot = sheet, schsym, x, y, rot
        self.pins = {}
        for p in _all_pins(libsym):
            rx, ry = _rot(p.position.X, p.position.Y, rot)
            out = (p.position.angle + 180 + rot) % 360
            self.pins[str(p.number)] = Pin(str(p.number), r(x + rx), r(y - ry), out)

    def pin(self, number):
        return self.pins[str(number)]


class Sheet:
    def __init__(self, title, inst_path, paper="A1", sheet_uuid=None, rev="1", date=""):
        self.sch = Schematic.create_new()
        self.sch.version = "20230121"
        self.sch.generator = "eeschema"
        self.sch.uuid = sheet_uuid or uid()
        self.sch.paper = PageSettings(paperSize=paper)
        self.sch.titleBlock = TitleBlock(title=title, date=date, revision=rev,
                                         company="PicoMondo")
        self.sch.sheetInstances = []
        self.inst_path = inst_path
        self._embedded = {}
        self._pwr = 0

    # ------------------------------------------------------------------ symbols
    def _embed(self, libid):
        if libid not in self._embedded:
            sym = lib_symbol(libid)
            self._embedded[libid] = sym
            self.sch.libSymbols.append(sym)
        return self._embedded[libid]

    def _props(self, libsym, x, y, rot, ref, value, footprint, extra, show_value, show_ref):
        props = []
        libp = {p.key: p for p in libsym.properties}

        def mk(key, val, pid, hide):
            lp = libp.get(key)
            if lp is not None and lp.position is not None:
                rx, ry = _rot(lp.position.X, lp.position.Y, rot)
                ang = (lp.position.angle + (rot % 180)) % 180 if rot % 90 == 0 else 0
                pos = Position(r(x + rx), r(y - ry), ang)
                eff = copy.deepcopy(lp.effects) if lp.effects else Effects(font=Font(height=1.27, width=1.27))
            else:
                pos = Position(x, y, 0)
                eff = Effects(font=Font(height=1.27, width=1.27))
            eff.hide = hide
            if rot % 180 == 90 and key in ("Reference", "Value"):
                # horizontal part: keep text horizontal, reference above and value below
                pos = Position(r(x), r(y - 2.54 if key == "Reference" else y + 2.54), 0)
                eff.justify = Justify()
            return Property(key=key, value=val, id=pid, position=pos, effects=eff)

        props.append(mk("Reference", ref, 0, not show_ref))
        props.append(mk("Value", value, 1, not show_value))
        props.append(mk("Footprint", footprint, 2, True))
        props.append(mk("Datasheet", "", 3, True))
        for i, (k, v) in enumerate((extra or {}).items(), start=4):
            props.append(mk(k, v, i, True))
        return props

    def add(self, libid, ref, value, footprint="", x=0, y=0, rot=0, dnp=False, extra=None,
            show_value=True, show_ref=True, power=False, in_bom=None):
        libsym = self._embed(libid)
        nick, name = libid.split(":")
        s = SchematicSymbol()
        s.libraryNickname, s.entryName = nick, name
        s.position = Position(r(x), r(y), rot)
        s.unit = 1
        s.inBom = (not power) if in_bom is None else in_bom
        s.onBoard = not power
        s.dnp = dnp
        s.uuid = uid()
        s.properties = self._props(libsym, x, y, rot, ref, value, footprint, extra,
                                   show_value, show_ref)
        part = Part(self, s, libsym, x, y, rot)
        s.pins = {num: uid() for num in part.pins}
        s.instances = [SymbolProjectInstance(
            name=PROJECT, paths=[SymbolProjectPath(sheetInstancePath=self.inst_path,
                                                   reference=ref, unit=1)])]
        self.sch.schematicSymbols.append(s)
        return part

    # ------------------------------------------------------------------ wires and labels
    def wire(self, p1, p2):
        if p1 == p2:
            return
        self.sch.graphicalItems.append(Connection(
            type="wire", points=[Position(r(p1[0]), r(p1[1])), Position(r(p2[0]), r(p2[1]))],
            stroke=Stroke(width=0, type="default"), uuid=uid()))

    def no_connect(self, pin):
        """Mark a pin as intentionally unconnected."""
        self.sch.noConnects.append(NoConnect(position=Position(r(pin.x), r(pin.y)), uuid=uid()))

    def junction(self, p):
        self.sch.junctions.append(Junction(position=Position(r(p[0]), r(p[1])), diameter=0,
                                           uuid=uid()))

    def label(self, text, p, angle, glob=False):
        just = Justify(horizontally="right") if angle in (180, 270) else Justify()
        eff = Effects(font=Font(height=1.27, width=1.27), justify=just)
        pos = Position(r(p[0]), r(p[1]), angle)
        if glob:
            hid = Effects(font=Font(height=1.27, width=1.27), hide=True)
            self.sch.globalLabels.append(GlobalLabel(
                text=text, shape="bidirectional", position=pos, effects=eff, uuid=uid(),
                properties=[Property(key="Intersheetrefs", value="${INTERSHEET_REFS}", id=0,
                                     position=Position(r(p[0]), r(p[1]), 0), effects=hid)]))
        else:
            self.sch.labels.append(LocalLabel(text=text, position=pos, effects=eff, uuid=uid()))

    def note(self, text, x, y, size=1.8):
        text = text.replace("\n", "\\n")   # KiCad needs escaped newlines inside quoted strings
        self.sch.texts.append(Text(text=text, position=Position(x, y, 0),
                                   effects=Effects(font=Font(height=size, width=size),
                                                   justify=Justify(horizontally="left")),
                                   uuid=uid()))

    def power_symbol(self, net, p, direction):
        """Place a power symbol whose connection point is p and whose body points `direction`."""
        default = POWER_SYMBOLS[net]
        base = 90 if default == "up" else 270
        rot = (direction - base) % 360
        self._pwr += 1
        return self.add(f"power:{POWER_LIB.get(net, net)}", f"#PWR{self.sheet_index()}{self._pwr:03d}", net,
                        x=p[0], y=p[1], rot=rot, power=True, show_ref=False)

    def sheet_index(self):
        return getattr(self, "_idx", 0)

    def attach(self, pin, net, length=5.08, glob=False):
        """Connect a pin to a net: power symbol for power nets, label otherwise.

        The connection extends `length` mm outward from the pin (0 = directly on the pin)."""
        dx, dy = _dir(pin.out)
        end = (r(pin.x + dx * length), r(pin.y + dy * length))
        self.wire(pin.pos, end)
        glob = glob or net.startswith("GPIO") or net in GLOBAL_NETS
        if net in POWER_SYMBOLS and pin.out in (90, 270):
            self.power_symbol(net, end, pin.out)
        elif net in POWER_SYMBOLS:
            # Sideways power symbols read badly; a global label with the same name joins the
            # same net as the power symbols.
            self.label(net, end, pin.out, glob=True)
        else:
            self.label(net, end, pin.out, glob=glob)
        return end

    def bus(self, pins, net, rise=5.08, glob=False):
        """Join several pins on the same edge to one net with a common rail wire.

        Power nets get one power symbol; other nets get one label (global if `glob`)."""
        dx, dy = _dir(pins[0].out)
        pts = [(r(p.x + dx * rise), r(p.y + dy * rise)) for p in pins]
        for p, e in zip(pins, pts):
            self.wire(p.pos, e)
        horiz = dy != 0                       # pins on a top/bottom edge -> horizontal rail
        pts.sort(key=lambda q: q[0] if horiz else q[1])
        for a, b in zip(pts, pts[1:]):
            self.wire(a, b)
        for q in pts[1:-1]:
            self.junction(q)
        glob = glob or net.startswith("GPIO") or net in GLOBAL_NETS
        if net in POWER_SYMBOLS:
            if horiz:
                self.power_symbol(net, pts[0], pins[0].out)
            elif POWER_SYMBOLS[net] == "down":
                self.power_symbol(net, pts[-1], 270)     # bottom end of a vertical rail
            else:
                self.power_symbol(net, pts[0], 90)       # top end of a vertical rail
        else:
            self.label(net, pts[0], pins[0].out, glob=glob)
        return pts

    def link(self, a, b):
        """Wire two pins together directly."""
        self.wire(a.pos, b.pos)

    def flag_net(self, p, direction=90):
        """PWR_FLAG on a non-power net (e.g. a filtered supply node) at wire point p."""
        dx, dy = _dir(direction)
        q = (r(p[0] + dx * 5.08), r(p[1] + dy * 5.08))
        self.wire(p, q)
        self._pwr += 1
        self.add("power:PWR_FLAG", f"#FLG{self.sheet_index()}{self._pwr:03d}", "PWR_FLAG",
                 x=q[0], y=q[1], rot=(direction - 90) % 360, power=True, show_ref=False)

    def flag(self, net, p):
        """Mark a power net as driven (ERC): power symbol at p plus a PWR_FLAG beside it."""
        self.power_symbol(net, p, 90 if POWER_SYMBOLS[net] == "up" else 270)
        q = (p[0] + 10.16, p[1])
        self.wire(p, q)
        self._pwr += 1
        self.add("power:PWR_FLAG", f"#FLG{self.sheet_index()}{self._pwr:03d}", "PWR_FLAG",
                 x=q[0], y=q[1], rot=270, power=True, show_ref=False)

    # ------------------------------------------------------------------ output
    def save(self, path):
        self.sch.to_file(str(path))


def new_root(title, paper="A1"):
    root = Sheet(title, "", paper=paper)
    root.inst_path = f"/{root.sch.uuid}"
    return root


def add_subsheet(root, name, filename, x, y, w, h, page, sheet_uuid=None):
    hs = HierarchicalSheet()
    hs.position = Position(x, y)
    hs.width, hs.height = w, h
    hs.stroke = Stroke(width=0.1524, type="solid")
    hs.uuid = sheet_uuid or uid()
    hs.sheetName = Property(key="Sheetname", value=name, id=0, position=Position(x, y - 1.27, 0),
                            effects=Effects(font=Font(height=1.27, width=1.27),
                                            justify=Justify(horizontally="left", vertically="bottom")))
    hs.fileName = Property(key="Sheetfile", value=filename, id=1,
                           position=Position(x, y + h + 1.27, 0),
                           effects=Effects(font=Font(height=1.27, width=1.27),
                                           justify=Justify(horizontally="left", vertically="top")))
    hs.instances = [HierarchicalSheetProjectInstance(
        name=PROJECT, paths=[HierarchicalSheetProjectPath(
            sheetInstancePath=f"/{root.sch.uuid}", page=str(page))])]
    root.sch.sheets.append(hs)
    return hs
