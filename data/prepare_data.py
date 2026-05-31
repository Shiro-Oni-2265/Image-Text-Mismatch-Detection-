import os, json, csv, random, requests
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

IMAGE_DIR = "data/images"
ANNOTATION_PATH = "data/annotations/captions_train2017.json"
OUTPUT_CSV = "data/captions_vi.csv"
NUM_IMAGES = 4000

os.makedirs(IMAGE_DIR, exist_ok=True)

with open(ANNOTATION_PATH, "r", encoding="utf-8") as f:
    coco = json.load(f)

image_ids = list({ann["image_id"] for ann in coco["annotations"]})[:NUM_IMAGES]
image_ids_set = set(image_ids)

captions_en = {}
for ann in coco["annotations"]:
    if ann["image_id"] in image_ids_set:
        img_name = f"{ann['image_id']:012d}.jpg"
        captions_en.setdefault(img_name, []).append(ann["caption"])

model_name = "Helsinki-NLP/opus-mt-en-vi"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

rows = []

for img_name, caps in tqdm(captions_en.items(), desc="Download + Translate"):
    img_path = os.path.join(IMAGE_DIR, img_name)

    if not os.path.exists(img_path):
        url = f"http://images.cocodataset.org/train2017/{img_name}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(r.content)
            else:
                continue
        except:
            continue

    cap_en = random.choice(caps)

    inputs = tokenizer(cap_en, return_tensors="pt", truncation=True)
    outputs = model.generate(**inputs, max_length=80)
    cap_vi = tokenizer.decode(outputs[0], skip_special_tokens=True)

    rows.append({
        "image_path": img_name,
        "caption": cap_vi,
        "label": 1
    })

with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
    writer.writeheader()
    writer.writerows(rows)

print("DONE")
print("Tong so anh/caption:", len(rows))
print("Luu tai:", OUTPUT_CSV)