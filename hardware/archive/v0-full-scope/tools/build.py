"""Generate the initial KiCad project files (root schematic + sheets + project/library tables).

Run from kicad/tools:  python build.py
WARNING: overwrites the generated schematic files. Do not run after editing them in KiCad.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kihelp as kh                      # noqa: E402
import sheet_mcu_core                    # noqa: E402
import sheet_power_buck                  # noqa: E402
import sheet_power_input                 # noqa: E402
import sheet_power_ldo                   # noqa: E402
import sheet_power_outputs               # noqa: E402
import sheet_usb_pd                      # noqa: E402
import project_settings                  # noqa: E402
import sheet_io_edgelock                 # noqa: E402
import sheet_io_indicators               # noqa: E402
import sheet_io_headers                  # noqa: E402
import sheet_io_misc                     # noqa: E402

OUT = Path(__file__).resolve().parent.parent


class Refs:
    """Reference designator allocator. Numbers reserved with `reserved` are only handed out by
    `fixed()`, so connectors keep the J1-J10 names used in the board specification."""

    def __init__(self, reserved=None):
        self.n = {}
        self.reserved = {k: set(v) for k, v in (reserved or {}).items()}

    def next(self, prefix):
        while True:
            self.n[prefix] = self.n.get(prefix, 0) + 1
            if self.n[prefix] not in self.reserved.get(prefix, ()):
                return f"{prefix}{self.n[prefix]}"

    def fixed(self, prefix, number):
        assert number in self.reserved.get(prefix, ()), f"{prefix}{number} is not reserved"
        return f"{prefix}{number}"


def main():
    refs = Refs(reserved={"J": range(1, 11)})
    root = kh.new_root("PicoMondo RP2350B exhibit board")
    root.sch.titleBlock.date = "2026-10-01"

    sheets = [("MCU core", "mcu_core.kicad_sch", sheet_mcu_core.build, "A1"),
              ("5V buck-boost", "power_buck.kicad_sch", sheet_power_buck.build, "A2"),
              ("Power input", "power_input.kicad_sch", sheet_power_input.build, "A3"),
              ("3V3 regulators", "power_ldo.kicad_sch", sheet_power_ldo.build, "A4"),
              ("Switched outputs", "power_outputs.kicad_sch", sheet_power_outputs.build, "A2"),
              ("USB-C PD", "usb_pd.kicad_sch", sheet_usb_pd.build, "A3"),
              ("EdgeLock connectors", "io_edgelock.kicad_sch", sheet_io_edgelock.build, "A2"),
              ("GPIO indicators", "io_indicators.kicad_sch", sheet_io_indicators.build, "A2"),
              ("Arduino and Pico headers", "io_headers.kicad_sch", sheet_io_headers.build, "A2"),
              ("Board support", "io_misc.kicad_sch", sheet_io_misc.build, "A2")]
    for i, (name, fname, builder, paper) in enumerate(sheets, start=2):
        sheet_uuid = kh.uid()
        s = kh.Sheet(name, f"/{root.sch.uuid}/{sheet_uuid}", paper=paper)
        s._idx = i
        s.sch.titleBlock.date = "2026-10-01"
        builder(s, refs)
        s.save(OUT / fname)
        kh.add_subsheet(root, name, fname, 25.4 + (i - 2) * 76.2, 25.4, 63.5, 25.4, page=i,
                        sheet_uuid=sheet_uuid)
    root.save(OUT / "picomondo.kicad_sch")

    (OUT / "picomondo.kicad_pro").write_text(json.dumps(
        {"meta": {"filename": "picomondo.kicad_pro", "version": 1}, "sheets": [],
         "text_variables": {}}, indent=2) + "\n")
    project_settings.apply()
    write_lib_table("sym-lib-table", "sym_lib_table", SYMBOL_LIBS)
    write_lib_table("fp-lib-table", "fp_lib_table", FOOTPRINT_LIBS)
    print("written to", OUT)


# Project-local libraries: nickname -> path relative to the project folder.
SYMBOL_LIBS = {"MCU_RaspberryPi_RP2350": "lib/MCU_RaspberryPi_RP2350.kicad_sym",
               "lcsc": "lib/lcsc/lcsc.kicad_sym"}
FOOTPRINT_LIBS = {"picomondo": "lib/picomondo.pretty", "lcsc": "lib/lcsc/lcsc.pretty"}


def write_lib_table(filename, tag, libs):
    lines = [f"({tag}", "  (version 7)"]
    for name, path in libs.items():
        lines.append(f'  (lib (name "{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{path}")'
                     f'(options "")(descr ""))')
    lines.append(")")
    (OUT / filename).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
