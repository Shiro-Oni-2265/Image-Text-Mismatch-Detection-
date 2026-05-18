# Phát hiện Không khớp Ảnh-Chữ (Image-Text Mismatch Detection - ITMD)

Một dự án Python HOÀN CHỈNH dùng để phát hiện xem một bức ảnh và câu chú thích (caption) của nó có khớp ý nghĩa với nhau hay không. Dự án này sử dụng phương pháp trí tuệ nhân tạo (AI) thông qua mô hình CLIP nổi tiếng của OpenAI (`openai/clip-vit-base-patch32`).

## 1. Tổng quan Dự án

Dự án này là một quy trình (pipeline) xử lý dữ liệu mạnh mẽ, bao gồm các chức năng:
- Sử dụng mô hình CLIP đã được công ty mẹ dạy từ trước (pre-trained) để rút trích đặc trưng (tức là chuyển đổi cốt lõi nội dung của ảnh và chữ thành các dãy số AI hiểu được).
- Tính toán "độ giống nhau" (công thức toán cosine similarity) giữa đặc trưng của ảnh và chữ (chấm thang điểm từ 0 đến 1).
- Đưa ra quyết định là "Khớp" (Match) hay "Không Khớp" (Mismatch) dựa trên một mức điểm qua hạn mức (ngưỡng - threshold) có thể tự chỉnh.
- Cung cấp tính năng tải dữ liệu và huấn luyện (train) tập trung vào một mạng nơ-ron phân loại kích thước nhỏ (quy mô phân loại nhị phân) gắn trên phần đỉnh của bộ cấu trúc CLIP.
- Tự động tính các điểm chuẩn đánh giá mức độ khôn ngoan của mô hình (Độ chính xác tỷ lệ - Accuracy, Precision, Recall, F1) và vẽ các biểu đồ trực quan (ví dụ: ma trận nhầm lẫn - confusion matrices, biểu đồ phân bố điểm - score distributions).
- Cấu trúc thư mục được quy hoạch gọn gàng, chia mô-đun chức năng dễ hiểu, có bắt lỗi (Error handling) và hỗ trợ chạy bằng phần cứng đồ họa máy tính tốc độ cao (GPU). Rất thích hợp cho các bạn thực tập sinh học hỏi cách thức đưa một dự án vào thực tế!

## 2. Các bước Cài đặt ban đầu

1. Xin hãy tải (clone) hoặc giải nén toàn bộ thư mục dự án này vào `D:\ITMD`.
2. Đảm bảo máy tính của bạn đã cài đặt ngôn ngữ Python (Bản 3.10 trở lên lân cận nhất).
3. Mở cửa sổ dòng lệnh (Terminal/Command Prompt) tại thư mục dự án và chạy câu lệnh sau để cài tất tần tật các thư viện bổ trợ:

```bash
pip install -r requirements.txt
```

## 3. Cách Chuẩn bị Dữ liệu (Dataset)

Để dạy cho AI (huấn luyện/train), bạn cần gom các file hình bạn có vào thư mục `data/images/` và tạo một file bảng tính định dạng CSV có tên là `captions.csv` cất vào đường dẫn `data/captions.csv`.

File bài tập `captions.csv` này bắt buộc chứa đúng 3 cột (ngăn nhau bằng dấu phẩy):
- `image_path`: Tên file của bức ảnh (ví dụ: `image1.jpg`)
- `caption`: Câu văn hoặc đoạn văn miêu tả bức ảnh đó
- `label`: Nhãn kết quả làm đáp án cho AI học (0 = Sai / Không khớp, 1 = Đúng / Mức độ khớp cao)

**Một ví dụ về dữ liệu bên trong `captions.csv`:**
```csv
image_path,caption,label
dog.jpg,Một chú chó nâu dễ thương đang chơi đùa trên bãi cỏ,1
car.png,Chiếc xe thể thao màu xanh đang chạy tốc độ cao,1
cat.jpg,Một con voi đang dùng vòi uống nước,0
```

## 4. Hướng dẫn Dạy AI (Huấn luyện / Training)

Nếu bạn muốn mở khóa tính năng tự học nâng cao của việc huấn luyện bộ phân loại để AI bám sát tình hình hình ảnh thực tế công ty bạn đang có:

1. Đảm bảo file `captions.csv` và thư mục ảnh đã được sắp xếp chính xác.
2. Mở file thư mục bối cảnh `configs/config.py` để chỉnh sửa các thông số kỹ thuật tối ưu như: số ảnh học cùng 1 dợt (batch size), tốc độ học hằng phẩy (learning rate), số lượt học quay vòng toàn cuốn sách (epochs) nếu muốn thay đổi.
3. Kích hoạt chạy lệnh sau trên Terminal:

```bash
python training/train.py
```

Hệ thống AI sẽ tự động kích hoạt học đi học lại! Tích hợp tiến trình theo dõi thời gian và vòng lặp (tqdm progress), nhẩm tính và đo đạc lại năng lực, sau đó nó sẽ tự động chắt lọc và sao lưu bộ não xịn nhất của nó với tên file `best_model.pth` lưu vào thư mục `outputs/`, đương nhiên là kèm theo cả các biểu phác thảo huấn luyện để bạn chèn vào báo cáo.

## 5. Hướng dẫn Chạy Suy luận Dự đoán Thực Tế (Inference / Predict)

Bạn có thể ra đề bài ép AI trả lời ngay tức thì xem một tấm hình và đoạn văn lạ bất kỳ có ăn khớp nhau không bằng giao diện điều khiển dòng lệnh. Quy trình này hoạt động bằng cách chiết xuất sự tương đồng theo góc hướng ma trận hình học (cosine-similarity) nguyên bản và tự so với điểm vượt qua khóa vạch. Nếu ở bước 4 bạn có cho AI học trọng số tuỳ chỉnh, lệnh này cũng rất khôn khi tự gọi đúng bộ não nhân tinh xảo vừa dạy ra để làm việc.

```bash
python inference/predict.py --image duong_dan/toi/anh_bat_ky_cua_ban.jpg --text "Câu nội dung caption mà bạn muốn kiểm tra"
```

Bạn cũng có thể bắt AI phải khắc khe hơn (hoặc dễ tính hơn) bằng cách tự chèn bộ số (ví dụ: `0.4`) đè lên khung qua ải mặc định (mặc định trong config là `0.25`):
```bash
python inference/predict.py --image duong_dan/toi/anh.jpg --text "Nội dung caption" --threshold 0.4
```

## 6. Sổ tay tra cứu câu lệnh

**1. Lệnh gọi toàn bộ quy trình mồi khép kín cho máy tự diễn tập để người mới quan sát:**
```bash
python main.py
```

**2. Lệnh yêu cầu phán đoán thông qua cách nhập đường dẫn thủ công vào Terminal (CLI):**
```bash
python inference/predict.py --image data/images/sample.jpg --text "Một bức tranh minh họa con trâu"
```

**Ví dụ khi AI trả lời lại cho người xem:**
```
Similarity score: 0.82
Prediction: MATCH
```

**3. Khởi động nhà máy luyện cấp cho mô hình (Training):**
```bash
python training/train.py
```
