"""
Mô tả file:
File này định nghĩa mạng nơ-ron chính được dùng trong dự án.

Chức năng chính:
- Tải mô hình CLIP từ HuggingFace
- Đóng băng phần lớn CLIP, chỉ mở băng N block cuối để fine-tune nhẹ
- Kết hợp embedding ảnh và text theo 4 chiều (concat + diff + product)
- Thêm classifier head sâu hơn với LayerNorm và GELU
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPModel, CLIPProcessor
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.config import Config


class ITMDCLIPModel(nn.Module):
    """
    Model kết hợp CLIP (frozen một phần) + classifier head để phát hiện mismatch.

    Cải tiến:
    - Mở băng NUM_UNFREEZE_LAYERS block cuối của CLIP để fine-tune nhẹ
    - Kết hợp embedding theo 4 cách: [img, text, img-text, img*text] (2048 chiều)
    - Classifier head sâu hơn: Linear → LayerNorm → GELU → Dropout × 2
    """

    def __init__(self, model_name=Config.MODEL_NAME, hidden_size=256):
        super(ITMDCLIPModel, self).__init__()

        # Luôn dùng CLIP base (ViT-B/32) làm backbone
        clip_base = "openai/clip-vit-base-patch32"
        self.clip = CLIPModel.from_pretrained(clip_base)
        self.processor = CLIPProcessor.from_pretrained(clip_base)
        self.embed_dim = self.clip.config.projection_dim  # 512

        # ── Đóng băng toàn bộ CLIP trước ───────────────────────────────────
        for param in self.clip.parameters():
            param.requires_grad = False

        # ── Mở băng N block cuối của vision + text encoder ──────────────────
        n = getattr(Config, "NUM_UNFREEZE_LAYERS", 2)
        if n > 0:
            for layer in self.clip.vision_model.encoder.layers[-n:]:
                for param in layer.parameters():
                    param.requires_grad = True
            for layer in self.clip.text_model.encoder.layers[-n:]:
                for param in layer.parameters():
                    param.requires_grad = True

        # ── Classifier head ─────────────────────────────────────────────────
        # Input: [img, text, img-text, img*text] = 4 × embed_dim = 2048
        input_dim = self.embed_dim * 4
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, 1)
        )

    def _get_embeddings(self, input_ids, attention_mask, pixel_values):
        """
        Trích xuất image_embeds và text_embeds từ CLIP.
        Dùng full forward pass để tương thích với mọi phiên bản transformers.
        """
        outputs = self.clip(
            input_ids=input_ids,
            attention_mask=attention_mask,
            pixel_values=pixel_values,
        )
        # CLIPOutput luôn có image_embeds và text_embeds là tensor
        return outputs.image_embeds, outputs.text_embeds

    def _combine(self, image_embeds, text_embeds):
        """Kết hợp embedding theo 4 chiều để giữ thông tin mối quan hệ."""
        img = F.normalize(image_embeds, p=2, dim=-1)
        txt = F.normalize(text_embeds,  p=2, dim=-1)
        diff = img - txt
        prod = img * txt
        return torch.cat((img, txt, diff, prod), dim=1)

    def forward(self, input_ids, attention_mask, pixel_values):
        """Forward pass cho training — trả về logit."""
        image_embeds, text_embeds = self._get_embeddings(
            input_ids, attention_mask, pixel_values
        )
        combined = self._combine(image_embeds, text_embeds)
        return self.classifier(combined)

    def extract_features(self, input_ids, attention_mask, pixel_values):
        """Trích xuất embedding thuần — dùng cho cosine similarity inference."""
        with torch.no_grad():
            image_embeds, text_embeds = self._get_embeddings(
                input_ids, attention_mask, pixel_values
            )
        return image_embeds, text_embeds
