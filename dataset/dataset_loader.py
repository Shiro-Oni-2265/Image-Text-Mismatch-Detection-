"""
Mô tả file:
File này chứa mã nguồn để tạo cấu trúc nạp dữ liệu (Dataset Loader).

Cải tiến so với phiên bản gốc:
- Bỏ qua sample lỗi (ảnh không đọc được) thay vì dùng ảnh đen — tránh contaminate training
- Chuẩn hóa caption: strip, lowercase, bỏ khoảng trắng thừa
- Data augmentation tùy chọn: flip, color jitter, random crop
- collate_skip_none: loại None khỏi batch để DataLoader không bị crash
"""

import os
import re
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.config import Config


def normalize_caption(text: str) -> str:
    """Chuẩn hóa caption: bỏ khoảng trắng thừa, strip."""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def collate_skip_none(batch):
    """Custom collate function: loại bỏ các sample None trước khi stack."""
    batch = [b for b in batch if b is not None]
    if len(batch) == 0:
        return None
    return torch.utils.data.dataloader.default_collate(batch)


class ImageTextDataset(Dataset):
    """
    Dataset loader cho Image-Text Mismatch Detection.
    CSV cần có các cột: image_path, caption, label (0=mismatch, 1=match).
    """

    def __init__(self, data_file, image_dir, processor, max_length=77, augment=False):
        self.image_dir = image_dir
        self.processor = processor
        self.max_length = max_length
        self.augment = augment

        if os.path.exists(data_file):
            df = pd.read_csv(data_file)
            if not {'image_path', 'caption', 'label'}.issubset(set(df.columns)):
                df = pd.read_csv(data_file, header=None, names=['image_path', 'caption', 'label'])
            # Chuẩn hóa caption ngay lúc load
            df['caption'] = df['caption'].apply(normalize_caption)
            self.data = df.reset_index(drop=True)
        else:
            print(f"Warning: Data file {data_file} not found. Creating empty dataset.")
            self.data = pd.DataFrame(columns=['image_path', 'caption', 'label'])

    def __len__(self):
        return len(self.data)

    def _apply_augmentation(self, image: Image.Image) -> Image.Image:
        """Áp dụng augmentation ngẫu nhiên cho ảnh khi đang train (dùng PIL thuần)."""
        import random
        from PIL import ImageOps, ImageEnhance

        # Random horizontal flip
        if random.random() < 0.5:
            image = ImageOps.mirror(image)

        # Color jitter: brightness
        if random.random() < 0.5:
            factor = random.uniform(0.8, 1.2)
            image = ImageEnhance.Brightness(image).enhance(factor)

        # Color jitter: contrast
        if random.random() < 0.5:
            factor = random.uniform(0.8, 1.2)
            image = ImageEnhance.Contrast(image).enhance(factor)

        # Color jitter: saturation
        if random.random() < 0.5:
            factor = random.uniform(0.85, 1.15)
            image = ImageEnhance.Color(image).enhance(factor)

        # Random crop (scale 85-100%)
        if random.random() < 0.5:
            w, h = image.size
            scale = random.uniform(0.85, 1.0)
            new_w, new_h = int(w * scale), int(h * scale)
            left = random.randint(0, w - new_w)
            top = random.randint(0, h - new_h)
            image = image.crop((left, top, left + new_w, top + new_h)).resize((w, h), Image.BILINEAR)

        return image

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        img_name = str(row['image_path'])
        caption = str(row['caption'])
        label = row.get('label', 0)

        img_path = os.path.join(self.image_dir, img_name)
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            # Bỏ qua sample lỗi — collate_skip_none sẽ lọc None ra khỏi batch
            print(f"[SKIP] Không đọc được ảnh {img_path}: {e}")
            return None

        if self.augment:
            image = self._apply_augmentation(image)

        inputs = self.processor(
            text=[caption],
            images=image,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
        )

        return {
            'input_ids': inputs['input_ids'].squeeze(0),
            'attention_mask': inputs['attention_mask'].squeeze(0),
            'pixel_values': inputs['pixel_values'].squeeze(0),
            'label': torch.tensor(label, dtype=torch.float32),
        }
