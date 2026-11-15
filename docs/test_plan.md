# Kế hoạch kiểm thử giao diện

| Mục | Cách kiểm tra |
| --- | --- |
| Phạm vi | Form Desktop/Laptop, năm game, validate phía trình duyệt, kết nối API, kết quả, so sánh preset và hiển thị đáp ứng. |
| Môi trường đã chuẩn bị | Playwright, Chromium, frontend tại `127.0.0.1:5500`, API kiểm thử HTTP tại `127.0.0.1:8000`. |
| Nghiệm thu tích hợp | Chạy lại trên Chrome và Edge Windows với backend TV3 và mô hình thật. Đối chiếu cùng cấu hình trong Swagger và giao diện, giữ lại mã phiên bản mô hình. |
| Dữ liệu đầu vào | Mỗi game thử Desktop và Laptop. Thử cả cấu hình thiếu TGP, ngoài catalog và kết quả 1% Low bị thiếu. Các số FPS trong fixture chỉ phục vụ kiểm thử. |
| Danh sách ca | [test_cases.csv](test_cases.csv) có bước chạy, kỳ vọng, kết quả thực tế với fixture và cột theo dõi khi chạy model thật. |
| Điều kiện hoàn thành TEST-02 | Tối thiểu 20 ca đã chạy trên bản tích hợp và không còn lỗi Critical hoặc High đang mở. |

## Xử lý lỗi

- **Critical** — Luồng dự đoán bị chặn với cấu hình hợp lệ hoặc kết quả bị gắn nhầm cấu hình.
- **High** — Sai dữ liệu gửi/hiển thị, thiếu nhãn STUB hoặc luồng chính bị chặn ở một thiết bị.
- **Medium** — Lỗi so sánh hoặc lỗi hiển thị có cách tiếp tục.
- **Low** — Lỗi chính tả hoặc khoảng cách nhỏ.

Khi tái hiện được lỗi trên bản tích hợp, tạo GitHub Issue kèm mã ca kiểm thử, phiên bản trình duyệt, phiên bản mô hình, bước tái hiện, ảnh và kết quả mong đợi/thực tế. Ghi link Issue vào kết quả kiểm thử và chạy lại ca liên quan sau bản sửa.
