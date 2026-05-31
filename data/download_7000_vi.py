import os
import sys
import csv
import json
import random
import requests
import torch
from tqdm import tqdm
from transformers import MarianTokenizer, MarianMTModel

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
ANNOTATION_PATH = os.path.join(BASE_DIR, "annotations", "captions_train2017.json")
INPUT_CSV = os.path.join(BASE_DIR, "captions.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "captions_vi_4000.csv")

NUM_NEW_IMAGES = 7000
DOWNLOAD_TIMEOUT = 15
BATCH_SIZE = 32

os.makedirs(IMAGE_DIR, exist_ok=True)

# Device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Using device: {device}")

# Load Translation Model
print("[INFO] Loading translation model Helsinki-NLP/opus-mt-en-vi...")
model_name = "Helsinki-NLP/opus-mt-en-vi"
tokenizer = MarianTokenizer.from_pretrained(model_name)
translate_model = MarianMTModel.from_pretrained(model_name, use_safetensors=True).to(device)
print("[INFO] Translation model loaded.")

def translate_batch(sentences):
    inputs = tokenizer(
        sentences,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    ).to(device)
    with torch.no_grad():
        outputs = translate_model.generate(**inputs, max_length=128)
    return tokenizer.batch_decode(outputs, skip_special_tokens=True)

# 1. Check/Create OUTPUT_CSV
existing_images = set()
if os.path.exists(OUTPUT_CSV):
    print(f"[INFO] {OUTPUT_CSV} already exists. Reading existing images...")
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_images.add(row["image_path"])
    print(f"[INFO] Found {len(existing_images)} existing images in output CSV.")
else:
    print(f"[INFO] Creating new output CSV at {OUTPUT_CSV}...")
    if os.path.exists(INPUT_CSV):
        print(f"[INFO] Translating existing captions from {INPUT_CSV} to Vietnamese...")
        rows_to_translate = []
        with open(INPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows_to_translate.append(row)
        
        translated_rows = []
        # Translate in batches
        for i in tqdm(range(0, len(rows_to_translate), BATCH_SIZE), desc="Translating existing CSV"):
            batch = rows_to_translate[i : i + BATCH_SIZE]
            caps_en = [r["caption"] for r in batch]
            try:
                caps_vi = translate_batch(caps_en)
            except Exception as e:
                print(f"[WARN] Error translating batch: {e}. Using fallback.")
                caps_vi = caps_en
            
            for row, cap_vi in zip(batch, caps_vi):
                translated_rows.append({
                    "image_path": row["image_path"],
                    "caption": cap_vi,
                    "label": row["label"]
                })
                existing_images.add(row["image_path"])
        
        # Write to new CSV
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
            writer.writeheader()
            writer.writerows(translated_rows)
        print(f"[INFO] Successfully translated and wrote {len(translated_rows)} existing images to {OUTPUT_CSV}.")
    else:
        # Create empty CSV with header
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
            writer.writeheader()

# 2. Read COCO Annotations
print("[INFO] Reading COCO annotations...")
with open(ANNOTATION_PATH, "r", encoding="utf-8") as f:
    coco = json.load(f)

# Group captions by image name
captions_en = {}
for ann in coco["annotations"]:
    img_name = f"{ann['image_id']:012d}.jpg"
    captions_en.setdefault(img_name, []).append(ann["caption"])

# 3. Filter candidates
disk_images = set(os.listdir(IMAGE_DIR))
all_processed = existing_images.union(disk_images)
candidates = [img for img in captions_en if img not in all_processed]

print(f"[INFO] Total COCO images: {len(captions_en)}")
print(f"[INFO] Processed/disk images: {len(all_processed)}")
print(f"[INFO] Remaining candidates: {len(candidates)}")

if len(candidates) < NUM_NEW_IMAGES:
    print(f"[WARN] Not enough candidates! Reducing download count to {len(candidates)}.")
    NUM_NEW_IMAGES = len(candidates)

# Select candidates
random.seed(42)
random.shuffle(candidates)
selected = candidates[:NUM_NEW_IMAGES]
print(f"[INFO] Selected {len(selected)} new images to download and translate.")

# 4. Download and translate
batch_rows = []
skipped = 0

# Progress bar
pbar = tqdm(total=len(selected), desc="Downloading + Translating")

for idx, img_name in enumerate(selected):
    img_path = os.path.join(IMAGE_DIR, img_name)
    url = f"http://images.cocodataset.org/train2017/{img_name}"
    
    # Download
    success = False
    if os.path.exists(img_path):
        success = True
    else:
        try:
            r = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            if r.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(r.content)
                success = True
            else:
                skipped += 1
        except Exception:
            skipped += 1
            
    if not success:
        pbar.update(1)
        continue
        
    # Pick a random caption and save
    cap_en = random.choice(captions_en[img_name])
    batch_rows.append((img_name, cap_en))
    
    # Translate and write in batches
    if len(batch_rows) >= BATCH_SIZE or idx == len(selected) - 1:
        img_names = [r[0] for r in batch_rows]
        caps_en = [r[1] for r in batch_rows]
        
        try:
            caps_vi = translate_batch(caps_en)
        except Exception as e:
            print(f"\n[WARN] Translation batch failed: {e}. Using English fallback.")
            caps_vi = caps_en
            
        # Append to CSV
        rows_to_write = []
        for name, cap_vi in zip(img_names, caps_vi):
            rows_to_write.append({
                "image_path": name,
                "caption": cap_vi,
                "label": 1
            })
            
        with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
            writer.writerows(rows_to_write)
            
        pbar.update(len(batch_rows))
        batch_rows = []

pbar.close()
print(f"\n[INFO] Done! Added {len(selected) - skipped} images to {OUTPUT_CSV}.")
print(f"[INFO] Skipped: {skipped} due to download errors.")
