# Kết quả kiểm thử Frontend

| Môi trường | Đạt | Lỗi | Phạm vi |
| --- | ---: | ---: | --- |
| Chromium 141 headless trên Linux với API mô phỏng qua HTTP | 33 | 0 | 10 luồng chính, 20 ca hành vi và lỗi, 3 kích thước màn hình |
| Chrome và Edge trên Windows với FastAPI và model của nhóm | Chờ chạy | Chờ chạy | Kiểm thử tích hợp theo TEST-02 |

Dữ liệu thực thi nằm trong [test_cases.csv](test_cases.csv). Bộ test tự khởi tạo hai origin riêng để kiểm tra luồng JSON qua CORS với fixture. Ca mất kết nối chặn kết nối từ trình duyệt, và ca timeout giữ phản hồi 11 giây để xác minh giới hạn 10 giây. Ca demo offline chặn mọi truy cập ngoài máy chủ frontend.

Trong quá trình thử, phát hiện nút Đặt lại có thể giữ phần TGP và kết quả cũ. Sau khi sửa, ca FE-27 kiểm tra cả giá trị biểu mẫu, trạng thái TGP và biểu đồ. Ca này đạt ở lần chạy cuối.

Khi BE-09 và model thật sẵn sàng, đối chiếu `GET /options` và `POST /predict` với Swagger và chạy lại trên trình duyệt đích. Cập nhật cột `Chạy model thật` bằng bằng chứng từ bản tích hợp.
