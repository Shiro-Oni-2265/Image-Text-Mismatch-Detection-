# -*- coding: utf-8 -*-
"""Script tao tai lieu ky thuat PDF cho du an ITMD."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Font hỗ trợ tiếng Việt (DejaVu Sans) ─────────────────────────────────────
FONT_DIR = os.path.dirname(os.path.abspath(__file__))

def try_register_font():
    """Thử đăng ký font DejaVu hỗ trợ Unicode/tiếng Việt."""
    import urllib.request, zipfile, io
    font_path = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    font_bold = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

    if not os.path.exists(font_path):
        print("Tải font DejaVu Sans...")
        url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                zdata = r.read()
            with zipfile.ZipFile(io.BytesIO(zdata)) as z:
                for name in z.namelist():
                    if name.endswith("DejaVuSans.ttf") and "Bold" not in name and "Oblique" not in name:
                        with open(font_path, "wb") as f:
                            f.write(z.read(name))
                    if name.endswith("DejaVuSans-Bold.ttf"):
                        with open(font_bold, "wb") as f:
                            f.write(z.read(name))
        except Exception as e:
            print(f"Không tải được font: {e}. Dùng Helvetica.")
            return False

    try:
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))
        if os.path.exists(font_bold):
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_bold))
        return True
    except Exception as e:
        print(f"Lỗi đăng ký font: {e}")
        return False

HAS_UNICODE = try_register_font()
FONT_NORMAL = "DejaVu" if HAS_UNICODE else "Helvetica"
FONT_BOLD   = "DejaVu-Bold" if HAS_UNICODE else "Helvetica-Bold"

# ── Màu sắc ───────────────────────────────────────────────────────────────────
C_PRIMARY   = colors.HexColor("#1a56db")
C_DARK      = colors.HexColor("#1e2937")
C_GRAY      = colors.HexColor("#6b7280")
C_LIGHT     = colors.HexColor("#f3f4f6")
C_BORDER    = colors.HexColor("#d1d5db")
C_GREEN     = colors.HexColor("#065f46")
C_GREEN_BG  = colors.HexColor("#d1fae5")
C_RED       = colors.HexColor("#991b1b")
C_RED_BG    = colors.HexColor("#fee2e2")
C_YELLOW_BG = colors.HexColor("#fef9c3")
C_CODE_BG   = colors.HexColor("#1e293b")
C_CODE_FG   = colors.HexColor("#e2e8f0")

# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    s = getSampleStyleSheet()

    def ps(name, **kw):
        kw.setdefault("fontName", FONT_NORMAL)
        return ParagraphStyle(name, **kw)

    styles = {
        "cover_title": ps("cover_title",
            fontSize=32, leading=40, textColor=C_PRIMARY,
            fontName=FONT_BOLD, alignment=TA_CENTER, spaceAfter=10),
        "cover_sub": ps("cover_sub",
            fontSize=16, leading=22, textColor=C_DARK,
            alignment=TA_CENTER, spaceAfter=6),
        "cover_meta": ps("cover_meta",
            fontSize=11, leading=16, textColor=C_GRAY,
            alignment=TA_CENTER, spaceAfter=4),

        "h1": ps("h1",
            fontSize=20, leading=26, textColor=C_PRIMARY,
            fontName=FONT_BOLD, spaceBefore=22, spaceAfter=10,
            borderPad=4),
        "h2": ps("h2",
            fontSize=15, leading=20, textColor=C_DARK,
            fontName=FONT_BOLD, spaceBefore=16, spaceAfter=7),
        "h3": ps("h3",
            fontSize=12, leading=17, textColor=C_PRIMARY,
            fontName=FONT_BOLD, spaceBefore=12, spaceAfter=5),

        "body": ps("body",
            fontSize=10, leading=16, textColor=C_DARK,
            alignment=TA_JUSTIFY, spaceAfter=6),
        "body_left": ps("body_left",
            fontSize=10, leading=16, textColor=C_DARK,
            alignment=TA_LEFT, spaceAfter=4),
        "bullet": ps("bullet",
            fontSize=10, leading=15, textColor=C_DARK,
            leftIndent=18, bulletIndent=6, spaceAfter=3),
        "code": ps("code",
            fontSize=8.5, leading=13, textColor=C_CODE_FG,
            backColor=C_CODE_BG, fontName="Courier",
            leftIndent=10, rightIndent=10,
            spaceBefore=6, spaceAfter=6,
            borderPad=8),
        "note": ps("note",
            fontSize=9.5, leading=14, textColor=C_GREEN,
            backColor=C_GREEN_BG, leftIndent=10,
            spaceBefore=4, spaceAfter=4, borderPad=6),
        "warn": ps("warn",
            fontSize=9.5, leading=14, textColor=C_RED,
            backColor=C_RED_BG, leftIndent=10,
            spaceBefore=4, spaceAfter=4, borderPad=6),
        "tip": ps("tip",
            fontSize=9.5, leading=14, textColor=colors.HexColor("#78350f"),
            backColor=C_YELLOW_BG, leftIndent=10,
            spaceBefore=4, spaceAfter=4, borderPad=6),
        "toc_entry": ps("toc_entry",
            fontSize=10, leading=18, textColor=C_DARK,
            leftIndent=0, spaceAfter=2),
        "toc_sub": ps("toc_sub",
            fontSize=9.5, leading=16, textColor=C_GRAY,
            leftIndent=16, spaceAfter=1),
    }
    return styles

ST = build_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
def p(text, style="body"):        return Paragraph(text, ST[style])
def h1(text):                     return p(f"&#9632; {text}", "h1")
def h2(text):                     return p(text, "h2")
def h3(text):                     return p(text, "h3")
def sp(h=6):                      return Spacer(1, h)
def hr():                         return HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=6)
def note(text):                   return p(f"&#10003; {text}", "note")
def warn(text):                   return p(f"&#9888; {text}", "warn")
def tip(text):                    return p(f"&#9654; {text}", "tip")
def code(text):
    safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return Paragraph(safe, ST["code"])
def bullet(text):                 return p(f"&bull; &nbsp;{text}", "bullet")
def sub_bullet(text):             return p(f"&nbsp;&nbsp;&nbsp;&nbsp;&#8227; &nbsp;{text}", "bullet")

def table(data, col_widths, header=True):
    tbl = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style_cmds = [
        ("FONTNAME",    (0,0), (-1,-1), FONT_NORMAL),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("LEADING",     (0,0), (-1,-1), 13),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("GRID",        (0,0), (-1,-1), 0.4, C_BORDER),
        ("BACKGROUND",  (0,0), (-1,0),  C_PRIMARY),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  FONT_BOLD),
        ("FONTSIZE",    (0,0), (-1,0),  9.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING",(0,0), (-1,-1), 7),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    return tbl

def section_box(items):
    """Đóng gói nhóm phần tử để tránh bị cắt trang."""
    return KeepTogether(items)

# ── Số trang ──────────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Header line
    canvas.setStrokeColor(C_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(2*cm, h - 1.5*cm, w - 2*cm, h - 1.5*cm)
    canvas.setFont(FONT_BOLD, 8)
    canvas.setFillColor(C_PRIMARY)
    canvas.drawString(2*cm, h - 1.2*cm, "ITMD — Tài liệu kỹ thuật")
    canvas.setFillColor(C_GRAY)
    canvas.setFont(FONT_NORMAL, 8)
    canvas.drawRightString(w - 2*cm, h - 1.2*cm, "Image-Text Mismatch Detection")
    # Footer
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.5*cm, w - 2*cm, 1.5*cm)
    canvas.setFont(FONT_NORMAL, 8)
    canvas.setFillColor(C_GRAY)
    canvas.drawString(2*cm, 1.1*cm, "Tài liệu nội bộ — Phiên bản 1.0")
    canvas.drawRightString(w - 2*cm, 1.1*cm, f"Trang {doc.page}")
    canvas.restoreState()

def on_first_page(canvas, doc):
    pass  # Trang bìa không có header/footer

# ══════════════════════════════════════════════════════════════════════════════
# NỘI DUNG TÀI LIỆU
# ══════════════════════════════════════════════════════════════════════════════

def build_story():
    story = []

    # ── TRANG BÌA ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 3*cm),
        p("ITMD", "cover_title"),
        p("Image-Text Mismatch Detection", "cover_sub"),
        sp(6),
        HRFlowable(width="60%", thickness=2, color=C_PRIMARY,
                   hAlign="CENTER", spaceAfter=16),
        p("Tài liệu kỹ thuật chuyên sâu", "cover_sub"),
        sp(8),
        p("Phiên bản: 1.0 &nbsp;|&nbsp; Ngôn ngữ: Tiếng Việt", "cover_meta"),
        p("Công nghệ: Python 3.14 · PyTorch 2.11 · CLIP · React 19 · Flask 3", "cover_meta"),
        p("Môi trường: CPU/GPU · Windows/Linux", "cover_meta"),
        Spacer(1, 4*cm),
        HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=10),
        p("Tài liệu này mô tả toàn bộ kiến trúc, luồng xử lý, cách cài đặt và<br/>"
          "vận hành hệ thống phát hiện sự không khớp giữa ảnh và văn bản (ITMD).<br/>"
          "Dành cho developer mới onboarding, nhà đầu tư kỹ thuật và đội vận hành.",
          "cover_meta"),
        PageBreak(),
    ]

    # ── MỤC LỤC ─────────────────────────────────────────────────────────────
    story += [
        p("MỤC LỤC", "h1"),
        hr(),
        sp(4),
    ]
    toc = [
        ("1.", "Tổng quan dự án", ""),
        ("2.", "Kiến trúc tổng thể", ""),
        ("3.", "Cấu trúc thư mục", ""),
        ("4.", "Điểm khởi động hệ thống", ""),
        ("5.", "Hướng dẫn cài đặt và chạy", ""),
        ("6.", "Công nghệ sử dụng", ""),
        ("7.", "Luồng hoạt động chính", ""),
        ("8.", "API và Backend", ""),
        ("9.", "Frontend / UI", ""),
        ("10.", "Cấu hình môi trường", ""),
        ("11.", "Bảo mật", ""),
        ("12.", "Build, Deploy và Vận hành", ""),
        ("13.", "Lỗi thường gặp & Xử lý", ""),
        ("14.", "Hướng dẫn mở rộng dự án", ""),
        ("15.", "Kết luận & Đề xuất", ""),
    ]
    toc_data = [["#", "Nội dung"]]
    for num, title, _ in toc:
        toc_data.append([num, title])
    story.append(table(toc_data, [1.2*cm, 14*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════
    # 1. TỔNG QUAN DỰ ÁN
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("1. Tổng quan dự án"), hr()]

    story += [
        h2("1.1 Tên và mục đích"),
        p("Tên dự án: <b>Image-Text Mismatch Detection (ITMD)</b>"),
        p("ITMD là hệ thống AI phát hiện xem một bức ảnh và đoạn văn bản mô tả (caption) "
          "có <b>khớp nghĩa</b> với nhau hay không. Hệ thống trả về quyết định nhị phân: "
          "<b>MATCH</b> (khớp) hoặc <b>MISMATCH</b> (không khớp), kèm điểm tương đồng "
          "(similarity score) trong khoảng [0, 1]."),
        sp(4),

        h2("1.2 Dự án dành cho ai"),
        bullet("Nhà phát triển phần mềm: cần tích hợp kiểm duyệt ảnh-văn bản vào sản phẩm."),
        bullet("Nền tảng thương mại điện tử: xác thực ảnh sản phẩm khớp với mô tả."),
        bullet("Hệ thống kiểm duyệt nội dung: phát hiện thông tin sai lệch (misinformation)."),
        bullet("Nghiên cứu học thuật: thử nghiệm mô hình vision-language."),
        bullet("Nhà đầu tư / khách hàng kỹ thuật: hiểu năng lực AI của hệ thống."),
        sp(4),

        h2("1.3 Vấn đề được giải quyết"),
        p("Trong thực tế, nhiều hệ thống gặp vấn đề ảnh và caption không khớp: "
          "sản phẩm bị gán nhầm mô tả, tin tức bị ghép ảnh sai, hồ sơ có ảnh giả. "
          "ITMD tự động hóa quá trình kiểm tra này bằng AI thay vì kiểm duyệt thủ công."),
        sp(4),

        h2("1.4 Kết quả đầu ra chính"),
        bullet("Dự đoán: MATCH hoặc MISMATCH"),
        bullet("Điểm tương đồng: số thực [0.0 – 1.0]"),
        bullet("API REST: endpoint POST /api/predict nhận ảnh + caption"),
        bullet("Giao diện web: upload ảnh và nhập caption trực tiếp trên trình duyệt"),
        bullet("Script đánh giá hàng loạt: evaluate.py chạy trên toàn bộ dataset CSV"),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 2. KIẾN TRÚC TỔNG THỂ
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("2. Kiến trúc tổng thể"), hr()]

    story += [
        h2("2.1 Mô hình kiến trúc"),
        p("Hệ thống theo mô hình <b>Client–Server</b> với 3 tầng độc lập:"),
        bullet("<b>Frontend</b> (React + Vite): giao diện người dùng chạy trên trình duyệt."),
        bullet("<b>Backend</b> (Flask API): nhận request, chạy model AI, trả kết quả."),
        bullet("<b>AI Core</b> (PyTorch + CLIP): mô hình học sâu xử lý ảnh và văn bản."),
        sp(6),

        h2("2.2 Sơ đồ luồng hệ thống"),
        code("""
[Người dùng]
     |
     | Upload ảnh + nhập caption
     v
[React Frontend  :  localhost:5173]
     |
     | POST /api/predict  (multipart/form-data)
     | imageFile + caption
     v
[Flask Backend  :  localhost:5000]
     |
     | 1. Validate file (type, size)
     | 2. Lưu file tạm  (UUID.ext)
     | 3. Gọi predict()
     v
[AI Core — predict.py]
     |
     | 4. Load ảnh → PIL Image → RGB
     | 5. Tokenize caption → input_ids
     | 6. CLIP Processor → pixel_values
     v
[ITMDCLIPModel — clip_model.py]
     |
     | 7a. Nếu có checkpoint:
     |     → Classifier head → sigmoid → prob
     | 7b. Nếu không có checkpoint:
     |     → CLIP embeddings → cosine similarity
     v
[Kết quả]
     |
     | 8. prob >= threshold → MATCH / MISMATCH
     | 9. Xóa file tạm
     v
[Flask → JSON response]
     { isMatch, simScore }
     |
     v
[React → Hiển thị kết quả]
        """),
        sp(6),

        h2("2.3 Vai trò các thành phần"),
    ]
    arch_data = [
        ["Thành phần", "File chính", "Vai trò"],
        ["Config",        "configs/config.py",          "Quản lý tham số toàn hệ thống"],
        ["AI Model",      "models/clip_model.py",        "CLIP + Classifier Head"],
        ["Dataset",       "dataset/dataset_loader.py",   "Load & augment dữ liệu train"],
        ["Training",      "training/train.py",           "Huấn luyện mô hình"],
        ["Inference",     "inference/predict.py",        "Dự đoán đơn lẻ"],
        ["Evaluation",    "evaluate.py",                 "Đánh giá trên dataset CSV"],
        ["Data Prep",     "data/prepare_data.py",        "Tạo captions.csv cho training"],
        ["Flask API",     "app.py",                      "REST API server port 5000"],
        ["React UI",      "frontend/src/App.jsx",        "Giao diện người dùng"],
        ["API Service",   "frontend/src/services/predictService.js", "Gọi API từ frontend"],
        ["Utils",         "utils/similarity.py",         "Tính cosine similarity"],
        ["Metrics",       "utils/metrics.py",            "Accuracy, F1, AUC-ROC"],
        ["Visualize",     "visualization/visualize.py",  "Confusion matrix, ROC curve"],
    ]
    story.append(table(arch_data, [3.5*cm, 5.5*cm, 7.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════
    # 3. CẤU TRÚC THƯ MỤC
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("3. Cấu trúc thư mục dự án"), hr()]

    story += [
        code("""
Image-Text-Mismatch-Detection/
|
|-- configs/
|   `-- config.py            # Tham so toan he thong (model, threshold, LR...)
|
|-- models/
|   `-- clip_model.py        # Kien truc mang: CLIP + Classifier Head
|
|-- dataset/
|   `-- dataset_loader.py    # PyTorch Dataset: load CSV, augment, tokenize
|
|-- training/
|   `-- train.py             # Pipeline huan luyen day du
|
|-- inference/
|   `-- predict.py           # Du doan cho 1 cap anh-caption
|
|-- utils/
|   |-- similarity.py        # Tinh cosine similarity
|   `-- metrics.py           # Accuracy, Precision, Recall, F1, AUC-ROC
|
|-- visualization/
|   `-- visualize.py         # Ve confusion matrix, ROC curve, distribution
|
|-- data/
|   |-- images/              # Thu muc chua anh training
|   |-- captions.csv         # Du lieu: image_path, caption, label
|   `-- prepare_data.py      # Tao captions.csv tu anh local hoac COCO
|
|-- frontend/
|   |-- src/
|   |   |-- App.jsx          # Component goc cua React app
|   |   |-- main.jsx         # Entry point React (createRoot)
|   |   |-- App.css          # Global CSS styles
|   |   |-- index.css        # Base CSS reset
|   |   `-- services/
|   |       `-- predictService.js  # Ham goi API /api/predict
|   |-- package.json         # Dependencies: React 19, Vite 8
|   `-- vite.config.js       # Cau hinh build tool
|
|-- outputs/                 # Ket qua training: best_model.pth, bieu do
|-- app.py                   # Flask API server
|-- evaluate.py              # Script danh gia model tren CSV
|-- main.py                  # Demo pipeline
|-- requirements.txt         # Python dependencies
`-- generate_docs.py         # Script tao tai lieu PDF nay
        """),
        sp(6),
    ]

    dir_data = [
        ["Thư mục/File", "Khi muốn sửa..."],
        ["configs/config.py",     "Đổi model, ngưỡng, learning rate, số epoch"],
        ["models/clip_model.py",  "Thay đổi kiến trúc mạng, cách kết hợp embedding"],
        ["training/train.py",     "Thêm kỹ thuật train, sửa optimizer, scheduler"],
        ["dataset/dataset_loader.py", "Thêm augmentation mới, đổi format dữ liệu"],
        ["inference/predict.py",  "Sửa logic dự đoán, thêm post-processing"],
        ["app.py",                "Thêm API endpoint, sửa validation"],
        ["frontend/src/App.jsx",  "Sửa giao diện, thêm tính năng UI"],
        ["data/prepare_data.py",  "Đổi cách tạo dữ liệu MATCH/MISMATCH"],
    ]
    story.append(table(dir_data, [6*cm, 10.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════
    # 4. ĐIỂM KHỞI ĐỘNG
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("4. Điểm khởi động hệ thống"), hr()]

    story += [
        h2("4.1 Backend (Flask API) — app.py"),
        p("Đây là entry point chính của hệ thống phục vụ AI. Khi chạy:"),
        code("python app.py"),
        p("Các bước xảy ra:"),
        bullet("<b>Bước 1:</b> Import Config, ITMDCLIPModel, predict() từ các module."),
        bullet("<b>Bước 2:</b> Tạo Flask app, bật CORS (cho phép frontend gọi API)."),
        bullet("<b>Bước 3:</b> Khởi tạo ITMDCLIPModel → tải CLIP weights từ HuggingFace."),
        bullet("<b>Bước 4:</b> Kiểm tra outputs/best_model.pth → load nếu tồn tại."),
        bullet("<b>Bước 5:</b> Đăng ký route POST /api/predict."),
        bullet("<b>Bước 6:</b> Server lắng nghe tại <b>http://localhost:5000</b>."),
        note("Lần đầu chạy: CLIP model (~600MB) sẽ tự tải về từ HuggingFace."),
        sp(6),

        h2("4.2 Frontend (React + Vite)"),
        p("Entry point: <b>frontend/src/main.jsx</b>. Khởi động bằng:"),
        code("cd frontend\nnpm install\nnpm run dev"),
        p("Vite dev server chạy tại <b>http://localhost:5173</b>. "
          "main.jsx gọi <b>createRoot()</b> mount App component vào DOM. "
          "App.jsx render toàn bộ giao diện bao gồm header, hero section, form upload."),
        sp(6),

        h2("4.3 Training Pipeline — training/train.py"),
        code("python training/train.py\npython training/train.py --resume  # Tiep tuc tu checkpoint"),
        p("Khi chạy: load dataset → tạo DataLoader → khởi tạo optimizer/scheduler "
          "→ vòng lặp epoch → lưu best_model.pth → vẽ biểu đồ."),
        sp(6),

        h2("4.4 Demo Pipeline — main.py"),
        code("python main.py"),
        p("Kiểm tra môi trường, tạo ảnh mẫu, chạy 4 test case và in hướng dẫn sử dụng."),
        sp(6),

        h2("4.5 Evaluation — evaluate.py"),
        code("python evaluate.py --data data/captions.csv --save-predictions"),
        p("Đánh giá toàn bộ dataset, tính metrics, vẽ biểu đồ, lưu kết quả vào outputs/eval/."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 5. HƯỚNG DẪN CÀI ĐẶT
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("5. Hướng dẫn cài đặt và chạy dự án"), hr()]

    story += [
        h2("5.1 Yêu cầu môi trường"),
    ]
    req_data = [
        ["Thành phần", "Phiên bản", "Ghi chú"],
        ["Python",       "3.8 – 3.14",  "3.14 đã được kiểm tra với torch 2.11"],
        ["PyTorch",      ">= 1.13",     "2.11.0 khuyến nghị. GPU tùy chọn"],
        ["Node.js",      ">= 18",       "Cần để chạy frontend React/Vite"],
        ["RAM",          ">= 4 GB",     "8 GB khuyến nghị khi chạy CLIP"],
        ["Disk",         ">= 3 GB",     "CLIP model ~600MB, M-CLIP ~2GB"],
        ["GPU",          "Tùy chọn",    "CUDA 11+ nếu có, tăng tốc train 5-10x"],
    ]
    story.append(table(req_data, [3.5*cm, 3*cm, 10*cm]))
    story += [sp(6)]

    story += [
        h2("5.2 Cài đặt từng bước"),
        h3("Bước 1: Lấy source code"),
        code("git clone <repo-url>\ncd Image-Text-Mismatch-Detection"),
        h3("Bước 2: Cài Python dependencies"),
        code("pip install -r requirements.txt"),
        note("requirements.txt đã bao gồm: torch, transformers, Flask, scikit-learn, pandas, matplotlib..."),
        h3("Bước 3: Cài M-CLIP (hỗ trợ tiếng Việt)"),
        code("pip install multilingual-clip ftfy"),
        tip("Bỏ qua bước này nếu chỉ dùng tiếng Anh. "
            "Hệ thống tự fallback về CLIP tiếng Anh."),
        h3("Bước 4: Cài frontend dependencies"),
        code("cd frontend\nnpm install\ncd .."),
        h3("Bước 5: Chuẩn bị dữ liệu training"),
        code(
            "# Tao anh mau va captions.csv tu anh local\n"
            "python data/prepare_data.py\n\n"
            "# Hoac neu da co CSV chi chua MATCH:\n"
            "python data/prepare_data.py --from-csv data/captions.csv"
        ),
        h3("Bước 6: Train model"),
        code("python training/train.py"),
        p("Kết quả: <b>outputs/best_model.pth</b>, "
          "<b>outputs/confusion_matrix.png</b>, <b>outputs/roc_curve.png</b>"),
        h3("Bước 7: Khởi động hệ thống"),
        code(
            "# Terminal 1: Backend\n"
            "python app.py\n\n"
            "# Terminal 2: Frontend\n"
            "cd frontend && npm run dev"
        ),
        p("Truy cập: <b>http://localhost:5173</b> — Giao diện web"),
        p("API trực tiếp: <b>http://localhost:5000/api/predict</b>"),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 6. CÔNG NGHỆ SỬ DỤNG
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("6. Công nghệ sử dụng"), hr()]

    tech_data = [
        ["Thành phần",        "Công nghệ",                     "Vai trò",                           "File liên quan"],
        ["AI Model",          "CLIP (ViT-Base-Patch32)",       "Trích xuất embedding ảnh & text",   "models/clip_model.py"],
        ["Đa ngôn ngữ",       "M-CLIP XLM-Roberta",           "Hỗ trợ tiếng Việt + 100 ngôn ngữ", "models/clip_model.py"],
        ["Deep Learning",     "PyTorch 2.11",                  "Train, inference, tensor ops",      "training/, models/"],
        ["Transformers",      "HuggingFace 5.8",               "Load CLIP, tokenizer",              "models/clip_model.py"],
        ["Data Augment",      "torchvision",                   "RandomFlip, ColorJitter, Crop",     "dataset/dataset_loader.py"],
        ["Metrics",           "scikit-learn",                  "F1, AUC-ROC, confusion matrix",     "utils/metrics.py"],
        ["Visualization",     "matplotlib + seaborn",          "Vẽ biểu đồ kết quả",               "visualization/visualize.py"],
        ["Data handling",     "pandas",                        "Đọc/ghi CSV",                       "dataset/, data/"],
        ["Image handling",    "Pillow (PIL)",                  "Đọc, convert ảnh RGB",              "dataset/, inference/"],
        ["Backend",           "Flask 3.1",                     "REST API server port 5000",         "app.py"],
        ["CORS",              "flask-cors 6.0",                "Cho phép React gọi API",            "app.py"],
        ["Frontend",          "React 19.2",                    "UI component framework",            "frontend/src/App.jsx"],
        ["Build tool",        "Vite 8.0",                      "Dev server + production build",     "frontend/vite.config.js"],
        ["HTTP Client",       "Fetch API (native)",            "Gọi /api/predict từ frontend",      "frontend/src/services/predictService.js"],
        ["Progress bar",      "tqdm",                          "Thanh tiến trình training",         "training/train.py"],
        ["File upload",       "Werkzeug",                      "secure_filename()",                 "app.py"],
    ]
    story.append(table(tech_data, [2.8*cm, 3.5*cm, 4.5*cm, 5.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════
    # 7. LUỒNG HOẠT ĐỘNG
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("7. Luồng hoạt động chính"), hr()]

    story += [
        h2("7.1 Luồng Inference (Dự đoán đơn lẻ qua API)"),
        p("Đây là luồng quan trọng nhất của hệ thống production:"),
        sp(4),
    ]

    flow_api_data = [
        ["Bước", "Diễn giải", "File xử lý", "Hàm/Class"],
        ["1",  "User upload ảnh + nhập caption trên web",          "App.jsx",          "handleCheck()"],
        ["2",  "Validate: phải đăng nhập, ảnh và caption không rỗng", "App.jsx",       "validateInput()"],
        ["3",  "Tạo FormData, POST tới http://127.0.0.1:5000/api/predict", "predictService.js", "predictImageTextMismatch()"],
        ["4",  "Flask nhận request, kiểm tra imageFile + caption",  "app.py",           "api_predict()"],
        ["5",  "Validate file extension (png/jpg/jpeg/webp...)",    "app.py",           "allowed_file()"],
        ["6",  "Lưu file tạm với UUID unique (thread-safe)",        "app.py",           "uuid.uuid4()"],
        ["7",  "Gọi predict(filepath, caption, model, checkpoint_loaded)", "inference/predict.py", "predict()"],
        ["8",  "Đọc ảnh: PIL Image.open().convert('RGB')",          "inference/predict.py", "predict()"],
        ["9",  "CLIP processor tokenize text + resize ảnh",         "inference/predict.py", "processor()"],
        ["10", "Nếu checkpoint: chạy classifier head → sigmoid",    "models/clip_model.py",  "forward()"],
        ["11", "Nếu không checkpoint: cosine similarity embeddings", "utils/similarity.py", "compute_similarity()"],
        ["12", "prob >= threshold → MATCH / MISMATCH",              "inference/predict.py", "predict()"],
        ["13", "Xóa file tạm",                                      "app.py",           "os.remove()"],
        ["14", "Trả JSON: {isMatch, simScore}",                     "app.py",           "jsonify()"],
        ["15", "React hiển thị badge MATCH (xanh) hoặc MISMATCH (đỏ)", "App.jsx",      "result.isMatch"],
    ]
    story.append(table(flow_api_data, [0.8*cm, 5.5*cm, 4.2*cm, 4*cm]))
    story += [sp(8)]

    story += [
        h2("7.2 Luồng Training (Huấn luyện mô hình)"),
        sp(4),
    ]
    flow_train_data = [
        ["Bước", "Diễn giải", "File"],
        ["1",  "Đọc captions.csv, normalize caption, check ảnh tồn tại", "dataset_loader.py"],
        ["2",  "Chia train/val (90%/10%), seed cố định = 42",           "train.py"],
        ["3",  "Train set: áp dụng augmentation (flip, jitter, crop)",  "dataset_loader.py"],
        ["4",  "Tạo batch negatives nếu ENABLE_BATCH_NEGATIVES=True",   "train.py"],
        ["5",  "Forward pass qua ITMDCLIPModel → logits",               "clip_model.py"],
        ["6",  "BCEWithLogitsLoss (có pos_weight cân bằng class)",      "train.py"],
        ["7",  "AMP autocast (nếu GPU), backward, gradient clip 1.0",   "train.py"],
        ["8",  "AdamW step: classifier LR=2e-4, CLIP fine-tune LR=5e-6","train.py"],
        ["9",  "Cuối epoch: validation, tính metrics + AUC-ROC",        "train.py + metrics.py"],
        ["10", "Nếu val_loss cải thiện: lưu best_model.pth",            "train.py"],
        ["11", "Nếu không cải thiện 5 epoch liên tiếp: early stopping", "train.py"],
        ["12", "Sau training: tìm ngưỡng tối ưu (Youden's J)",          "train.py"],
        ["13", "Vẽ confusion matrix, ROC curve, similarity distribution","visualize.py"],
    ]
    story.append(table(flow_train_data, [0.8*cm, 9.5*cm, 6.2*cm]))
    story += [sp(8)]

    story += [
        h2("7.3 Luồng đăng ký / đăng nhập (Frontend)"),
        p("Hệ thống authentication của frontend là <b>client-side only</b>, "
          "lưu trong localStorage. <b>Không có database backend</b>."),
        bullet("Đăng ký: tạo account object {name, email, password} lưu vào localStorage[itmd-auth-accounts]."),
        bullet("Đăng nhập: tìm email trong accounts[], so sánh password plain text."),
        bullet("Session: lưu {name, email} vào localStorage[itmd-auth-user]."),
        warn("Mật khẩu lưu plain text trong localStorage — chỉ phù hợp cho demo. "
             "Cần backend auth thực sự cho production."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 8. API VÀ BACKEND
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("8. API và Backend"), hr()]

    story += [
        h2("8.1 Danh sách API Endpoints"),
    ]
    api_data = [
        ["Method", "Endpoint",       "Mô tả",              "Request",                         "Response"],
        ["POST",   "/api/predict",   "Dự đoán Match/Mismatch", "multipart: imageFile, caption", '{"isMatch": bool, "simScore": float}'],
    ]
    story.append(table(api_data, [1.5*cm, 3*cm, 4*cm, 5*cm, 3*cm]))
    story += [sp(6)]

    story += [
        h2("8.2 Chi tiết endpoint POST /api/predict"),
        h3("Request"),
        bullet("Content-Type: multipart/form-data"),
        bullet("imageFile: file ảnh (PNG, JPG, JPEG, WEBP, GIF, BMP — tối đa 16MB)"),
        bullet("caption: chuỗi văn bản mô tả ảnh"),
        h3("Response thành công (200)"),
        code('{\n  "isMatch": true,\n  "simScore": 0.7234,\n  "suggestedCaption": ""\n}'),
        h3("Response lỗi"),
        code('{ "error": "Missing imageFile or caption" }  // 400\n'
             '{ "error": "File type not supported" }       // 400\n'
             '{ "error": "File too large..." }             // 413\n'
             '{ "error": "..." }                           // 500'),
        h3("Validation trong app.py"),
        bullet("Kiểm tra có imageFile và caption trong request."),
        bullet("Kiểm tra extension file hợp lệ (ALLOWED_EXTENSIONS)."),
        bullet("Giới hạn kích thước: MAX_CONTENT_LENGTH = 16MB."),
        bullet("Filename thread-safe bằng uuid.uuid4()."),
        bullet("Xóa file tạm sau mỗi request (trong finally block)."),
        sp(6),

        h2("8.3 Model được load khi Flask khởi động"),
        p("Khi <b>python app.py</b> chạy, model được load <b>một lần duy nhất</b> "
          "vào bộ nhớ (biến global), không reload mỗi request — giúp API nhanh hơn nhiều."),
        code(
            "model = ITMDCLIPModel(Config.MODEL_NAME).to(device)\n"
            "model.eval()\n"
            "# Load checkpoint neu co\n"
            "if os.path.exists(checkpoint_path):\n"
            "    model.load_state_dict(torch.load(checkpoint_path, map_location=device))\n"
            "    checkpoint_loaded = True"
        ),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 9. FRONTEND / UI
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("9. Frontend / UI"), hr()]

    story += [
        h2("9.1 Tổng quan Frontend"),
        bullet("Framework: <b>React 19.2.5</b> (Hooks, functional components)"),
        bullet("Build tool: <b>Vite 8.0</b> (dev server HMR, production build)"),
        bullet("State management: <b>useState / useEffect</b> (không dùng Redux)"),
        bullet("HTTP: <b>Fetch API</b> native (không dùng Axios)"),
        bullet("Styling: <b>Custom CSS</b> (App.css, index.css)"),
        sp(6),

        h2("9.2 Cấu trúc Component"),
    ]
    comp_data = [
        ["Component/File",          "Vai trò",                                           "State quan trọng"],
        ["App.jsx",                 "Root component — chứa toàn bộ logic",              "authUser, imageFile, caption, result, isLoading"],
        ["Header (.topbar)",        "Logo, nav links, auth buttons/user chip",           "authUser"],
        ["Hero Section (#hero)",    "Upload form + result display + insight panel",      "imageFile, caption, errors, result"],
        ["Feature Section (#features)", "Mô tả tính năng AI detector",                 "—"],
        ["Steps Section (#how-it-works)", "3 bước hướng dẫn sử dụng",                 "—"],
        ["Auth Modal (.auth-modal)", "Popup đăng nhập / đăng ký",                      "authMode, authForm, authError"],
        ["predictService.js",       "Hàm gọi API — tách biệt khỏi UI logic",          "—"],
    ]
    story.append(table(comp_data, [4.5*cm, 5.5*cm, 6.5*cm]))
    story += [sp(6)]

    story += [
        h2("9.3 Luồng xử lý UI khi người dùng kiểm tra"),
        bullet("<b>1.</b> User chọn ảnh → handleImageChange() → tạo blob URL preview → revoke URL cũ."),
        bullet("<b>2.</b> User nhập caption → handleCaptionChange() → clear error."),
        bullet("<b>3.</b> User bấm 'Kiểm tra' → handleCheck() chạy:"),
        sub_bullet("Nếu chưa đăng nhập → mở Auth Modal với thông báo yêu cầu login."),
        sub_bullet("validateInput(): kiểm tra imageFile và caption không rỗng."),
        sub_bullet("setIsLoading(true) → hiển thị 'Đang phân tích ảnh...'"),
        sub_bullet("Gọi predictImageTextMismatch() — await fetch() tới Flask."),
        sub_bullet("setResult(prediction) → render badge MATCH (xanh) hoặc MISMATCH (đỏ)."),
        bullet("<b>4.</b> Nếu API lỗi → catch block → result.isMatch = false (fallback)."),
        sp(6),

        h2("9.4 Authentication Frontend"),
        p("Authentication là <b>client-side only</b>, không có backend:"),
        bullet("Accounts lưu trong <b>localStorage['itmd-auth-accounts']</b> dạng JSON array."),
        bullet("Session lưu trong <b>localStorage['itmd-auth-user']</b>."),
        bullet("useState + useEffect sync với localStorage mỗi khi state thay đổi."),
        warn("Đây là authentication demo. Không phù hợp production vì mật khẩu plain text trong localStorage."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 10. CẤU HÌNH MÔI TRƯỜNG
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("10. Cấu hình môi trường"), hr()]

    story += [
        h2("10.1 File configs/config.py — Tham số quan trọng"),
    ]
    cfg_data = [
        ["Tham số",                 "Mặc định",                                "Ý nghĩa",                                "Ảnh hưởng"],
        ["MODEL_NAME",              "M-CLIP/XLM-Roberta-Large-Vit-L-14",       "Tên model CLIP trên HuggingFace",        "Toàn hệ thống"],
        ["DEVICE",                  "auto (cuda/cpu)",                         "Thiết bị tính toán",                     "Train + Inference"],
        ["SIMILARITY_THRESHOLD",    "0.25",                                    "Ngưỡng cosine similarity (khi không train)", "inference/predict.py"],
        ["CLASSIFIER_THRESHOLD",    "0.5",                                     "Ngưỡng sigmoid classifier",             "inference/predict.py"],
        ["USE_CLASSIFIER_IN_INFERENCE", "True",                                "Dùng classifier hay cosine similarity", "inference/predict.py"],
        ["BATCH_SIZE",              "16",                                      "Kích thước batch training",             "training/train.py"],
        ["LEARNING_RATE",           "2e-4",                                    "LR cho classifier head",                "training/train.py"],
        ["CLIP_FINETUNE_LR",        "5e-6",                                    "LR cho CLIP layers mở băng",            "training/train.py"],
        ["NUM_EPOCHS",              "30",                                      "Số vòng lặp training tối đa",           "training/train.py"],
        ["NUM_UNFREEZE_LAYERS",     "2",                                       "Số CLIP block cuối được fine-tune",     "models/clip_model.py"],
        ["EARLY_STOPPING_PATIENCE", "5",                                       "Dừng sớm sau N epoch không cải thiện", "training/train.py"],
        ["ENABLE_BATCH_NEGATIVES",  "True",                                    "Tạo MISMATCH từ batch",                 "training/train.py"],
        ["USE_AMP",                 "True",                                    "Mixed precision (GPU only)",            "training/train.py"],
        ["VAL_SPLIT",               "0.1",                                     "Tỷ lệ dữ liệu validation",             "training/train.py"],
        ["SEED",                    "42",                                      "Random seed tái tạo kết quả",           "training/train.py"],
    ]
    story.append(table(cfg_data, [4.5*cm, 4*cm, 4.5*cm, 3.5*cm]))
    story += [sp(6)]

    story += [
        h2("10.2 Biến cần thay đổi theo môi trường"),
        tip("Không cần file .env vì không có secret key. "
            "Tất cả config nằm trong configs/config.py."),
        bullet("Đổi <b>MODEL_NAME</b> nếu muốn dùng CLIP khác (tiết kiệm RAM hoặc chính xác hơn)."),
        bullet("Tăng <b>BATCH_SIZE</b> nếu có GPU nhiều RAM (giảm nếu Out of Memory)."),
        bullet("Đổi <b>CLASSIFIER_THRESHOLD</b> theo ngưỡng tối ưu mà evaluate.py gợi ý."),
        bullet("Tắt <b>USE_AMP</b> nếu gặp lỗi trên CPU."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 11. BẢO MẬT
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("11. Bảo mật"), hr()]

    story += [
        h2("11.1 Điểm bảo mật đã có"),
        bullet("<b>File type validation:</b> app.py chỉ chấp nhận png/jpg/jpeg/webp/gif/bmp."),
        bullet("<b>File size limit:</b> 16MB (app.config['MAX_CONTENT_LENGTH'])."),
        bullet("<b>Thread-safe upload:</b> UUID filename tránh race condition và path traversal."),
        bullet("<b>Auto cleanup:</b> File tạm bị xóa sau mỗi request (finally block)."),
        bullet("<b>CORS:</b> flask-cors bật sẵn, cần restrict origin trong production."),
        sp(6),

        h2("11.2 Rủi ro bảo mật hiện tại"),
    ]
    sec_data = [
        ["Rủi ro",                          "Mức độ",   "Chi tiết",                                         "Khuyến nghị"],
        ["Mật khẩu plain text localStorage", "CAO",     "Frontend lưu password không hash trong localStorage", "Thêm backend auth + bcrypt"],
        ["Không có rate limiting",           "TRUNG BÌNH", "API /api/predict có thể bị spam",               "Thêm Flask-Limiter"],
        ["CORS mở toàn bộ",                  "TRUNG BÌNH", "flask-cors(app) cho phép mọi origin",           "Giới hạn origins trong production"],
        ["Không có HTTPS",                   "TRUNG BÌNH", "Chạy HTTP local, dễ bị MITM",                  "Dùng HTTPS + cert khi deploy"],
        ["Model weights không ký",           "THẤP",    "best_model.pth không có checksum",                  "Thêm SHA256 verification"],
        ["Debug mode Flask",                 "THẤP",    "app.run(debug=True) lộ traceback",                 "debug=False trong production"],
    ]
    story.append(table(sec_data, [4*cm, 2*cm, 5.5*cm, 5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════
    # 12. BUILD, DEPLOY, VẬN HÀNH
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("12. Build, Deploy và Vận hành"), hr()]

    story += [
        h2("12.1 Development"),
        code(
            "# Terminal 1 — Backend\n"
            "python app.py\n"
            "# Chay tai: http://localhost:5000\n\n"
            "# Terminal 2 — Frontend\n"
            "cd frontend && npm run dev\n"
            "# Chay tai: http://localhost:5173"
        ),
        sp(6),
        h2("12.2 Production Build"),
        code(
            "# Build frontend\n"
            "cd frontend && npm run build\n"
            "# Output: frontend/dist/\n\n"
            "# Phuc vu static files qua Flask (tuy chon)\n"
            "# Hoac deploy frontend len Vercel/Netlify rieng"
        ),
        sp(6),
        h2("12.3 Gợi ý Deploy"),
    ]
    deploy_data = [
        ["Thành phần",    "Nền tảng gợi ý",           "Ghi chú"],
        ["Backend Flask", "Render / Railway / VPS",    "Dùng gunicorn thay flask dev server"],
        ["Frontend",      "Vercel / Netlify",           "npm run build → deploy dist/"],
        ["Model weights", "HuggingFace Model Hub / S3", "Lưu best_model.pth ổn định"],
    ]
    story.append(table(deploy_data, [4*cm, 5*cm, 7.5*cm]))
    story += [
        sp(6),
        h2("12.4 Lệnh production Backend"),
        code(
            "pip install gunicorn\n"
            "gunicorn -w 4 -b 0.0.0.0:5000 app:app"
        ),
        note("Tắt debug=True trong app.py trước khi deploy production."),
        sp(6),
        h2("12.5 Monitoring & Logs"),
        bullet("Flask log: stdout/stderr khi chạy python app.py."),
        bullet("Training log: in trực tiếp ra terminal, dùng tqdm progress bar."),
        bullet("Kết quả train: outputs/confusion_matrix.png, outputs/roc_curve.png, outputs/eval_metrics.txt."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 13. LỖI THƯỜNG GẶP
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("13. Lỗi thường gặp và cách xử lý"), hr()]

    err_data = [
        ["Lỗi",                              "Nguyên nhân",                              "Cách sửa"],
        ["ModuleNotFoundError: torch",        "Chưa cài requirements",                   "pip install -r requirements.txt"],
        ["ModuleNotFoundError: multilingual_clip", "Chưa cài M-CLIP",                  "pip install multilingual-clip ftfy"],
        ["CLIP model tải mãi không xong",     "Lần đầu tải ~600MB",                     "Chờ hoặc set HF_HOME env var"],
        ["RuntimeError: out of memory",       "GPU RAM không đủ",                        "Giảm BATCH_SIZE trong config.py"],
        ["Dataset is empty",                  "Thiếu captions.csv",                      "python data/prepare_data.py"],
        ["Error loading image [SKIP]",         "Ảnh trong CSV không tồn tại trong data/images/", "Kiểm tra lại đường dẫn ảnh"],
        ["best_model.pth not found",          "Chưa train model",                        "python training/train.py"],
        ["API 400: Missing imageFile",        "Frontend gửi sai field name",             "Kiểm tra FormData key = 'imageFile'"],
        ["API 413: File too large",           "Ảnh > 16MB",                              "Nén ảnh hoặc tăng MAX_CONTENT_LENGTH"],
        ["CORS error từ frontend",            "Backend chưa chạy hoặc sai port",         "Kiểm tra Flask chạy port 5000"],
        ["npm run dev lỗi",                   "Chưa npm install",                        "cd frontend && npm install"],
        ["NaN loss trong training",           "Learning rate quá cao hoặc dữ liệu lỗi", "Giảm LR, kiểm tra CSV không có null"],
        ["AUC-ROC: N/A",                     "Chỉ có 1 class trong val set",             "Tăng dữ liệu, đảm bảo cân bằng label"],
    ]
    story.append(table(err_data, [5*cm, 4.5*cm, 7*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════
    # 14. HƯỚNG DẪN MỞ RỘNG
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("14. Hướng dẫn mở rộng dự án"), hr()]

    story += [
        h2("14.1 Thêm API endpoint mới"),
        bullet("Mở <b>app.py</b>, thêm route mới:"),
        code(
            "@app.route('/api/batch_predict', methods=['POST'])\n"
            "def batch_predict():\n"
            "    # Xu ly nhieu cap anh-caption mot luc\n"
            "    ..."
        ),
        sp(6),

        h2("14.2 Thêm model CLIP mới"),
        bullet("Mở <b>configs/config.py</b>, đổi MODEL_NAME:"),
        code('MODEL_NAME = "openai/clip-vit-large-patch14"  # Chinh xac hon'),
        bullet("Cập nhật <b>models/clip_model.py</b> nếu embed_dim khác 512."),
        sp(6),

        h2("14.3 Thêm kỹ thuật augmentation mới"),
        bullet("Mở <b>dataset/dataset_loader.py</b>, sửa hàm _apply_augmentation():"),
        code(
            "aug = transforms.Compose([\n"
            "    transforms.RandomHorizontalFlip(p=0.5),\n"
            "    transforms.RandomRotation(degrees=10),   # Them moi\n"
            "    transforms.GaussianBlur(kernel_size=3),  # Them moi\n"
            "    transforms.ColorJitter(...),\n"
            "])"
        ),
        sp(6),

        h2("14.4 Thêm metric đánh giá mới"),
        bullet("Mở <b>utils/metrics.py</b>, thêm vào hàm calculate_metrics():"),
        code(
            "from sklearn.metrics import matthews_corrcoef\n"
            "metrics['mcc'] = matthews_corrcoef(y_true, y_pred)"
        ),
        sp(6),

        h2("14.5 Thêm tính năng UI mới"),
        bullet("Mở <b>frontend/src/App.jsx</b>, thêm state mới và render component."),
        bullet("Tạo component mới trong <b>frontend/src/components/</b> (thư mục cần tạo)."),
        bullet("Nếu cần gọi API mới, thêm hàm trong <b>frontend/src/services/predictService.js</b>."),
        sp(6),

        h2("14.6 Thêm hỗ trợ video/batch upload"),
        bullet("Backend: thêm endpoint /api/batch nhận array files."),
        bullet("Dùng <b>utils/similarity.py:compute_batch_similarity()</b> cho xử lý song song."),
        bullet("Frontend: sửa handleImageChange() chấp nhận multiple files."),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 15. KẾT LUẬN
    # ══════════════════════════════════════════════════════════════════════
    story += [h1("15. Kết luận & Đề xuất"), hr()]

    story += [
        h2("15.1 Tóm tắt hệ thống"),
        p("ITMD là hệ thống AI end-to-end phát hiện sự không khớp giữa ảnh và văn bản, "
          "được xây dựng trên nền tảng CLIP của OpenAI với nhiều cải tiến về kiến trúc và huấn luyện. "
          "Hệ thống gồm 3 tầng độc lập: AI Core (PyTorch/CLIP), REST API (Flask), và UI (React/Vite)."),
        sp(4),

        h2("15.2 Các thành phần quan trọng nhất"),
    ]
    key_data = [
        ["Thành phần",              "Tầm quan trọng", "Lý do"],
        ["configs/config.py",       "Rất cao",        "Điều khiển toàn bộ hành vi hệ thống"],
        ["models/clip_model.py",    "Rất cao",        "Trái tim AI của dự án"],
        ["training/train.py",       "Cao",            "Chất lượng model phụ thuộc vào pipeline train"],
        ["inference/predict.py",    "Cao",            "Được gọi mỗi request production"],
        ["app.py",                  "Cao",            "Entry point production backend"],
        ["dataset/dataset_loader.py","Trung bình",    "Chất lượng dữ liệu ảnh hưởng train"],
    ]
    story.append(table(key_data, [5*cm, 3*cm, 8.5*cm]))
    story += [sp(6)]

    story += [
        h2("15.3 Roadmap cải thiện đề xuất"),
        bullet("<b>Ngắn hạn:</b> Thêm backend authentication thực sự (JWT + database)."),
        bullet("<b>Ngắn hạn:</b> Thêm rate limiting cho API (Flask-Limiter)."),
        bullet("<b>Ngắn hạn:</b> Sử dụng đủ dữ liệu tiếng Việt để train (>500 cặp)."),
        bullet("<b>Trung hạn:</b> Deploy lên cloud (Backend: Render, Frontend: Vercel)."),
        bullet("<b>Trung hạn:</b> Thêm lịch sử kiểm tra lưu server-side."),
        bullet("<b>Dài hạn:</b> Fine-tune M-CLIP trên corpus tiếng Việt chuyên biệt."),
        bullet("<b>Dài hạn:</b> Hỗ trợ batch prediction và video frame analysis."),
        sp(8),
        HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceAfter=8),
        p("Tài liệu này được tạo tự động bởi <b>generate_docs.py</b>. "
          "Phiên bản 1.0 — Mọi thắc mắc về kiến trúc, vui lòng tham khảo "
          "trực tiếp source code tại các file đã được dẫn chiếu trong tài liệu.",
          "body"),
    ]

    return story


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out_path = os.path.join(os.path.expanduser("~"), "Desktop", "ITMD_Technical_Documentation.pdf")

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2*cm,
        title="ITMD — Tài liệu kỹ thuật",
        author="AI Technical Writer",
        subject="Image-Text Mismatch Detection",
    )

    story = build_story()

    doc.build(
        story,
        onFirstPage=on_first_page,
        onLaterPages=on_page,
    )

    size_kb = os.path.getsize(out_path) // 1024
    print(f"\nPDF da tao thanh cong!")
    print(f"Duong dan: {out_path}")
    print(f"Kich thuoc: {size_kb} KB")
