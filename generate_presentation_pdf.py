# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Đăng ký font DejaVu (hỗ trợ tiếng Việt đầy đủ) ─────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))

def try_reg():
    fp = os.path.join(BASE, "DejaVuSans.ttf")
    fb = os.path.join(BASE, "DejaVuSans-Bold.ttf")
    try:
        pdfmetrics.registerFont(TTFont("DV",  fp))
        if os.path.exists(fb):
            pdfmetrics.registerFont(TTFont("DVB", fb))
        return True
    except Exception as e:
        print(f"[WARN] Không đăng ký được font: {e}")
        return False

HAS = try_reg()
FN  = "DV"  if HAS else "Helvetica"
FNB = "DVB" if HAS else "Helvetica-Bold"

# ── Màu sắc ──────────────────────────────────────────────────────────────────
BLUE    = colors.HexColor("#1a56db")
DKBLUE  = colors.HexColor("#1e3a8a")
LTBLUE  = colors.HexColor("#dbeafe")
DARK    = colors.HexColor("#111827")
GRAY    = colors.HexColor("#6b7280")
LGRAY   = colors.HexColor("#f9fafb")
BORDER  = colors.HexColor("#e5e7eb")
GREEN   = colors.HexColor("#065f46")
GBG     = colors.HexColor("#d1fae5")
RED     = colors.HexColor("#991b1b")
RBG     = colors.HexColor("#fee2e2")
YELBG   = colors.HexColor("#fef3c7")
YELTXT  = colors.HexColor("#92400e")
CODEBG  = colors.HexColor("#0f172a")
CODEFG  = colors.HexColor("#e2e8f0")
CMTFG   = colors.HexColor("#64748b")
ORANGE  = colors.HexColor("#c2410c")
PURPBG  = colors.HexColor("#ede9fe")
PURPTXT = colors.HexColor("#5b21b6")
IOBG    = colors.HexColor("#134e4a")

# ── Styles ────────────────────────────────────────────────────────────────────
def ps(name, **kw):
    kw.setdefault("fontName", FN)
    return ParagraphStyle(name, **kw)

S = {
    "cov_title": ps("ct",  fontSize=34, leading=42, textColor=BLUE,   fontName=FNB, alignment=TA_CENTER, spaceAfter=10),
    "cov_sub":   ps("cs",  fontSize=15, leading=23, textColor=DARK,   alignment=TA_CENTER, spaceAfter=6),
    "cov_meta":  ps("cm",  fontSize=10, leading=15, textColor=GRAY,   alignment=TA_CENTER, spaceAfter=3),
    "h1":  ps("h1",  fontSize=19, leading=26, textColor=BLUE,   fontName=FNB, spaceBefore=18, spaceAfter=8),
    "h2":  ps("h2",  fontSize=13, leading=19, textColor=DARK,   fontName=FNB, spaceBefore=13, spaceAfter=6),
    "h3":  ps("h3",  fontSize=11, leading=16, textColor=DKBLUE, fontName=FNB, spaceBefore=9,  spaceAfter=4),
    "body":ps("bd",  fontSize=10, leading=16, textColor=DARK,   alignment=TA_JUSTIFY, spaceAfter=5),
    "left":ps("bl",  fontSize=10, leading=16, textColor=DARK,   alignment=TA_LEFT,    spaceAfter=4),
    "bul": ps("bu",  fontSize=10, leading=15, textColor=DARK,   leftIndent=14, spaceAfter=3),
    "sub": ps("sb",  fontSize=9.5,leading=14, textColor=GRAY,   leftIndent=28, spaceAfter=2),
    "code":ps("co",  fontSize=8.2,leading=12.5, textColor=CODEFG, backColor=CODEBG,
              fontName="Courier", leftIndent=10, rightIndent=10, spaceBefore=0, spaceAfter=0, borderPad=6),
    "diag":ps("dg",  fontSize=8.5,leading=13,   textColor=CODEFG, backColor=colors.HexColor("#1e293b"),
              fontName="Courier", leftIndent=10, rightIndent=10, spaceBefore=0, spaceAfter=0, borderPad=10),
    "io":  ps("io",  fontSize=8.5,leading=13,   textColor=CODEFG, backColor=IOBG,
              fontName="Courier", leftIndent=10, rightIndent=10, spaceBefore=0, spaceAfter=0, borderPad=6),
    "note":ps("nt",  fontSize=10, leading=15, textColor=GREEN,   backColor=GBG,    leftIndent=10, spaceBefore=4, spaceAfter=4, borderPad=7),
    "warn":ps("wn",  fontSize=10, leading=15, textColor=RED,     backColor=RBG,    leftIndent=10, spaceBefore=4, spaceAfter=4, borderPad=7),
    "tip": ps("tp",  fontSize=10, leading=15, textColor=YELTXT,  backColor=YELBG,  leftIndent=10, spaceBefore=4, spaceAfter=4, borderPad=7),
    "purp":ps("pp",  fontSize=10, leading=15, textColor=PURPTXT, backColor=PURPBG, leftIndent=10, spaceBefore=4, spaceAfter=4, borderPad=7),
}

def p(t, s="body"):   return Paragraph(t, S[s])
def h1(t):  return p(f"<b>{t}</b>", "h1")
def h2(t):  return p(f"<b>{t}</b>", "h2")
def h3(t):  return p(f"<b>{t}</b>", "h3")
def sp(n=6):return Spacer(1, n)
def hr():   return HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=6, spaceBefore=4)
def hr2():  return HRFlowable(width="100%", thickness=1.8, color=BLUE,   spaceAfter=8, spaceBefore=4)
def note(t):return p(f"<b>✓</b>  {t}", "note")
def warn(t):return p(f"<b>⚠</b>  {t}", "warn")
def tip(t): return p(f"<b>▶</b>  {t}", "tip")
def purp(t):return p(f"<b>◆</b>  {t}", "purp")
def bul(t): return p(f"•  {t}", "bul")
def sub(t): return p(f"    ↳  {t}", "sub")

def code(text):
    out = []
    for line in text.split("\n"):
        s = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        out.append(Paragraph(s if s.strip() else "&nbsp;", S["code"]))
    return out

def diag(text):
    out = []
    for line in text.split("\n"):
        s = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        out.append(Paragraph(s if s.strip() else "&nbsp;", S["diag"]))
    return out

def io_block(text):
    out = []
    for line in text.split("\n"):
        s = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        out.append(Paragraph(s if s.strip() else "&nbsp;", S["io"]))
    return out

def tbl(data, widths, header=True):
    style = [
        ("FONTNAME",     (0,0),(-1,-1), FN),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
        ("LEADING",      (0,0),(-1,-1), 14),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("GRID",         (0,0),(-1,-1), 0.4, BORDER),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), 7),
        ("RIGHTPADDING", (0,0),(-1,-1), 7),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LGRAY]),
    ]
    if header:
        style += [
            ("BACKGROUND",  (0,0),(-1,0),  BLUE),
            ("TEXTCOLOR",   (0,0),(-1,0),  colors.white),
            ("FONTNAME",    (0,0),(-1,0),  FNB),
            ("FONTSIZE",    (0,0),(-1,0),  9.5),
        ]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(style))
    return t

def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(BLUE); canvas.setLineWidth(1.5)
    canvas.line(2*cm, h-1.4*cm, w-2*cm, h-1.4*cm)
    canvas.setFont(FNB, 8); canvas.setFillColor(BLUE)
    canvas.drawString(2*cm, h-1.25*cm, "Image-Text Mismatch Detection — Thuyết trình kỹ thuật")
    canvas.setFont(FN, 8); canvas.setFillColor(GRAY)
    canvas.drawRightString(w-2*cm, h-1.25*cm, f"Trang {doc.page}")
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.3*cm, w-2*cm, 1.3*cm)
    canvas.setFont(FN, 7.5); canvas.setFillColor(GRAY)
    canvas.drawCentredString(w/2, 0.85*cm, "ITMD — openai/clip-vit-base-patch32 + Custom Classifier Head")
    canvas.restoreState()

# ══════════════════════════════════════════════════════════════════════════════
def build():
    story = []

    # ── TRANG BÌA ─────────────────────────────────────────────────────────────
    story += [sp(55)]
    story.append(p("IMAGE-TEXT MISMATCH DETECTION", "cov_title"))
    story += [sp(8)]
    story.append(HRFlowable(width="70%", thickness=2, color=BLUE, hAlign="CENTER", spaceAfter=12))
    story.append(p("Thuyết trình kỹ thuật chi tiết — Toàn bộ luồng hoạt động", "cov_sub"))
    story += [sp(6)]
    story.append(p("Kiến trúc: CLIP ViT-B/32 + 4-way Embedding + Deep Classifier", "cov_meta"))
    story.append(p("Ngôn ngữ: Python 3.x  |  Framework: PyTorch + Transformers + Flask + React", "cov_meta"))
    story.append(p("Mục tiêu: Tự động phát hiện cặp ảnh–chú thích không khớp nhau", "cov_meta"))
    story += [sp(40)]
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, hAlign="CENTER"))
    story += [sp(6)]
    story.append(p("Nội dung gồm 12 chương — Từ chuẩn bị dữ liệu đến deploy API", "cov_meta"))
    story.append(PageBreak())

    # ── MỤC LỤC ──────────────────────────────────────────────────────────────
    story += [h1("MỤC LỤC"), hr2()]
    story.append(tbl([
        ["Chương", "Tiêu đề",                                        "Nội dung chính"],
        ["0",  "Kiến trúc tổng quan",                                "Sơ đồ toàn hệ thống, vai trò từng thành phần"],
        ["1",  "configs/config.py — Trung tâm cấu hình",            "Tham số, ngưỡng, device, hyperparameters"],
        ["2",  "data/prepare_data.py — Chuẩn bị dữ liệu",          "Tạo MATCH + MISMATCH, thuật toán derangement"],
        ["3",  "dataset/dataset_loader.py — Nạp dữ liệu",          "ImageTextDataset, augmentation, collate_skip_none"],
        ["4",  "models/clip_model.py — Kiến trúc model",            "CLIP backbone, 4-way embedding, classifier head"],
        ["5",  "training/train.py — Quá trình huấn luyện",         "Loss, optimizer, AMP, gradient clip, early stop"],
        ["6",  "utils/similarity.py — Tính toán tương đồng",       "Cosine similarity, batch mode, check_mismatch"],
        ["7",  "inference/predict.py — Suy luận",                   "Hai chế độ: cosine vs classifier, chọn ngưỡng"],
        ["8",  "app.py — Flask REST API",                            "Upload ảnh, UUID, validate, trả kết quả JSON"],
        ["9",  "utils/metrics.py — Đo lường chất lượng",           "Accuracy, Precision, Recall, F1, AUC-ROC"],
        ["10", "visualization/visualize.py — Biểu đồ",             "Confusion matrix, ROC curve, similarity dist"],
        ["11", "Luồng đầu cuối (End-to-End)",                       "Training flow + Inference flow + Bảng so sánh"],
    ], [1.3*cm, 6.7*cm, 8.3*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 0
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 0 — TỔNG QUAN HỆ THỐNG"), hr2()]
    story += [
        h2("0.1  Bài toán cần giải quyết"),
        p("Hệ thống trả lời câu hỏi: <b>Cặp (ảnh, chú thích) này có khớp nhau không?</b> "
          "Đây là bài toán phân loại nhị phân — kết quả chỉ là MATCH (khớp) hoặc MISMATCH (không khớp)."),
        sp(4),
        bul("<b>Ví dụ MATCH:</b>   Ảnh con chó chạy  +  Caption \"A dog running in the park\"  →  ✅ Khớp"),
        bul("<b>Ví dụ MISMATCH:</b>   Ảnh con chó chạy  +  Caption \"A red sports car\"  →  ❌ Không khớp"),
        sp(8),
        h2("0.2  Sơ đồ kiến trúc toàn bộ hệ thống"),
        sp(4),
    ]
    story += diag("""\
┌──────────────────────────────────────────────────────────────────────────────┐
│              KIEN TRUC IMAGE-TEXT MISMATCH DETECTION (ITMD)                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Anh JPG/PNG]  ──► Vision Encoder (ViT-B/32)                               │
│                      - Chia anh 224x224 thanh 49 patches (7x7)              │
│                      - Moi patch → vector 768D                               │
│                      - [CLS] token → Linear Projection → 512D               │
│                      → image_embeds: [B, 512]                               │
│                                                                              │
│  [Caption text] ──► Text Encoder (Transformer 12 layers)                    │
│                      - Tokenize → toi da 77 tokens                          │
│                      - Transformer → token [EOT] → Linear → 512D            │
│                      → text_embeds: [B, 512]                                │
│                                                                              │
│                ↓                                                             │
│   _combine() — Ket hop 4 chieu:                                              │
│   [img] + [txt] + [img - txt] + [img * txt] = [B, 2048]                     │
│    512D    512D      512D           512D                                     │
│                ↓                                                             │
│   Classifier Head:                                                           │
│   Linear(2048→256) → LayerNorm → GELU → Dropout(0.3)                        │
│   → Linear(256→128) → GELU → Dropout(0.2) → Linear(128→1)                  │
│                ↓                                                             │
│   logit → sigmoid → score [0.0 … 1.0]                                       │
│   score >= 0.2343 → MATCH  ✓                                                │
│   score <  0.2343 → MISMATCH  ✗                                             │
└──────────────────────────────────────────────────────────────────────────────┘""")

    story += [sp(8), h2("0.3  Vai trò từng file trong dự án"), sp(4)]
    story.append(tbl([
        ["File",                        "Vai trò"],
        ["configs/config.py",           "Trung tâm tham số — mọi file đều import từ đây"],
        ["data/prepare_data.py",        "Tạo cặp MATCH + MISMATCH từ ảnh local hoặc COCO dataset"],
        ["dataset/dataset_loader.py",   "Đọc CSV, mở ảnh, augmentation, đưa vào batch"],
        ["models/clip_model.py",        "CLIP backbone + 4-way embedding + classifier head"],
        ["training/train.py",           "Vòng lặp train, loss, optimizer, early stopping, tìm ngưỡng"],
        ["utils/similarity.py",         "Tính cosine similarity, hỗ trợ batch"],
        ["inference/predict.py",        "Suy luận 1 cặp ảnh–text, chọn chế độ tự động"],
        ["app.py",                      "Flask REST API, nhận upload, trả JSON"],
        ["utils/metrics.py",            "Accuracy, Precision, Recall, F1, AUC-ROC"],
        ["visualization/visualize.py",  "Vẽ confusion matrix, ROC curve, similarity distribution"],
        ["frontend/src/",               "React UI, gọi API, hiển thị kết quả cho người dùng"],
    ], [5.5*cm, 10.8*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 1: CONFIG
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 1 — configs/config.py (Trung tâm cấu hình)"), hr2()]
    story += [
        h2("1.1  Tại sao cần file config riêng?"),
        p("Thay vì \"cứng code\" (hardcode) tham số rải rác khắp nơi, tất cả tập trung vào "
          "1 file duy nhất. Khi muốn thay đổi BATCH_SIZE hay ngưỡng phân loại, "
          "chỉ sửa 1 chỗ, có hiệu lực toàn bộ dự án ngay lập tức."),
        note("Mọi file khác đều bắt đầu bằng: from configs.config import Config"),
        sp(6),
        h2("1.2  Toàn bộ nội dung configs/config.py — giải thích từng dòng"),
    ]
    story += code("""\
# configs/config.py
import os, torch

class Config:
    # ─── ĐƯỜNG DẪN DỰ ÁN ────────────────────────────────────────────────
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # os.path.abspath(__file__)  →  .../configs/config.py
    # dirname x2                →  thư mục gốc của dự án

    DATA_DIR   = os.path.join(ROOT_DIR, 'data')     # .../data/
    IMAGE_DIR  = os.path.join(DATA_DIR, 'images')   # .../data/images/
    OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')  # .../outputs/

    CAPTIONS_FILE = (
        os.path.join(DATA_DIR, 'captions.csv')   # ưu tiên file này
        if os.path.exists(os.path.join(DATA_DIR, 'captions.csv'))
        else os.path.join(DATA_DIR, 'caption.csv')  # fallback tên cũ
    )

    # ─── CHỌN MODEL ──────────────────────────────────────────────────────
    MODEL_NAME = "openai/clip-vit-base-patch32"
    # ViT-B/32: Vision Transformer Base, patch size 32×32 px
    # Ảnh 224×224 được chia thành (224/32)² = 49 patches
    # Embedding dimension: 512

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    # Tự động chọn GPU nếu có, ngược lại dùng CPU

    # ─── THAM SỐ SUY LUẬN ────────────────────────────────────────────────
    SIMILARITY_THRESHOLD = 0.25
    # Dùng khi CHƯA có file best_model.pth (chưa train)

    USE_CLASSIFIER_IN_INFERENCE = True
    # True: dùng classifier head sau khi đã train xong

    CLASSIFIER_THRESHOLD = 0.2343
    # Ngưỡng tối ưu được tính bằng Youden's J statistic
    # Lấy từ validation set sau khi train xong

    # ─── THAM SỐ HUẤN LUYỆN ─────────────────────────────────────────────
    BATCH_SIZE        = 16       # số mẫu xử lý 1 lần forward pass
    LEARNING_RATE     = 2e-4    # LR cho classifier head (mới, cần học nhanh)
    CLIP_FINETUNE_LR  = 5e-6   # LR cho CLIP layers (cũ, học chậm)
    NUM_EPOCHS        = 30      # tối đa 30 epoch

    NUM_UNFREEZE_LAYERS = 2
    # Mở băng 2 block transformer cuối của CLIP để fine-tune nhẹ
    # 0 = đóng băng toàn bộ (nhanh, kém linh hoạt)

    VAL_SPLIT = 0.1             # 10% dữ liệu dành cho validation
    SEED      = 42              # random seed để tái tạo kết quả

    EARLY_STOPPING_PATIENCE = 5
    # Nếu val_loss không tốt hơn sau 5 epoch liên tiếp → dừng

    ENABLE_BATCH_NEGATIVES = True
    NEGATIVE_RATIO         = 1.0
    # Tạo thêm 1 mẫu MISMATCH cho mỗi mẫu MATCH → gấp đôi batch

    USE_AMP = True
    # Mixed Precision: FP16 thay vì FP32, nhanh ~2× trên GPU""")

    story += [sp(6), h2("1.3  Bảng ảnh hưởng khi thay đổi tham số"), sp(4)]
    story.append(tbl([
        ["Tham số",             "Giá trị",  "Tăng → ảnh hưởng gì",                  "Giảm → ảnh hưởng gì"],
        ["BATCH_SIZE",          "16",       "Ổn định hơn, cần nhiều RAM",            "Gradient ồn nhiều hơn, nhanh hơn"],
        ["LEARNING_RATE",       "2e-4",     "Học nhanh, có thể diverge (phát tán)",  "Học chậm, ổn định hơn"],
        ["CLIP_FINETUNE_LR",    "5e-6",     "CLIP thay đổi nhiều — nguy hiểm",      "CLIP giữ nguyên — an toàn"],
        ["NUM_UNFREEZE_LAYERS", "2",        "Fine-tune sâu hơn, cần nhiều dữ liệu", "Phụ thuộc kiến thức CLIP gốc"],
        ["EARLY_STOP_PATIENCE", "5",        "Train lâu hơn, có thể overfit",         "Dừng sớm, có thể underfit"],
        ["NEGATIVE_RATIO",      "1.0",      "Thêm nhiều mẫu MISMATCH giả",          "Ít mẫu MISMATCH giả hơn"],
    ], [3.8*cm, 1.8*cm, 5*cm, 5.7*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 2: PREPARE DATA
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 2 — data/prepare_data.py (Chuẩn bị dữ liệu)"), hr2()]
    story += [
        h2("2.1  Vấn đề: Tại sao phải tạo MISMATCH?"),
        p("Trong thực tế, dữ liệu thu thập được thường chỉ có cặp (ảnh, chú thích đúng) "
          "— tức là chỉ có MATCH. Nhưng model cần học cả 2 loại. Script này tự động "
          "tạo ra các cặp MISMATCH bằng cách ghép ảnh với chú thích của <b>ảnh khác</b>."),
        warn("Nếu chỉ huấn luyện với MATCH, model sẽ luôn đoán MATCH và vẫn đạt accuracy cao — "
             "nhưng thực ra không học được gì cả."),
        sp(6),
        h2("2.2  Hàm build_from_local_images() — toàn bộ code + giải thích"),
    ]
    story += code("""\
# data/prepare_data.py

# Dictionary: tên ảnh → danh sách caption có thể dùng
PLACEHOLDER_CAPTIONS = {
    "blue_circle.jpg":  ["A blue circle", "A round blue shape", "Blue circular object"],
    "red_square.jpg":   ["A red square",  "Red square shape",   "Bright red colored square"],
    "green_rect.jpg":   ["A green rectangle", "Green rectangular shape"],
    # ... (định nghĩa cho 12 ảnh placeholder)
}

def build_from_local_images(image_dir: str, output_csv: str):

    # BƯỚC 1: Tìm tất cả ảnh trong thư mục
    images = [f for f in os.listdir(image_dir)
              if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    # os.listdir() → list tên file trong thư mục
    # .lower().endswith() → kiểm tra đuôi file (không phân biệt hoa/thường)

    rows = []

    # BƯỚC 2: Tạo MATCH samples
    for img in images:
        caps = PLACEHOLDER_CAPTIONS.get(img, [f"An image named {img}"])
        # .get(key, default) → nếu ảnh không có trong dict thì dùng caption mặc định
        cap = random.choice(caps)   # chọn 1 caption ngẫu nhiên từ list
        rows.append({
            "image_path": img,
            "caption":    cap,
            "label":      1     # 1 = MATCH ✅
        })

    # BƯỚC 3: Tạo MISMATCH samples (ghép ảnh với caption của ảnh KHÁC)
    img_list = [r["image_path"] for r in rows]
    cap_list = [r["caption"]    for r in rows]

    for i, img in enumerate(img_list):
        candidates = [j for j in range(len(img_list)) if j != i]
        # Loại chính nó (j != i) để đảm bảo không tự ghép với mình
        j = random.choice(candidates)
        rows.append({
            "image_path": img,
            "caption":    cap_list[j],  # caption của ảnh KHÁC
            "label":      0             # 0 = MISMATCH ❌
        })

    # BƯỚC 4: Trộn ngẫu nhiên để tránh model học theo thứ tự
    random.shuffle(rows)

    # BƯỚC 5: Lưu ra file CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path","caption","label"])
        writer.writeheader()
        writer.writerows(rows)""")

    story += [sp(6), h2("2.3  Ví dụ kết quả file captions.csv"), sp(4)]
    story += io_block("""\
image_path,caption,label
blue_circle.jpg,A blue circle,1        ← MATCH: ảnh xanh + caption "blue circle"
blue_circle.jpg,A red square,0         ← MISMATCH: ảnh xanh nhưng caption "red square"
red_square.jpg,A red square,1          ← MATCH
red_square.jpg,A dark image,0          ← MISMATCH
green_rect.jpg,A green rectangle,1     ← MATCH
green_rect.jpg,Blue circular object,0  ← MISMATCH
... (tiếp tục cho 12 ảnh)
→ Tổng: 24 dòng, 12 MATCH (label=1), 12 MISMATCH (label=0)""")

    story += [
        sp(6),
        note("Chạy với ảnh local: python data/prepare_data.py"),
        tip("Chạy với COCO dataset: python data/prepare_data.py "
            "--annotations data/annotations/captions_train2017.json --max-samples 2000"),
        sp(4),
        h2("2.4  Tại sao cần dữ liệu cân bằng 50/50?"),
        p("Nếu có 90% MATCH và 10% MISMATCH, model có thể đạt accuracy 90% chỉ bằng cách "
          "lúc nào cũng đoán MATCH — mà không hoc được gì. 50/50 buộc model "
          "phải học phân biệt thực sự."),
        warn("Nếu dữ liệu lệch, dùng pos_weight trong BCEWithLogitsLoss để bù trừ "
             "(được giải thích chi tiết ở Chương 5)."),
    ]
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 3: DATASET LOADER
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 3 — dataset/dataset_loader.py (Nạp dữ liệu)"), hr2()]
    story += [
        h2("3.1  Khái niệm Dataset trong PyTorch"),
        p("PyTorch yêu cầu bất kỳ dữ liệu nào phải kế thừa <b>torch.utils.data.Dataset</b> "
          "và cài đặt 2 method: __len__() (số mẫu) và __getitem__(idx) (lấy 1 mẫu theo chỉ số). "
          "DataLoader sau đó tự động gom các mẫu thành batch để huấn luyện."),
        sp(6),
        h2("3.2  normalize_caption() — Làm sạch chú thích"),
    ]
    story += code("""\
import re

def normalize_caption(text: str) -> str:
    text = str(text).strip()          # bỏ khoảng trắng đầu/cuối
    text = re.sub(r'\\s+', ' ', text)  # thay nhiều khoảng trắng bởi 1
    return text

# Ví dụ:
# "  A   dog   running  "  →  "A dog running"
# "\\nBlue\\t\\tcircle"     →  "Blue circle"
# Được gọi lúc load CSV: df['caption'] = df['caption'].apply(normalize_caption)""")

    story += [sp(6), h2("3.3  __init__() và __len__() — Khởi tạo Dataset")]
    story += code("""\
class ImageTextDataset(Dataset):

    def __init__(self, data_file, image_dir, processor, max_length=77, augment=False):
        self.image_dir  = image_dir   # thư mục chứa ảnh
        self.processor  = processor   # CLIP processor (xử lý ảnh + text)
        self.max_length = max_length  # tối đa 77 token (giới hạn của CLIP)
        self.augment    = augment     # True khi train, False khi val/test

        if os.path.exists(data_file):
            df = pd.read_csv(data_file)
            # Kiểm tra có đủ 3 cột cần thiết
            if not {'image_path','caption','label'}.issubset(set(df.columns)):
                df = pd.read_csv(data_file, header=None,
                                 names=['image_path','caption','label'])
            df['caption'] = df['caption'].apply(normalize_caption)
            self.data = df.reset_index(drop=True)
        else:
            self.data = pd.DataFrame(columns=['image_path','caption','label'])

    def __len__(self):
        return len(self.data)   # số dòng trong CSV""")

    story += [sp(6), h2("3.4  __getitem__() — Xử lý 1 mẫu dữ liệu")]
    story += code("""\
    def __getitem__(self, idx):
        row     = self.data.iloc[idx]      # lấy dòng thứ idx trong DataFrame
        img_name= str(row['image_path'])   # tên file ảnh, VD: "red_square.jpg"
        caption = str(row['caption'])      # chuỗi chú thích
        label   = row.get('label', 0)      # 0 hoặc 1

        img_path = os.path.join(self.image_dir, img_name)

        # Mở ảnh — xử lý lỗi thay vì dùng ảnh đen giả
        try:
            image = Image.open(img_path).convert("RGB")
            # .convert("RGB") đảm bảo ảnh luôn có 3 kênh màu
            # Xử lý được cả ảnh grayscale, RGBA, palette...
        except Exception as e:
            print(f"[SKIP] Không đọc được ảnh {img_path}: {e}")
            return None
            # Trả về None → collate_skip_none sẽ lọc ra khỏi batch

        # Data Augmentation (chỉ khi train)
        if self.augment:
            image = self._apply_augmentation(image)

        # CLIP Processor: xử lý đồng thời cả ảnh và text
        inputs = self.processor(
            text=[caption],          # list chứa 1 chuỗi
            images=image,            # PIL Image object
            return_tensors="pt",     # trả về PyTorch tensor
            padding="max_length",    # padding text về đúng 77 token
            truncation=True,         # cắt nếu dài hơn 77 token
            max_length=self.max_length,
        )

        return {
            'input_ids':      inputs['input_ids'].squeeze(0),
            # Shape: [77] — index của từng token trong vocabulary
            # VD: "A dog" → [49406, 320, 1929, 49407, 0, 0, ..., 0]

            'attention_mask': inputs['attention_mask'].squeeze(0),
            # Shape: [77] — 1 tại vị trí token thật, 0 tại padding
            # VD:           [    1,   1,    1,     1, 0, 0, ..., 0]

            'pixel_values':   inputs['pixel_values'].squeeze(0),
            # Shape: [3, 224, 224] — ảnh resize 224×224, 3 kênh RGB
            # Đã normalize: mean=[0.48, 0.46, 0.41], std=[0.27, 0.26, 0.28]

            'label': torch.tensor(label, dtype=torch.float32)
            # 0.0 = MISMATCH, 1.0 = MATCH
        }""")

    story += [sp(6), h2("3.5  _apply_augmentation() — Tăng cường dữ liệu")]
    story += code("""\
    def _apply_augmentation(self, image):
        aug = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            # 50% cơ hội lật ngang ảnh
            # Giúp model không phụ thuộc hướng ảnh

            transforms.ColorJitter(brightness=0.2, contrast=0.2,
                                   saturation=0.15, hue=0.05),
            # Thay đổi nhỏ độ sáng, tương phản, độ bão hòa
            # Giúp model học nội dung, không phụ thuộc màu sắc cụ thể

            transforms.RandomResizedCrop(
                size=(image.height, image.width),
                scale=(0.85, 1.0),   # cắt 85–100% diện tích ảnh
                ratio=(0.9,  1.1),   # tỷ lệ width/height ±10%
            ),
            # Giúp model nhận dạng đối tượng ở các vị trí khác nhau
        ])
        return aug(image)""")

    story += [sp(6), h2("3.6  collate_skip_none() — Xử lý ảnh lỗi trong batch")]
    story += code("""\
def collate_skip_none(batch):
    # batch là list các mẫu trả về bởi __getitem__
    # Có thể chứa None nếu ảnh bị lỗi khi đọc
    batch = [b for b in batch if b is not None]
    if len(batch) == 0:
        return None    # toàn batch lỗi → bỏ qua
    return torch.utils.data.dataloader.default_collate(batch)
    # default_collate: stack các tensor lại thành batch
    # VD: 16 tensor shape [77] → 1 tensor shape [16, 77]

# Sử dụng trong DataLoader:
dataloader = DataLoader(
    dataset,
    batch_size=16,
    shuffle=True,
    collate_fn=collate_skip_none   # thay thế hàm mặc định
)

# Trong vòng lặp train, kiểm tra None:
for batch in dataloader:
    if batch is None:
        continue    # bỏ qua batch rỗng""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 4: MODEL
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 4 — models/clip_model.py (Kiến trúc Model)"), hr2()]
    story += [
        h2("4.1  CLIP là gì? Tại sao dùng CLIP?"),
        p("CLIP (Contrastive Language-Image Pretraining) là mô hình của OpenAI được huấn luyện "
          "trên 400 triệu cặp (ảnh, chú thích) từ internet. Nó học cách ánh xạ cả ảnh "
          "lẫn text vào cùng một không gian vector 512 chiều, sao cho cặp khớp nhau "
          "→ vector gần nhau, cặp không khớp → vector xa nhau."),
        sp(4),
    ]
    story += diag("""\
Quá trình CLIP được huấn luyện (400 triệu cặp ảnh–text):

         Ảnh 1         Ảnh 2         Ảnh 3
           ↓             ↓             ↓
   [Vision Enc]   [Vision Enc]  [Vision Enc]
       v1             v2            v3          Ma trận similarity 3×3:
                                               CLIP học: (v1,t1)=MAX, (v1,t2)=min
   [Text Enc]    [Text Enc]    [Text Enc]               (v2,t2)=MAX, (v2,t1)=min
       t1             t2            t3                   (v3,t3)=MAX, ...

Sau khi train xong:
  "A blue circle"    → [0.12, -0.34, 0.87, ...]  (vector 512 chiều)
  Ảnh vòng tròn xanh → [0.11, -0.32, 0.89, ...]  (← RẤT GẦN nhau → MATCH)
  Ảnh hình vuông đỏ  → [-0.45, 0.67, -0.23, ...] (← RẤT XA  nhau → MISMATCH)""")

    story += [sp(8), h2("4.2  __init__() — Khởi tạo và đóng băng CLIP")]
    story += code("""\
class ITMDCLIPModel(nn.Module):

    def __init__(self, model_name=Config.MODEL_NAME, hidden_size=256):
        super().__init__()

        clip_base      = "openai/clip-vit-base-patch32"
        self.clip      = CLIPModel.from_pretrained(clip_base)
        self.processor = CLIPProcessor.from_pretrained(clip_base)
        self.embed_dim = self.clip.config.projection_dim   # = 512

        # BƯỚC 1: Đóng băng TOÀN BỘ CLIP
        for param in self.clip.parameters():
            param.requires_grad = False
        # requires_grad=False: gradient sẽ không tính cho tham số này
        # → Tiết kiệm bộ nhớ, train nhanh hơn
        # → Không làm hỏng kiến thức CLIP đã có (400M cặp)

        # BƯỚC 2: Mở băng N block cuối (fine-tune nhẹ)
        n = getattr(Config, "NUM_UNFREEZE_LAYERS", 2)   # mặc định = 2
        if n > 0:
            # Mở băng Vision Encoder — n block cuối
            for layer in self.clip.vision_model.encoder.layers[-n:]:
                for param in layer.parameters():
                    param.requires_grad = True   # được phép cập nhật

            # Mở băng Text Encoder — n block cuối
            for layer in self.clip.text_model.encoder.layers[-n:]:
                for param in layer.parameters():
                    param.requires_grad = True

        # Kết quả: CLIP có 12 block, chỉ 2 block cuối được fine-tune nhẹ""")

    story += [sp(4), h2("4.3  Classifier Head — Mạng nơ-ron nhỏ để phân loại")]
    story += code("""\
        # Input: vector 2048 chiều (từ _combine)
        input_dim = self.embed_dim * 4    # 512 × 4 = 2048

        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_size),
            # Ma trận trọng số: 2048 × 256 = 524,288 tham số
            # Biến đổi: [B, 2048] → [B, 256]

            nn.LayerNorm(hidden_size),
            # Chuẩn hóa: trung bình=0, phương sai=1 trên chiều hidden
            # Giúp gradient ổn định, học nhanh hơn

            nn.GELU(),
            # Gaussian Error Linear Unit: mượt hơn ReLU
            # Không bị "chết" (dead neuron) như ReLU khi x < 0

            nn.Dropout(0.3),
            # Tắt ngẫu nhiên 30% neuron trong training
            # Ép model học nhiều đặc trưng, không phụ thuộc vài neuron

            nn.Linear(hidden_size, hidden_size // 2),
            # [B, 256] → [B, 128]

            nn.GELU(),

            nn.Dropout(0.2),
            # Tắt 20% (ít hơn vì đã học được nhiều ở trên)

            nn.Linear(hidden_size // 2, 1)
            # [B, 128] → [B, 1] — ra 1 logit duy nhất
            # Chưa qua sigmoid, sẽ tính trong BCEWithLogitsLoss
        )""")

    story += [sp(4), h2("4.4  _combine() — Kết hợp embedding 4 chiều (quan trọng nhất!)")]
    story += code("""\
    def _combine(self, image_embeds, text_embeds):
        # Normalize L2: đưa về độ dài = 1 (unit vector)
        img  = F.normalize(image_embeds, p=2, dim=-1)   # [B, 512]
        txt  = F.normalize(text_embeds,  p=2, dim=-1)   # [B, 512]

        diff = img - txt    # [B, 512] — độ khác biệt chiều-wise
        # Nếu khớp: img ≈ txt → diff ≈ 0 (vector gần zero)
        # Nếu mismatch: img ≠ txt → diff có giá trị lớn

        prod = img * txt    # [B, 512] — tích element-wise
        # Nếu khớp: cùng chiều → prod dương và lớn
        # Nếu mismatch: ngược chiều → prod âm hoặc nhỏ

        return torch.cat((img, txt, diff, prod), dim=1)
        # Nối tiếp 4 vector theo chiều feature: [B, 512×4] = [B, 2048]

    # Tại sao 4 chiều tốt hơn chỉ dùng cosine similarity?
    # Cosine → 1 con số duy nhất → mất hết thông tin chi tiết từng chiều
    # 4-way concat → 2048 số → classifier học được các quan hệ phức tạp
    # VD: "hai vật tròn" có thể MATCH dù khác màu
    #     (diff nhỏ ở chiều hình dạng, prod lớn ở chiều hình dạng)
    #     → Classifier học được điều này, cosine đơn thuần không làm được""")

    story += [sp(4), h2("4.5  forward() và extract_features()")]
    story += code("""\
    def forward(self, input_ids, attention_mask, pixel_values):
        # Dùng trong TRAINING — trả về logit chưa sigmoid
        image_embeds, text_embeds = self._get_embeddings(
            input_ids, attention_mask, pixel_values
        )
        combined = self._combine(image_embeds, text_embeds)  # [B, 2048]
        return self.classifier(combined)                      # [B, 1]

    def extract_features(self, input_ids, attention_mask, pixel_values):
        # Dùng trong INFERENCE FALLBACK (khi chưa có checkpoint)
        with torch.no_grad():
            image_embeds, text_embeds = self._get_embeddings(
                input_ids, attention_mask, pixel_values
            )
        return image_embeds, text_embeds
        # Sau đó dùng compute_similarity() để tính cosine""")
    story += [
        sp(4),
        note("Phân biệt: forward() dùng trong training, extract_features() dùng khi chưa có checkpoint."),
    ]
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 5: TRAINING
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 5 — training/train.py (Quá trình huấn luyện)"), hr2()]
    story += [h2("5.1  Tổng thể quá trình training"), sp(4)]
    story += diag("""\
train()
  │
  ├─► Khởi tạo model ITMDCLIPModel
  ├─► Load checkpoint (nếu có --resume)
  ├─► Tạo dataset + split train/val (90%/10%)
  ├─► Tính pos_weight để xử lý class imbalance
  ├─► Tạo optimizer AdamW (2 learning rate khác nhau)
  ├─► Tạo LR scheduler (Cosine Annealing)
  ├─► Tạo GradScaler (cho AMP mixed precision)
  │
  └─► Vòng lặp epoch (tối đa 30):
       │
       ├─► Training phase (model.train()):
       │    ├─► Đọc từng batch (16 mẫu) từ DataLoader
       │    ├─► _make_batch_negatives() → gấp đôi batch thành 32
       │    ├─► Forward pass (có AMP autocast)
       │    ├─► Tính loss (BCEWithLogitsLoss + pos_weight)
       │    ├─► Backward pass (scaler.scale)
       │    ├─► Gradient clipping (max_norm=1.0)
       │    └─► Cập nhật trọng số (scaler.step + scaler.update)
       │
       ├─► Validation phase (model.eval() + no_grad):
       │    └─► Tính val_loss, thu thập probs và labels
       │
       ├─► Lưu best_model.pth (nếu val_loss tốt hơn lần trước)
       ├─► LR scheduler.step() (giảm LR theo cosine)
       └─► Kiểm tra Early Stopping (patience=5)
  │
  └─► Tìm ngưỡng tối ưu (Youden's J trên validation set)
  └─► Vẽ biểu đồ: confusion matrix, ROC curve, similarity distribution""")

    story += [sp(6), h2("5.2  Loss Function — BCEWithLogitsLoss với pos_weight")]
    story += code("""\
# Tính pos_weight để xử lý mất cân bằng dữ liệu
labels_series = dataset.data['label']
pos = float((labels_series == 1).sum())   # số lượng MATCH
neg = float((labels_series == 0).sum())   # số lượng MISMATCH
pos_weight = torch.tensor([neg / pos])
# Ví dụ: 60 MISMATCH và 40 MATCH → pos_weight = 60/40 = 1.5
# Ý nghĩa: lỗi trên MATCH bị phạt nặng hơn 1.5× so với MISMATCH
# → Cân bằng ảnh hưởng của class ít hơn

criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
# BCEWithLogitsLoss = sigmoid + binary cross-entropy gộp lại
# Ổn định số hơn BCELoss riêng (tránh log(0))
# Công thức:
#   loss = -[w * y * log(σ(x)) + (1-y) * log(1-σ(x))]
#   với w = pos_weight khi y=1, w=1 khi y=0""")

    story += [sp(4), h2("5.3  Optimizer AdamW với 2 Learning Rate khác nhau")]
    story += code("""\
# Lấy danh sách tham số CLIP đã mở băng (requires_grad=True)
clip_trainable = [p for p in model.clip.parameters() if p.requires_grad]

param_groups = [
    {
        'params': model.classifier.parameters(),
        'lr':     Config.LEARNING_RATE     # 2e-4 (lớp mới, cần học nhanh)
    },
    {
        'params': clip_trainable,
        'lr':     Config.CLIP_FINETUNE_LR  # 5e-6 (CLIP cũ, học rất chậm)
    },
]
optimizer = torch.optim.AdamW(param_groups, weight_decay=1e-4)
# AdamW = Adam + Weight Decay (L2 regularization)
# weight_decay=1e-4: phạt trọng số lớn → chống overfit
# Adam: tự động điều chỉnh LR riêng cho từng tham số theo lịch sử gradient

# Tại sao cần 2 LR khác nhau?
# Classifier học từ đầu → cần LR lớn để hội tụ nhanh
# CLIP đã có kiến thức sẵn → LR nhỏ để tinh chỉnh nhẹ nhàng, không phá vỡ""")

    story += [sp(4), h2("5.4  Hard Negatives — _make_batch_negatives()")]
    story += code("""\
def _make_batch_negatives(input_ids, attention_mask, pixel_values, labels,
                           negative_ratio=1.0):
    # Mục tiêu: từ batch 16 mẫu MATCH, tạo thêm 16 mẫu MISMATCH
    # Cách làm: giữ nguyên ảnh, XOAY VÒNG caption sang phải 1 bước

    bsz  = input_ids.size(0)   # batch size = 16
    k    = max(1, int(round(float(negative_ratio))))  # k = 1

    neg_inputs, neg_masks, neg_pixels, neg_labels = [], [], [], []
    for i in range(1, k+1):
        perm = torch.roll(torch.arange(bsz), shifts=i)
        # shifts=1: [0,1,2,...,15] → [15,0,1,...,14]
        # Caption của mẫu 15 chuyển sang vị trí 0,
        # Caption của mẫu 0  chuyển sang vị trí 1, ...

        neg_inputs.append(input_ids[perm])       # caption bị xoay
        neg_masks.append(attention_mask[perm])
        neg_pixels.append(pixel_values)           # ảnh GIỮ NGUYÊN
        neg_labels.append(torch.zeros_like(labels))  # label = 0 (MISMATCH)

    return (
        torch.cat([input_ids]  + neg_inputs, dim=0),   # [32, 77]
        torch.cat([attention_mask]+neg_masks, dim=0),
        torch.cat([pixel_values]+neg_pixels, dim=0),   # [32, 3,224,224]
        torch.cat([labels]     + neg_labels, dim=0),   # [32, 1]
    )

# Ví dụ cụ thể với batch_size=4:
#   Gốc:  [(ảnh1, cap1, 1), (ảnh2, cap2, 1), (ảnh3, cap3, 1), (ảnh4, cap4, 1)]
#   Thêm: [(ảnh1, cap4, 0), (ảnh2, cap1, 0), (ảnh3, cap2, 0), (ảnh4, cap3, 0)]
#   Kết quả: 8 mẫu, 4 MATCH + 4 MISMATCH""")

    story += [sp(4), h2("5.5  Vòng lặp training — AMP + Gradient Clipping")]
    story += code("""\
for epoch in range(Config.NUM_EPOCHS):
    model.train()   # bật chế độ train (Dropout hoạt động)

    for batch in progress_bar:
        if batch is None:   # bỏ qua batch rỗng (ảnh lỗi)
            continue

        input_ids      = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        pixel_values   = batch['pixel_values'].to(device)
        labels         = batch['label'].unsqueeze(1).to(device)
        # unsqueeze(1): [B] → [B,1] để khớp với output classifier [B,1]

        if Config.ENABLE_BATCH_NEGATIVES:
            input_ids, attention_mask, pixel_values, labels = \\
                _make_batch_negatives(input_ids, attention_mask,
                                     pixel_values, labels)

        optimizer.zero_grad()   # xóa gradient cũ

        with torch.cuda.amp.autocast():
            # AMP: tự động dùng FP16 cho các phép tính an toàn
            # Giữ FP32 cho các phép tính cần độ chính xác cao
            logits = model(input_ids, attention_mask, pixel_values)
            loss   = criterion(logits, labels)

        scaler.scale(loss).backward()
        # scale: nhân loss với hệ số lớn để tránh underflow FP16
        # backward: tính gradient của tất cả tham số

        scaler.unscale_(optimizer)
        # unscale: chia gradient cho hệ số (khôi phục độ chính xác)

        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        # Giới hạn độ dài vector gradient ≤ 1.0
        # Tránh gradient explosion → trọng số dao loạn

        scaler.step(optimizer)   # cập nhật trọng số
        scaler.update()          # điều chỉnh hệ số scale cho lần sau""")

    story += [sp(4), h2("5.6  Cosine Annealing + Early Stopping")]
    story += code("""\
# LR giảm theo đường cong cosine từ 2e-4 xuống 1e-7 trong 30 epoch
scheduler = CosineAnnealingLR(optimizer, T_max=30, eta_min=1e-7)
# Không giảm đột ngột (khác StepLR), tránh bỏ qua điểm tối ưu

# Early Stopping
best_val_loss     = float('inf')   # vô cùng lúc đầu
epochs_no_improve = 0

if val_loss < best_val_loss:
    best_val_loss     = val_loss
    epochs_no_improve = 0
    torch.save(model.state_dict(), "outputs/best_model.pth")
    # model.state_dict(): dict chứa tên_layer → tensor trọng số
else:
    epochs_no_improve += 1
    if epochs_no_improve >= Config.EARLY_STOPPING_PATIENCE:  # = 5
        print("Early stopping triggered!")
        break   # thoát vòng lặp epoch""")

    story += [sp(4), h2("5.7  Tìm ngưỡng tối ưu — Youden's J Statistic")]
    story += code("""\
def find_optimal_threshold(labels, probs):
    fpr, tpr, thresholds = roc_curve(labels, probs)
    # roc_curve trả về FPR, TPR tại mỗi ngưỡng từ 0 đến 1

    # Youden's J = TPR - FPR = Sensitivity + Specificity - 1
    # Đo cải thiện so với đoán ngẫu nhiên
    # TPR cao (bắt được MATCH) + FPR thấp (ít báo động giả) = J cao
    j_scores  = tpr - fpr
    best_idx  = j_scores.argmax()
    best_threshold = float(thresholds[best_idx])

    preds = [1 if p >= best_threshold else 0 for p in probs]
    best_f1 = f1_score(labels, preds, zero_division=0)

    print(f"Ngưỡng tối ưu: {best_threshold:.4f}  |  F1: {best_f1:.4f}")
    print(f"→ Cập nhật CLASSIFIER_THRESHOLD = {best_threshold:.4f}")
    return best_threshold, best_f1

# Ví dụ kết quả sau training:
# Epoch 28 → val_loss = 0.1823 (best)
# Ngưỡng tối ưu: 0.2343  |  F1: 0.8571
# → Copy 0.2343 vào configs/config.py""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 6: SIMILARITY
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 6 — utils/similarity.py (Tính toán độ tương đồng)"), hr2()]
    story += [
        h2("6.1  Cosine Similarity là gì?"),
        p("Cosine similarity đo góc giữa 2 vector — không quan tâm độ dài, chỉ quan tâm chiều. "
          "Kết quả từ -1 (ngược chiều hoàn toàn) đến +1 (cùng chiều hoàn toàn). "
          "Ta chuyển về [0, 1] để dễ hiểu: 1.0 = giống hoàn toàn, 0.0 = khác hoàn toàn."),
        sp(4),
    ]
    story += diag("""\
Ví dụ trực quan (2 chiều đơn giản để dễ hình dung):

                 y
                 |
  "A dog"  ──►  [0.8, 0.6]   (vector text)
                 |  ↗
                 | ↗  góc nhỏ ≈ 8° → cos ≈ 0.99 → MATCH ✅
                 |↗
                 └──────────────── x
                 ↑
  Ảnh con chó ──► [0.7, 0.7]   (vector ảnh)

  "A red car" ──► [-0.3, 0.9]  (vector text khác)
                  góc lớn ≈ 76° → cos ≈ 0.24 → MISMATCH ❌""")

    story += [sp(6), h2("6.2  compute_similarity() — Tính cho 1 cặp")]
    story += code("""\
def compute_similarity(image_embeds, text_embeds):
    # Normalize L2: chia cho độ dài (norm)
    img = F.normalize(image_embeds, p=2, dim=-1)
    txt = F.normalize(text_embeds,  p=2, dim=-1)
    # Sau normalize: ||img|| = ||txt|| = 1.0
    # → cosine_similarity = dot product (đơn giản hơn)

    sim = F.cosine_similarity(img, txt, dim=-1)
    # sim ∈ [-1, 1]

    return (sim + 1.0) / 2.0
    # Chuyển về [0, 1]:
    # -1 → 0.0 (hoàn toàn ngược chiều → MISMATCH chắc chắn)
    #  0 → 0.5 (vuông góc → không liên quan)
    # +1 → 1.0 (cùng chiều hoàn toàn → MATCH chắc chắn)

# Ví dụ số cụ thể:
# img_norm = [0.8/1.0, 0.6/1.0] = [0.8, 0.6]  (đã normalize)
# txt_norm = [0.7/1.0, 0.7/1.0] = [0.707, 0.707]
# cos = 0.8*0.707 + 0.6*0.707 = 0.566 + 0.424 = 0.99
# score = (0.99 + 1) / 2 = 0.995  → MATCH ✅""")

    story += [sp(4), h2("6.3  compute_batch_similarity() — Tính cho cả batch")]
    story += code("""\
def compute_batch_similarity(image_embeds, text_embeds):
    # image_embeds: [N, 512], text_embeds: [N, 512]
    img = F.normalize(image_embeds, p=2, dim=-1)
    txt = F.normalize(text_embeds,  p=2, dim=-1)

    # Tính đường chéo của ma trận similarity N×N
    # Chỉ lấy các cặp tương ứng (i, i)
    sim = (img * txt).sum(dim=-1)
    # img * txt: [N, 512] nhân element-wise
    # .sum(dim=-1): cộng theo chiều 512 → [N] (N điểm số)

    return (sim + 1.0) / 2.0   # [N] giá trị trong [0, 1]""")

    story += [sp(4), h2("6.4  check_mismatch() — Ra quyết định cuối cùng")]
    story += code("""\
def check_mismatch(similarity_score, threshold):
    return (similarity_score >= threshold).long()
    # >= threshold → True  → .long() → 1  (MATCH)
    # <  threshold → False → .long() → 0  (MISMATCH)

# Ví dụ:
# scores    = tensor([0.78, 0.12, 0.45, 0.91, 0.20])
# threshold = 0.25
# kết quả   = tensor([  1,    0,    1,    1,    0 ])
#             MATCH MISMATCH MATCH MATCH MISMATCH""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 7: INFERENCE
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 7 — inference/predict.py (Suy luận)"), hr2()]
    story += [
        h2("7.1  Hai chế độ suy luận"),
        p("Hệ thống tự động chọn chế độ phù hợp dựa vào có file checkpoint hay không:"),
        bul("<b>Chưa train</b> (không có best_model.pth): dùng cosine similarity thuần túy, ngưỡng 0.25"),
        bul("<b>Đã train</b> (có best_model.pth): dùng classifier head đã học, ngưỡng 0.2343"),
        sp(4),
    ]
    story += diag("""\
predict() được gọi
       │
       ├── Kiểm tra outputs/best_model.pth có tồn tại?
       │
       ├── KHÔNG CÓ ──────────────────────────────────────────────────────┐
       │   extract_features() → image_embeds, text_embeds                 │
       │   compute_similarity(img_emb, txt_emb) → score [0, 1]           │
       │   ngưỡng = SIMILARITY_THRESHOLD = 0.25                          │
       │                                                                   │
       └── CÓ ─────────────────────────────────────────────────────────── ┘
           model.forward() → logit                                         │
           sigmoid(logit) → score [0, 1]                                  │
           ngưỡng = CLASSIFIER_THRESHOLD = 0.2343                         │
                                                                           │
           score >= ngưỡng → "MATCH"   ◄──────────────────────────────── ┘
           score <  ngưỡng → "MISMATCH"
           return (score, prediction)""")

    story += [sp(6), h2("7.2  Toàn bộ hàm predict() — giải thích từng dòng")]
    story += code("""\
def predict(image_path, text, model=None, threshold=None, checkpoint_loaded=None):

    device = torch.device(Config.DEVICE)
    _checkpoint_loaded = checkpoint_loaded

    # Nếu không truyền model từ ngoài vào → tự tạo
    if model is None:
        model = ITMDCLIPModel(Config.MODEL_NAME).to(device)
        model.eval()   # tắt Dropout, BatchNorm dùng giá trị trung bình

        checkpoint_path = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
        _checkpoint_loaded = False
        if os.path.exists(checkpoint_path):
            try:
                model.load_state_dict(
                    torch.load(checkpoint_path, map_location=device)
                    # map_location: load trên CPU dù file được lưu trên GPU
                )
                _checkpoint_loaded = True
            except Exception as e:
                print(f"Load thất bại: {e}. Dùng cosine fallback.")

    processor = model.processor

    # Mở ảnh
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        return None, None   # trả về None nếu ảnh hỏng

    # Tiền xử lý (cùng processor với lúc train)
    inputs = processor(
        text=[text], images=image,
        return_tensors="pt", padding=True, truncation=True
    ).to(device)   # chuyển tensor lên GPU nếu có

    with torch.no_grad():
        # torch.no_grad(): không tính gradient → tiết kiệm ~50% memory
        use_classifier = (
            getattr(Config, "USE_CLASSIFIER_IN_INFERENCE", False)
            and _checkpoint_loaded
            # CHỈ dùng classifier khi ĐÃ LOAD THÀNH CÔNG checkpoint
        )

        if use_classifier:
            logit     = model(inputs['input_ids'],
                              inputs['attention_mask'],
                              inputs['pixel_values'])
            sim_score = torch.sigmoid(logit).item()
            # sigmoid: chuyển logit bất kỳ → xác suất [0,1]
            # .item(): lấy Python float từ 1-element tensor
        else:
            image_embeds, text_embeds = model.extract_features(
                inputs['input_ids'],
                inputs['attention_mask'],
                inputs['pixel_values']
            )
            sim_score = compute_similarity(image_embeds, text_embeds).item()

    # Chọn ngưỡng phù hợp với chế độ đang dùng
    if threshold is None:
        threshold = (
            getattr(Config, "CLASSIFIER_THRESHOLD", 0.5)
            if use_classifier else Config.SIMILARITY_THRESHOLD
        )

    prediction = "MATCH" if sim_score >= threshold else "MISMATCH"
    return sim_score, prediction""")

    story += [sp(4), h2("7.3  Ví dụ chạy tay từ command line"), sp(4)]
    story += io_block("""\
$ python inference/predict.py --image data/images/blue_circle.jpg --text "A blue circle"
Loaded checkpoint from outputs/best_model.pth
Similarity score: 0.8123
Prediction: MATCH  ✅

$ python inference/predict.py --image data/images/blue_circle.jpg --text "A red sports car"
Loaded checkpoint from outputs/best_model.pth
Similarity score: 0.0941
Prediction: MISMATCH  ❌""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 8: APP.PY
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 8 — app.py (Flask REST API Server)"), hr2()]
    story += [h2("8.1  Luồng request từ Frontend đến Backend"), sp(4)]
    story += diag("""\
BROWSER (React)                              SERVER (Flask - port 5000)
     │                                              │
     │  POST /api/predict                           │
     │  Content-Type: multipart/form-data           │
     │  Body:                                       │
     │    imageFile: [binary ảnh]                   │
     │    caption:   "A blue circle"                │
     │───────────────────────────────────────────►  │
     │                                              │
     │                               Kiểm tra file (allowed_file)
     │                               Lưu file UUID: a3f8c2d1...jpg
     │                               predict(filepath, caption, model)
     │                               Xóa file tạm (finally)
     │                                              │
     │  ◄─────────────────────────────────────────  │
     │  200 OK                                      │
     │  {                                           │
     │    "isMatch":          true,                 │
     │    "simScore":         0.8123,               │
     │    "suggestedCaption": ""                    │
     │  }                                           │""")

    story += [sp(6), h2("8.2  Khởi động server — Load model 1 lần duy nhất")]
    story += code("""\
# Phần này chạy 1 lần khi khởi động server, không chạy lại theo request
print("Loading model for API...")
device = torch.device(Config.DEVICE)
model  = ITMDCLIPModel(Config.MODEL_NAME).to(device)
model.eval()
# ⚠️ QUAN TRỌNG: Load model trước khi nhận request
# Nếu load trong mỗi request → mỗi request mất 5–10 giây!

checkpoint_path   = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
checkpoint_loaded = False
if os.path.exists(checkpoint_path):
    try:
        model.load_state_dict(
            torch.load(checkpoint_path, map_location=device)
        )
        checkpoint_loaded = True
        print(f"Loaded tuned checkpoint from {checkpoint_path}")
    except Exception as e:
        print(f"Failed: {e}. Dùng base CLIP.")

if not checkpoint_loaded:
    print("Không có checkpoint — dùng cosine similarity mode.")""")

    story += [sp(4), h2("8.3  Endpoint /api/predict — Xử lý từng request")]
    story += code("""\
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024   # giới hạn 16MB

def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
# rsplit('.', 1): cắt từ phải sang, tối đa 1 lần
# "photo.jpeg" → ["photo", "jpeg"] → "jpeg" → có trong set → True
# "malware.exe" → "exe" → không có → False → từ chối

@app.route('/api/predict', methods=['POST'])
def api_predict():
    # BƯỚC 1: Kiểm tra đầu vào
    if 'imageFile' not in request.files or 'caption' not in request.form:
        return jsonify({"error": "Thiếu imageFile hoặc caption"}), 400
    file    = request.files['imageFile']
    caption = request.form['caption'].strip()
    if file.filename == '' or not caption:
        return jsonify({"error": "File hoặc caption rỗng"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Định dạng file không hỗ trợ"}), 400

    # BƯỚC 2: Lưu file với tên UUID (thread-safe)
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    # uuid.uuid4(): tạo ID ngẫu nhiên 128-bit, không bao giờ trùng
    # VD: "a3f8c2d1-4b5e-6f7a-8b9c-0d1e2f3a4b5c.jpg"
    # → 2 user upload cùng lúc với tên file giống nhau vẫn an toàn

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # BƯỚC 3: Chạy inference (có AMP trên GPU)
        use_amp = device.type == "cuda"
        if use_amp:
            with torch.cuda.amp.autocast():
                sim_score, result = predict(
                    filepath, caption, model=model,
                    checkpoint_loaded=checkpoint_loaded)
        else:
            sim_score, result = predict(
                filepath, caption, model=model,
                checkpoint_loaded=checkpoint_loaded)

        # BƯỚC 4: Trả kết quả JSON
        return jsonify({
            "isMatch":          result == "MATCH",     # bool: True/False
            "simScore":         round(sim_score, 4),   # float: 0.8123
            "suggestedCaption": ""
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # BƯỚC 5: Xóa file tạm — LUÔN LUÔN chạy dù thành công hay lỗi
        if os.path.exists(filepath):
            try: os.remove(filepath)
            except: pass""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 9: METRICS
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 9 — utils/metrics.py (Đo lường chất lượng)"), hr2()]
    story += [
        h2("9.1  Các chỉ số đánh giá — Giải thích bằng số cụ thể"),
        p("Giả sử có 100 mẫu, model dự đoán và kết quả như sau:"),
        sp(4),
    ]
    story += diag("""\
Kết quả dự đoán (ví dụ):
   TP = 40  (đoán MATCH,    thực tế MATCH    → đúng)
   TN = 35  (đoán MISMATCH, thực tế MISMATCH → đúng)
   FP = 10  (đoán MATCH,    thực tế MISMATCH → sai: "báo động giả")
   FN = 15  (đoán MISMATCH, thực tế MATCH    → sai: "bỏ sót")

             Predicted MISMATCH  |  Predicted MATCH
  Actual                         |
  MISMATCH      TN = 35          |  FP = 10
  MATCH         FN = 15          |  TP = 40

Accuracy  = (TP+TN)/(TP+TN+FP+FN) = (40+35)/100 = 0.75  → 75% đúng tổng thể
Precision = TP/(TP+FP)             = 40/(40+10)  = 0.80  → 80% dự đoán MATCH là đúng
Recall    = TP/(TP+FN)             = 40/(40+15)  = 0.73  → Bắt được 73% MATCH thực sự
F1        = 2×P×R/(P+R)           = 2×0.80×0.73/1.53 = 0.76
AUC-ROC   = diện tích dưới đường ROC (1.0 = hoàn hảo, 0.5 = ngẫu nhiên)""")

    story += [sp(6), h2("9.2  Code calculate_metrics() — giải thích từng dòng")]
    story += code("""\
def calculate_metrics(y_true, y_pred, y_prob=None):
    metrics = {
        'accuracy':  accuracy_score(y_true, y_pred),
        # (TP + TN) / tổng số mẫu

        'precision': precision_score(y_true, y_pred, zero_division=0),
        # zero_division=0: nếu TP+FP=0 (không đoán MATCH nào) → trả 0, không lỗi

        'recall':    recall_score(y_true, y_pred, zero_division=0),
        # TP / (TP + FN)

        'f1_score':  f1_score(y_true, y_pred, zero_division=0),
        # Trung bình điều hòa Precision và Recall
        # Tốt khi cần cân bằng cả 2 chỉ số
    }

    if y_prob is not None:
        try:
            metrics['auc_roc'] = roc_auc_score(y_true, y_prob)
            # y_prob: xác suất [0,1], không phải label 0/1
            # Tính diện tích dưới ROC curve
        except ValueError:
            # Xảy ra khi chỉ có 1 class trong y_true (batch validation nhỏ)
            metrics['auc_roc'] = None
    return metrics""")

    story += [sp(4), h2("9.3  Khi nào nên xem chỉ số nào?"), sp(4)]
    story.append(tbl([
        ["Chỉ số",   "Dùng khi nào",                                    "Ví dụ thực tế"],
        ["Accuracy",  "Dataset cân bằng 50/50",                         "Kiểm tra tổng quát nhanh"],
        ["Precision", "Chi phí báo động giả cao",                       "Hệ thống kiểm duyệt nội dung"],
        ["Recall",    "Không được bỏ sót MATCH thực sự",                "Tìm kiếm ảnh trong kho lưu trữ"],
        ["F1 Score",  "Dataset lệch + cần cả Precision lẫn Recall",    "Phân loại văn bản y tế"],
        ["AUC-ROC",   "Muốn đánh giá độc lập với ngưỡng",              "So sánh 2 phiên bản model"],
    ], [2.5*cm, 5.8*cm, 7.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 10: VISUALIZATION
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 10 — visualization/visualize.py (Biểu đồ)"), hr2()]
    story += [h2("10.1  plot_confusion_matrix() — Ma trận nhầm lẫn")]
    story += code("""\
def plot_confusion_matrix(y_true, y_pred, save_path=None):
    cm = confusion_matrix(y_true, y_pred)
    # cm là ma trận 2×2:
    # [[TN, FP],
    #  [FN, TP]]

    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Mismatch (0)', 'Match (1)'],
                yticklabels=['Mismatch (0)', 'Match (1)'])
    # annot=True: hiện số trong ô
    # fmt='d': định dạng số nguyên
    # cmap='Blues': màu xanh đậm = nhiều mẫu hơn

    # Cách đọc biểu đồ:
    # Ô TN (trên trái):  MISMATCH đoán đúng → tốt ✅
    # Ô TP (dưới phải):  MATCH đoán đúng    → tốt ✅
    # Ô FP (trên phải):  MISMATCH nhưng đoán là MATCH → báo động giả ⚠️
    # Ô FN (dưới trái):  MATCH nhưng đoán là MISMATCH → bỏ sót ⚠️
    # → Ô TN và TP càng đậm, model càng tốt""")

    story += [sp(4), h2("10.2  plot_roc_curve() — Đường ROC")]
    story += code("""\
def plot_roc_curve(y_true, y_prob, save_path=None):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    # Khi thay đổi ngưỡng từ 0 đến 1:
    # Ngưỡng cao → ít đoán MATCH → FPR thấp, TPR thấp
    # Ngưỡng thấp → nhiều đoán MATCH → FPR cao, TPR cao

    roc_auc = auc(fpr, tpr)
    # 1.0 = model hoàn hảo (biết phân biệt 100%)
    # 0.5 = model đoán ngẫu nhiên (đường chéo)
    # < 0.5 = model sai hơn máy (kém hơn coin flip!)

    plt.plot(fpr, tpr, color='darkorange',
             label=f'ROC curve (AUC = {roc_auc:.4f})')
    plt.plot([0,1],[0,1], 'b--', label='Random (AUC=0.5)')
    # Đường cong càng gần góc trên trái → AUC càng cao → càng tốt""")

    story += [sp(4), h2("10.3  plot_similarity_distribution() — Phân bố điểm số")]
    story += code("""\
def plot_similarity_distribution(similarities, labels, save_path=None):
    match_scores    = [s for s,l in zip(similarities, labels) if l == 1]
    mismatch_scores = [s for s,l in zip(similarities, labels) if l == 0]

    # Vẽ KDE (Kernel Density Estimation) — đường mật độ xác suất
    sns.kdeplot(match_scores,    fill=True, color='green', label='Match')
    sns.kdeplot(mismatch_scores, fill=True, color='red',   label='Mismatch')

    # Vẽ đường trung bình của mỗi phân bố
    plt.axvline(mean(match_scores),    color='green', linestyle='--')
    plt.axvline(mean(mismatch_scores), color='red',   linestyle='--')

    # Cách đọc biểu đồ:
    # 2 đỉnh tách biệt xa nhau → model phân biệt tốt ✅
    # 2 đỉnh chồng lên nhau   → model khó phân biệt  ⚠️
    # Đỉnh MATCH nên ở bên phải (score cao)
    # Đỉnh MISMATCH nên ở bên trái (score thấp)""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHƯƠNG 11: END-TO-END
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("CHƯƠNG 11 — Luồng đầu cuối (End-to-End)"), hr2()]
    story += [h2("11.1  Luồng TRAINING (Từ dữ liệu thô đến model)"), sp(4)]
    story += diag("""\
[BƯỚC 1] data/prepare_data.py
  └─► Đọc ảnh trong data/images/
  └─► Tạo MATCH samples (ảnh + caption đúng, label=1)
  └─► Tạo MISMATCH samples (ảnh + caption ảnh khác, label=0)
  └─► Xuất ra data/captions.csv (50% MATCH, 50% MISMATCH)

[BƯỚC 2] training/train.py
  └─► Đọc captions.csv → ImageTextDataset
  └─► Split: 90% train / 10% validation
  └─► Khởi tạo ITMDCLIPModel:
       ├─► CLIP ViT-B/32 (12 block, đóng băng 10, mở 2 block cuối)
       └─► Classifier: Linear(2048→256→128→1)
  └─► Vòng lặp train (tối đa 30 epoch):
       ├─► Mỗi batch (16→32 mẫu sau hard negatives):
       │    ├─► Forward: CLIP encode → _combine 4 chiều → classifier → logit
       │    ├─► Loss: BCEWithLogitsLoss(pos_weight)
       │    ├─► Backward: AMP scaler + gradient clip max_norm=1.0
       │    └─► Update: AdamW (2 LR: 2e-4 classifier, 5e-6 CLIP)
       ├─► Sau mỗi epoch: validate, lưu best_model.pth, early stop
       └─► Sau train: tìm ngưỡng tối ưu bằng Youden's J
  └─► Xuất: outputs/best_model.pth + confusion_matrix.png + roc_curve.png

[BƯỚC 3] configs/config.py
  └─► Cập nhật CLASSIFIER_THRESHOLD = <ngưỡng_tối_ưu>""")

    story += [sp(8), h2("11.2  Luồng INFERENCE (Từ request đến kết quả)"), sp(4)]
    story += diag("""\
[KHỞI ĐỘNG SERVER] python app.py
  └─► Load ITMDCLIPModel lên GPU/CPU (1 lần duy nhất)
  └─► Load outputs/best_model.pth (nếu có)
  └─► Flask lắng nghe port 5000

[NHẬN REQUEST] POST /api/predict
  └─► Kiểm tra: có imageFile và caption không?
  └─► Kiểm tra: định dạng file hợp lệ? (jpg/png/webp...)
  └─► Lưu file: uuid.uuid4().jpg (thread-safe)
  └─► Gọi predict():
       ├─► Mở ảnh: Image.open().convert("RGB")
       ├─► CLIP Processor: resize 224×224, tokenize text (77 tokens)
       ├─► model.forward(): CLIP encode → _combine → classifier → logit
       ├─► sigmoid(logit) → score [0, 1]
       └─► score >= 0.2343 ? "MATCH" : "MISMATCH"
  └─► Xóa file tạm (finally block — luôn chạy)
  └─► Trả JSON: { "isMatch": true, "simScore": 0.78 }

[FRONTEND] React nhận JSON
  └─► Hiển thị: "MATCH (0.78)" hoặc "MISMATCH (0.12)"
  └─► Màu xanh = MATCH ✅,  Màu đỏ = MISMATCH ❌""")

    story += [sp(8), h2("11.3  So sánh 2 chế độ suy luận"), sp(4)]
    story.append(tbl([
        ["Tiêu chí",        "Cosine Similarity (chưa train)",              "Classifier Head (đã train)"],
        ["Điều kiện",       "Luôn hoạt động, không cần train",             "Cần file best_model.pth"],
        ["Cách tính score", "cosine(img_embed, txt_embed) → [0,1]",       "sigmoid(classifier(2048D)) → [0,1]"],
        ["Ngưỡng dùng",     "SIMILARITY_THRESHOLD = 0.25",                 "CLASSIFIER_THRESHOLD = 0.2343"],
        ["Độ chính xác",    "Trung bình (phụ thuộc CLIP gốc)",            "Cao hơn (đã học từ dữ liệu thực)"],
        ["Khi nào dùng",    "Demo nhanh, chưa có dữ liệu train",          "Production, sau khi train xong"],
    ], [3*cm, 6*cm, 7.3*cm]))

    story += [sp(10), h2("11.4  Thứ tự chạy toàn bộ dự án từ đầu"), sp(4)]
    story.append(tbl([
        ["Bước", "Lệnh chạy",                                    "Kết quả tạo ra"],
        ["1",  "pip install -r requirements.txt",                 "Cài đặt thư viện Python"],
        ["2",  "pip install multilingual-clip ftfy",              "Hỗ trợ tiếng Việt (M-CLIP)"],
        ["3",  "python data/prepare_data.py",                     "data/captions.csv"],
        ["4",  "python training/train.py",                        "outputs/best_model.pth + biểu đồ"],
        ["5",  "python evaluate.py --data data/captions.csv",     "Metrics và biểu đồ đánh giá"],
        ["6",  "python app.py",                                   "API server tại http://localhost:5000"],
        ["7",  "cd frontend && npm install && npm run dev",       "Giao diện tại http://localhost:5173"],
    ], [0.8*cm, 7.5*cm, 8*cm]))

    story += [
        sp(14),
        HRFlowable(width="100%", thickness=1.5, color=BLUE, spaceAfter=10),
        p("<b>Tài liệu được tạo bởi generate_presentation_pdf.py</b>  |  "
          "Dự án: Image-Text Mismatch Detection  |  "
          "Model: openai/clip-vit-base-patch32 + Custom Classifier Head", "left"),
    ]
    return story

# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    out_path = os.path.join(os.path.expanduser("~"), "Desktop", "ITMD_Presentation.pdf")
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2*cm,
        title="ITMD Presentation",
        author="Image-Text Mismatch Detection",
    )
    doc.build(build(), onFirstPage=lambda c,d: None, onLaterPages=on_page)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"PDF tạo thành công: {out_path}  ({size_kb} KB)")
