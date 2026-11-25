# Frontend dự đoán FPS

Giao diện dùng HTML, CSS, JavaScript, Bootstrap và Chart.js. Các thư viện và font được phục vụ từ `vendor/`.

## Chạy cùng FastAPI

Từ thư mục gốc repo, cài môi trường theo [README](../README.md) rồi chạy:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Mở [giao diện](http://127.0.0.1:8000/app/), chọn game và dùng nút **Dùng cấu hình mẫu** hoặc tự nhập CPU, GPU và RAM. Chọn **1080p High** rồi bấm **Dự đoán FPS**.

Giao diện đọc `fps_source` và `fps_message` từ API để ghi rõ FPS tham chiếu, FPS ước tính hoặc lý do thiếu FPS. Khi có kết quả rule-based, ba thẻ CPU, GPU và RAM hiển thị mức đáp ứng yêu cầu game.

## Chạy frontend riêng

```bash
python -m http.server 5501 --bind 127.0.0.1 --directory frontend
```

Mở [frontend cổng 5501](http://127.0.0.1:5501/). FastAPI chạy ở cổng 8000, được cấu hình CORS cho localhost cổng 5500 và 5501. Có thể thêm origin bằng biến môi trường `FPS_CORS_ORIGINS` và đổi URL API cho frontend chạy riêng trong `config.js`.

## Demo giao diện

Mở [demo offline](http://127.0.0.1:5501/?demo=1), hoặc chạy `Chay_Demo.bat` trên Windows. Demo có nhãn minh họa và so sánh ba mức Low, Medium, High bằng dữ liệu mẫu.

## Kiểm thử giao diện

```bash
python -m playwright install chromium --only-shell
python tests/frontend/check_ui.py
```

Dừng các tiến trình đang giữ cổng 5500 hoặc 8000 trước khi chạy bộ test giao diện.
