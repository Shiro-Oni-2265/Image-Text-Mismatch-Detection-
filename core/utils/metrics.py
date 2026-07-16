"""
Mô tả file:
File này dùng để tính toán các chỉ số đánh giá chất lượng của AI.

Cải tiến so với phiên bản gốc:
- Thêm AUC-ROC (đánh giá tổng thể không phụ thuộc ngưỡng)
- Thêm hỗ trợ tính metrics từ probability (y_prob) thay vì chỉ 0/1
"""

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)


def calculate_metrics(y_true, y_pred, y_prob=None):
    """
    Tính các chỉ số đánh giá phân loại nhị phân.

    Args:
        y_true: nhãn thực tế (list/array)
        y_pred: nhãn dự đoán 0/1 (list/array)
        y_prob: xác suất dự đoán [0,1] — dùng để tính AUC-ROC (tuỳ chọn)

    Returns:
        dict chứa accuracy, precision, recall, f1_score, và auc_roc (nếu có y_prob)
    """
    metrics = {
        'accuracy':  accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall':    recall_score(y_true, y_pred, zero_division=0),
        'f1_score':  f1_score(y_true, y_pred, zero_division=0),
    }

    if y_prob is not None:
        try:
            metrics['auc_roc'] = roc_auc_score(y_true, y_prob)
        except ValueError:
            # Xảy ra khi chỉ có 1 class trong y_true (dataset nhỏ)
            metrics['auc_roc'] = None

    return metrics


def print_metrics(metrics):
    """In bảng metrics ra màn hình."""
    print("-" * 32)
    print("   EVALUATION METRICS")
    print("-" * 32)
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1_score']:.4f}")
    if 'auc_roc' in metrics:
        auc = metrics['auc_roc']
        print(f"  AUC-ROC:   {auc:.4f}" if auc is not None else "  AUC-ROC:   N/A (chỉ 1 class)")
    print("-" * 32)
