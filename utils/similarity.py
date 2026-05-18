"""
Mô tả file:
File này chứa các hàm tính toán độ giống nhau toán học giữa ảnh và văn bản.

Chức năng chính:
- compute_similarity: tính cosine similarity cho một cặp (ảnh, text)
- compute_batch_similarity: tính cosine similarity cho cả batch, trả về tensor 1D
- check_mismatch: phán đoán MATCH/MISMATCH dựa trên ngưỡng
"""

import torch
import torch.nn.functional as F


def compute_similarity(image_embeds: torch.Tensor, text_embeds: torch.Tensor) -> torch.Tensor:
    """
    Tính cosine similarity giữa image embedding và text embedding.
    Ánh xạ kết quả từ [-1, 1] về [0, 1].

    Args:
        image_embeds: tensor shape (1, D) hoặc (D,)
        text_embeds:  tensor shape (1, D) hoặc (D,)

    Returns:
        sim_score: scalar tensor trong khoảng [0, 1]
    """
    img = F.normalize(image_embeds, p=2, dim=-1)
    txt = F.normalize(text_embeds,  p=2, dim=-1)
    sim = F.cosine_similarity(img, txt, dim=-1)
    return (sim + 1.0) / 2.0


def compute_batch_similarity(image_embeds: torch.Tensor, text_embeds: torch.Tensor) -> torch.Tensor:
    """
    Tính cosine similarity cho cả batch.

    Args:
        image_embeds: tensor shape (N, D)
        text_embeds:  tensor shape (N, D)

    Returns:
        sim_scores: tensor shape (N,) trong khoảng [0, 1]
    """
    img = F.normalize(image_embeds, p=2, dim=-1)
    txt = F.normalize(text_embeds,  p=2, dim=-1)
    # Tính diagonal của ma trận similarity N×N (chỉ lấy cặp tương ứng)
    sim = (img * txt).sum(dim=-1)
    return (sim + 1.0) / 2.0


def check_mismatch(similarity_score: torch.Tensor, threshold: float) -> torch.Tensor:
    """
    Phán đoán MATCH (1) hoặc MISMATCH (0) dựa vào ngưỡng.

    Args:
        similarity_score: tensor điểm số [0, 1]
        threshold: ngưỡng cắt

    Returns:
        Tensor long: 1 = MATCH, 0 = MISMATCH
    """
    return (similarity_score >= threshold).long()
