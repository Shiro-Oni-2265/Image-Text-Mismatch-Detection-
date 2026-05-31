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
from transformers import CLIPModel, AutoModel, AutoTokenizer, CLIPImageProcessor
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.config import Config


class MultilingualCLIPProcessor:
    """
    Wrapper class to replace CLIPProcessor.
    Tokenizes multilingual text using BertTokenizer and processes images using CLIPImageProcessor.
    """
    class BatchEncodingWrapper(dict):
        def to(self, device):
            for k, v in self.items():
                if isinstance(v, torch.Tensor):
                    self[k] = v.to(device)
            return self

    def __init__(self, tokenizer, image_processor):
        self.tokenizer = tokenizer
        self.image_processor = image_processor

    def __call__(self, text, images, return_tensors="pt", padding=True, truncation=True, max_length=None):
        text_inputs = self.tokenizer(
            text,
            return_tensors=return_tensors,
            padding=padding,
            truncation=truncation,
            max_length=max_length
        )
        image_inputs = self.image_processor(
            images,
            return_tensors=return_tensors
        )
        res = self.BatchEncodingWrapper()
        res['input_ids'] = text_inputs['input_ids']
        res['attention_mask'] = text_inputs['attention_mask']
        res['pixel_values'] = image_inputs['pixel_values']
        return res


class ITMDCLIPModel(nn.Module):
    """
    Model kết hợp CLIP (frozen một phần) + classifier head để phát hiện mismatch.
    Hỗ trợ động cả hai kiến trúc:
    1. Đa ngôn ngữ (Vietnamese): DistilBert + CLIP Vision
    2. Tiếng Anh (Original): CLIP Model gốc
    """

    def __init__(self, model_name=Config.MODEL_NAME, hidden_size=256):
        super(ITMDCLIPModel, self).__init__()

        self.is_multilingual = "multilingual" in model_name
        clip_base = "openai/clip-vit-base-patch32"

        if self.is_multilingual:
            # ── ARCHITECTURE A: Multilingual CLIP (for Vietnamese) ───────────
            # Image backbone (standard OpenAI CLIP ViT-B/32)
            self.clip = CLIPModel.from_pretrained(clip_base, use_safetensors=True)
            self.image_processor = CLIPImageProcessor.from_pretrained(clip_base)
            self.embed_dim = self.clip.config.projection_dim  # 512

            # Text backbone (sentence-transformers multilingual DistilBert)
            self.text_model = AutoModel.from_pretrained(model_name, use_safetensors=True)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Dense linear projection layer to project DistilBert's 768 dim to 512 dim
            self.text_projection = nn.Linear(768, 512, bias=False)
            
            # Load pre-trained projection weights from sentence-transformers repo
            try:
                dense_path = hf_hub_download(model_name, '2_Dense/model.safetensors')
                state_dict = load_file(dense_path, device='cpu')
                if 'linear.weight' in state_dict:
                    self.text_projection.weight.data.copy_(state_dict['linear.weight'])
                else:
                    self.text_projection.load_state_dict(state_dict)
                print(f"Successfully loaded multilingual text projection weights from Hugging Face.")
            except Exception as e:
                print(f"Warning: Could not load pre-trained text projection weights: {e}. It will be trained from scratch.")

            # Processor wrapper compatible with existing training and inference pipelines
            self.processor = MultilingualCLIPProcessor(self.tokenizer, self.image_processor)
        else:
            # ── ARCHITECTURE B: Original English CLIP ─────────────────────────
            from transformers import CLIPProcessor
            self.clip = CLIPModel.from_pretrained(clip_base, use_safetensors=True)
            self.processor = CLIPProcessor.from_pretrained(clip_base)
            self.embed_dim = self.clip.config.projection_dim  # 512

        # ── Đóng băng toàn bộ trước ──────────────────────────────────────────
        for param in self.clip.parameters():
            param.requires_grad = False
        if self.is_multilingual:
            for param in self.text_model.parameters():
                param.requires_grad = False
            for param in self.text_projection.parameters():
                param.requires_grad = False

        # ── Mở băng N block cuối của vision + text encoder ──────────────────
        n = getattr(Config, "NUM_UNFREEZE_LAYERS", 2)
        if n > 0:
            # 1. Unfreeze CLIP vision layers
            for layer in self.clip.vision_model.encoder.layers[-n:]:
                for param in layer.parameters():
                    param.requires_grad = True
            
            if self.is_multilingual:
                # 2. Unfreeze DistilBert transformer layers and projection
                for layer in self.text_model.transformer.layer[-n:]:
                    for param in layer.parameters():
                        param.requires_grad = True
                for param in self.text_projection.parameters():
                    param.requires_grad = True
            else:
                # 2. Unfreeze CLIP text layers
                for layer in self.clip.text_model.encoder.layers[-n:]:
                    for param in layer.parameters():
                        param.requires_grad = True

        # ── Classifier head ─────────────────────────────────────────────────
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
        """Trích xuất image_embeds và text_embeds."""
        if self.is_multilingual:
            # 1. Image embeddings (using standard CLIP Vision)
            vision_outputs = self.clip.vision_model(pixel_values=pixel_values)
            pooled_output = vision_outputs[1]  # pooled_output
            image_embeds = self.clip.visual_projection(pooled_output)

            # 2. Text embeddings (using DistilBert + Mean Pooling + Linear Projection)
            text_outputs = self.text_model(input_ids=input_ids, attention_mask=attention_mask)
            token_embeddings = text_outputs[0]
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            pooled_text = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            text_embeds = self.text_projection(pooled_text)
        else:
            # Standard OpenAI CLIP embeddings
            outputs = self.clip(
                input_ids=input_ids,
                attention_mask=attention_mask,
                pixel_values=pixel_values,
            )
            image_embeds, text_embeds = outputs.image_embeds, outputs.text_embeds

        return image_embeds, text_embeds

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
