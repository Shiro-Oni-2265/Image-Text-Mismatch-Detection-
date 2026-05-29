"""
Script tải thêm 2000 cặp ảnh-text mới từ COCO dataset.
- Đọc CSV hiện có để bỏ qua ảnh đã tồn tại
- Tải ảnh mới từ COCO train2017
- Dịch caption sang tiếng Việt
- Gắn thêm vào file CSV hiện tại
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
IMAGE_DIR       = os.path.join(os.path.dirname(__file__), "images")
ANNOTATION_PATH = os.path.join(os.path.dirname(__file__), "annotations", "captions_train2017.json")
OUTPUT_CSV      = os.path.join(os.path.dirname(__file__), "captions_vi_4000.csv")
NUM_NEW_IMAGES  = 2000
DOWNLOAD_TIMEOUT = 20

os.makedirs(IMAGE_DIR, exist_ok=True)

# ── Đọc ảnh đã tồn tại trong CSV ────────────────────────────────────────────
existing_images = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_images.add(row["image_path"])

print(f"Số ảnh đã có trong CSV: {len(existing_images)}")

# ── Đọc COCO annotations ────────────────────────────────────────────────────
print("Đang đọc file annotation COCO...")
with open(ANNOTATION_PATH, "r", encoding="utf-8") as f:
    coco = json.load(f)

# Gom caption theo image_id
captions_en = {}
for ann in coco["annotations"]:
    img_name = f"{ann['image_id']:012d}.jpg"
    captions_en.setdefault(img_name, []).append(ann["caption"])

# Lọc ra những ảnh chưa có trong CSV
new_candidates = [img for img in captions_en if img not in existing_images]
random.seed(42)
random.shuffle(new_candidates)
selected = new_candidates[:NUM_NEW_IMAGES]

print(f"Số ảnh mới sẽ tải: {len(selected)}")

# ── Load model dịch ─────────────────────────────────────────────────────────
print("Đang tải model dịch Helsinki-NLP/opus-mt-en-vi...")
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "Helsinki-NLP/opus-mt-en-vi"
tokenizer = AutoTokenizer.from_pretrained(model_name)
translate_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print("Model dịch đã sẵn sàng.")

# ── Tải ảnh + dịch caption ─────────────────────────────────────────────────
rows = []
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
        except Exception as e:
            skipped += 1
            continue

    # Dịch caption
    cap_en = random.choice(captions_en[img_name])
    try:
        inputs = tokenizer(cap_en, return_tensors="pt", truncation=True)
        outputs = translate_model.generate(**inputs, max_length=80)
        cap_vi = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception:
        cap_vi = cap_en  # fallback nếu dịch lỗi

    rows.append({
        "image_path": img_name,
        "caption": cap_vi,
        "label": 1
    })

# ── Ghi thêm vào CSV ────────────────────────────────────────────────────────
with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
    writer.writerows(rows)

print(f"\n✓ Đã thêm {len(rows)} cặp ảnh-text mới vào {OUTPUT_CSV}")
print(f"  Bỏ qua (lỗi tải): {skipped}")
print(f"  Tổng mẫu trong CSV bây giờ: {len(existing_images) + len(rows)}")
