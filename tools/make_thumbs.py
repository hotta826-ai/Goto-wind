from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = ROOT / "photos"
THUMBS = ROOT / "thumbs"

MAX_W, MAX_H = 920, 680  # 一覧の見え方優先（適宜調整OK）
JPEG_QUALITY = 82

def is_image(p: Path) -> bool:
    return p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]

def main():
    THUMBS.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in PHOTOS.glob("*") if p.is_file() and is_image(p)])
    if not files:
        print(f"[WARN] No images in {PHOTOS}")
        return

    for p in files:
        out = THUMBS / f"{p.stem}_thumb.jpg"
        try:
            img = Image.open(p)
            img = ImageOps.exif_transpose(img)  # iPhone回転対策
            img.thumbnail((MAX_W, MAX_H))
            img = img.convert("RGB")
            img.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
            print("OK", out.relative_to(ROOT))
        except Exception as e:
            print("NG", p.name, e)

if __name__ == "__main__":
    main()
