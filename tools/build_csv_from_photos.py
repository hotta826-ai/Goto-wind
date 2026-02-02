# tools/build_csv_from_photos.py
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]      # Goto_Wind/
PHOTOS_DIR = ROOT / "photos"
OUT_CSV = ROOT / "data.csv"

def find_exiftool() -> Path:
    # 1) tools/exiftool.exe
    cand = Path(__file__).resolve().parent / "exiftool.exe"
    if cand.exists():
        return cand

    # 2) tools/exiftool (拡張子なし)
    cand2 = Path(__file__).resolve().parent / "exiftool"
    if cand2.exists():
        return cand2

    # 3) PATH 上の exiftool
    #    (Windowsなら "exiftool" で見つかることもある)
    return Path("exiftool")

def run_exiftool_json(exiftool: Path) -> list[dict[str, Any]]:
    if not PHOTOS_DIR.exists():
        raise FileNotFoundError(f"photos folder not found: {PHOTOS_DIR}")

    # exiftool にフォルダを渡して、jpg/jpegを再帰対象にする
    cmd = [
        str(exiftool),
        "-j",          # JSON
        "-G1",         # グループ名付き
        "-n",          # 緯度経度を数値
        "-q", "-q",    # 余計な出力を抑制
        "-r",          # 再帰
        "-ext", "jpg",
        "-ext", "jpeg",
        str(PHOTOS_DIR),
    ]

    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # exiftool がstderrに警告を出すことがあるが、stdoutがJSONなら読み進める
    out = (res.stdout or "").strip()
    if not out:
        raise RuntimeError(f"exiftool returned empty output.\nstderr:\n{res.stderr}")

    try:
        data = json.loads(out)
        if not isinstance(data, list):
            raise ValueError("exiftool JSON is not a list")
        return data
    except json.JSONDecodeError as e:
        # 壊れてる場合は、先頭/末尾だけ見せる
        head = out[:800]
        tail = out[-800:] if len(out) > 800 else ""
        raise RuntimeError(
            "Failed to parse exiftool JSON.\n"
            f"JSONDecodeError: {e}\n\n--- stdout head ---\n{head}\n\n--- stdout tail ---\n{tail}\n\n--- stderr ---\n{res.stderr}"
        )

def pick(meta: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in meta:
            return meta[k]
    return None

def main() -> None:
    exiftool = find_exiftool()
    metas = run_exiftool_json(exiftool)

    rows: list[dict[str, Any]] = []
    next_id = 1

    for m in metas:
        src = m.get("SourceFile") or ""
        # exiftoolは "./photos/xxx.jpg" みたいに返すことがある
        p = Path(str(src).replace("\\", "/")).name
        if not p:
            continue

        # datetime は EXIF優先、なければ FileModifyDate
        dt = pick(m, [
            "EXIF:DateTimeOriginal",
            "EXIF:CreateDate",
            "QuickTime:CreateDate",   # 念のため
            "System:FileModifyDate",
        ]) or ""

        lat = pick(m, ["Composite:GPSLatitude", "EXIF:GPSLatitude"])
        lon = pick(m, ["Composite:GPSLongitude", "EXIF:GPSLongitude"])
        alt = pick(m, ["Composite:GPSAltitude", "EXIF:GPSAltitude"])

        # 出力上の「file」「thumb」は index.html が読む前提に合わせる
        file_rel = f"photos/{p}"
        thumb_name = Path(p).stem + "_thumb.jpg"
        thumb_rel = f"thumbs/{thumb_name}"

        rows.append({
            "id": next_id,
            "kind": "photo",
            "file": file_rel,
            "thumb": thumb_rel,
            "lat": "" if lat is None else lat,
            "lon": "" if lon is None else lon,
            "alt_m": "" if alt is None else alt,
            "datetime": str(dt),
            "type": "",
            "caption": "",
            "url": "",
        })
        next_id += 1

    # 日時で軽く安定ソート（空欄は最後）
    rows.sort(key=lambda r: (r["datetime"] == "", str(r["datetime"]), int(r["id"])))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id","kind","file","thumb","lat","lon","alt_m","datetime","type","caption","url"]
        )
        w.writeheader()
        w.writerows(rows)

    print(f"OK: wrote {len(rows)} rows -> {OUT_CSV}")

if __name__ == "__main__":
    main()
