# tools/import_csv_with_video.py
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data.csv"
OUT_JS = ROOT / "data.js"

def to_float(x: str):
    x = (x or "").strip()
    if x == "":
        return None
    try:
        return float(x)
    except:
        return None

def to_int(x: str):
    x = (x or "").strip()
    if x == "":
        return None
    try:
        return int(float(x))
    except:
        return None

def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"data.csv not found: {CSV_PATH}")

    items = []
    next_id = 1

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            kind = (row.get("kind") or "photo").strip()
            lat = to_float(row.get("lat",""))
            lon = to_float(row.get("lon",""))
            alt = to_float(row.get("alt_m",""))
            dt = (row.get("datetime") or "").strip()
            typ = (row.get("type") or "").strip()
            cap = (row.get("caption") or "").strip()

            # lat/lonが無い行は地図に出せないのでスキップ（事故防止）
            if lat is None or lon is None:
                continue

            rid = to_int(row.get("id",""))
            if rid is None:
                rid = next_id
                next_id += 1
            else:
                next_id = max(next_id, rid + 1)

            thumb = (row.get("thumb") or "").strip()

            if kind == "video":
                url = (row.get("url") or "").strip()
                if not url:
                    # video で url なしは表示不能なのでスキップ
                    continue
                it = {
                    "id": rid,
                    "kind": "video",
                    "type": typ,
                    "caption": cap,
                    "datetime": dt,
                    "lat": lat,
                    "lon": lon,
                    "alt_m": alt if alt is not None else None,
                    "thumb": thumb,
                    "url": url,
                }
            else:
                file_rel = (row.get("file") or row.get("path") or "").strip()
                if not file_rel:
                    continue
                it = {
                    "id": rid,
                    "kind": "photo",
                    "type": typ,
                    "caption": cap,
                    "datetime": dt,
                    "lat": lat,
                    "lon": lon,
                    "alt_m": alt if alt is not None else None,
                    "thumb": thumb,
                    "path": file_rel,  # index.html側は path を見る想定
                }

            items.append(it)

    # idで安定化
    items.sort(key=lambda x: x["id"])

    js = "const DATA = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n"
    OUT_JS.write_text(js, encoding="utf-8")
    print(f"OK: wrote {len(items)} items -> {OUT_JS}")

if __name__ == "__main__":
    main()
