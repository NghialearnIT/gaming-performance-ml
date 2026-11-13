# Data Dictionary

| Column | Data Type | Description | Example |
|---|---|---|---|
| device_type | String | Loại thiết bị | desktop / laptop |
| cpu_model | String | Tên CPU | Intel Core i5-12400F |
| gpu_model | String | Tên GPU | NVIDIA RTX 3060 |
| gpu_type | String | Loại GPU | desktop / laptop / integrated |
| gpu_vram_gb | Float | Dung lượng VRAM (GB) | 12 |
| gpu_tgp_w | Float | Công suất GPU (W) | 170 |
| ram_gb | Integer | Dung lượng RAM (GB) | 16 |
| ram_type | String | Thế hệ RAM | DDR4 / DDR5 |
| ram_channels | String | Cấu hình kênh RAM | single / dual |
| game | String | Tên game | valorant / cs2 |
| resolution | String | Độ phân giải | 1920x1080 |
| graphics_preset | String | Thiết lập đồ họa | low / medium / high |
| avg_fps | Float | FPS trung bình | 144 |
| one_percent_low_fps | Float | FPS 1% Low | 90 |
| benchmark_method | String | Phương pháp thu thập | measured / estimated |
| benchmark_source | String | Tên nguồn dữ liệu | Example Source |
| benchmark_url | String | Đường dẫn nguồn | URL |
| game_version | String | Phiên bản game | Version |
| benchmark_runs | Integer | Số lần chạy benchmark | 3 |