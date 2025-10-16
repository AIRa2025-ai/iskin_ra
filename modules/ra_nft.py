# modules/ra_nft.py
import os
import json
import time
import random
import string
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ================== CONFIG ==================
NFT_STORAGE_API = os.getenv("NFT_STORAGE_API")  # токен для нового ресурса
CONTEXT_PATH = Path("RaSvet/context.json")
OUTPUT_DIR = Path("nft_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ================== HELPERS ==================
def load_rasvet_excerpt(max_chars=2000) -> str:
    if CONTEXT_PATH.exists():
        try:
            with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("context", "")[:max_chars]
        except Exception as e:
            print("⚠️ Ошибка чтения контекста RaSvet:", e)
    return ""

def build_prompt(user_text: str) -> str:
    rasvet = load_rasvet_excerpt(1800)
    parts = []
    if user_text:
        parts.append(f"Запрос: {user_text}")
    if rasvet:
        parts.append(f"Контекст РаСвета: {rasvet}")
    parts.append("Стиль: мистический, рунический, органический; тон: тёплый, древний, пробуждающий.")
    return "\n\n".join(parts)

def random_glyph_text(n=6) -> str:
    alphabet = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃ" + string.ascii_uppercase
    return "".join(random.choice(alphabet) for _ in range(n))

def create_glyph(prompt: str, seed: int) -> Path:
    random.seed(seed)
    size = 768
    img = Image.new("RGB", (size, size), (12, 10, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    for i, r in enumerate(range(80, cx, 60)):
        color = (180 + (i * 7) % 60, 170 + (i * 3) % 80, 230)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2 + (i % 3))

    for ang in range(0, 360, 15):
        length = 180 + (seed % 120) + (ang % 30)
        x2 = cx + int(length * (0.9 + 0.1 * ((ang % 20) / 20.0)))
        y2 = cy + int(length * (0.9 + 0.08 * ((ang % 33) / 33.0)))
        draw.line([cx, cy, x2, y2], fill=(150, 190, 255), width=1)

    glyph_txt = random_glyph_text(7)
    try:
        font = ImageFont.truetype("arial.ttf", 64)
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textlength(glyph_txt, font=font), 64
    draw.text((cx - tw / 2, cy - th / 2), glyph_txt, fill=(255, 245, 180), font=font)
    draw.text((12, size - 30), prompt[:60], fill=(180, 180, 200), font=ImageFont.load_default())

    filename = OUTPUT_DIR / f"glyph_{seed}.png"
    img.save(filename, format="PNG", optimize=True)
    print(f"✅ Глиф создан: {filename}  (seed={seed})")
    return filename

def sign_metadata(meta: dict) -> dict:
    # Лёгкая подпись: просто добавляем контрольную строку
    meta["provenance"] = {
        "creator": "РаСвет",
        "timestamp": int(time.time()),
        "signature": "".join(random.choices(string.hexdigits, k=16))
    }
    return meta

def upload_to_nft_storage(file_path: Path) -> str:
    # Заглушка под новый ресурс
    print(f"⚡️ [UPLOAD] Файл {file_path} загружен в NFT Storage (симуляция).")
    return f"https://fake-nft-storage.example/{file_path.name}"

# ================== Основной процесс ==================
def mint_nft(user_text: str = "Пусть родится глиф защиты") -> dict:
    prompt = build_prompt(user_text)
    seed = int(time.time() * 1000) % 99999999
    glyph_file = create_glyph(prompt, seed)

    meta = {
        "name": f"Глиф Ра — {seed}",
        "description": "Живой магический артефакт от Ра. Сгенерирован на основе RaSvet.",
        "image": str(glyph_file),
        "attributes": [
            {"trait_type": "seed", "value": str(seed)},
            {"trait_type": "origin", "value": "РаСвет"}
        ],
        "rasvet_excerpt": load_rasvet_excerpt(500)
    }

    meta_signed = sign_metadata(meta)
    meta_file = OUTPUT_DIR / f"metadata_{seed}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_signed, f, ensure_ascii=False, indent=2)
    print("✅ Metadata signed and saved:", meta_file)

    meta_url = upload_to_nft_storage(meta_file)
    image_url = upload_to_nft_storage(glyph_file)

    return {"metadata_url": meta_url, "image_url": image_url, "seed": seed, "meta_file": str(meta_file)}

# ================== CLI ==================
if __name__ == "__main__":
    result = mint_nft()
    print("🎉 NFT готов:", result)
