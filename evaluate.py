"""
Mô tả file:
Script đánh giá độ chính xác của model trên bất kỳ CSV dataset.

Chức năng chính:
- Load model (checkpoint nếu có, fallback cosine similarity)
- Chạy prediction trên toàn bộ dataset
- Tính Accuracy, Precision, Recall, F1, AUC-ROC
- Tự động tìm ngưỡng tối ưu
- Lưu kết quả chi tiết ra CSV và biểu đồ ra thư mục outputs/

Cách dùng:
    python evaluate.py --data data/captions.csv
    python evaluate.py --data data/test.csv --threshold 0.4
    python evaluate.py --data data/test.csv --output-dir outputs/eval_results
"""

import argparse
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import torch
import pandas as pd
from tqdm import tqdm
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from configs.config import Config
from models.clip_model import ITMDCLIPModel
from utils.similarity import compute_similarity
from utils.metrics import calculate_metrics, print_metrics
from visualization.visualize import plot_confusion_matrix, plot_similarity_distribution, plot_roc_curve
from dataset.dataset_loader import normalize_caption


def load_model(device):
    """Load model và checkpoint (nếu có). Trả về (model, checkpoint_loaded)."""
    model = ITMDCLIPModel(Config.MODEL_NAME).to(device)
    model.eval()

    checkpoint_path = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
    checkpoint_loaded = False
    if os.path.exists(checkpoint_path):
        try:
            model.load_state_dict(torch.load(checkpoint_path, map_location=device))
            checkpoint_loaded = True
            print(f"Loaded checkpoint: {checkpoint_path}")
        except Exception as e:
            print(f"[WARNING] Không load được checkpoint: {e}")
            print("→ Dùng cosine similarity thuần.")
    else:
        print("Không có checkpoint → dùng cosine similarity thuần.")

    return model, checkpoint_loaded


def predict_batch(model, processor, rows, device, checkpoint_loaded, threshold):
    """Chạy prediction cho một danh sách rows (dicts với image_path và caption)."""
    results = []
    use_classifier = getattr(Config, "USE_CLASSIFIER_IN_INFERENCE", False) and checkpoint_loaded

    for row in tqdm(rows, desc="Evaluating"):
        img_path = os.path.join(Config.IMAGE_DIR, str(row["image_path"]))
        caption  = normalize_caption(str(row["caption"]))
        true_label = int(row.get("label", -1))

        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"[SKIP] {img_path}: {e}")
            continue

        inputs = processor(
            text=[caption],
            images=image,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(device)

        with torch.no_grad():
            if use_classifier:
                logit = model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    pixel_values=inputs['pixel_values'],
                )
                prob = torch.sigmoid(logit).item()
            else:
                img_emb, txt_emb = model.extract_features(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    pixel_values=inputs['pixel_values'],
                )
                prob = compute_similarity(img_emb, txt_emb).item()

        pred = 1 if prob >= threshold else 0
        results.append({
            "image_path": row["image_path"],
            "caption": caption,
            "true_label": true_label,
            "predicted_label": pred,
            "score": round(prob, 4),
            "correct": int(pred == true_label) if true_label >= 0 else None,
        })

    return results


def find_optimal_threshold(labels, probs):
    from sklearn.metrics import roc_curve, f1_score
    fpr, tpr, thresholds = roc_curve(labels, probs)
    j = tpr - fpr
    idx = j.argmax()
    best_thr = float(thresholds[idx])
    preds = [1 if p >= best_thr else 0 for p in probs]
    best_f1 = f1_score(labels, preds, zero_division=0)
    return best_thr, best_f1


def main():
    parser = argparse.ArgumentParser(description="Đánh giá model ITMD trên dataset CSV")
    parser.add_argument("--data", required=True, type=str,
                        help="Đường dẫn file CSV (cột: image_path, caption, label)")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Ngưỡng phân loại (mặc định: lấy từ Config)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Thư mục lưu kết quả (mặc định: outputs/eval/)")
    parser.add_argument("--save-predictions", action="store_true",
                        help="Lưu kết quả dự đoán chi tiết ra CSV")
    args = parser.parse_args()

    # ── Kiểm tra file dữ liệu ──────────────────────────────────────────────────
    if not os.path.exists(args.data):
        print(f"[ERROR] Không tìm thấy file: {args.data}")
        sys.exit(1)

    df = pd.read_csv(args.data)
    if not {'image_path', 'caption'}.issubset(df.columns):
        print("[ERROR] CSV cần có cột: image_path, caption (và label để tính metrics)")
        sys.exit(1)

    has_labels = 'label' in df.columns
    rows = df.to_dict('records')
    print(f"Dataset: {len(rows)} samples | Labels: {'có' if has_labels else 'không có'}")

    # ── Load model ────────────────────────────────────────────────────────────
    Config.setup_dirs()
    device = torch.device(Config.DEVICE)
    print(f"Device: {device}")
    model, checkpoint_loaded = load_model(device)

    # ── Chọn ngưỡng ──────────────────────────────────────────────────────────
    use_classifier = getattr(Config, "USE_CLASSIFIER_IN_INFERENCE", False) and checkpoint_loaded
    if args.threshold is not None:
        threshold = args.threshold
    elif use_classifier:
        threshold = getattr(Config, "CLASSIFIER_THRESHOLD", 0.5)
    else:
        threshold = Config.SIMILARITY_THRESHOLD
    print(f"Ngưỡng phân loại: {threshold} ({'classifier' if use_classifier else 'cosine similarity'})")

    # ── Chạy đánh giá ────────────────────────────────────────────────────────
    results = predict_batch(model, model.processor, rows, device, checkpoint_loaded, threshold)

    if not results:
        print("[ERROR] Không có sample nào được xử lý.")
        sys.exit(1)

    # ── Tính metrics ──────────────────────────────────────────────────────────
    output_dir = args.output_dir or os.path.join(Config.OUTPUT_DIR, "eval")
    os.makedirs(output_dir, exist_ok=True)

    if has_labels:
        y_true  = [r["true_label"]      for r in results if r["correct"] is not None]
        y_pred  = [r["predicted_label"] for r in results if r["correct"] is not None]
        y_prob  = [r["score"]           for r in results if r["correct"] is not None]

        print("\n" + "=" * 40)
        print(f"  EVALUATION RESULTS  (n={len(y_true)})")
        print("=" * 40)
        metrics = calculate_metrics(y_true, y_pred, y_prob=y_prob)
        print_metrics(metrics)

        # Tìm ngưỡng tối ưu
        opt_thr, opt_f1 = find_optimal_threshold(y_true, y_prob)
        print(f"  Ngưỡng tối ưu (Youden's J): {opt_thr:.4f}  →  F1={opt_f1:.4f}")
        if abs(opt_thr - threshold) > 0.05:
            print(f"  → Gợi ý: đặt threshold={opt_thr:.4f} trong configs/config.py")

        # Vẽ biểu đồ
        plot_confusion_matrix(y_true, y_pred,
                              save_path=os.path.join(output_dir, "eval_confusion_matrix.png"))
        plot_similarity_distribution(y_prob, y_true,
                                     save_path=os.path.join(output_dir, "eval_sim_distribution.png"))
        plot_roc_curve(y_true, y_prob,
                       save_path=os.path.join(output_dir, "eval_roc_curve.png"))

        # Lưu metrics tóm tắt
        summary_path = os.path.join(output_dir, "eval_metrics.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"Dataset: {args.data}\n")
            f.write(f"Samples: {len(y_true)}\n")
            f.write(f"Threshold used: {threshold}\n")
            f.write(f"Optimal threshold: {opt_thr:.4f}\n\n")
            for k, v in metrics.items():
                f.write(f"{k}: {v:.4f}\n" if v is not None else f"{k}: N/A\n")
        print(f"\nMetrics đã lưu → {summary_path}")

    else:
        print("\nKhông có cột 'label' → chỉ in phân bố score.")
        scores = [r["score"] for r in results]
        print(f"  Score trung bình : {sum(scores)/len(scores):.4f}")
        print(f"  Score min / max  : {min(scores):.4f} / {max(scores):.4f}")
        n_match = sum(1 for s in scores if s >= threshold)
        print(f"  MATCH (≥{threshold})   : {n_match} / {len(scores)}")
        print(f"  MISMATCH (<{threshold}): {len(scores)-n_match} / {len(scores)}")

    # ── Lưu predictions chi tiết ──────────────────────────────────────────────
    if args.save_predictions or not has_labels:
        pred_path = os.path.join(output_dir, "predictions.csv")
        pd.DataFrame(results).to_csv(pred_path, index=False)
        print(f"Predictions đã lưu → {pred_path}")

    print(f"\nBiểu đồ đã lưu vào: {output_dir}/")


if __name__ == "__main__":
    main()
