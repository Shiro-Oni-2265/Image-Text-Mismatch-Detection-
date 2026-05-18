"""
Mô tả file:
File này chứa luồng chạy demo chính (main pipeline).

Chức năng chính:
- Kiểm tra môi trường (GPU, thư viện M-CLIP)
- Chạy thử dự đoán với ảnh và caption mẫu
- In hướng dẫn sử dụng đầy đủ
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from configs.config import Config
from inference.predict import predict


def check_environment():
    """Kiểm tra và in thông tin môi trường."""
    import torch
    print("=" * 55)
    print("   Image-Text Mismatch Detection (ITMD) — Demo")
    print("=" * 55)
    print(f"  PyTorch version : {torch.__version__}")
    print(f"  Device          : {Config.DEVICE}")
    if torch.cuda.is_available():
        print(f"  GPU             : {torch.cuda.get_device_name(0)}")
    else:
        print("  GPU             : không có (dùng CPU)")


    # Kiểm tra checkpoint
    ckpt = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
    if os.path.exists(ckpt):
        import torch
        size_mb = os.path.getsize(ckpt) / 1024 / 1024
        print(f"  Checkpoint      : {ckpt} ({size_mb:.1f} MB) ✓")
    else:
        print(f"  Checkpoint      : chưa có — sẽ dùng cosine similarity thuần")
    print()


def run_demo(image_path: str, text: str, label: str = None):
    """Chạy một lần dự đoán và in kết quả."""
    print(f"  Ảnh    : {image_path}")
    print(f"  Caption: {text}")
    if label:
        print(f"  Nhãn đúng: {label}")

    sim_score, prediction = predict(image_path, text)

    if sim_score is None:
        print("  [LỖI] Không thể đọc ảnh hoặc chạy model.")
        return

    icon = "✓" if prediction == "MATCH" else "✗"
    print(f"  Kết quả: {prediction} {icon}  (score={sim_score:.4f})")

    if label:
        correct = "✓ Đúng" if prediction == label else "✗ Sai"
        print(f"  Đánh giá: {correct}")
    print()


def run_pipeline():
    check_environment()
    Config.setup_dirs()

    # Tạo ảnh mẫu nếu chưa có
    sample_img = os.path.join(Config.IMAGE_DIR, "sample_red.jpg")
    if not os.path.exists(sample_img):
        from PIL import Image
        img = Image.new('RGB', (224, 224), color=(200, 50, 50))
        img.save(sample_img)

    sample_img2 = os.path.join(Config.IMAGE_DIR, "sample_blue.jpg")
    if not os.path.exists(sample_img2):
        from PIL import Image
        img2 = Image.new('RGB', (224, 224), color=(50, 100, 200))
        img2.save(sample_img2)

    print("─" * 55)
    print("  Thử nghiệm dự đoán:")
    print("─" * 55)

    # Test case 1: MATCH — ảnh đỏ + caption mô tả đúng màu đỏ
    run_demo(sample_img, "A red colored square image.", label="MATCH")

    # Test case 2: MISMATCH — ảnh đỏ + caption sai (xanh)
    run_demo(sample_img, "A blue ocean with waves.", label="MISMATCH")

    # Test case 3: MATCH — ảnh xanh + caption đúng
    run_demo(sample_img2, "A blue colored image.", label="MATCH")

    # Test case 4: MISMATCH — ảnh xanh + caption hoàn toàn không liên quan
    run_demo(sample_img2, "A dog running in the park.", label="MISMATCH")

    print("─" * 55)
    print("  Hướng dẫn sử dụng:")
    print("─" * 55)
    print()
    print("  1. Chuẩn bị dữ liệu:")
    print("     python data/prepare_data.py --from-csv data/captions.csv")
    print()
    print("  2. Huấn luyện model:")
    print("     python training/train.py")
    print("     python training/train.py --resume   # tiếp tục từ checkpoint")
    print()
    print("  3. Dự đoán một ảnh:")
    print("     python inference/predict.py --image path/to/img.jpg --text 'caption'")
    print()
    print("  4. Đánh giá trên tập dữ liệu:")
    print("     python evaluate.py --data data/captions.csv")
    print()
    print("  5. Khởi động API server:")
    print("     python app.py")
    print()
    print("  6. Cài M-CLIP để hỗ trợ tiếng Việt:")
    print("     pip install multilingual-clip ftfy")
    print()


if __name__ == "__main__":
    run_pipeline()
