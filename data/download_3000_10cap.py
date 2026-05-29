"""
Tải thêm 3000 ảnh mới từ COCO dataset.
Mỗi ảnh tạo 10 cặp:
  - 5 match   (caption đúng của ảnh đó, label=1)
  - 5 mismatch (caption lấy từ ảnh khác,  label=0)
Dịch sang tiếng Việt bằng GPU theo batch để nhanh.
Kết quả được ghi thêm vào captions_vi_4000.csv.
"""

import os
import sys
import csv
import json
import random
import requests
from tqdm import tqdm

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ── Cấu hình ────────────────────────────────────────────────────────────────
IMAGE_DIR        = os.path.join(os.path.dirname(__file__), "images")
ANNOTATION_PATH  = os.path.join(os.path.dirname(__file__), "annotations", "captions_train2017.json")
OUTPUT_CSV       = os.path.join(os.path.dirname(__file__), "captions_vi_4000.csv")
NUM_NEW_IMAGES   = 3000
MATCH_PER_IMG    = 5    # số caption đúng mỗi ảnh
MISMATCH_PER_IMG = 5    # số caption sai mỗi ảnh
TRANSLATE_BATCH  = 64   # kích thước batch dịch trên GPU (giảm xuống 32 nếu OOM)
DOWNLOAD_TIMEOUT = 20
SEED             = 999

os.makedirs(IMAGE_DIR, exist_ok=True)

# ── Đọc ảnh đã tồn tại trong CSV ────────────────────────────────────────────
existing_images = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_images.add(row["image_path"])

print(f"[INFO] Ảnh đã có trong CSV : {len(existing_images)} ảnh")

# ── Đọc COCO annotations ────────────────────────────────────────────────────
print("[INFO] Đọc COCO annotations...")
with open(ANNOTATION_PATH, "r", encoding="utf-8") as f:
    coco = json.load(f)

captions_en: dict[str, list[str]] = {}
for ann in coco["annotations"]:
    img_name = f"{ann['image_id']:012d}.jpg"
    captions_en.setdefault(img_name, []).append(ann["caption"])

# Chỉ chọn ảnh có đủ MATCH_PER_IMG caption và chưa có trong CSV
new_candidates = [
    img for img, caps in captions_en.items()
    if img not in existing_images and len(caps) >= MATCH_PER_IMG
]
random.seed(SEED)
random.shuffle(new_candidates)
selected = new_candidates[:NUM_NEW_IMAGES]

print(f"[INFO] Số ảnh mới sẽ tải   : {len(selected)}")

# ── Load model dịch lên GPU ─────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Sử dụng device       : {device}")
if device == "cpu":
    print("[WARN] Không tìm thấy GPU — dịch trên CPU sẽ chậm hơn.")

model_name  = "Helsinki-NLP/opus-mt-en-vi"
print(f"[INFO] Tải model dịch {model_name}...")
tokenizer   = AutoTokenizer.from_pretrained(model_name)
trans_model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
trans_model.eval()
print("[INFO] Model dịch sẵn sàng.")

# ── Bước 1: Tải ảnh ─────────────────────────────────────────────────────────
print("\n[Bước 1] Tải ảnh từ COCO train2017...")
valid_images: list[str] = []
skipped      = 0
already_have = 0

for img_name in tqdm(selected, desc="Tải ảnh", unit="ảnh"):
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path):
        # Ảnh đã có trên disk — bỏ qua tải, dùng luôn
        already_have += 1
    else:
        url = f"http://images.cocodataset.org/train2017/{img_name}"
        try:
            r = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            if r.status_code == 200:
                with open(img_path, "wb") as fout:
                    fout.write(r.content)
            else:
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue
    valid_images.append(img_name)

print(f"[INFO] Tải mới        : {len(valid_images) - already_have} ảnh")
print(f"[INFO] Đã có trên disk: {already_have} ảnh  (bỏ qua, không tải lại)")
print(f"[INFO] Lỗi / bỏ qua  : {skipped} ảnh")
print(f"[INFO] Tổng xử lý     : {len(valid_images)} ảnh")

# ── Bước 2: Tạo danh sách caption cần dịch ─────────────────────────────────
print("\n[Bước 2] Chuẩn bị captions...")

all_captions_en: list[str] = []
meta: list[tuple[str, int]] = []  # (img_name, label)
all_img_list = list(captions_en.keys())

for img_name in valid_images:
    caps = captions_en[img_name]

    # 5 match — lấy chính xác 5 caption của ảnh này
    match_caps = random.sample(caps, MATCH_PER_IMG)
    for c in match_caps:
        all_captions_en.append(c)
        meta.append((img_name, 1))

    # 5 mismatch — lấy caption từ 5 ảnh khác nhau
    other_imgs = random.sample([x for x in all_img_list if x != img_name], MISMATCH_PER_IMG)
    for other in other_imgs:
        c = random.choice(captions_en[other])
        all_captions_en.append(c)
        meta.append((img_name, 0))

print(f"[INFO] Tổng captions cần dịch: {len(all_captions_en)}")
print(f"         Match (label=1)      : {sum(1 for _, l in meta if l == 1)}")
print(f"         Mismatch (label=0)   : {sum(1 for _, l in meta if l == 0)}")

# ── Bước 3: Dịch batch trên GPU ─────────────────────────────────────────────
print(f"\n[Bước 3] Dịch sang tiếng Việt (batch={TRANSLATE_BATCH}, device={device})...")

all_captions_vi: list[str] = []

for i in tqdm(range(0, len(all_captions_en), TRANSLATE_BATCH), desc="Dịch batch", unit="batch"):
    batch_en = all_captions_en[i : i + TRANSLATE_BATCH]
    try:
        inputs = tokenizer(
            batch_en,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        ).to(device)
        with torch.no_grad():
            outputs = trans_model.generate(
                **inputs,
                max_length=128,
                num_beams=4,
                early_stopping=True,
            )
        decoded = [tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
    except Exception as e:
        # Fallback: giữ nguyên tiếng Anh nếu dịch lỗi
        print(f"\n[WARN] Lỗi dịch batch {i//TRANSLATE_BATCH}: {e}")
        decoded = batch_en
    all_captions_vi.extend(decoded)

# ── Bước 4: Ghi thêm vào CSV ─────────────────────────────────────────────────
print("\n[Bước 4] Ghi vào CSV...")

rows = [
    {"image_path": img_name, "caption": cap_vi, "label": label}
    for (img_name, label), cap_vi in zip(meta, all_captions_vi)
]

with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
    writer.writerows(rows)

match_added    = sum(1 for r in rows if r["label"] == 1)
mismatch_added = sum(1 for r in rows if r["label"] == 0)
total_new      = len(existing_images) + len(rows)

print(f"\n{'='*55}")
print(f"  ✓ Đã thêm {len(rows):,} dòng mới vào {os.path.basename(OUTPUT_CSV)}")
print(f"    - Match    (label=1) : {match_added:,}")
print(f"    - Mismatch (label=0) : {mismatch_added:,}")
print(f"  Tổng mẫu trong CSV bây giờ : {total_new:,}")
print(f"{'='*55}")
