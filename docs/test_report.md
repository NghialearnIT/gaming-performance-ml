# Kết quả kiểm thử Frontend V3

| Môi trường | Đạt | Lỗi | Phạm vi |
| --- | ---: | ---: | --- |
| Chromium 141 headless trên Linux với API mô phỏng qua HTTP | 42 | 0 | 36 ca kiểm thử từ V2 và 6 ca bổ sung cho luồng chọn game trước |
| Chrome và Edge trên Windows với FastAPI và mô hình của nhóm | Chờ chạy | Chờ chạy | Kiểm thử tích hợp theo TEST-02 |

Toàn bộ kết quả có trong [test_cases.csv](test_cases.csv). Bộ test khởi tạo hai origin riêng để kiểm tra CORS, mô phỏng lỗi mạng, lỗi 422 và timeout 10 giây. Ca offline chặn tất cả truy cập ngoài máy chủ frontend. Kiểm tra hình ảnh ở 1440, 768 và 375 px.

| Ca mới | Hành vi đã xác minh |
| --- | --- |
| FE-37 | Đổi game giữ phần cứng và preset. Kết quả cũ được đánh dấu cho tới khi dự đoán lại. |
| FE-38 | Chọn Laptop tự mở thông số nâng cao và cho phép gửi thiếu TGP. |
| FE-39 | Phản hồi 422 mở thông số nâng cao nếu lỗi thuộc trường đang được thu gọn. |
| FE-40 | Biểu đồ và bảng số liệu đánh dấu đúng preset gắn với kết quả đã trả. |
| FE-41 | Có thể chọn game bằng bàn phím và cuộn tới thẻ cuối ở 375 px. |
| FE-42 | Catalog có một game và một preset vẫn yêu cầu người dùng chọn cả hai. |

Khi BE-09 và mô hình thật sẵn sàng, đối chiếu `GET /options` và `POST /predict` với Swagger, chạy lại trên trình duyệt đích và cập nhật cột `Chạy model thật`.
