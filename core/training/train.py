"""
Mô tả file:
File này dùng để huấn luyện (train) mô hình AI phân loại xem ảnh và văn bản có khớp nhau không.

Cải tiến so với phiên bản gốc:
- Optimizer với learning rate riêng cho classifier và CLIP fine-tune
- Cosine Annealing LR Scheduler
- Early Stopping
- Gradient Clipping
- Mixed Precision Training (AMP)
- Tự động tìm ngưỡng tối ưu từ validation set
- Confusion matrix vẽ từ validation set (khách quan hơn)
- Vẽ similarity distribution từ validation set
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.config import Config
from models.clip_model import ITMDCLIPModel
from dataset.dataset_loader import ImageTextDataset, collate_skip_none
from utils.metrics import calculate_metrics, print_metrics
from visualization.visualize import plot_similarity_distribution, plot_confusion_matrix, plot_roc_curve


def _make_batch_negatives(input_ids, attention_mask, pixel_values, labels, negative_ratio=1.0):
    """
    Tạo hard negatives bằng cách xoay caption trong batch.
    Giữ nguyên ảnh, hoán vị text. Label của negative là 0.
    """
    if negative_ratio <= 0:
        return input_ids, attention_mask, pixel_values, labels

    bsz = input_ids.size(0)
    if bsz < 2:
        return input_ids, attention_mask, pixel_values, labels

    k = max(1, int(round(float(negative_ratio))))

    neg_inputs, neg_masks, neg_pixels, neg_labels = [], [], [], []
    for i in range(1, k + 1):
        perm = torch.roll(torch.arange(bsz, device=input_ids.device), shifts=i)
        neg_inputs.append(input_ids[perm])
        neg_masks.append(attention_mask[perm])
        neg_pixels.append(pixel_values)
        neg_labels.append(torch.zeros_like(labels))

    return (
        torch.cat([input_ids] + neg_inputs, dim=0),
        torch.cat([attention_mask] + neg_masks, dim=0),
        torch.cat([pixel_values] + neg_pixels, dim=0),
        torch.cat([labels] + neg_labels, dim=0),
    )


def find_optimal_threshold(labels, probs):
    """
    Tìm ngưỡng tối ưu dựa trên Youden's J statistic (TPR - FPR tối đa).
    Trả về ngưỡng tốt nhất và F1 tương ứng.
    """
    from sklearn.metrics import roc_curve, f1_score
    fpr, tpr, thresholds = roc_curve(labels, probs)
    j_scores = tpr - fpr
    best_idx = j_scores.argmax()
    best_threshold = float(thresholds[best_idx])

    preds_at_best = [1 if p >= best_threshold else 0 for p in probs]
    best_f1 = f1_score(labels, preds_at_best, zero_division=0)
    return best_threshold, best_f1


def train():
    device = torch.device(Config.DEVICE)
    use_amp = getattr(Config, "USE_AMP", True) and device.type == "cuda"
    print(f"Using device: {device} | AMP: {use_amp}")

    Config.setup_dirs()
    checkpoint_path = os.path.join(Config.OUTPUT_DIR, "best_model.pth")

    # ── Khởi tạo model ───────────────────────────────────────────────────────
    model = ITMDCLIPModel(model_name=Config.MODEL_NAME).to(device)
    processor = model.processor

    if '--resume' in sys.argv and os.path.exists(checkpoint_path):
        print(f"Nạp lại checkpoint từ {checkpoint_path} để học tiếp...")
        try:
            model.load_state_dict(torch.load(checkpoint_path, map_location=device))
            print("Đã nạp thành công, tiếp tục huấn luyện!")
        except Exception as e:
            print(f"\n[CẢNH BÁO] Không thể nạp checkpoint do kiến trúc mô hình không khớp (ví dụ: chuyển từ English CLIP sang Multilingual CLIP hoặc ngược lại).")
            print(f"Chi tiết lỗi: {e}")
            print("Chương trình sẽ tiến hành huấn luyện lại từ đầu!\n")

    # ── Dataset ──────────────────────────────────────────────────────────────
    print("Loading dataset...")
    dataset = ImageTextDataset(
        data_file=Config.CAPTIONS_FILE,
        image_dir=Config.IMAGE_DIR,
        processor=processor,
        augment=True,
    )

    if len(dataset) == 0:
        print(f"Dataset trống. Thêm dữ liệu vào '{Config.CAPTIONS_FILE}' để train.")
        return

    val_size = max(1, int(len(dataset) * Config.VAL_SPLIT)) if len(dataset) > 1 else 0
    train_size = len(dataset) - val_size
    if val_size > 0 and train_size > 0:
        gen = torch.Generator().manual_seed(Config.SEED)
        train_ds, val_ds = random_split(dataset, [train_size, val_size], generator=gen)
    else:
        train_ds, val_ds = dataset, None

    dataloader = DataLoader(
        train_ds, batch_size=Config.BATCH_SIZE, shuffle=True,
        collate_fn=collate_skip_none
    )
    val_loader = DataLoader(
        val_ds, batch_size=Config.BATCH_SIZE, shuffle=False,
        collate_fn=collate_skip_none
    ) if val_ds is not None else None

    # ── Loss function ─────────────────────────────────────────────────────────
    pos_weight = None
    try:
        labels_series = dataset.data['label'] if hasattr(dataset, "data") else None
        if labels_series is not None:
            pos = float((labels_series == 1).sum())
            neg = float((labels_series == 0).sum())
            if pos > 0 and neg > 0:
                pos_weight = torch.tensor([neg / pos], dtype=torch.float32, device=device)
    except Exception:
        pass

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # ── Optimizer: learning rate riêng cho classifier vs CLIP fine-tune ───────
    clip_finetune_lr = getattr(Config, "CLIP_FINETUNE_LR", 5e-6)
    
    backbone_trainable = []
    if hasattr(model, 'clip'):
        backbone_trainable.extend([p for p in model.clip.parameters() if p.requires_grad])
    if hasattr(model, 'text_model'):
        backbone_trainable.extend([p for p in model.text_model.parameters() if p.requires_grad])
    if hasattr(model, 'text_projection'):
        backbone_trainable.extend([p for p in model.text_projection.parameters() if p.requires_grad])

    param_groups = [
        {'params': model.classifier.parameters(), 'lr': Config.LEARNING_RATE},
    ]
    if backbone_trainable:
        param_groups.append({'params': backbone_trainable, 'lr': clip_finetune_lr})

    optimizer = torch.optim.AdamW(param_groups, weight_decay=1e-4)

    # ── LR Scheduler: Cosine Annealing ───────────────────────────────────────
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=Config.NUM_EPOCHS, eta_min=1e-7
    )

    # ── Mixed Precision Scaler ────────────────────────────────────────────────
    scaler = torch.cuda.amp.GradScaler() if use_amp else None

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_loss = float('inf')
    patience = getattr(Config, "EARLY_STOPPING_PATIENCE", 5)
    epochs_no_improve = 0

    print("Starting training...")
    for epoch in range(Config.NUM_EPOCHS):
        model.train()
        running_loss = 0.0
        all_preds, all_labels = [], []

        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{Config.NUM_EPOCHS} [train]")

        for batch in progress_bar:
            if batch is None:
                continue

            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            pixel_values = batch['pixel_values'].to(device)
            labels = batch['label'].unsqueeze(1).to(device)

            if getattr(Config, "ENABLE_BATCH_NEGATIVES", False):
                input_ids, attention_mask, pixel_values, labels = _make_batch_negatives(
                    input_ids, attention_mask, pixel_values, labels,
                    negative_ratio=getattr(Config, "NEGATIVE_RATIO", 1.0),
                )

            optimizer.zero_grad()

            if use_amp:
                with torch.cuda.amp.autocast():
                    logits = model(input_ids, attention_mask, pixel_values)
                    loss = criterion(logits, labels)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                logits = model(input_ids, attention_mask, pixel_values)
                loss = criterion(logits, labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

            running_loss += loss.item()
            preds = (torch.sigmoid(logits) >= 0.5).float()
            all_preds.extend(preds.cpu().numpy().flatten())
            all_labels.extend(labels.cpu().numpy().flatten())
            progress_bar.set_postfix({'loss': f"{loss.item():.4f}"})

        scheduler.step()

        epoch_loss = running_loss / max(1, len(dataloader))
        print(f"\nEpoch {epoch+1} Train Loss: {epoch_loss:.4f} | LR: {scheduler.get_last_lr()[0]:.2e}")
        print_metrics(calculate_metrics(all_labels, all_preds))

        # ── Validation ────────────────────────────────────────────────────────
        val_loss = None
        val_probs_list, val_labels_list, val_preds_list = [], [], []

        if val_loader is not None:
            model.eval()
            val_running_loss = 0.0
            with torch.no_grad():
                for vbatch in tqdm(val_loader, desc=f"Epoch {epoch+1}/{Config.NUM_EPOCHS} [val]"):
                    if vbatch is None:
                        continue
                    v_input_ids = vbatch['input_ids'].to(device)
                    v_attention_mask = vbatch['attention_mask'].to(device)
                    v_pixel_values = vbatch['pixel_values'].to(device)
                    v_labels = vbatch['label'].unsqueeze(1).to(device)

                    if getattr(Config, "ENABLE_BATCH_NEGATIVES", False):
                        v_input_ids, v_attention_mask, v_pixel_values, v_labels = _make_batch_negatives(
                            v_input_ids, v_attention_mask, v_pixel_values, v_labels,
                            negative_ratio=getattr(Config, "NEGATIVE_RATIO", 1.0),
                        )

                    if use_amp:
                        with torch.cuda.amp.autocast():
                            v_logits = model(v_input_ids, v_attention_mask, v_pixel_values)
                            v_loss = criterion(v_logits, v_labels)
                    else:
                        v_logits = model(v_input_ids, v_attention_mask, v_pixel_values)
                        v_loss = criterion(v_logits, v_labels)

                    val_running_loss += v_loss.item()
                    v_prob = torch.sigmoid(v_logits)
                    v_pred = (v_prob >= 0.5).float()
                    val_probs_list.extend(v_prob.cpu().numpy().flatten())
                    val_preds_list.extend(v_pred.cpu().numpy().flatten())
                    val_labels_list.extend(v_labels.cpu().numpy().flatten())

            val_loss = val_running_loss / max(1, len(val_loader))
            print(f"Epoch {epoch+1} Val Loss: {val_loss:.4f}")
            print_metrics(calculate_metrics(val_labels_list, val_preds_list, y_prob=val_probs_list))

        # ── Lưu model tốt nhất ────────────────────────────────────────────────
        score = val_loss if val_loss is not None else epoch_loss
        if score < best_val_loss:
            best_val_loss = score
            epochs_no_improve = 0
            torch.save(model.state_dict(), checkpoint_path)
            print(f"Saved best model → {checkpoint_path}")
        else:
            epochs_no_improve += 1
            print(f"Val loss không cải thiện ({epochs_no_improve}/{patience})")
            if epochs_no_improve >= patience:
                print("Early stopping triggered.")
                break

    # ── Tìm ngưỡng tối ưu từ validation set ──────────────────────────────────
    if val_probs_list and val_labels_list:
        opt_threshold, opt_f1 = find_optimal_threshold(val_labels_list, val_probs_list)
        print(f"\nNgưỡng tối ưu (Youden's J): {opt_threshold:.4f}  |  F1 tương ứng: {opt_f1:.4f}")
        print(f"→ Cập nhật CLASSIFIER_THRESHOLD = {opt_threshold:.4f} trong configs/config.py để dùng ngưỡng này.")

    # ── Vẽ biểu đồ từ validation set ─────────────────────────────────────────
    labels_for_plot = val_labels_list if val_labels_list else all_labels
    preds_for_plot = val_preds_list if val_preds_list else all_preds
    probs_for_plot = val_probs_list if val_probs_list else []

    cm_path = os.path.join(Config.OUTPUT_DIR, "confusion_matrix.png")
    plot_confusion_matrix(labels_for_plot, preds_for_plot, save_path=cm_path)

    if probs_for_plot:
        dist_path = os.path.join(Config.OUTPUT_DIR, "similarity_distribution.png")
        plot_similarity_distribution(probs_for_plot, labels_for_plot, save_path=dist_path)

        roc_path = os.path.join(Config.OUTPUT_DIR, "roc_curve.png")
        plot_roc_curve(labels_for_plot, probs_for_plot, save_path=roc_path)


if __name__ == "__main__":
    Config.setup_dirs()
    train()
