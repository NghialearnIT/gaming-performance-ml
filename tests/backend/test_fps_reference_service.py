"""Unit tests for FpsReferenceService."""
import pytest
from backend.services.fps_reference_service import (
    FpsReferenceService,
    fps_reference_service,
)


def test_fps_reference_valid_desktop():
    """Kiểm tra GPU Desktop có dữ liệu chuẩn trong bảng benchmark GTA V."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
    )
    assert result.has_reference is True
    assert result.reference_fps == 156.0
    assert result.resolution == "1920x1080"
    assert result.graphics_preset == "high"
    assert result.message is None


def test_fps_reference_laptop_dedicated_gpu_no_substitution():
    """Kiểm tra GPU Laptop không được dùng FPS của GPU Desktop."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="GeForce RTX 4060 Laptop GPU",
        device_type="laptop",
    )
    # Tuyệt đối không dùng FPS của RTX 4060 Desktop
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "không có cột đo FPS riêng" in result.message


def test_fps_reference_unsupported_gpu():
    """Kiểm tra GPU không có cột benchmark trong bảng games_fps_reference.csv."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="Radeon R9 350",
        device_type="desktop",
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "không có cột đo FPS thực tế" in result.message


def test_fps_reference_game_not_found():
    """Kiểm tra game không có trong bảng tham chiếu FPS."""
    result = fps_reference_service.get_fps_reference(
        game_name="Nonexistent Game Title 123",
        gpu_model="GeForce RTX 3060",
        device_type="desktop",
    )
    assert result.has_reference is False
    assert result.reference_fps is None
    assert "không có trong bảng dữ liệu tham chiếu" in result.message


def test_fps_reference_igpu():
    """Kiểm tra iGPU (Intel Iris Xe) được hỗ trợ trên laptop."""
    result = fps_reference_service.get_fps_reference(
        game_name="Grand Theft Auto V",
        gpu_model="Intel Iris Xe",
        device_type="laptop",
    )
    assert result.has_reference is True
    assert result.reference_fps == 33.0
