"""
Mô tả file:
File này chứa tất cả các cấu hình và tham số quan trọng cho dự án.

Chức năng chính:
- Định nghĩa đường dẫn tới các file dữ liệu, model, thư mục kết quả
- Thiết lập siêu tham số cho mô hình và quá trình huấn luyện
- Chứa các hàm tiện ích tạo thư mục tự động
"""

import os
import torch


class Config:
    # ── Đường dẫn dự án ──────────────────────────────────────────────────────
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT_DIR, 'data')
    IMAGE_DIR = os.path.join(DATA_DIR, 'images')
    CAPTIONS_FILE = (
        os.path.join(DATA_DIR, 'captions_vi_4000.csv')
        if os.path.exists(os.path.join(DATA_DIR, 'captions_vi_4000.csv'))
        else os.path.join(DATA_DIR, 'captions.csv')
    )
    OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')

    # ── Lựa chọn mô hình ─────────────────────────────────────────────────────
    # Ưu tiên M-CLIP (hỗ trợ tiếng Việt và 100+ ngôn ngữ).
    # Nếu chỉ dùng tiếng Anh, thay bằng "openai/clip-vit-large-patch14".
    # CLIP backbone. M-CLIP chưa tương thích với transformers 5.x.
    # Hiện tại dùng ViT-B/32. Nâng lên "openai/clip-vit-large-patch14" nếu cần độ chính xác cao hơn.
    MODEL_NAME = "openai/clip-vit-base-patch32"

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    # ── Tham số suy luận (Inference) ─────────────────────────────────────────
    # Ngưỡng cosine similarity (dùng khi KHÔNG có checkpoint đã train)
    SIMILARITY_THRESHOLD = 0.25
    # Dùng classifier head thay vì cosine similarity (chỉ có hiệu lực khi checkpoint tồn tại)
    USE_CLASSIFIER_IN_INFERENCE = True
    # Ngưỡng sigmoid của classifier head
    CLASSIFIER_THRESHOLD = 0.2268  # tối ưu từ validation set (Youden's J)

    # ── Tham số huấn luyện (Training) ────────────────────────────────────────
    BATCH_SIZE = 32
    # Learning rate nhỏ hơn để fine-tune tiếp từ checkpoint tốt (dataset ~70K)
    LEARNING_RATE = 2e-5
    # Learning rate rất nhỏ cho CLIP backbone (tránh catastrophic forgetting)
    CLIP_FINETUNE_LR = 5e-7
    NUM_EPOCHS = 15

    # Số transformer block cuối của CLIP sẽ được mở băng để fine-tune
    # 0 = đóng băng toàn bộ CLIP (nhanh nhưng kém linh hoạt)
    # 2 = mở 2 block cuối (khuyến nghị với dataset nhỏ ~500-2000 mẫu)
    NUM_UNFREEZE_LAYERS = 2

    # Train/Val split
    VAL_SPLIT = 0.1
    SEED = 42

    # Early stopping: dừng nếu val loss không cải thiện sau N epoch
    EARLY_STOPPING_PATIENCE = 5

    # Hard-negative pairing: tự tạo thêm mẫu MISMATCH từ mỗi batch
    ENABLE_BATCH_NEGATIVES = True
    NEGATIVE_RATIO = 1.0  # 1.0 => thêm 1 negative cho mỗi positive

    # Mixed precision training (nhanh hơn, tiết kiệm GPU memory)
    USE_AMP = True  # Tự động tắt nếu không có GPU

    @classmethod
    def setup_dirs(cls):
        os.makedirs(cls.IMAGE_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
