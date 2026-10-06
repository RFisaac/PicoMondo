"""JLCPCB assembly files from the saved board, plus a live stock / basic-vs-extended check.

Reads the board's footprints (LCSC field, set by apply_parts.py / sync_board_parts.py), skips DNP and board-only
parts, and writes to kicad/bom/:
  jlcpcb_bom.csv   Comment, Designator, Footprint, LCSC Part #   (upload with the Gerbers)
  jlcpcb_cpl.csv   Designator, Mid X, Mid Y, Layer, Rotation      (from kicad-cli pcb export pos)
  BOM_REPORT.md    what each part is, stock, basic / extended, parts that need attention

Run (KiCad's Python, any time, KiCad may stay open since it only reads):
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\bom.py [--boards 5] [--offline]

JLCPCB's CPL viewer is the final word on rotation: some packages (SOT-23, QFN, polarized parts) need a rotation
correction. Check the preview on their order page before paying.
"""
import argparse
import csv
import json
import re
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "picomondo.kicad_pcb"
OUT = ROOT / "bom"
CACHE = OUT / ".jlc_cache.json"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
UA = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
JLC = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
LCSC = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode="
# parts that are only a footprint on the board, never bought
FOOTPRINT_ONLY = ("TP", "FID", "H", "JP", "NT")


def natural(ref):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def web(url, body=None):
    req = urllib.request.Request(url, json.dumps(body).encode() if body else None, UA)
    return json.load(urllib.request.urlopen(req, timeout=40))


def lookup(code, mpn, cache):
    """Stock, library type and price for one LCSC part number (cached for the day)."""
    hit = cache.get(code)
    if hit and time.time() - hit["t"] < 86400:
        return hit
    info = {"t": time.time(), "stock": None, "type": "?", "model": "", "price": None, "pkg": ""}
    try:
        d = web(LCSC + code)["result"] or {}                       # empty for some parts LCSC has delisted
        info.update(stock=d.get("stockNumber"), model=d.get("productModel") or mpn, pkg=d.get("encapStandard", ""))
        tiers = d.get("productPriceList") or []
        if tiers:
            info["price"] = tiers[0].get("productPrice")
        r = web(JLC, {"currentPage": 1, "pageSize": 20, "keyword": info["model"], "searchSource": "search",
                      "firstSortName": "", "secondSortName": "", "componentLibraryType": "", "stockFlag": False})
        for c in r["data"]["componentPageInfo"]["list"] or []:
            if c["componentCode"] == code:
                info["type"] = ("basic" if c["componentLibraryType"] == "base"
                                else "preferred" if c.get("preferredComponentFlag") else "extended")
                info["jlc_stock"] = c["stockCount"]
                break
    except Exception as e:                                           # noqa: BLE001
        info["error"] = str(e)
    cache[code] = info
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", type=int, default=5, help="boards in the order, for the stock check")
    ap.add_argument("--offline", action="store_true", help="skip the web lookups")
    args = ap.parse_args()

    board = pcbnew.LoadBoard(str(PCB))
    groups = defaultdict(list)       # LCSC -> [(ref, value, footprint name)]
    mpns = {}
    nopart, hand = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if fp.IsDNP() or fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
            continue
        code = fp.GetFieldText("LCSC").strip() if fp.HasField("LCSC") else ""
        name = str(fp.GetFPID().GetLibItemName())
        if code:
            groups[code].append((ref, fp.GetValue(), name))
            mpns.setdefault(code, fp.GetFieldText("MPN") if fp.HasField("MPN") else "")
        elif re.match(r"(%s)\d" % "|".join(FOOTPRINT_ONLY), ref):
            nopart.append(ref)
        else:
            hand.append((ref, fp.GetValue()))

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    OUT.mkdir(exist_ok=True)
    rows, problems, lines = [], [], []
    ext = 0
    for code, items in sorted(groups.items(), key=lambda kv: natural(kv[1][0][0])):
        refs = sorted((i[0] for i in items), key=natural)
        info = {} if args.offline else lookup(code, mpns.get(code, ""), cache)
        need = len(refs) * args.boards
        kind = info.get("type", "?")
        stock = info.get("jlc_stock", info.get("stock"))      # JLCPCB's own stock when the search found it
        if kind in ("extended", "preferred"):
            ext += 1
        flag = ""
        if args.offline:
            flag = "not checked"
        elif info.get("error"):
            flag = "lookup failed"
        elif stock is None or stock < need * 3:
            flag = "LOW STOCK" if stock else "OUT OF STOCK"
            problems.append(f"{code} ({items[0][1]}, {', '.join(refs[:4])}): stock {stock}, need {need}")
        rows.append([items[0][1], ",".join(refs), items[0][2], code])
        lines.append((refs[0], code, items[0][1], len(refs), kind, stock, info.get("price"), flag, info.get("model", ""), refs))
    CACHE.write_text(json.dumps(cache))

    with open(OUT / "jlcpcb_bom.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writerows(rows)

    # placement file via KiCad's own exporter (handles side, rotation and the exclude-from-position-files flag)
    raw = OUT / "_pos.csv"
    subprocess.run([CLI, "pcb", "export", "pos", str(PCB), "-o", str(raw), "--format", "csv", "--units", "mm",
                    "--exclude-dnp", "--smd-only"], check=True, capture_output=True)
    bomrefs = {r for g in groups.values() for r, _, _ in g}
    with open(raw, newline="", encoding="utf-8") as f, open(OUT / "jlcpcb_cpl.csv", "w", newline="", encoding="utf-8") as g:
        w = csv.writer(g)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        n = 0
        for r in csv.DictReader(f):
            if r["Ref"] in bomrefs:
                w.writerow([r["Ref"], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm",
                            "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])
                n += 1
    raw.unlink()
    through = sorted(bomrefs - {r["Designator"] for r in csv.DictReader(open(OUT / "jlcpcb_cpl.csv"))}, key=natural)

    total = sum(len(v) for v in groups.values())
    md = [f"# BOM report\n",
          f"Generated by `tools/bom.py` from `picomondo.kicad_pcb`. {total} parts with an LCSC number on "
          f"{len(groups)} line items; {ext} extended or preferred line items (JLCPCB charges a loading fee per "
          f"extended part type; check their current fee schedule). Stock check assumes {args.boards} boards "
          f"and a 3x margin.\n"]
    if problems:
        md += ["## Stock problems\n", *[f"- {p}" for p in problems], ""]
    md += ["## Line items\n", "| Refs | Qty | Value | LCSC | Type | Stock | Unit price | Note |", "|---|---|---|---|---|---|---|---|"]
    for first, code, val, qty, kind, stock, price, flag, model, refs in lines:
        short = ",".join(refs[:3]) + ("..." if len(refs) > 3 else "")
        md.append(f"| {short} | {qty} | {val} | {code} | {kind} | {stock if stock is not None else ''} | "
                  f"{price if price is not None else ''} | {flag} |")
    if hand:
        md += ["\n## No LCSC part: not assembled\n", *[f"- {r} {v}" for r, v in sorted(hand, key=lambda x: natural(x[0]))]]
    if through:
        md += ["\n## Through-hole parts in the BOM (not in the SMD placement file)\n", ", ".join(through)]
    md += ["\n## Footprint-only items (no purchase)\n", ", ".join(sorted(nopart, key=natural))]
    (OUT / "BOM_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"{total} parts, {len(groups)} line items, {ext} extended/preferred, CPL rows {n}")
    for p in problems:
        print("PROBLEM:", p)
    if hand:
        print("no LCSC (not assembled):", ", ".join(r for r, _ in hand))


if __name__ == "__main__":
    sys.exit(main())
