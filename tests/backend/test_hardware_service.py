"""Unit tests for HardwareService."""
import pytest
from backend.services.hardware_service import (
    DataIntegrityError,
    DeviceTypeMismatchError,
    HardwareNotFoundError,
    HardwareService,
    hardware_service,
)


def test_lookup_valid_cpu():
    """Kiểm tra tra cứu CPU hợp lệ từ dữ liệu thật."""
    cpu_name, score = hardware_service.get_cpu_score("Core i3-13100F")
    assert cpu_name == "Core i3-13100F"
    assert score == 4750.0


def test_lookup_nonexistent_cpu_raises_error():
    """Kiểm tra CPU không tồn tại phải raise HardwareNotFoundError."""
    with pytest.raises(HardwareNotFoundError) as exc_info:
        hardware_service.get_cpu_score("CPU Nonexistent 9999X")
    assert "Không tìm thấy CPU" in str(exc_info.value)


def test_lookup_valid_desktop_gpu():
    """Kiểm tra tra cứu GPU Desktop hợp lệ."""
    gpu_name, gpu_type, score = hardware_service.get_gpu_info("GeForce RTX 3060", "desktop")
    assert "3060" in gpu_name
    assert gpu_type == "Desktop"
    assert score > 0


def test_lookup_valid_laptop_gpu():
    """Kiểm tra tra cứu GPU Laptop hợp lệ."""
    gpu_name, gpu_type, score = hardware_service.get_gpu_info("GeForce RTX 4060 Laptop GPU", "laptop")
    assert "4060" in gpu_name
    assert gpu_type == "Mobile"
    assert score > 0


def test_device_mismatch_desktop_gpu_on_laptop():
    """Kiểm tra dùng GPU Desktop cho Laptop phải báo lỗi DeviceTypeMismatchError."""
    with pytest.raises(DeviceTypeMismatchError) as exc_info:
        hardware_service.get_gpu_info("GeForce RTX 3060", "laptop")
    assert "là card dành cho thiết bị Desktop" in str(exc_info.value)


def test_device_mismatch_laptop_gpu_on_desktop():
    """Kiểm tra dùng GPU Laptop cho Desktop phải báo lỗi DeviceTypeMismatchError."""
    with pytest.raises(DeviceTypeMismatchError) as exc_info:
        hardware_service.get_gpu_info("GeForce RTX 4060 Laptop GPU", "desktop")
    assert "là card dành cho thiết bị Laptop" in str(exc_info.value)


def test_invalid_device_type_raises_value_error():
    """Kiểm tra device_type không hợp lệ phải raise ValueError."""
    with pytest.raises(ValueError):
        hardware_service.get_gpu_info("GeForce RTX 3060", "tablet")


def test_lookup_nonexistent_gpu_raises_error():
    """Kiểm tra GPU không có trong dataset phải raise HardwareNotFoundError."""
    with pytest.raises(HardwareNotFoundError) as exc_info:
        hardware_service.get_gpu_info("Super Unknown GPU 9000", "desktop")
    assert "Không tìm thấy GPU" in str(exc_info.value)


def test_list_hardware():
    """Kiểm tra hàm liệt kê CPU và GPU trả về danh sách không rỗng."""
    cpus = hardware_service.list_all_cpus()
    desktop_gpus = hardware_service.list_gpus_by_device("desktop")
    laptop_gpus = hardware_service.list_gpus_by_device("laptop")

    assert len(cpus) >= 400
    assert len(desktop_gpus) > 0
    assert len(laptop_gpus) > 0
    # Đảm bảo không có GPU nào trùng nhau giữa desktop và laptop trong dataset
    common = set(desktop_gpus).intersection(set(laptop_gpus))
    assert len(common) == 0


def test_data_integrity_error_on_conflicting_scores(tmp_path):
    """Kiểm tra phát hiện và báo lỗi khi dataset có bản ghi không thống nhất điểm số."""
    csv_file = tmp_path / "conflicted_train.csv"
    csv_file.write_text(
        "record_type,device_type,game_name,game_release_year,cpu_name,cpu_gaming_score,gpu_name,gpu_type,gpu_g3d_mark,ram_gb,min_cpu_score,rec_cpu_score,min_gpu_g3d,rec_gpu_g3d,min_ram_gb,rec_ram_gb,target_class,target_label,source_game_url\n"
        "synth,Desktop,Game1,2020,CPU-A,5000,GPU-A,Desktop,10000,16,1000,2000,3000,4000,8,16,1,Pass,url\n"
        "synth,Desktop,Game2,2020,CPU-A,6000,GPU-A,Desktop,10000,16,1000,2000,3000,4000,8,16,1,Pass,url\n",  # CPU-A has conflicting 5000 vs 6000
        encoding="utf-8",
    )
    with pytest.raises(DataIntegrityError) as exc_info:
        HardwareService(dataset_path=csv_file)
    assert "Xung đột điểm CPU" in str(exc_info.value)

