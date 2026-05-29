"""
Tải 3000 ảnh mới từ COCO dataset, mỗi ảnh có 10 captions:
  - 5 match   (label=1): caption thật của ảnh đó
  - 5 mismatch (label=0): caption lấy từ ảnh khác ngẫu nhiên
Bỏ qua ảnh đã tồn tại trong CSV và trên disk.
"""

import os
import sys
import csv
import json
import random
import requests
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ── Cấu hình ────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(__file__)
IMAGE_DIR       = os.path.join(BASE_DIR, "images")
ANNOTATION_PATH = os.path.join(BASE_DIR, "annotations", "captions_train2017.json")
OUTPUT_CSV      = os.path.join(BASE_DIR, "captions_vi_4000.csv")
NUM_NEW_IMAGES  = 3000
NUM_MATCH       = 5   # caption match mỗi ảnh
NUM_MISMATCH    = 5   # caption mismatch mỗi ảnh
DOWNLOAD_TIMEOUT = 20
BATCH_SIZE      = 16  # số câu dịch cùng lúc
RANDOM_SEED     = 99

os.makedirs(IMAGE_DIR, exist_ok=True)

# ── Đọc ảnh đã có trong CSV (bỏ qua) ────────────────────────────────────────
existing_images = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_images.add(row["image_path"])

print(f"Ảnh đã có trong CSV: {len(existing_images)}")

# ── Đọc COCO annotations ────────────────────────────────────────────────────
print("Đọc file annotation COCO...")
with open(ANNOTATION_PATH, "r", encoding="utf-8") as f:
    coco = json.load(f)

# Gom caption tiếng Anh theo tên ảnh
captions_en: dict[str, list[str]] = {}
for ann in coco["annotations"]:
    img_name = f"{ann['image_id']:012d}.jpg"
    captions_en.setdefault(img_name, []).append(ann["caption"])

# Lọc ảnh chưa có trong CSV
candidates = [img for img in captions_en if img not in existing_images]
random.seed(RANDOM_SEED)
random.shuffle(candidates)
selected = candidates[:NUM_NEW_IMAGES]

print(f"Ảnh mới sẽ tải: {len(selected)}")

# ── Load model dịch ─────────────────────────────────────────────────────────
print("Tải model dịch Helsinki-NLP/opus-mt-en-vi...")
from transformers import MarianTokenizer, MarianMTModel
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "Helsinki-NLP/opus-mt-en-vi"
tokenizer = MarianTokenizer.from_pretrained(model_name)
trans_model = MarianMTModel.from_pretrained(model_name).to(device)
print(f"Model dịch sẵn sàng (device={device}).")


def translate_batch(sentences: list[str]) -> list[str]:
    """Dịch một batch câu tiếng Anh sang tiếng Việt."""
    results = []
    for i in range(0, len(sentences), BATCH_SIZE):
        batch = sentences[i : i + BATCH_SIZE]
        inputs = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        ).to(device)
        with torch.no_grad():
            outputs = trans_model.generate(**inputs, max_length=128)
        results.extend(
            tokenizer.batch_decode(outputs, skip_special_tokens=True)
        )
    return results


# ── Tải ảnh + sinh caption ───────────────────────────────────────────────────
all_img_names = list(captions_en.keys())  # pool để lấy mismatch caption

rows: list[dict] = []
skipped = 0

for img_name in tqdm(selected, desc="Download + Translate"):
    img_path = os.path.join(IMAGE_DIR, img_name)

    # Tải ảnh nếu chưa có trên disk
    if not os.path.exists(img_path):
        url = f"http://images.cocodataset.org/train2017/{img_name}"
        try:
            r = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            if r.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(r.content)
            else:
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue

    # --- 5 caption MATCH (caption thật của ảnh) ---
    real_caps = captions_en[img_name]
    if len(real_caps) >= NUM_MATCH:
        match_caps_en = random.sample(real_caps, NUM_MATCH)
    else:
        # Nếu ảnh có ít hơn 5 caption thì lặp lại
        match_caps_en = (real_caps * ((NUM_MATCH // len(real_caps)) + 1))[:NUM_MATCH]

    # --- 5 caption MISMATCH (caption từ ảnh khác) ---
    mismatch_caps_en: list[str] = []
    while len(mismatch_caps_en) < NUM_MISMATCH:
        other = random.choice(all_img_names)
        if other != img_name:
            mismatch_caps_en.append(random.choice(captions_en[other]))

    # --- Dịch tất cả 10 caption cùng lúc ---
    all_en = match_caps_en + mismatch_caps_en
    try:
        all_vi = translate_batch(all_en)
    except Exception:
        all_vi = all_en  # fallback nếu lỗi

    match_vi    = all_vi[:NUM_MATCH]
    mismatch_vi = all_vi[NUM_MATCH:]

    for cap in match_vi:
        rows.append({"image_path": img_name, "caption": cap, "label": 1})
    for cap in mismatch_vi:
        rows.append({"image_path": img_name, "caption": cap, "label": 0})

# ── Ghi thêm vào CSV ────────────────────────────────────────────────────────
file_exists = os.path.exists(OUTPUT_CSV)
with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
    if not file_exists:
        writer.writeheader()
    writer.writerows(rows)

imgs_added = len(rows) // (NUM_MATCH + NUM_MISMATCH)
print(f"\n✓ Đã thêm {imgs_added} ảnh mới ({len(rows)} cặp ảnh-caption) vào {OUTPUT_CSV}")
print(f"  Bỏ qua (lỗi tải): {skipped}")
print(f"  Tổng mẫu trong CSV: {len(existing_images) + len(rows)}")
