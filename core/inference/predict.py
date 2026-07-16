"""
Mô tả file:
File này dùng để chạy dự đoán xem một bức ảnh và một đoạn văn bản (text) có khớp nhau không.

Chức năng chính:
- Tải ảnh và tải text của người dùng
- Dùng mô hình AI (CLIP) để trích xuất đặc trưng
- Chấm điểm tương đồng (similarity score) để ra quyết định
"""

import argparse
import sys
import os
import torch
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.config import Config
from models.clip_model import ITMDCLIPModel
from utils.similarity import compute_similarity


def predict(image_path, text, model=None, threshold=None, checkpoint_loaded=None):
    """
    Dự đoán độ khớp giữa ảnh và text.

    Args:
        image_path: Đường dẫn tới bức ảnh
        text: Câu chữ cần so sánh
        model: Mô hình (nếu None sẽ tự tạo mới)
        threshold: Ngưỡng phân loại (None = dùng từ Config)
        checkpoint_loaded: True/False cho biết checkpoint đã được load chưa.
                           None = tự kiểm tra khi tạo model mới.

    Returns:
        (sim_score, prediction): điểm số và "MATCH" / "MISMATCH"
    """
    device = torch.device(Config.DEVICE)

    _checkpoint_loaded = checkpoint_loaded  # track riêng khi tự load

    if model is None:
        model = ITMDCLIPModel(Config.MODEL_NAME).to(device)
        model.eval()

        checkpoint_path = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
        _checkpoint_loaded = False
        if os.path.exists(checkpoint_path):
            try:
                model.load_state_dict(torch.load(checkpoint_path, map_location=device))
                _checkpoint_loaded = True
                print(f"Loaded tuned checkpoint from {checkpoint_path}")
            except Exception as e:
                print(f"Failed to load checkpoint: {e}. Using base CLIP cosine similarity.")

    # Nếu caller đã biết trạng thái checkpoint thì dùng giá trị đó
    if _checkpoint_loaded is None:
        _checkpoint_loaded = False

    processor = model.processor

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None, None

    inputs = processor(
        text=[text],
        images=image,
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(device)

    with torch.no_grad():
        # Chỉ dùng classifier head khi checkpoint đã được load thành công
        use_classifier = getattr(Config, "USE_CLASSIFIER_IN_INFERENCE", False) and _checkpoint_loaded
        if use_classifier:
            logit = model(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                pixel_values=inputs['pixel_values']
            )
            sim_score = torch.sigmoid(logit).item()
        else:
            # Fallback: cosine similarity giữa CLIP embeddings
            image_embeds, text_embeds = model.extract_features(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                pixel_values=inputs['pixel_values']
            )
            sim_score = compute_similarity(image_embeds, text_embeds).item()

    # Chọn ngưỡng phù hợp với chế độ đang dùng
    if threshold is None:
        if use_classifier:
            threshold = getattr(Config, "CLASSIFIER_THRESHOLD", 0.5)
        else:
            threshold = Config.SIMILARITY_THRESHOLD

    prediction = "MATCH" if sim_score >= threshold else "MISMATCH"
    return sim_score, prediction


def main():
    parser = argparse.ArgumentParser(description="Image-Text Mismatch Detection Inference")
    parser.add_argument("--image", required=True, type=str, help="Path to the image file")
    parser.add_argument("--text", required=True, type=str, help="Caption text to compare")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Decision threshold (default: auto from Config)")

    args = parser.parse_args()

    sim_score, prediction = predict(args.image, args.text, threshold=args.threshold)

    if sim_score is not None:
        print(f"Similarity score: {sim_score:.4f}")
        print(f"Prediction: {prediction}")


if __name__ == "__main__":
    main()
