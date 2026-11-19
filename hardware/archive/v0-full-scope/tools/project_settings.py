"""Board design rules and net classes for picomondo.kicad_pro (JLCPCB 4-layer, 1.6 mm, ENIG).

Merges into the existing project file, keeping any other settings. Run:  python project_settings.py

Numbers and where they come from
  * JLCPCB 4-layer capabilities: track/space 0.09 mm minimum (0.127 used here for margin), via 0.45 / 0.2 mm,
    NPTH slots 1.0 mm, copper to board edge 0.3 mm.
  * USB pair: 90 ohm differential on the outer layer over the L2 ground plane. Stackup JLC04161H-3313:
    prepreg 0.0994 mm (epsilon_r 4.05), copper 35 um. Single-ended microstrip
    Z0 = 87 / sqrt(er + 1.41) * ln(5.98 h / (0.8 w + t))  ->  w = 0.15 mm gives about 50 ohm;
    Zdiff = 2 Z0 (1 - 0.48 exp(-0.96 s / h))  ->  s = 0.16 mm gives about 90 ohm.
    These approximations are good to about 10%; check with JLCPCB's impedance calculator before ordering.
"""
import json
from pathlib import Path

PRO = Path(__file__).resolve().parent.parent / "picomondo.kicad_pro"


def netclass(name, track, clearance, via, drill, dp_width=None, dp_gap=None, priority=0):
    return {"name": name, "track_width": track, "clearance": clearance, "via_diameter": via, "via_drill": drill,
            "diff_pair_width": dp_width or track, "diff_pair_gap": dp_gap or clearance,
            "diff_pair_via_gap": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6,
            "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": priority}


CLASSES = [
    netclass("Default", 0.2, 0.127, 0.6, 0.3, priority=3),
    netclass("USB", 0.15, 0.127, 0.6, 0.3, dp_width=0.15, dp_gap=0.16, priority=0),
    netclass("Power", 0.5, 0.127, 0.8, 0.4, priority=1),
    netclass("PowerHigh", 1.0, 0.127, 0.8, 0.4, priority=2),
]

PATTERNS = (
    [("USB", "*USB_D*")]
    + [("PowerHigh", p) for p in ("V_INPUT", "+5V", "+5V_SW", "VBUS", "*VOUT_PRE", "*SW1", "*SW2", "*V_RAW",
                                  "*BARREL_IN", "*TERM_IN", "*J7_SRC", "*J7_DRAIN", "*J7_OUT", "*J8_SRC",
                                  "*J8_DRAIN", "*J8_OUT")]
    + [("Power", p) for p in ("+3V3", "+3V3_AUX", "+1V1", "*WS_VDD")]
)

RULES = {
    "min_clearance": 0.127, "min_track_width": 0.127, "min_connection": 0.09,
    "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2, "min_via_annular_width": 0.1,
    "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
    "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_text_height": 0.8,
    "min_text_thickness": 0.08, "min_silk_clearance": 0.0, "solder_mask_to_copper_clearance": 0.0,
    "min_resolved_spacing": 0.127, "use_height_for_length_calcs": True,
}

SEVERITIES = {
    # a solder jumper is meant to be bridged; mask apertures merge by design
    "solder_mask_bridge": "warning",
    # footprints are copied into the board; ignore tiny library differences
    "lib_footprint_mismatch": "ignore",
    "silk_over_copper": "ignore",
}


def apply():
    data = json.loads(PRO.read_text(encoding="utf-8")) if PRO.exists() else {}
    board = data.setdefault("board", {})
    ds = board.setdefault("design_settings", {})
    ds.setdefault("defaults", {}).update({"board_outline_line_width": 0.1, "copper_line_width": 0.2})
    ds["rules"] = RULES
    ds["rule_severities"] = SEVERITIES
    ds["track_widths"] = [0.0, 0.15, 0.2, 0.3, 0.5, 1.0, 1.5]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.45, "drill": 0.2},
                            {"diameter": 0.6, "drill": 0.3}, {"diameter": 0.8, "drill": 0.4}]
    ds["diff_pair_dimensions"] = [{"gap": 0.0, "via_gap": 0.0, "width": 0.0}, {"gap": 0.16, "via_gap": 0.25, "width": 0.15}]
    data["net_settings"] = {
        "classes": CLASSES, "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
        "netclass_patterns": [{"netclass": c, "pattern": p} for c, p in PATTERNS],
    }
    data.setdefault("meta", {"filename": PRO.name, "version": 1})
    PRO.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("updated", PRO.name)


if __name__ == "__main__":
    apply()
