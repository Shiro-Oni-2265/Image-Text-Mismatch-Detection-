"""
Mô tả file:
File này dùng để vẽ biểu đồ minh họa kết quả sau khi mô hình suy luận/luyện tập xong.

Cải tiến so với phiên bản gốc:
- Thêm vẽ AUC-ROC curve
- Thêm thông số thống kê (mean, median) lên similarity distribution plot
"""

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc
import os


def plot_similarity_distribution(similarities, labels, save_path=None):
    """Vẽ phân bố điểm số similarity theo nhãn."""
    plt.figure(figsize=(9, 6))

    match_scores    = [s for s, l in zip(similarities, labels) if l == 1]
    mismatch_scores = [s for s, l in zip(similarities, labels) if l == 0]

    if match_scores:
        sns.kdeplot(match_scores, fill=True, label=f'Match (n={len(match_scores)})',
                    color='green', alpha=0.5)
        plt.axvline(sum(match_scores)/len(match_scores), color='green',
                    linestyle='--', alpha=0.7, label=f'Match mean={sum(match_scores)/len(match_scores):.3f}')

    if mismatch_scores:
        sns.kdeplot(mismatch_scores, fill=True, label=f'Mismatch (n={len(mismatch_scores)})',
                    color='red', alpha=0.5)
        plt.axvline(sum(mismatch_scores)/len(mismatch_scores), color='red',
                    linestyle='--', alpha=0.7, label=f'Mismatch mean={sum(mismatch_scores)/len(mismatch_scores):.3f}')

    plt.title('Similarity Score Distribution (Validation Set)')
    plt.xlabel('Score')
    plt.ylabel('Density')
    plt.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved similarity distribution → {save_path}")
    plt.close()


def plot_confusion_matrix(y_true, y_pred, save_path=None):
    """Vẽ confusion matrix."""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Mismatch (0)', 'Match (1)'],
                yticklabels=['Mismatch (0)', 'Match (1)'])
    plt.title('Confusion Matrix (Validation Set)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved confusion matrix → {save_path}")
    plt.close()


def plot_roc_curve(y_true, y_prob, save_path=None):
    """Vẽ AUC-ROC curve."""
    try:
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_auc = auc(fpr, tpr)
    except ValueError:
        print("Không thể vẽ ROC curve: cần ít nhất 2 class trong y_true.")
        return

    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2,
             label=f'ROC curve (AUC = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=1, linestyle='--', label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve (Validation Set)')
    plt.legend(loc='lower right')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved ROC curve → {save_path}")
    plt.close()
