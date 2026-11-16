# Thiết kế giao diện dự đoán FPS V3

- [Desktop có kết quả và biểu đồ so sánh](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=7-123)
- [Desktop trước khi chọn game](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=7-286)
- [Mobile với Laptop thiếu TGP](https://www.figma.com/design/DUms4LmlRBXIBvKHTwqF4T?node-id=7-419)

V3 dùng dải chọn game, form cấu hình gọn và hai chỉ số FPS đặt cạnh nhau. Luồng này tham khảo [FPS Calculator của HowManyFPS](https://howmanyfps.com/games/counter-strike-2). Năm ảnh trong `frontend/assets/*.webp` là minh họa mới tạo và lưu cục bộ để chạy demo offline. Prompt tạo ảnh yêu cầu một bản ghép 3 × 2 gồm đấu trường khoa học viễn tưởng, phố Địa Trung Hải, vùng hoang dã có tháp canh, sân bóng đá, khu rừng phép thuật và một ô nền trung tính. Ảnh không chứa nhân vật, tên game hoặc logo.

| Đầu việc | Thiết kế và hành vi |
| --- | --- |
| FE-01 | [Wireframe chọn game trước](ui_wireframe.png) và các khung Figma cho desktop và mobile. |
| FE-02 | 5 thẻ game, form Desktop/Laptop có đủ 11 trường theo PM-02. VRAM, loại RAM và kênh RAM thuộc mục nâng cao. Chọn Laptop tự mở mục này và hiện TGP. |
| FE-03 | Khóa gửi nếu thiếu dữ liệu bắt buộc hoặc có lỗi. Đổi game giữ cấu hình máy và preset, đồng thời đánh dấu kết quả thuộc lựa chọn cũ. |
| FE-04 | Tải danh sách qua `/options` và gửi cấu hình sang `/predict`. API contract chính thức cần đối chiếu khi TV3 bàn giao. |
| FE-05 | Hai thẻ Average FPS và 1% Low FPS. Game, độ phân giải, preset, phiên bản mô hình và trạng thái thử nghiệm đi cùng kết quả. |
| FE-06 | Trạng thái đang tải, lỗi theo trường, lỗi kết nối và nút thử lại. Mục nâng cao tự mở nếu API báo lỗi trong đó. |
| FE-07 | Biểu đồ và bảng số liệu đánh dấu mức đã dự đoán. Dải nhấn giữ nguyên cho đến khi người dùng gửi dự đoán mới. |
| FE-08 | Màn hình rộng dùng hai cột, tablet và mobile xếp dọc. Khi thiếu chiều ngang, dải game cuộn độc lập và có thể chọn bằng bàn phím. |

Xem [hướng dẫn chạy](../frontend/README.md), [ảnh demo](demo_preview.png) và [kết quả kiểm thử](test_report.md).
