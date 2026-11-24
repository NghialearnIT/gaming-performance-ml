
# 🎮 Gaming Performance ML

**Xây dựng hệ thống dự đoán hiệu năng PC/Laptop khi chơi game bằng Machine Learning**

## 1. Giới thiệu dự án

Gaming Performance ML là dự án ứng dụng Machine Learning nhằm dự đoán hiệu năng chơi game của máy tính Desktop và Laptop dựa trên cấu hình phần cứng và thiết lập đồ họa.

Người dùng có thể cung cấp thông tin cấu hình máy tính, lựa chọn trò chơi, độ phân giải và mức thiết lập đồ họa. Hệ thống sẽ sử dụng mô hình Machine Learning đã được huấn luyện để dự đoán hiệu năng chơi game tương ứng.

Dự án được xây dựng với mục tiêu kết hợp kiến thức về Data Science, Machine Learning và phát triển phần mềm thành một sản phẩm có khả năng ứng dụng thực tế.

## 2. Mục tiêu dự án

Các mục tiêu chính:

- Thu thập và xây dựng bộ dữ liệu benchmark hiệu năng chơi game.
- Phân tích dữ liệu cấu hình phần cứng và FPS bằng Exploratory Data Analysis (EDA).
- Tiền xử lý dữ liệu và xây dựng Feature Engineering Pipeline.
- Huấn luyện và so sánh nhiều mô hình Machine Learning.
- Đánh giá hiệu quả mô hình bằng các chỉ số phù hợp.
- Xây dựng Backend API để cung cấp chức năng dự đoán.
- Xây dựng giao diện cho phép người dùng nhập cấu hình và xem kết quả.

### Các giá trị dự đoán

| Chỉ số | Ý nghĩa |
|---|---|
| Average FPS | Số khung hình trung bình hiển thị mỗi giây |
| 1% Low FPS | Chỉ số FPS thấp ở nhóm 1% khung hình chậm nhất, phản ánh độ ổn định khi chơi game |

## 3. Phạm vi dự án

### 3.1. Thiết bị

- Desktop PC.
- Laptop.

### 3.2. Trò chơi

Phạm vi dự kiến:

- Valorant.
- Counter-Strike 2 (CS2).
- PUBG.
- FC Online.
- League of Legends (LoL).

### 3.3. Thiết lập đồ họa

| Thuộc tính | Phạm vi dự kiến |
|---|---|
| Resolution | 1920x1080 (1080p) |
| Graphics Preset | Low |
| Graphics Preset | Medium |
| Graphics Preset | High |

Phạm vi có thể được điều chỉnh dựa trên số lượng và chất lượng benchmark thu thập được.

## 4. Công nghệ sử dụng

| Nhóm | Công nghệ | Vai trò |
|---|---|---|
| Programming Language | Python | Ngôn ngữ chính |
| Data Processing | Pandas, NumPy | Xử lý và phân tích dữ liệu |
| Data Visualization | Matplotlib, Seaborn | Trực quan hóa dữ liệu |
| Machine Learning | Scikit-learn | Xây dựng và đánh giá mô hình |
| Machine Learning | XGBoost | Mô hình Gradient Boosting |
| Development Environment | Jupyter Notebook | Phân tích và thử nghiệm |
| Backend | FastAPI hoặc Flask | Xây dựng API dự đoán |
| Frontend | Đang lựa chọn | Giao diện người dùng |
| Version Control | Git, GitHub | Quản lý mã nguồn và cộng tác |

## 5. Machine Learning Approach

Dự án dự kiến thử nghiệm và so sánh các mô hình hồi quy:

1. **Linear Regression:** Mô hình baseline để thiết lập kết quả tham chiếu.
2. **Random Forest Regressor:** Mô hình ensemble có khả năng học các quan hệ phi tuyến.
3. **XGBoost Regressor:** Mô hình Gradient Boosting để thử nghiệm khả năng cải thiện hiệu suất dự đoán.

### Input Features

Các đặc trưng đầu vào dự kiến:

| Feature | Description |
|---|---|
| device_type | Loại thiết bị: Desktop hoặc Laptop |
| cpu_model | Model CPU |
| gpu_model | Model GPU |
| gpu_type | Loại GPU |
| gpu_vram_gb | Dung lượng VRAM |
| gpu_tgp_w | Công suất GPU Laptop |
| ram_gb | Dung lượng RAM |
| ram_type | Loại RAM |
| ram_channels | Số kênh RAM |
| game | Trò chơi được lựa chọn |
| resolution | Độ phân giải |
| graphics_preset | Thiết lập đồ họa |

### Target Variables

- `avg_fps`: Average FPS.
- `one_percent_low_fps`: 1% Low FPS.

### Evaluation Metrics

| Metric | Ý nghĩa |
|---|---|
| MAE | Sai số tuyệt đối trung bình |
| RMSE | Căn bậc hai của sai số bình phương trung bình |
| R² | Hệ số xác định, phản ánh mức độ giải thích biến thiên của dữ liệu |

Các mô hình sẽ được đánh giá và so sánh trên dữ liệu kiểm thử phù hợp. Không sử dụng dữ liệu kiểm thử trong quá trình huấn luyện.

## 6. Dataset

Dữ liệu được xây dựng từ các nguồn benchmark phần cứng và kết quả đo hiệu năng chơi game.

Dataset được lưu dưới định dạng CSV.

### Dataset Schema

```text
device_type
cpu_model
gpu_model
gpu_type
gpu_vram_gb
gpu_tgp_w
ram_gb
ram_type
ram_channels
game
resolution
graphics_preset
avg_fps
one_percent_low_fps
benchmark_method
benchmark_source
benchmark_url
game_version
benchmark_runs
```

### Data Quality Principles

Dự án tuân thủ các nguyên tắc:

- Không tự tạo hoặc bịa số liệu benchmark.
- Lưu lại nguồn dữ liệu để có thể kiểm chứng.
- Phân biệt dữ liệu đo thực tế (`measured`) và dữ liệu ước tính (`estimated`).
- Kiểm tra dữ liệu thiếu, dữ liệu trùng lặp và giá trị bất thường.
- Không xóa dữ liệu một cách tùy tiện chỉ vì một vài thuộc tính bị thiếu.
- Không sử dụng thông tin nguồn dữ liệu hoặc URL làm đặc trưng đầu vào cho mô hình.
- Chú ý sự khác biệt giữa GPU Desktop và GPU Laptop.

Chi tiết các thuộc tính được mô tả trong `data/DATA_DICTIONARY.md`.

## 7. Project Structure

```text
gaming-performance-ml/
│
├── data/
│   ├── raw/
│   │   └── benchmark_raw.csv
│   │
│   ├── processed/
│   │
│   ├── external/
│   │
│   ├── DATA_DICTIONARY.md
│   └── benchmark_sources.csv
│
├── notebooks/
│   └── 01_data_exploration.ipynb
│
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   └── evaluation/
│
├── backend/
│
├── frontend/
│
├── models/
│
├── reports/
│
├── requirements.txt
│
└── README.md
```

### Directory Description

| Directory | Chức năng |
|---|---|
| `data/raw/` | Lưu dữ liệu benchmark ban đầu |
| `data/processed/` | Lưu dữ liệu sau khi xử lý |
| `data/external/` | Lưu dữ liệu tham khảo bên ngoài |
| `notebooks/` | Phân tích dữ liệu và thử nghiệm |
| `src/data/` | Các module xử lý dữ liệu |
| `src/features/` | Feature Engineering |
| `src/models/` | Xây dựng và huấn luyện mô hình |
| `src/evaluation/` | Đánh giá mô hình |
| `backend/` | Xây dựng API |
| `frontend/` | Giao diện người dùng |
| `models/` | Lưu mô hình đã huấn luyện |
| `reports/` | Báo cáo và tài liệu dự án |

## 8. Installation & Setup

### 8.1. Requirements

- Python 3.12 trở lên.
- Git.
- Visual Studio Code.
- Jupyter Notebook extension.
- Python extension.

Khuyến nghị sử dụng môi trường Linux hoặc WSL2 Ubuntu để phát triển dự án.

### 8.2. Clone repository

```bash
git clone <repository-url>
cd gaming-performance-ml
```

### 8.3. Create virtual environment

```bash
python3 -m venv .venv
```

### 8.4. Activate virtual environment

Ubuntu / WSL:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 8.5. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 8.6. Verify installation

```bash
python -c "import pandas, numpy, sklearn, matplotlib, seaborn; print('Environment ready!')"
```

## 9. Running the Project

### Data Exploration

Mở project bằng Visual Studio Code:

```bash
code .
```

Mở notebook:

```text
notebooks/01_data_exploration.ipynb
```

Chọn Python Interpreter từ virtual environment:

```text
.venv/bin/python
```

Sau đó chạy lần lượt các cell để thực hiện:
- Dataset Overview.
- Data Types Inspection.
- Missing Values Analysis.
- Duplicate Detection.
- Descriptive Statistics.
- Exploratory Data Analysis.

### Model Training

Các bước huấn luyện mô hình sẽ được triển khai trong các notebook và module thuộc `src/models/` sau khi dataset đủ điều kiện.

### Backend & Frontend

Cách chạy Backend và Frontend sẽ được cập nhật khi nhóm hoàn thiện công nghệ và API Contract.

## 10. Development Workflow

Dự án được phát triển theo quy trình:

```text
Data Collection
      |
      v
Data Validation
      |
      v
Exploratory Data Analysis
      |
      v
Data Preprocessing
      |
      v
Feature Engineering
      |
      v
Model Training
      |
      v
Model Evaluation
      |
      v
Model Integration
      |
      v
Backend API
      |
      v
Frontend Interface
      |
      v
Testing & Deployment
```

## 11. Team Responsibilities

Dự án được thực hiện bởi nhóm 4 thành viên.

| Member | Role | Main Responsibilities |
|---|---|---|
| Member 1 | Leader & AI/ML Engineer | Project Management, EDA, Data Preprocessing, Feature Engineering, Model Training, Model Evaluation, Integration |
| Member 2 | Data Engineer / Data Analyst | Benchmark Collection, Data Cleaning, Data Validation, Data Dictionary |
| Member 3 | Backend Developer | API Design, Backend Development, Model Integration, API Testing |
| Member 4 | Frontend Developer / Tester | UI Development, API Integration, Result Visualization, Testing |

## 12. Current Development Status

Dự án đang trong giai đoạn xây dựng nền tảng dữ liệu và môi trường phát triển.

| Component | Status |
|---|---|
| Project Structure | In Progress |
| Python Environment | Completed |
| Dependency Installation | Completed |
| Dataset Schema | Defined |
| Data Collection | In Progress |
| Data Exploration | In Progress |
| Data Preprocessing | Planned |
| Model Training | Planned |
| Model Evaluation | Planned |
| Backend Development | Planned |
| Frontend Development | Planned |
| System Integration | Planned |
| Final Report | Planned |

*Trạng thái cần được cập nhật theo tiến độ thực tế của nhóm.*

## 13. Project Limitations

Một số yếu tố có thể ảnh hưởng đến độ chính xác của hệ thống:

- Số lượng benchmark có thể chưa đủ lớn.
- Kết quả benchmark phụ thuộc vào phiên bản game và driver.
- Hiệu năng Laptop phụ thuộc vào TGP, hệ thống tản nhiệt và giới hạn công suất.
- Kết quả giữa các nguồn benchmark có thể khác nhau do điều kiện thử nghiệm.
- Mô hình có thể dự đoán kém đối với cấu hình phần cứng chưa xuất hiện trong dữ liệu huấn luyện.

Do đó, kết quả dự đoán chỉ mang tính tham khảo và phụ thuộc vào phạm vi dữ liệu đã thu thập.

## 14. Future Improvements

Các hướng phát triển trong tương lai:

- Mở rộng số lượng game và cấu hình phần cứng.
- Bổ sung thêm độ phân giải 1440p và 4K.
- Cải thiện chất lượng và độ phủ của dataset.
- Thử nghiệm thêm các thuật toán Machine Learning.
- Phát triển chức năng đề xuất cấu hình tối ưu.
- Phân loại khả năng chơi game theo mục tiêu FPS.
- Xây dựng hệ thống cập nhật benchmark định kỳ.
- Triển khai hệ thống lên môi trường Cloud.

## 15. License

Dự án được phát triển phục vụ mục đích học tập và nghiên cứu trong khuôn khổ đồ án sinh viên.

Các dữ liệu benchmark sử dụng cần tuân thủ điều khoản và quyền sử dụng của nguồn cung cấp tương ứng.
