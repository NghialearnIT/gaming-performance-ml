# Frontend dự đoán FPS

Frontend một trang dùng HTML, CSS, Bootstrap 5.3.3 và JavaScript thuần. Chart.js 4.4.9, Bootstrap và font Inter được phục vụ từ `vendor/`, kèm giấy phép MIT và SIL Open Font License tương ứng. Frontend không cần npm hoặc CDN. Xem [thiết kế và luồng sử dụng](../docs/ui_design.md).

## Chạy giao diện

Trên Windows, mở thư mục `frontend` rồi bấm đúp **Chay_Demo.bat**. File này dùng Python đã cài để mở demo trong trình duyệt. Giữ cửa sổ lệnh mở khi sử dụng.

Nếu chạy bằng terminal từ thư mục gốc repo, dùng:

```bash
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

- [Bản demo offline](http://127.0.0.1:5500/?demo=1). Nhấn **Dùng cấu hình mẫu** rồi **Dự đoán FPS**. Bản demo dùng số minh họa, luôn có nhãn thử nghiệm.
- [Bản kết nối API](http://127.0.0.1:5500/). Nếu chưa có API, trang hiện danh sách nhập mẫu và báo lỗi kết nối khi gửi dự đoán.

## Kết nối FastAPI

Khi nhóm backend đã có entry point theo kế hoạch, mở một terminal khác và chạy:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Backend cần cho phép origin `http://127.0.0.1:5500` qua CORS cho GET, POST và header `Content-Type`. Sửa `API_BASE_URL` ở `config.js` nếu endpoint chạy ở địa chỉ khác.

### Hợp đồng tạm theo PM-02 và BE-02

| Endpoint | Kiểu dữ liệu frontend đọc hoặc gửi |
| --- | --- |
| `GET /options` | Danh sách `device_types`, `games`, `resolutions`, `graphics_presets`, `cpu_models`, `gpu_models`, `ram_types`, `ram_channels`. Phần tử là giá trị nguyên thủy hoặc cặp `{ "value": ..., "label": "..." }`. |
| `POST /predict` | JSON chứa 11 trường như ví dụ. Các trường VRAM, TGP, loại RAM và kênh RAM gửi `null` nếu chưa biết. TGP luôn là `null` với Desktop. |
| Phản hồi | `avg_fps` là số hữu hạn không âm, `one_percent_low_fps` là số hoặc `null`, `model_version` là chuỗi, `warnings` là danh sách chuỗi và `is_stub` là boolean nếu API có cờ này. |
| Lỗi | 422 dùng mảng `detail` theo FastAPI (`loc`, `type`, `msg`). Lỗi 400 có thể trả chuỗi `detail` hoặc `message`. |

```json
{
  "device_type": "desktop",
  "cpu_model": "Intel Core i5-12400F",
  "gpu_model": "NVIDIA RTX 3060",
  "gpu_vram_gb": 12,
  "gpu_tgp_w": null,
  "ram_gb": 16,
  "ram_type": "DDR4",
  "ram_channels": "dual",
  "game": "valorant",
  "resolution": "1920x1080",
  "graphics_preset": "high"
}
```

Enum lấy từ catalog của API và giữ nguyên kiểu dữ liệu khi gửi lại. Catalog mẫu dùng dạng chuỗi chữ thường theo Data Dictionary ở nhánh `nghĩa`. Giá trị `gpu_type` thuộc schema dữ liệu huấn luyện và không nằm trong danh sách request PM-02. Khi có contract BE-02, đối chiếu schema `/options`, các enum, giới hạn số, trường nullable và cách suy ra `gpu_type`.

Biểu đồ dùng kết quả từ preset đã gửi và gọi thêm cho hai preset còn lại khi đủ ba mức. Mức gợi ý dựa vào Average FPS chưa làm tròn. Request có timeout 10 giây. Máy chủ frontend vẫn phục vụ được toàn bộ tài nguyên giao diện khi ngắt mạng.

## Chạy kiểm thử

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/frontend/check_ui.py --out docs/test_cases.csv
```

Trên máy có Chrome hoặc Edge, chạy thêm với `--channel chrome` hoặc `--channel msedge`. Dừng các tiến trình đang chiếm 5500 và 8000 trước khi chạy bộ test. Xem [kế hoạch](../docs/test_plan.md), [kết quả](../docs/test_report.md) và [kịch bản demo](../docs/demo_script.md).
