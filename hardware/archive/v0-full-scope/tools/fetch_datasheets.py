"""Download datasheets for LCSC parts into resources/datasheets/.

Usage:
  python fetch_datasheets.py                 # every LCSC ID found in resources/bom/*.csv
  python fetch_datasheets.py C2864583 C7519  # specific LCSC IDs

Files are named <MPN>_<LCSC>.pdf. Existing files are skipped. A manifest of what was found
(MPN, manufacturer, package, source URL) is written to resources/datasheets/MANIFEST.csv.
"""
import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "resources" / "datasheets"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lcsc_ids_from_boms():
    ids = []
    for f in sorted((ROOT / "resources" / "bom").glob("*.csv")):
        for row in csv.DictReader(open(f, encoding="utf-8-sig")):
            for key in ("LCSC Part #", "LCSC", "lcsc"):
                v = (row.get(key) or "").strip()
                if re.fullmatch(r"C\d+", v) and v not in ids:
                    ids.append(v)
    return ids


def safe(name):
    return re.sub(r"[^A-Za-z0-9._+-]+", "_", name).strip("_")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = sys.argv[1:] or lcsc_ids_from_boms()
    manifest = OUT / "MANIFEST.csv"
    rows = {}
    if manifest.exists():
        for row in csv.DictReader(open(manifest, encoding="utf-8")):
            rows[row["lcsc"]] = row
    failed = []
    for lcsc in ids:
        try:
            info = json.loads(get(f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={lcsc}"))["result"]
        except Exception as e:                       # noqa: BLE001
            failed.append((lcsc, f"lookup failed: {e}"))
            print(f"{lcsc:10} lookup failed: {e}")
            continue
        if not info:
            failed.append((lcsc, "not found on LCSC (delisted or wrong ID?)"))
            print(f"{lcsc:10} not found on LCSC (delisted or wrong ID?)")
            continue
        time.sleep(0.3)
        mpn = info.get("productModel") or lcsc
        url = info.get("pdfUrl")
        fname = f"{safe(mpn)}_{lcsc}.pdf"
        path = OUT / fname
        status = "ok"
        if path.exists():
            status = "exists"
        elif not url:
            status = "no datasheet link"
        else:
            try:
                data = get(url, timeout=120)
                if not data.startswith(b"%PDF"):
                    status = "not a pdf"
                else:
                    path.write_bytes(data)
            except Exception as e:                   # noqa: BLE001
                status = f"download failed: {e}"
        rows[lcsc] = {"lcsc": lcsc, "mpn": mpn, "manufacturer": info.get("brandNameEn") or "",
                      "package": info.get("encapStandard") or "", "file": fname if path.exists() else "",
                      "source": url or "", "status": status}
        print(f"{lcsc:10} {mpn[:34]:34} {status}")
        if status not in ("ok", "exists"):
            failed.append((lcsc, status))
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lcsc", "mpn", "manufacturer", "package", "file", "source", "status"])
        w.writeheader()
        w.writerows(rows.values())
    print(f"\n{len(ids) - len(failed)} of {len(ids)} ok; {len(failed)} need attention")


if __name__ == "__main__":
    main()
