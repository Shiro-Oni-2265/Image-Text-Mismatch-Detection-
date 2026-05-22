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
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Font ──────────────────────────────────────────────────────────────────────
def try_register_font():
    font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
    font_bold = os.path.join(os.path.dirname(__file__), "DejaVuSans-Bold.ttf")
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))
        if os.path.exists(font_bold):
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_bold))
        return True
    except:
        return False

HAS_FONT = try_register_font()
FN  = "DejaVu"      if HAS_FONT else "Helvetica"
FNB = "DejaVu-Bold" if HAS_FONT else "Helvetica-Bold"

# ── Colors ────────────────────────────────────────────────────────────────────
BLUE   = colors.HexColor("#1a56db")
DARK   = colors.HexColor("#1e2937")
GRAY   = colors.HexColor("#6b7280")
LIGHT  = colors.HexColor("#f3f4f6")
BORDER = colors.HexColor("#d1d5db")
GREEN  = colors.HexColor("#065f46")
GREENBG= colors.HexColor("#d1fae5")
RED    = colors.HexColor("#991b1b")
REDBG  = colors.HexColor("#fee2e2")
YELBG  = colors.HexColor("#fef9c3")
CODEBG = colors.HexColor("#0f172a")
CODEFG = colors.HexColor("#e2e8f0")
ORANGE = colors.HexColor("#c2410c")
PURPLE = colors.HexColor("#6d28d9")

# ── Styles ────────────────────────────────────────────────────────────────────
def ps(name, **kw):
    kw.setdefault("fontName", FN)
    return ParagraphStyle(name, **kw)

S = {
    "cover_title": ps("ct", fontSize=34, leading=42, textColor=BLUE, fontName=FNB, alignment=TA_CENTER, spaceAfter=8),
    "cover_sub":   ps("cs", fontSize=15, leading=22, textColor=DARK, alignment=TA_CENTER, spaceAfter=5),
    "cover_meta":  ps("cm", fontSize=10, leading=16, textColor=GRAY, alignment=TA_CENTER, spaceAfter=3),
    "h1":  ps("h1", fontSize=18, leading=24, textColor=BLUE, fontName=FNB, spaceBefore=20, spaceAfter=8),
    "h2":  ps("h2", fontSize=13, leading=19, textColor=DARK, fontName=FNB, spaceBefore=14, spaceAfter=6),
    "h3":  ps("h3", fontSize=11, leading=16, textColor=BLUE, fontName=FNB, spaceBefore=10, spaceAfter=4),
    "h4":  ps("h4", fontSize=10, leading=15, textColor=ORANGE, fontName=FNB, spaceBefore=8, spaceAfter=3),
    "body":  ps("body", fontSize=10, leading=16, textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=5),
    "body_l":ps("bl",   fontSize=10, leading=16, textColor=DARK, alignment=TA_LEFT,    spaceAfter=4),
    "bullet":ps("bul",  fontSize=10, leading=15, textColor=DARK, leftIndent=16, spaceAfter=3),
    "sub":   ps("sub",  fontSize=9.5,leading=14, textColor=GRAY, leftIndent=32, spaceAfter=2),
    "code":  ps("code", fontSize=8,  leading=12, textColor=CODEFG, backColor=CODEBG,
                fontName="Courier", leftIndent=8, rightIndent=8, spaceBefore=5, spaceAfter=5, borderPad=8),
    "code_comment": ps("cc", fontSize=8, leading=12, textColor=colors.HexColor("#94a3b8"),
                backColor=CODEBG, fontName="Courier", leftIndent=8, rightIndent=8, spaceAfter=0, borderPad=0),
    "inline":ps("il",  fontSize=9,  leading=13, textColor=DARK, backColor=LIGHT,
                fontName="Courier", leftIndent=4, rightIndent=4, borderPad=3),
    "note":  ps("note",fontSize=9.5,leading=14, textColor=GREEN, backColor=GREENBG, leftIndent=10, spaceBefore=4,spaceAfter=4,borderPad=6),
    "warn":  ps("warn",fontSize=9.5,leading=14, textColor=RED,   backColor=REDBG,   leftIndent=10, spaceBefore=4,spaceAfter=4,borderPad=6),
    "tip":   ps("tip", fontSize=9.5,leading=14, textColor=colors.HexColor("#78350f"), backColor=YELBG,
                leftIndent=10, spaceBefore=4, spaceAfter=4, borderPad=6),
    "diagram":ps("dg", fontSize=8.5, leading=13, textColor=CODEFG, backColor=colors.HexColor("#1e293b"),
                fontName="Courier", leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4, borderPad=10),
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def p(text, s="body"):  return Paragraph(text, S[s])
def h1(t):   return p(f"&#9632;  {t}", "h1")
def h2(t):   return p(t, "h2")
def h3(t):   return p(f"&#9670; {t}", "h3")
def h4(t):   return p(t, "h4")
def sp(n=6): return Spacer(1, n)
def hr():    return HRFlowable(width="100%", thickness=0.6, color=BORDER, spaceAfter=5)
def note(t): return p(f"&#10003;  {t}", "note")
def warn(t): return p(f"&#9888;  {t}", "warn")
def tip(t):  return p(f"&#9654;  {t}", "tip")

def bul(t):  return p(f"&#8226;  {t}", "bullet")
def sub(t):  return p(f"&#8627;  {t}", "sub")

def code_block(lines):
    """Nhận list các tuple (text, loại) hoặc string thuần."""
    result = []
    if isinstance(lines, str):
        lines = lines.split("\n")
    for line in lines:
        safe = str(line).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        result.append(Paragraph(safe if safe.strip() else "&nbsp;", S["code"]))
    return result

def code(text):
    lines = text.split("\n")
    items = []
    for line in lines:
        safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        items.append(Paragraph(safe if safe.strip() else "&nbsp;", S["code"]))
    return items

def diagram(text):
    lines = text.split("\n")
    items = []
    for line in lines:
        safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        items.append(Paragraph(safe if safe.strip() else "&nbsp;", S["diagram"]))
    return items

def tbl(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle([
        ("FONTNAME",    (0,0),(-1,-1), FN),
        ("FONTSIZE",    (0,0),(-1,-1), 9),
        ("LEADING",     (0,0),(-1,-1), 13),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
        ("GRID",        (0,0),(-1,-1), 0.4, BORDER),
        ("BACKGROUND",  (0,0),(-1,0),  BLUE),
        ("TEXTCOLOR",   (0,0),(-1,0),  colors.white),
        ("FONTNAME",    (0,0),(-1,0),  FNB),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT]),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING", (0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
    ]))
    return t

def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(BLUE); canvas.setLineWidth(1.5)
    canvas.line(2*cm, h-1.5*cm, w-2*cm, h-1.5*cm)
    canvas.setFont(FNB, 8); canvas.setFillColor(BLUE)
    canvas.drawString(2*cm, h-1.2*cm, "ITMD — Giải thích chi tiết kèm code")
    canvas.setFont(FN, 8);  canvas.setFillColor(GRAY)
    canvas.drawRightString(w-2*cm, h-1.2*cm, "Image-Text Mismatch Detection")
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.5*cm, w-2*cm, 1.5*cm)
    canvas.setFont(FN, 8); canvas.setFillColor(GRAY)
    canvas.drawString(2*cm, 1.1*cm, "Tài liệu kỹ thuật — Phiên bản 1.0")
    canvas.drawRightString(w-2*cm, 1.1*cm, f"Trang {doc.page}")
    canvas.restoreState()

# ══════════════════════════════════════════════════════════════════════════════
def build():
    story = []

    # ── TRANG BÌA ─────────────────────────────────────────────────────────────
    story += [
        sp(3*cm),
        p("ITMD", "cover_title"),
        p("Giải thích chi tiết cách hoạt động kèm code", "cover_sub"),
        sp(6),
        HRFlowable(width="55%", thickness=2, color=BLUE, hAlign="CENTER", spaceAfter=14),
        p("Image-Text Mismatch Detection", "cover_sub"),
        sp(10),
        p("Python 3.14 · PyTorch 2.11 · CLIP · M-CLIP · Flask 3 · React 19", "cover_meta"),
        p("Đọc từng dòng code và hiểu chính xác hệ thống làm gì", "cover_meta"),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 1: Ý TƯỞNG CỐT LÕI
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 1 — Ý tưởng cốt lõi"), hr()]
    story += [
        h2("1.1 Bài toán cần giải quyết"),
        p("Câu hỏi trung tâm: <b>\"Bức ảnh này và câu mô tả có cùng nói về một thứ không?\"</b>"),
        p("Ví dụ:"),
        bul("Ảnh <b>con chó</b> + caption <b>\"A cute dog playing\"</b> → <b>MATCH ✓</b>"),
        bul("Ảnh <b>con chó</b> + caption <b>\"A red sports car\"</b> → <b>MISMATCH ✗</b>"),
        sp(6),

        h2("1.2 Kỹ thuật Embedding — Dịch ảnh và chữ thành số"),
        p("Cả ảnh lẫn văn bản đều được dịch thành <b>vector số (embedding)</b> — một dãy 512 số thực. "
          "Hai thứ có nghĩa gần nhau thì vector của chúng <b>gần nhau</b> trong không gian toán học."),
    ]
    story += diagram("""
  "A cute dog"   ──► CLIP Text Encoder  ──► [ 0.12, -0.34,  0.87, 0.05, ... ]  (512 so)
                                                         ↑
                                              HAI VECTOR GAN NHAU
                                             cos_sim ≈ 0.85 → MATCH ✓
                                                         ↓
  [Anh con cho]  ──► CLIP Vision Encoder ──► [ 0.11, -0.31,  0.85, 0.04, ... ]  (512 so)


  "A red car"    ──► CLIP Text Encoder  ──► [-0.50,  0.22, -0.10, 0.77, ... ]
                                                         ↑
                                              HAI VECTOR XA NHAU
                                             cos_sim ≈ 0.15 → MISMATCH ✗
                                                         ↓
  [Anh con cho]  ──► CLIP Vision Encoder ──► [ 0.11, -0.31,  0.85, 0.04, ... ]
    """)
    story += [
        sp(6),
        h2("1.3 Hai chế độ dự đoán"),
        bul("<b>Cosine Similarity thuần</b>: Tính góc giữa 2 vector → nếu ≥ 0.25 thì MATCH. Không cần train."),
        bul("<b>Classifier Head</b>: Ghép 2 vector → cho qua mạng nơ-ron nhỏ → sigmoid → xác suất MATCH. Cần train trước."),
        note("Hệ thống ưu tiên dùng Classifier Head nếu đã có file best_model.pth. Nếu không có, dùng cosine similarity."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 2: CONFIG
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 2 — configs/config.py (Trung tâm điều khiển)"), hr()]
    story += [
        h2("2.1 Mục đích"),
        p("Tất cả tham số của toàn dự án đặt tại đây. Các file khác đều import "
          "<b>Config</b> để lấy giá trị — chỉ cần sửa một chỗ, toàn hệ thống nhận."),
        sp(4),
        h2("2.2 Toàn bộ code và giải thích từng dòng"),
    ]
    story += code("""class Config:
    # os.path.abspath(__file__)  → tuyệt đối hóa đường dẫn file config.py
    # os.path.dirname(...)       → lấy thư mục chứa file
    # dirname 2 lần              → đi lên 2 cấp → thư mục gốc dự án
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DATA_DIR    = os.path.join(ROOT_DIR, 'data')
    IMAGE_DIR   = os.path.join(DATA_DIR, 'images')
    OUTPUT_DIR  = os.path.join(ROOT_DIR, 'outputs')

    # Tên model trên HuggingFace — lần đầu tự tải về (~600MB)
    # M-CLIP hỗ trợ tiếng Việt; nếu chưa cài → fallback về CLIP tiếng Anh
    MODEL_NAME = "M-CLIP/XLM-Roberta-Large-Vit-L-14"

    # torch.cuda.is_available() → True nếu có GPU NVIDIA + CUDA đã cài
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    # Ngưỡng quyết định MATCH/MISMATCH
    SIMILARITY_THRESHOLD = 0.25   # Dùng khi không có checkpoint
    CLASSIFIER_THRESHOLD = 0.5    # Dùng khi có checkpoint đã train
    USE_CLASSIFIER_IN_INFERENCE = True  # Ưu tiên dùng classifier

    # Tham số training
    BATCH_SIZE            = 16    # 16 cặp ảnh-text mỗi lần update trọng số
    LEARNING_RATE         = 2e-4  # LR cho classifier head (mới, học nhanh)
    CLIP_FINETUNE_LR      = 5e-6  # LR cho CLIP layers (đã có kiến thức, học chậm)
    NUM_EPOCHS            = 30    # Tối đa 30 vòng (có early stopping)
    NUM_UNFREEZE_LAYERS   = 2     # Mở 2 transformer block cuối CLIP
    EARLY_STOPPING_PATIENCE = 5   # Dừng nếu 5 epoch liên tiếp không cải thiện
    ENABLE_BATCH_NEGATIVES = True  # Tự tạo MISMATCH từ batch
    NEGATIVE_RATIO         = 1.0  # Tỷ lệ: 1 negative / 1 positive
    USE_AMP                = True  # Mixed precision (chỉ có tác dụng trên GPU)
    VAL_SPLIT              = 0.1  # 10% dataset dùng để validation
    SEED                   = 42   # Seed cố định để kết quả tái tạo được""")
    story += [
        sp(4),
        h3("Tại sao CLIP_FINETUNE_LR nhỏ hơn LEARNING_RATE 40 lần?"),
        p("CLIP đã được train trên hàng tỷ cặp ảnh-text, nó 'giỏi' rồi. "
          "Nếu cho học rate cao → phá vỡ kiến thức cũ (catastrophic forgetting). "
          "Classifier head thì mới hoàn toàn, cần học nhanh hơn."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 3: MODEL
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 3 — models/clip_model.py (Trái tim AI)"), hr()]
    story += [
        h2("3.1 Kiến trúc tổng thể"),
    ]
    story += diagram("""
  Input: (pixel_values, input_ids, attention_mask)
         |                    |
         v                    v
  CLIP Vision Encoder    CLIP Text Encoder   ← Đóng băng (except 2 block cuối)
         |                    |
         v                    v
  image_embeds (512)    text_embeds (512)
         |                    |
         +────────────────────+
                   |
         [img, txt, img-txt, img*txt]   ← Kết hợp 4 chiều = 2048 số
                   |
         Linear(2048 → 256)
         LayerNorm(256)
         GELU activation
         Dropout(0.3)
         Linear(256 → 128)
         GELU
         Dropout(0.2)
         Linear(128 → 1)
                   |
                logit (1 số)
                   |
              sigmoid(logit) = xác suất [0,1]
                   |
           >= 0.5 → MATCH / < 0.5 → MISMATCH
    """)
    story += [sp(6), h2("3.2 Code khởi tạo — __init__")]
    story += code("""def __init__(self, model_name=Config.MODEL_NAME, hidden_size=256):
    super(ITMDCLIPModel, self).__init__()

    # Tải CLIP base (vision + text encoder tiếng Anh)
    self.clip      = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    self.embed_dim = self.clip.config.projection_dim  # = 512

    # ── Đóng băng toàn bộ CLIP ──────────────────────────────────────────
    # requires_grad = False: khi backward() chạy, param này KHÔNG được
    # tính đạo hàm → không được cập nhật → giữ nguyên kiến thức CLIP
    for param in self.clip.parameters():
        param.requires_grad = False

    # ── Mở băng 2 transformer block cuối của vision encoder ─────────────
    # Tại sao? Các block cuối học đặc trưng cấp cao (semantic)
    # → cho chúng học thêm từ dữ liệu của chúng ta
    n = getattr(Config, "NUM_UNFREEZE_LAYERS", 2)
    if n > 0:
        vision_layers = self.clip.vision_model.encoder.layers
        for layer in vision_layers[-n:]:   # Lấy n layer cuối
            for param in layer.parameters():
                param.requires_grad = True  # Mở băng

        # Mở băng text encoder nếu không dùng M-CLIP
        if not self.use_mclip:
            text_layers = self.clip.text_model.encoder.layers
            for layer in text_layers[-n:]:
                for param in layer.parameters():
                    param.requires_grad = True""")
    story += code("""    # ── Classifier Head ─────────────────────────────────────────────────
    # Input dim = 4 * 512 = 2048 vì kết hợp 4 cách:
    # [img_embed, text_embed, img-text (diff), img*text (product)]
    input_dim = self.embed_dim * 4  # = 2048

    self.classifier = nn.Sequential(
        nn.Linear(input_dim, hidden_size),  # 2048 → 256
        nn.LayerNorm(hidden_size),           # Chuẩn hóa → ổn định training
        nn.GELU(),                           # Hàm kích hoạt mượt hơn ReLU
        nn.Dropout(0.3),                     # 30% neuron bị tắt ngẫu nhiên → chống overfit
        nn.Linear(hidden_size, hidden_size // 2),  # 256 → 128
        nn.GELU(),
        nn.Dropout(0.2),
        nn.Linear(hidden_size // 2, 1)       # 128 → 1 (logit cuối cùng)
    )
    # Lưu ý: KHÔNG có Sigmoid ở đây vì BCEWithLogitsLoss tự tính Sigmoid
    # (chính xác hơn về mặt số học, tránh overflow)""")
    story += [sp(6), h2("3.3 Hàm _combine — Tại sao kết hợp 4 chiều?")]
    story += code("""def _combine(self, image_embeds, text_embeds):
    # Normalize về độ dài = 1 (unit vector) để cosine similarity có nghĩa
    img = F.normalize(image_embeds, p=2, dim=-1)
    txt = F.normalize(text_embeds,  p=2, dim=-1)

    diff = img - txt   # Hiệu: nếu khớp → gần 0; nếu lệch → xa 0
    prod = img * txt   # Tích: nếu khớp → dương lớn; nếu lệch → gần 0

    # Ghép cả 4: classifier nhìn thấy thông tin từ nhiều góc độ
    return torch.cat((img, txt, diff, prod), dim=1)
    # Shape: (batch, 512+512+512+512) = (batch, 2048)""")
    story += [
        sp(4),
        tbl([
            ["Chiều", "Ý nghĩa", "Giá trị khi MATCH", "Giá trị khi MISMATCH"],
            ["img",      "Đặc trưng ảnh",           "Vector ảnh chuẩn hóa",    "Vector ảnh chuẩn hóa"],
            ["txt",      "Đặc trưng text",           "Vector text chuẩn hóa",   "Vector text chuẩn hóa"],
            ["img-txt",  "Sự khác biệt",             "Gần 0 (hai vector gần)",  "Xa 0 (hai vector xa)"],
            ["img*txt",  "Tương quan từng chiều",    "Nhiều giá trị dương lớn", "Nhiều giá trị gần 0"],
        ], [1.8*cm, 4*cm, 4.5*cm, 4.5*cm]),
        sp(6),
        h2("3.4 Forward pass — Dùng khi training"),
    ]
    story += code("""def forward(self, input_ids, attention_mask, pixel_values):
    # Lấy image embedding từ vision encoder
    image_embeds = self.clip.get_image_features(pixel_values=pixel_values)
    # Shape: (batch_size, 512)

    # Lấy text embedding (M-CLIP nếu có, CLIP nếu không)
    text_embeds = self._get_text_embeds(input_ids, attention_mask)
    # Shape: (batch_size, 512)

    # Kết hợp 4 chiều → (batch_size, 2048)
    combined = self._combine(image_embeds, text_embeds)

    # Qua classifier head → (batch_size, 1)
    logits = self.classifier(combined)
    return logits  # Chưa qua sigmoid — BCEWithLogitsLoss tự xử lý""")
    story += [sp(6), h2("3.5 extract_features — Dùng khi inference không có checkpoint")]
    story += code("""def extract_features(self, input_ids, attention_mask, pixel_values):
    with torch.no_grad():  # Không tính gradient → tiết kiệm RAM
        image_embeds = self.clip.get_image_features(pixel_values=pixel_values)
        text_embeds  = self._get_text_embeds(input_ids, attention_mask)
    return image_embeds, text_embeds
    # Trả về 2 vector thô để tính cosine similarity bên ngoài""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 4: DATASET
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 4 — dataset/dataset_loader.py (Nạp dữ liệu)"), hr()]
    story += [
        h2("4.1 Cấu trúc file CSV đầu vào"),
    ]
    story += code("""# data/captions.csv
image_path,caption,label
dog.jpg,A cute brown dog playing in the grass,1   ← MATCH
car.png,A blue sports car driving fast,1           ← MATCH
dog.jpg,An elephant using its trunk,0              ← MISMATCH (sai caption)""")
    story += [sp(4), h2("4.2 Hàm normalize_caption")]
    story += code("""def normalize_caption(text: str) -> str:
    text = str(text).strip()          # Bỏ khoảng trắng đầu/cuối
    text = re.sub(r'\\s+', ' ', text)  # "hello   world" → "hello world"
    return text
# Tại sao cần? Vì tokenizer nhạy cảm với khoảng trắng thừa.
# "a dog" và "a  dog" có thể cho token IDs khác nhau.""")
    story += [sp(4), h2("4.3 collate_skip_none — Xử lý ảnh lỗi")]
    story += code("""def collate_skip_none(batch):
    # batch là list các item trả về từ __getitem__
    # Nếu __getitem__ gặp ảnh lỗi → trả None
    batch = [b for b in batch if b is not None]  # Lọc None ra
    if len(batch) == 0:
        return None   # Toàn batch lỗi → bỏ qua cả batch
    return torch.utils.data.dataloader.default_collate(batch)
# Phiên bản gốc dùng ảnh đen thay thế → model học pattern sai
# Phiên bản mới: bỏ qua hoàn toàn → sạch hơn""")
    story += [sp(4), h2("4.4 __getitem__ — Đọc 1 sample")]
    story += code("""def __getitem__(self, idx):
    row       = self.data.iloc[idx]   # Lấy hàng idx từ DataFrame
    img_name  = str(row['image_path'])
    caption   = str(row['caption'])
    label     = row.get('label', 0)   # 0 nếu không có cột label

    img_path = os.path.join(self.image_dir, img_name)
    try:
        image = Image.open(img_path).convert("RGB")
        # convert("RGB"): đảm bảo ảnh RGBA, grayscale, PNG... đều về RGB 3 kênh
    except Exception as e:
        print(f"[SKIP] {img_path}: {e}")
        return None   # DataLoader sẽ bỏ qua qua collate_skip_none""")
    story += code("""    # Augmentation khi training (augment=True)
    if self.augment:
        image = self._apply_augmentation(image)
        # RandomHorizontalFlip: lật ngang ngẫu nhiên 50%
        # ColorJitter: thay đổi độ sáng/tương phản ngẫu nhiên
        # RandomResizedCrop: cắt ngẫu nhiên 85-100% diện tích

    # CLIP Processor: chuẩn hóa ảnh + tokenize text
    inputs = self.processor(
        text=[caption],       # List vì processor thiết kế cho batch
        images=image,
        return_tensors="pt",  # Trả về PyTorch tensor
        padding="max_length", # Pad đến đúng max_length=77 token
        truncation=True,      # Cắt nếu dài hơn 77
        max_length=77,        # CLIP giới hạn 77 token text
    )
    return {
        # squeeze(0): bỏ dimension batch (processor trả [1, len] → cần [len])
        'input_ids':      inputs['input_ids'].squeeze(0),       # (77,)
        'attention_mask': inputs['attention_mask'].squeeze(0),  # (77,) - 1=token thật, 0=padding
        'pixel_values':   inputs['pixel_values'].squeeze(0),    # (3, 224, 224) RGB
        'label':          torch.tensor(label, dtype=torch.float32),  # 0.0 hoặc 1.0
    }""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 5: TRAINING
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 5 — training/train.py (Huấn luyện mô hình)"), hr()]
    story += [
        h2("5.1 Sơ đồ toàn bộ quá trình training"),
    ]
    story += diagram("""
  captions.csv
       │
       ▼
  ImageTextDataset (augment=True)
       │
  random_split (90% train / 10% val)
       │              │
  DataLoader       DataLoader
  (shuffle=True)  (shuffle=False)
       │
  ┌────▼──── vòng lặp epoch (tối đa 30) ───────────────────────────┐
  │                                                                  │
  │  Batch (16 cặp) ──► _make_batch_negatives ──► 32 cặp (thêm 16 MISMATCH)
  │        │
  │        ▼
  │  ITMDCLIPModel.forward() ──► logits (32, 1)
  │        │
  │        ▼
  │  BCEWithLogitsLoss(logits, labels) ──► loss (số thực)
  │        │
  │        ▼
  │  loss.backward() ──► tính gradient cho tất cả param requires_grad=True
  │        │
  │  clip_grad_norm_(max=1.0) ──► cắt gradient nếu quá lớn (tránh NaN)
  │        │
  │  optimizer.step() ──► cập nhật trọng số
  │        │
  │  scheduler.step() ──► giảm learning rate theo cosine
  │        │
  │  validation ──► tính val_loss
  │        │
  │  val_loss < best? ──► lưu best_model.pth
  │        │
  │  5 epoch không cải thiện? ──► EARLY STOPPING
  └──────────────────────────────────────────────────────────────────┘
       │
  Tìm ngưỡng tối ưu (Youden's J)
       │
  Vẽ: confusion_matrix.png, roc_curve.png, similarity_distribution.png
    """)
    story += [sp(6), h2("5.2 Hard Negatives — _make_batch_negatives")]
    story += code("""def _make_batch_negatives(input_ids, attention_mask, pixel_values, labels, ...):
    # Ý tưởng: trong batch có 16 cặp MATCH,
    # Ta tạo thêm 16 cặp MISMATCH bằng cách:
    # - Giữ nguyên ảnh của cặp i
    # - Ghép với caption của cặp (i+1), (i+2)... (xoay vòng)
    # → Ảnh và caption chắc chắn không khớp nhau

    bsz = input_ids.size(0)  # batch_size = 16
    k   = 1                  # negative_ratio = 1.0 → tạo 1 bản negative

    for i in range(1, k + 1):
        # torch.roll: dịch tensor sang phải i vị trí (cuối vòng lên đầu)
        # [0,1,2,...,15] → roll(1) → [15,0,1,...,14]
        perm = torch.roll(torch.arange(bsz), shifts=i)
        neg_inputs.append(input_ids[perm])    # Caption bị xoay
        neg_pixels.append(pixel_values)       # Ảnh KHÔNG thay đổi
        neg_labels.append(torch.zeros_like(labels))  # Label = 0 (MISMATCH)

    # Ghép batch gốc + negatives
    # Kết quả: batch_size tăng từ 16 → 32
    return (
        torch.cat([input_ids] + neg_inputs),       # (32, 77)
        torch.cat([attention_mask] + neg_masks),   # (32, 77)
        torch.cat([pixel_values] + neg_pixels),    # (32, 3, 224, 224)
        torch.cat([labels] + neg_labels),          # (32, 1)
    )""")
    story += [sp(6), h2("5.3 Loss Function — BCEWithLogitsLoss")]
    story += code("""# pos_weight cân bằng class imbalance
# Nếu dataset có 800 MATCH và 200 MISMATCH:
# pos_weight = 200/800 = 0.25 → phạt nhẹ khi đoán sai MATCH
# pos_weight = 800/200 = 4.0  → phạt nặng khi đoán sai MISMATCH
pos_weight = torch.tensor([neg / pos])  # neg=số mẫu 0, pos=số mẫu 1

criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

# BCEWithLogitsLoss tính:
# loss = -[y * log(sigmoid(x)) + (1-y) * log(1 - sigmoid(x))]
# Trong đó: x = logit (output của model), y = label (0 hoặc 1)
# Nếu y=1 (MATCH) và x lớn dương → sigmoid(x)≈1 → loss ≈ 0 (đúng)
# Nếu y=1 (MATCH) và x âm lớn  → sigmoid(x)≈0 → loss lớn (sai)""")
    story += [sp(6), h2("5.4 Optimizer với 2 learning rate khác nhau")]
    story += code("""param_groups = [
    # Classifier head: mới hoàn toàn → học nhanh
    {'params': model.classifier.parameters(), 'lr': 2e-4},
]
if clip_trainable:  # Các param CLIP được mở băng
    # CLIP đã có kiến thức → học rất chậm để không quên
    param_groups.append({'params': clip_trainable, 'lr': 5e-6})

optimizer = torch.optim.AdamW(param_groups, weight_decay=1e-4)
# AdamW = Adam + weight decay (L2 regularization) → chống overfit""")
    story += [sp(6), h2("5.5 Mixed Precision Training (AMP)")]
    story += code("""# AMP = Automatic Mixed Precision
# Thay vì tính toán bằng float32 (32 bit), dùng float16 (16 bit)
# → Nhanh hơn ~2x, tiết kiệm GPU memory ~50%
# GradScaler bù đắp cho giá trị nhỏ bị mất khi dùng float16

scaler = torch.cuda.amp.GradScaler()

with torch.cuda.amp.autocast():  # Tự động chọn float16 hay float32
    logits = model(input_ids, attention_mask, pixel_values)
    loss   = criterion(logits, labels)

scaler.scale(loss).backward()  # Scale loss để tránh underflow
scaler.unscale_(optimizer)
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
# Clip gradient: nếu norm gradient > 1.0 → scale xuống còn 1.0
# Tại sao? Gradient quá lớn → bước nhảy lớn → model "điên"
scaler.step(optimizer)
scaler.update()""")
    story += [sp(6), h2("5.6 Cosine Annealing LR Scheduler")]
    story += code("""scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=30, eta_min=1e-7
)
# LR thay đổi theo hàm cosine trong 30 epoch:
# Epoch 1:  LR = 2e-4 (cao nhất)
# Epoch 15: LR ≈ 1e-4 (giữa)
# Epoch 30: LR = 1e-7 (thấp nhất)
# → Học nhanh đầu, học chậm dần để converge ổn định

scheduler.step()  # Gọi cuối mỗi epoch (NGOÀI vòng batch)""")
    story += [sp(6), h2("5.7 Tìm ngưỡng tối ưu — Youden's J Statistic")]
    story += code("""def find_optimal_threshold(labels, probs):
    fpr, tpr, thresholds = roc_curve(labels, probs)
    # ROC curve: với mỗi ngưỡng T, tính:
    # TPR = TP/(TP+FN) = tỷ lệ MATCH đúng bắt được
    # FPR = FP/(FP+TN) = tỷ lệ MISMATCH bị đoán nhầm thành MATCH

    j_scores = tpr - fpr
    # Youden's J = TPR - FPR → tối đa hóa → ngưỡng cân bằng nhất
    # J=1: model hoàn hảo, J=0: model ngẫu nhiên

    best_idx       = j_scores.argmax()   # Vị trí J lớn nhất
    best_threshold = float(thresholds[best_idx])
    return best_threshold, best_f1
    # Ví dụ in ra: "Ngưỡng tối ưu: 0.4321 → F1=0.8765"
    # → Cập nhật CLASSIFIER_THRESHOLD = 0.4321 trong config.py""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 6: SIMILARITY
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 6 — utils/similarity.py (Đo độ tương đồng)"), hr()]
    story += [
        h2("6.1 Cosine Similarity là gì?"),
        p("Cosine similarity đo <b>góc giữa hai vector</b>. "
          "Hai vector cùng hướng → cos = 1. Vuông góc → cos = 0. Ngược chiều → cos = -1."),
    ]
    story += diagram("""
  vector A  →→→→→→→→→→
  vector B  →→→→→→→→→→→→   (gần cùng hướng) → cos(θ) ≈ 0.95 (MATCH)

  vector A  →→→→→→→→→→
  vector B          ↑       (vuông góc)       → cos(θ) = 0.0  (không liên quan)

  vector A  →→→→→→→→→→
  vector B  ←←←←←←←←←←   (ngược chiều)     → cos(θ) = -1   (đối lập)
    """)
    story += [sp(4), h2("6.2 Code compute_similarity")]
    story += code("""def compute_similarity(image_embeds, text_embeds):
    # Bước 1: Normalize về unit vector (độ dài = 1)
    # Tại sao? Để loại bỏ ảnh hưởng của độ lớn, chỉ giữ hướng
    img = F.normalize(image_embeds, p=2, dim=-1)
    txt = F.normalize(text_embeds,  p=2, dim=-1)
    # p=2: L2 norm = sqrt(x1^2 + x2^2 + ... + xn^2)
    # dim=-1: chuẩn hóa theo chiều cuối (chiều embedding)

    # Bước 2: Tính cosine similarity = dot product của 2 unit vector
    sim = F.cosine_similarity(img, txt, dim=-1)
    # Kết quả trong [-1, 1]

    # Bước 3: Ánh xạ [-1, 1] → [0, 1] để dễ đọc hơn
    sim_score = (sim + 1.0) / 2.0
    # sim = -1 → score = 0.0 (hoàn toàn không khớp)
    # sim =  0 → score = 0.5 (trung lập)
    # sim =  1 → score = 1.0 (hoàn toàn khớp)
    return sim_score""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 7: INFERENCE
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 7 — inference/predict.py (Dự đoán)"), hr()]
    story += [
        h2("7.1 Logic quyết định chế độ"),
    ]
    story += diagram("""
  predict() được gọi
         │
  checkpoint_loaded = True?
         │
    ┌────┴────┐
   YES        NO
    │          │
    ▼          ▼
  USE_CLASSIFIER  Dùng cosine similarity
  _IN_INFERENCE?  (extract_features → compute_similarity)
    │
  ┌─┴─┐
 YES   NO
  │     │
  ▼     ▼
Classifier Cosine
  head    similarity
  │          │
  ▼          ▼
sigmoid   (sim+1)/2
  │          │
  └────┬─────┘
       ▼
  sim_score [0,1]
       │
  >= threshold?
  ┌────┴────┐
 YES        NO
  │          │
 MATCH   MISMATCH
    """)
    story += [sp(4), h2("7.2 Toàn bộ code predict() giải thích từng dòng")]
    story += code("""def predict(image_path, text, model=None, threshold=None, checkpoint_loaded=None):
    device = torch.device(Config.DEVICE)  # "cpu" hoặc "cuda"

    # Nếu không truyền model từ ngoài → tạo model mới và load checkpoint
    if model is None:
        model = ITMDCLIPModel(Config.MODEL_NAME).to(device)
        model.eval()  # Tắt dropout, batchnorm về eval mode

        checkpoint_path = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
        _checkpoint_loaded = False

        if os.path.exists(checkpoint_path):
            try:
                # load_state_dict: nạp trọng số đã lưu vào model
                model.load_state_dict(
                    torch.load(checkpoint_path, map_location=device)
                )
                # map_location=device: nếu save trên GPU, load về CPU vẫn OK
                _checkpoint_loaded = True
            except Exception as e:
                print(f"Loi load checkpoint: {e}")
                # Không crash — tiếp tục dùng cosine similarity""")
    story += code("""    # Đọc ảnh
    image = Image.open(image_path).convert("RGB")
    # convert("RGB"): ảnh RGBA (4 kênh) → 3 kênh, grayscale → 3 kênh giống nhau

    # Tiền xử lý (CLIP Processor làm 2 việc):
    # 1. Text: tokenize → [101, 1037, 3899, 102, 0, 0, ...] (77 token IDs)
    # 2. Image: resize về 224×224 → normalize pixel values
    inputs = processor(
        text=[text], images=image,
        return_tensors="pt",  # PyTorch tensor
        padding=True, truncation=True
    ).to(device)

    with torch.no_grad():  # Không tính gradient → tiết kiệm bộ nhớ
        use_classifier = (USE_CLASSIFIER_IN_INFERENCE and _checkpoint_loaded)

        if use_classifier:
            # Đường 1: Classifier Head
            logit = model(inputs['input_ids'],
                         inputs['attention_mask'],
                         inputs['pixel_values'])   # Shape: (1, 1)
            sim_score = torch.sigmoid(logit).item()  # .item() → float Python
            # sigmoid(0) = 0.5, sigmoid(5) ≈ 0.99, sigmoid(-5) ≈ 0.01
        else:
            # Đường 2: Cosine Similarity thuần
            image_embeds, text_embeds = model.extract_features(...)
            sim_score = compute_similarity(image_embeds, text_embeds).item()

    # Chọn ngưỡng phù hợp với chế độ đang dùng
    if threshold is None:
        threshold = CLASSIFIER_THRESHOLD if use_classifier else SIMILARITY_THRESHOLD

    prediction = "MATCH" if sim_score >= threshold else "MISMATCH"
    return sim_score, prediction""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 8: FLASK API
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 8 — app.py (Flask API Backend)"), hr()]
    story += [
        h2("8.1 Khởi động server"),
    ]
    story += code("""# Khi chạy: python app.py
app = Flask(__name__)
CORS(app)  # Cho phép frontend (localhost:5173) gọi API (localhost:5000)
           # Nếu không có CORS → trình duyệt block request (same-origin policy)

# Model được load MỘT LẦN khi server khởi động
# Không load lại mỗi request → API nhanh hơn nhiều
model = ITMDCLIPModel(Config.MODEL_NAME).to(device)
model.eval()

checkpoint_loaded = False
if os.path.exists(checkpoint_path):
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    checkpoint_loaded = True  # Ghi nhớ để truyền vào predict()""")
    story += [sp(4), h2("8.2 Endpoint POST /api/predict")]
    story += code("""@app.route('/api/predict', methods=['POST'])
def api_predict():
    # Kiểm tra có đủ fields không
    if 'imageFile' not in request.files or 'caption' not in request.form:
        return jsonify({"error": "Missing imageFile or caption"}), 400

    file    = request.files['imageFile']   # File upload từ form
    caption = request.form['caption'].strip()

    # Validate: file rỗng hoặc caption rỗng
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    if not caption:          return jsonify({"error": "Caption empty"}), 400

    # Validate file type (tránh upload file độc hại)
    ALLOWED = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED:
        return jsonify({"error": "File type not supported"}), 400

    # Tên file unique bằng UUID → thread-safe khi nhiều request đồng thời
    # Không dùng filename gốc → tránh path traversal attack
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)  # Lưu file tạm

    try:
        sim_score, prediction_result = predict(
            filepath, caption, model=model, checkpoint_loaded=checkpoint_loaded
        )
        return jsonify({
            "isMatch":        prediction_result == "MATCH",  # bool
            "simScore":       round(sim_score, 4),            # float 4 chữ số
            "suggestedCaption": ""                            # Trống (không hardcode)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # finally LUÔN chạy dù try thành công hay lỗi → xóa file tạm
        if os.path.exists(filepath):
            os.remove(filepath)""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 9: FRONTEND
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 9 — Frontend React (App.jsx + predictService.js)"), hr()]
    story += [
        h2("9.1 State management — Các biến React"),
    ]
    story += code("""// Tất cả state trong App component
const [authUser,       setAuthUser]       = useState(...)  // User đang đăng nhập
const [imageFile,      setImageFile]      = useState(null) // File ảnh đã chọn
const [imagePreviewUrl,setImagePreviewUrl]= useState("")   // URL blob để preview
const [caption,        setCaption]        = useState("")   // Caption text
const [errors,         setErrors]         = useState(...)  // Lỗi validation
const [isLoading,      setIsLoading]      = useState(false)// Đang gọi API?
const [result,         setResult]         = useState(null) // Kết quả từ API""")
    story += [sp(4), h2("9.2 Xử lý upload ảnh")]
    story += code("""const handleImageChange = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Giải phóng URL blob cũ để tránh memory leak
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl)

    // createObjectURL tạo URL tạm (blob:http://...) để hiển thị ảnh trực tiếp
    // mà không cần upload lên server trước
    const previewUrl = URL.createObjectURL(file)

    setImageFile(file)           // Lưu File object để gửi lên API sau
    setImagePreviewUrl(previewUrl) // Hiển thị preview ngay lập tức
    setResult(null)               // Xóa kết quả cũ
}""")
    story += [sp(4), h2("9.3 Gọi API khi bấm Kiểm tra")]
    story += code("""const handleCheck = async (event) => {
    event.preventDefault()  // Ngăn form reload trang

    if (!authUser) {
        openAuth("login")  // Yêu cầu đăng nhập trước
        return
    }

    if (!validateInput()) return  // Kiểm tra ảnh và caption không rỗng

    setIsLoading(true)  // Hiển thị "Đang phân tích ảnh..."

    try {
        const prediction = await predictImageTextMismatch({ imageFile, caption })
        setResult(prediction)  // { isMatch, simScore, suggestedCaption }
    } catch {
        // API lỗi → vẫn hiển thị kết quả (fallback)
        setResult({ isMatch: false, suggestedCaption: "..." })
    } finally {
        setIsLoading(false)  // Tắt loading dù thành công hay lỗi
    }
}""")
    story += [sp(4), h2("9.4 predictService.js — Gọi API Flask")]
    story += code("""export async function predictImageTextMismatch({ imageFile, caption }) {
    // FormData: cách gửi file + text trong 1 HTTP request
    const formData = new FormData()
    formData.append("imageFile", imageFile)  // Field name phải khớp Flask
    formData.append("caption",   caption)

    const response = await fetch("http://127.0.0.1:5000/api/predict", {
        method: "POST",
        body: formData,
        // Không set Content-Type header → browser tự set multipart/form-data
        // Nếu set tay sẽ thiếu boundary → Flask không đọc được file
    })

    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
    }

    const data = await response.json()
    return {
        isMatch:          data.isMatch,           // true/false
        suggestedCaption: data.suggestedCaption || "",
        simScore:         data.simScore,          // 0.0 - 1.0
    }
}""")
    story += [sp(4), h2("9.5 Hiển thị kết quả")]
    story += code("""{result?.isMatch ? (
    // Optional chaining: result?.isMatch → không crash nếu result = null
    <div className="result-badge success">
        <h4>Anh va mo ta khop nhau</h4>
    </div>
) : null}

{result && !result.isMatch ? (
    <div className="result-badge danger">
        <h4>Anh va mo ta KHONG khop</h4>
    </div>
) : null}""")
    story += [
        sp(4),
        warn("Authentication frontend lưu password plain text trong localStorage. "
             "Chỉ phù hợp cho demo, không dùng trong production."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 10: LUỒNG ĐẦY ĐỦ
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 10 — Luồng đầy đủ từ đầu đến cuối"), hr()]
    story += [
        h2("10.1 Luồng khi người dùng kiểm tra ảnh"),
    ]
    story += diagram("""
  [USER]  Upload dog.jpg + nhap caption "a cute dog"
     │
     ▼
  [App.jsx: handleCheck]
     │  validateInput() → OK
     │  setIsLoading(true) → hien "Dang phan tich..."
     ▼
  [predictService.js: predictImageTextMismatch]
     │  new FormData() { imageFile: dog.jpg, caption: "a cute dog" }
     │  fetch POST http://127.0.0.1:5000/api/predict
     ▼
  [app.py: api_predict]
     │  Validate: file OK, caption OK, extension OK
     │  Luu file tam: /data/uploads/a3f8c2d1-....jpg
     ▼
  [inference/predict.py: predict]
     │  PIL.Image.open("a3f8c2d1-....jpg").convert("RGB")
     │  → (W, H, 3) numpy array
     │
     │  processor(text=["a cute dog"], images=image)
     │  → input_ids = [49406, 320, 4450, 2368, 49407, 0, 0, ... ] (77 tokens)
     │  → pixel_values = tensor(3, 224, 224) gia tri float chuẩn hóa
     ▼
  [models/clip_model.py: forward]
     │  clip.get_image_features(pixel_values) → [0.12, -0.34, ...] (512 so)
     │  clip.get_text_features(input_ids)     → [0.11, -0.31, ...] (512 so)
     │  _combine → [img, txt, diff, prod]     → 2048 so
     │  classifier(2048) → Linear → LayerNorm → GELU → Dropout → ... → 1 logit
     │  sigmoid(0.85) = 0.70
     ▼
  [inference/predict.py]
     │  sim_score = 0.70
     │  0.70 >= 0.5 (CLASSIFIER_THRESHOLD) → "MATCH"
     ▼
  [app.py]
     │  os.remove(filepath)  ← xoa file tam
     │  return {"isMatch": true, "simScore": 0.7}
     ▼
  [predictService.js]
     │  data = { isMatch: true, simScore: 0.7 }
     ▼
  [App.jsx]
     │  setResult({ isMatch: true, simScore: 0.7 })
     │  setIsLoading(false)
     ▼
  [Browser]
     Hien thi: badge xanh "Anh va mo ta khop nhau" ✓
    """)
    story += [sp(6), h2("10.2 Luồng khi train model")]
    story += diagram("""
  python training/train.py
     │
     ▼
  Config.setup_dirs()  ← tao outputs/ neu chua co
     │
  ITMDCLIPModel.__init__()
     │  Load CLIP (~600MB lan dau)
     │  Dong bang tat ca param
     │  Mo bang 2 block cuoi
     │  Tao classifier head
     ▼
  ImageTextDataset(augment=True)
     │  Doc captions.csv → DataFrame
     │  Chuan hoa caption
     ▼
  random_split → 90% train / 10% val (seed=42)
     │
  DataLoader(batch_size=16, shuffle=True)
     │
  ╔══════════════ Epoch 1 → 30 ══════════════╗
  ║ batch(16 cap) → hard negatives → 32 cap  ║
  ║ forward() → logits(32,1)                 ║
  ║ BCEWithLogitsLoss → loss                 ║
  ║ backward() → gradient                    ║
  ║ clip_grad_norm_(max=1.0)                 ║
  ║ optimizer.step() → cap nhat trong so     ║
  ║ scheduler.step() → giam LR theo cosine   ║
  ║                                          ║
  ║ Validation: tinh val_loss                ║
  ║ val_loss < best? → luu best_model.pth    ║
  ║ 5 epoch khong tot hon? → STOP            ║
  ╚══════════════════════════════════════════╝
     │
  Tim nguong toi uu (Youden's J)
     │  In: "Nguong toi uu: 0.4321, F1=0.8765"
     ▼
  Ve bieu do: confusion_matrix.png, roc_curve.png
    """)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 11: METRICS
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 11 — utils/metrics.py & visualization/visualize.py"), hr()]
    story += [
        h2("11.1 Các chỉ số đánh giá"),
    ]
    story.append(tbl([
        ["Chỉ số", "Công thức", "Ý nghĩa", "Khi nào quan trọng"],
        ["Accuracy",  "Đúng / Tổng",            "Tỷ lệ đúng tổng thể",                "Dataset cân bằng"],
        ["Precision", "TP / (TP + FP)",           "Trong những cái đoán MATCH, bao nhiêu thực sự MATCH", "Ít false alarm"],
        ["Recall",    "TP / (TP + FN)",           "Trong những cái thực sự MATCH, bắt được bao nhiêu",   "Không bỏ sót"],
        ["F1 Score",  "2*P*R / (P+R)",            "Trung bình điều hòa Precision và Recall",             "Dataset lệch"],
        ["AUC-ROC",   "Diện tích dưới ROC curve", "Chất lượng model ở mọi ngưỡng",                       "Đánh giá tổng thể"],
    ], [2*cm, 3.5*cm, 5.5*cm, 4.5*cm]))
    story += [sp(4), h2("11.2 Code calculate_metrics")]
    story += code("""def calculate_metrics(y_true, y_pred, y_prob=None):
    # y_true: [1, 0, 1, 1, 0, ...]  ← nhãn thực tế
    # y_pred: [1, 0, 0, 1, 0, ...]  ← nhãn model đoán
    # y_prob: [0.8, 0.3, 0.4, ...]  ← xác suất (cho AUC-ROC)

    metrics = {
        'accuracy':  accuracy_score(y_true, y_pred),
        # = (số đoán đúng) / (tổng số)

        'precision': precision_score(y_true, y_pred, zero_division=0),
        # zero_division=0: nếu không có TP+FP → trả 0 thay vì exception

        'recall':    recall_score(y_true, y_pred, zero_division=0),
        'f1_score':  f1_score(y_true, y_pred, zero_division=0),
    }

    if y_prob is not None:
        try:
            metrics['auc_roc'] = roc_auc_score(y_true, y_prob)
            # AUC = 0.5: random, AUC = 1.0: hoàn hảo, AUC < 0.5: tệ hơn random
        except ValueError:
            metrics['auc_roc'] = None  # Chỉ 1 class trong y_true
    return metrics""")
    story += [sp(4), h2("11.3 Biểu đồ được tạo sau training")]
    story.append(tbl([
        ["File",                       "Nội dung",                    "Đọc thế nào"],
        ["confusion_matrix.png",       "Ma trận 2x2 đúng/sai theo class", "Ô chéo (TN, TP) = đúng; ô chéo phụ = sai"],
        ["roc_curve.png",              "Đường ROC + AUC score",           "Đường càng gần góc trên trái, AUC càng cao"],
        ["similarity_distribution.png","Phân bố score theo MATCH/MISMATCH","2 đỉnh tách biệt = model phân biệt tốt"],
    ], [4.5*cm, 5*cm, 7*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 12: DATA PREPARATION
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 12 — data/prepare_data.py (Chuẩn bị dữ liệu)"), hr()]
    story += [
        h2("12.1 Tại sao cần chuẩn bị dữ liệu?"),
        p("Model cần học cả 2 loại mẫu: MATCH (label=1) và MISMATCH (label=0). "
          "Trong thực tế, chúng ta thường chỉ có ảnh + caption đúng. "
          "Script tự động tạo MISMATCH bằng cách ghép ảnh với caption <b>không phải của nó</b>."),
        sp(4),
        h2("12.2 Thuật toán tạo MISMATCH (Derangement)"),
    ]
    story += code("""def build_mismatch_samples(match_samples, seed=42):
    # match_samples = [
    #   {image_path: "dog.jpg",  caption: "a cute dog",   label: 1},
    #   {image_path: "car.png",  caption: "a red car",    label: 1},
    #   {image_path: "cat.jpg",  caption: "a black cat",  label: 1},
    # ]

    images   = ["dog.jpg",  "car.png",  "cat.jpg"]
    captions = ["a cute dog", "a red car", "a black cat"]

    # Derangement: hoán vị không có phần tử nào đứng đúng vị trí gốc
    # Ví dụ: [0,1,2] → [1,2,0] (OK) → không có dog→dog, car→car, cat→cat
    # [0,1,2] → [1,0,2] (KHÔNG OK) → cat vẫn ở vị trí 2 → cat.jpg + "a black cat"

    # Thử shuffle ngẫu nhiên tối đa 100 lần cho đến khi là derangement thực sự
    for _ in range(100):
        rng.shuffle(shuffled)
        if all(shuffled[i] != i for i in range(len(shuffled))):
            break  # Tìm được derangement hợp lệ

    # Kết quả MISMATCH:
    # dog.jpg + "a red car"   → label=0 (sai)
    # car.png + "a black cat" → label=0 (sai)
    # cat.jpg + "a cute dog"  → label=0 (sai)""")
    story += [sp(4), h2("12.3 Dùng script chuẩn bị dữ liệu")]
    story += code("""# Tao MISMATCH tu CSV da co san (cach don gian nhat)
python data/prepare_data.py --from-csv data/captions.csv

# Ket qua captions.csv sau khi chay:
# image_path, caption,          label
# dog.jpg,    "a cute dog",     1   ← MATCH goc
# car.png,    "a red car",      1   ← MATCH goc
# dog.jpg,    "a red car",      0   ← MISMATCH tao tu derangement
# car.png,    "a cute dog",     0   ← MISMATCH tao tu derangement""")
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 13: TỔNG KẾT
    # ══════════════════════════════════════════════════════════════════════════
    story += [h1("Phần 13 — Tổng kết mối liên hệ giữa các file"), hr()]
    story += [
        h2("13.1 Sơ đồ dependency giữa các module"),
    ]
    story += diagram("""
  configs/config.py
         ▲ (import bởi tất cả)
         │
  ┌──────┼──────────────────────────────────────────┐
  │      │                                          │
  │  models/clip_model.py                           │
  │      ▲ (import bởi)                             │
  │      ├── training/train.py                       │
  │      ├── inference/predict.py                   │
  │      ├── app.py                                 │
  │      └── evaluate.py                            │
  │                                                  │
  │  dataset/dataset_loader.py                       │
  │      ▲ (import bởi)                             │
  │      └── training/train.py                       │
  │                                                  │
  │  utils/similarity.py                             │
  │      ▲ (import bởi)                             │
  │      ├── inference/predict.py                   │
  │      └── evaluate.py                            │
  │                                                  │
  │  utils/metrics.py                                │
  │      ▲ (import bởi)                             │
  │      ├── training/train.py                       │
  │      └── evaluate.py                            │
  │                                                  │
  │  visualization/visualize.py                      │
  │      ▲ (import bởi)                             │
  │      ├── training/train.py                       │
  │      └── evaluate.py                            │
  └──────────────────────────────────────────────────┘

  app.py ──import──► inference/predict.py
  frontend/src/services/predictService.js ──HTTP──► app.py
    """)
    story += [
        sp(6),
        h2("13.2 Thứ tự chạy dự án từ đầu"),
    ]
    story.append(tbl([
        ["Buoc", "Lenh", "File thuc thi", "Ket qua"],
        ["1", "pip install -r requirements.txt",         "requirements.txt",       "Cai du thu vien"],
        ["2", "pip install multilingual-clip ftfy",      "-",                      "Ho tro tieng Viet"],
        ["3", "python data/prepare_data.py",             "data/prepare_data.py",   "Tao captions.csv"],
        ["4", "python training/train.py",                "training/train.py",      "Tao best_model.pth"],
        ["5", "python evaluate.py --data data/captions.csv", "evaluate.py",        "Xem metrics"],
        ["6", "python app.py",                           "app.py",                 "Backend port 5000"],
        ["7", "cd frontend && npm install && npm run dev","frontend/",             "UI port 5173"],
    ], [0.8*cm, 5.5*cm, 4.5*cm, 4.5*cm]))
    story += [
        sp(8),
        HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=8),
        p("Tài liệu này bao gồm giải thích chi tiết từng dòng code của toàn bộ dự án ITMD. "
          "Được tạo bởi <b>generate_code_explain.py</b>. Phiên bản 1.0.", "body"),
    ]
    return story

# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out_path = os.path.join(os.path.expanduser("~"), "Desktop", "ITMD_Code_Explained.pdf")

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2*cm,
        title="ITMD — Giải thích chi tiết kèm code",
        author="ITMD Technical Docs",
    )
    doc.build(build(), onFirstPage=lambda c,d: None, onLaterPages=on_page)

    size_kb = os.path.getsize(out_path) // 1024
    print(f"PDF tao thanh cong: {out_path}  ({size_kb} KB)")
