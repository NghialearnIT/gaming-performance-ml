# Thiết kế giao diện dự đoán FPS

Bản thiết kế có thể chỉnh sửa trong Figma, gồm các trường nhập dùng lại, ba màn hình và các trạng thái chính. Các số FPS trên bản vẽ được gắn nhãn thử nghiệm.

- [Desktop 1440 px trước khi dự đoán](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=3-69)
- [Desktop 1440 px có kết quả](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=2-13)
- [Mobile 375 px với Laptop thiếu TGP](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=2-193)
- [Trạng thái tương tác](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=2-363)

| Đầu việc | Thiết kế và hành vi |
| --- | --- |
| FE-01 | [Wireframe](ui_wireframe.png) và bản Figma với khối nhập cấu hình, kết quả và cảnh báo. |
| FE-02 | Form Desktop/Laptop có đủ 11 trường theo PM-02. TGP xuất hiện khi chọn Laptop. |
| FE-03 | Giữ nút gửi ở trạng thái khóa khi thiếu trường hoặc có lỗi. Lỗi hiển thị cạnh trường, chức năng đặt lại xóa cả kết quả cũ. |
| FE-04 | Tải danh sách qua `/options` và gửi cấu hình sang `/predict`. API contract chính thức cần đối chiếu khi TV3 bàn giao. |
| FE-05 | Trình bày Average FPS, 1% Low FPS, mức chơi, phiên bản mô hình và cảnh báo. Kết quả cũ được đánh dấu khi người dùng sửa cấu hình. |
| FE-06 | Có trạng thái đang tải, lỗi theo trường, lỗi kết nối và nút thử lại. |
| FE-07 | Biểu đồ cột và bảng số có thể mở rộng. Mỗi hàng là một preset, đủ hai chỉ số khi API trả về. |
| FE-08 | Màn hình rộng dùng hai cột. Tablet và mobile xếp dọc và đưa focus đến kết quả khi gửi thành công. |

Xem [trang chạy thử](../frontend/README.md), [ảnh giao diện chạy thật với dữ liệu demo](demo_preview.png) và [kết quả kiểm thử](test_report.md).
