# Gaming Performance ML

Đồ án dự đoán FPS chơi game trên Desktop và Laptop. Ứng dụng chạy bằng FastAPI, scikit-learn và frontend HTML/CSS/JavaScript. API đánh giá CPU, GPU và RAM so với yêu cầu của game khi có đủ ngưỡng, sau đó hiển thị FPS tham chiếu hoặc FPS ước tính ở **1080p High** nếu có đủ dữ liệu.

## Chạy đồ án

Yêu cầu Python 3.12 trở lên. Chạy các lệnh từ thư mục gốc repo.

```bash
git clone https://github.com/NghialearnIT/gaming-performance-ml.git
cd gaming-performance-ml
python -m venv .venv
```

Kích hoạt môi trường trên Windows PowerShell bằng `.venv\Scripts\Activate.ps1`, hoặc trên macOS/Linux bằng `source .venv/bin/activate`, rồi chạy:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

- [Giao diện dự đoán FPS](http://127.0.0.1:8000/app/)
- [Swagger UI](http://127.0.0.1:8000/docs)
- [Demo giao diện có dữ liệu minh họa](http://127.0.0.1:8000/app/?demo=1)

Ở lần chạy đầu tiên, API huấn luyện mô hình từ CSV và lưu vào `models/`. Các lần sau dùng lại mô hình đã lưu. Có thể chạy `python -m backend.fps_model` để in báo cáo đánh giá, hoặc thêm `--force` để huấn luyện lại. Khởi động lại API để dùng model mới.

## Dữ liệu và mô hình

| Tệp | Cách sử dụng |
| --- | --- |
| `data/raw/game_requirements.csv` | 585 game có điểm CPU, GPU và RAM ở mức tối thiểu và đề xuất. |
| `data/raw/games_fps_reference.csv` | Giá trị FPS tham chiếu 1080p High theo game và GPU. CSV có URL theo game. File thiếu thông tin về CPU, RAM, TGP và quy trình đo của từng giá trị FPS. |
| `data/raw/gaming_train_dataset.csv` | Dùng để tra điểm phần cứng. Các nhãn phân loại của 35.100 cấu hình tổng hợp được tạo từ quy tắc tối thiểu và đề xuất. |
| `data/raw/benchmark_raw.csv` | Mẫu schema để bổ sung số đo FPS với cấu hình và thiết lập đầy đủ. |

Mô hình **HistGradientBoostingRegressor** học từ 132.984 cặp game–GPU trong bảng FPS tham chiếu. Đầu vào gồm điểm GPU, thông tin yêu cầu GPU của game, năm phát hành, giới hạn FPS của game và FPS tham chiếu của cùng game trên GTX 1650, RTX 3060 và RTX 4070. Ba cột FPS đầu vào được loại khỏi nhãn huấn luyện. Mô hình chỉ suy luận trong phạm vi điểm GPU đã biết và áp dụng giới hạn FPS nếu dataset có thông tin.

Dữ liệu kiểm thử tách theo nhóm tên game. Kịch bản thứ hai giữ thêm hai cột GPU khỏi tập train để kiểm tra khả năng ước tính cho GPU thiếu số tham chiếu. Hai kịch bản dùng cùng dữ liệu nguồn và đo sai số so với **giá trị trong CSV**.

| Tập kiểm thử | Số cặp | MAE mô hình | RMSE mô hình | MAE baseline trung vị |
| --- | ---: | ---: | ---: | ---: |
| Game ngoài tập train | 26.640 | 4,42 FPS | 8,72 FPS | 100,50 FPS |
| Game và hai GPU ngoài tập train | 6.660 | 24,46 FPS | 31,87 FPS | 90,58 FPS |

Bảng trên chưa kiểm định sai số trên máy thật. Mô hình dùng điểm GPU tổng hợp, cùng một điểm có thể cho FPS khác nhau trên các laptop có TGP, CPU hoặc tản nhiệt khác nhau. Để kiểm định trên máy thật hoặc thêm kết quả cho Low, Medium, 1440p và 1% Low, cần benchmark đúng thiết lập với cấu hình và quy trình đo được ghi lại.

## API và cách đọc kết quả

| Endpoint | Chức năng |
| --- | --- |
| `GET /options` | Danh mục game, CPU, GPU Desktop/Laptop và thiết lập đồ họa. |
| `POST /predict` | Đánh giá cấu hình và trả kiểu kết quả FPS nếu đủ dữ liệu. |
| `POST /analyze` | Cùng hợp đồng dữ liệu với `/predict`. |

Ví dụ request:

```json
{
  "device_type": "desktop",
  "cpu_model": "Core i5-12400F",
  "gpu_model": "Radeon RX 6600",
  "ram_gb": 16,
  "game": "Red Dead Redemption 2",
  "resolution": "1920x1080",
  "graphics_preset": "high"
}
```

- `fps_source: "reference"` là FPS lấy từ bảng cho đúng game và GPU.
- `fps_source: "ml_estimate"` là kết quả mô hình cho GPU chưa có cột FPS riêng.
- `avg_fps: null` đi cùng `fps_message` giải thích trường hợp thiếu dữ liệu, preset chưa hỗ trợ hoặc cấu hình dưới tối thiểu.
- `rule_based: null` áp dụng cho Valorant, CS2 và LoL khi bảng hiện có FPS nhưng thiếu ngưỡng cấu hình đầy đủ.
- `one_percent_low_fps: null` vì dữ liệu hiện chưa có chỉ số này.
- `is_stub: true` xuất hiện ở demo UI để nhận diện số minh họa.

## Kiểm thử

```bash
python -m pytest -q tests/backend
python -m playwright install chromium --only-shell
python tests/frontend/check_ui.py
```

Bộ test giao diện dùng API fixture để kiểm tra form, lỗi HTTP và biểu đồ demo. Xem [hướng dẫn frontend](frontend/README.md) nếu cần chạy frontend riêng ở cổng 5500 hoặc 5501.

## Thành viên

| Thành viên | Vai trò |
| --- | --- |
| 1 | Quản lý dự án, phân tích dữ liệu và huấn luyện mô hình |
| 2 | Thu thập, làm sạch và kiểm tra dữ liệu benchmark |
| 3 | Xây dựng và kiểm thử FastAPI |
| 4 | Xây dựng và kiểm thử frontend |

Dự án được phát triển cho mục đích học tập.
