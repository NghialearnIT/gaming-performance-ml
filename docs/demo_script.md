# Kịch bản demo dự đoán FPS

## Chuẩn bị

- Mở frontend theo [hướng dẫn](../frontend/README.md). Cổng frontend là 5500. Trên Windows có thể bấm đúp `frontend/Chay_Demo.bat` để mở ngay bản demo. Máy trình bày cần mở được API FastAPI trên cổng 8000 để chạy dự đoán thật.
- Sáu cấu hình trong [demo_configs.json](demo_configs.json) dùng để diễn tập nhập liệu. Các FPS đo được để trống. Khi có tập test, chọn 5–6 cấu hình hold-out có nguồn, tối thiểu hai Desktop và hai Laptop. Ghi FPS đo được, nguồn, thiết lập và phiên bản mô hình.
- Mở [chế độ demo](http://127.0.0.1:5500/?demo=1) để dự phòng khi backend gặp lỗi. Tắt kết nối Internet và kiểm tra frontend, thư viện biểu đồ và tài nguyên local vẫn chạy.

## Trình bày trong khoảng 6 phút

| Thời gian | Thao tác và lời trình bày |
| --- | --- |
| 0:00–0:45 | Giới thiệu bài toán dự đoán FPS từ CPU, GPU, RAM và thiết lập game. Nêu phạm vi 1080p. |
| 0:45–2:00 | Chọn game từ dải thẻ, nhập một cấu hình Desktop và chọn mức đồ họa. Dự đoán rồi giải thích Average FPS và 1% Low FPS. |
| 2:00–3:15 | Chuyển sang Laptop để mở thông số nâng cao. Nhập TGP rồi thử lại với TGP để trống để trình bày cảnh báo nếu có. |
| 3:15–4:20 | Mở biểu đồ ba preset và chỉ rõ mức đã dự đoán. Đổi game để kiểm tra máy giữ nguyên cấu hình và đánh dấu kết quả cũ. Giải thích ngưỡng Average FPS 60 và vì sao 1% Low có thể thiếu. |
| 4:20–5:30 | Chiếu 3–4 cấu hình còn lại từ tập test. Với ca có số đo, nói chênh lệch FPS giữa dự đoán và phép đo cùng thiết lập. Giải thích ảnh hưởng của phiên bản game, driver và tản nhiệt. |
| 5:30–6:00 | Tóm tắt giới hạn của mô hình. Nếu dùng bản offline, chỉ rõ kết quả được gắn nhãn thử nghiệm. |

Tập trọn kịch bản hai lần với backend/mô hình thật trên máy trình bày. Đã có [video bản demo offline](demo_offline.mp4) và [ảnh giao diện](demo_preview.png) làm phương án dự phòng. Quay thêm bản chạy model thật sau buổi tập.
