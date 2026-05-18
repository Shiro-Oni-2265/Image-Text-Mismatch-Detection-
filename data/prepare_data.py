"""
Mô tả file:
Script chuẩn bị dữ liệu cho dự án Image-Text Mismatch Detection.

Chức năng chính:
1. Đọc các ảnh có sẵn trong data/images/
2. Tự động tạo MATCH samples (ảnh + caption đúng)
3. Tự động tạo MISMATCH samples (ảnh + caption sai)
4. Cân bằng số lượng MATCH và MISMATCH (50/50)
5. Xuất ra captions.csv chuẩn để dùng cho training

Cách dùng:
    python data/prepare_data.py
    python data/prepare_data.py --annotations data/annotations/captions_train2017.json
    python data/prepare_data.py --annotations data/annotations/captions_train2017.json --max-samples 2000
"""

import os
import csv
import json
import random
import argparse

# ── Captions mô tả cho từng ảnh placeholder ──────────────────────────────────
PLACEHOLDER_CAPTIONS = {
    "blue_circle.jpg":  ["A blue circle", "A round blue shape", "Blue circular object"],
    "cyan_img.jpg":     ["A cyan colored image", "Light blue cyan background", "Solid cyan color"],
    "dark_img.jpg":     ["A dark image", "Very dark background", "Black dark scene"],
    "green_rect.jpg":   ["A green rectangle", "Green rectangular shape", "Solid green image"],
    "orange_img.jpg":   ["An orange colored image", "Bright orange background", "Solid orange color"],
    "pink_img.jpg":     ["A pink image", "Soft pink background", "Solid pink color"],
    "purple_img.jpg":   ["A purple image", "Deep purple background", "Solid purple color"],
    "red_square.jpg":   ["A red square", "Red square shape", "Bright red colored square"],
    "sample_blue.jpg":  ["A blue sample image", "Blue colored sample", "Sample with blue color"],
    "sample_red.jpg":   ["A red sample image", "Red colored sample", "Sample with red color"],
    "white_img.jpg":    ["A white image", "Bright white background", "Pure white color"],
    "yellow_box.jpg":   ["A yellow box", "Bright yellow rectangle", "Yellow colored image"],
}


def build_from_local_images(image_dir: str, output_csv: str):
    """Tạo captions.csv từ ảnh local có sẵn."""
    images = [f for f in os.listdir(image_dir)
              if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not images:
        print(f"Không tìm thấy ảnh nào trong {image_dir}")
        return

    rows = []
    for img in images:
        caps = PLACEHOLDER_CAPTIONS.get(img, [f"An image named {os.path.splitext(img)[0]}"])
        cap = random.choice(caps)
        rows.append({"image_path": img, "caption": cap, "label": 1})   # MATCH

    # Tạo MISMATCH: ghép ảnh với caption của ảnh khác ngẫu nhiên
    img_list = [r["image_path"] for r in rows]
    cap_list  = [r["caption"]    for r in rows]
    for i, img in enumerate(img_list):
        candidates = [j for j in range(len(img_list)) if j != i]
        j = random.choice(candidates)
        rows.append({"image_path": img, "caption": cap_list[j], "label": 0})  # MISMATCH

    random.shuffle(rows)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
        writer.writeheader()
        writer.writerows(rows)

    match    = sum(1 for r in rows if r["label"] == 1)
    mismatch = sum(1 for r in rows if r["label"] == 0)
    print(f"DONE: {len(rows)} samples (MATCH={match}, MISMATCH={mismatch})")
    print(f"Đã lưu → {output_csv}")


def build_from_coco(annotations_path: str, image_dir: str, output_csv: str, max_samples: int):
    """Tạo captions.csv từ file annotations COCO (nếu có)."""
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = lambda x, **kw: x  # noqa: E731

    os.makedirs(image_dir, exist_ok=True)

    with open(annotations_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    image_ids = list({ann["image_id"] for ann in coco["annotations"]})[:max_samples]
    captions = {}
    for ann in coco["annotations"]:
        if ann["image_id"] in image_ids:
            img = f"{ann['image_id']:012d}.jpg"
            captions.setdefault(img, []).append(ann["caption"])

    rows = []
    for img_name, caps in tqdm(captions.items(), desc="Xử lý ảnh"):
        img_path = os.path.join(image_dir, img_name)
        if not os.path.exists(img_path):
            try:
                import requests
                url = f"http://images.cocodataset.org/train2017/{img_name}"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(r.content)
            except Exception as e:
                print(f"Bỏ qua {img_name}: {e}")
                continue
        cap = random.choice(caps)
        rows.append({"image_path": img_name, "caption": cap, "label": 1})

    # Tạo MISMATCH
    img_list = [r["image_path"] for r in rows]
    cap_list  = [r["caption"]    for r in rows]
    for i, img in enumerate(img_list):
        candidates = [j for j in range(len(img_list)) if j != i]
        if candidates:
            j = random.choice(candidates)
            rows.append({"image_path": img, "caption": cap_list[j], "label": 0})

    random.shuffle(rows)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "caption", "label"])
        writer.writeheader()
        writer.writerows(rows)

    match    = sum(1 for r in rows if r["label"] == 1)
    mismatch = sum(1 for r in rows if r["label"] == 0)
    print(f"DONE: {len(rows)} samples (MATCH={match}, MISMATCH={mismatch})")
    print(f"Đã lưu → {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chuẩn bị dữ liệu Image-Text Mismatch")
    parser.add_argument("--annotations", default=None,
                        help="Đường dẫn tới file captions_train2017.json (COCO). "
                             "Nếu không cung cấp, dùng ảnh local.")
    parser.add_argument("--image-dir", default="data/images",
                        help="Thư mục chứa ảnh (mặc định: data/images)")
    parser.add_argument("--output", default="data/captions.csv",
                        help="File CSV đầu ra (mặc định: data/captions.csv)")
    parser.add_argument("--max-samples", type=int, default=2000,
                        help="Số lượng ảnh tối đa từ COCO (mặc định: 2000)")
    args = parser.parse_args()

    if args.annotations and os.path.exists(args.annotations):
        print(f"Dùng COCO annotations: {args.annotations}")
        build_from_coco(args.annotations, args.image_dir, args.output, args.max_samples)
    else:
        if args.annotations:
            print(f"Không tìm thấy {args.annotations}, dùng ảnh local thay thế.")
        print(f"Dùng ảnh local trong: {args.image_dir}")
        build_from_local_images(args.image_dir, args.output)