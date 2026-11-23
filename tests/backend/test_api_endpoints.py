"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Kiểm tra health check GET /."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "options" in data["endpoints"]["catalog"]


def test_get_options_catalog():
    """Kiểm tra GET /options trả về đầy đủ danh mục không giới hạn 5 game."""
    response = client.get("/options")
    assert response.status_code == 200
    data = response.json()

    assert len(data["games"]) >= 580
    assert len(data["cpu_models"]) >= 400
    assert len(data["desktop_gpus"]) > 0
    assert len(data["laptop_gpus"]) > 0
    assert "desktop" in [d["value"] for d in data["device_types"]]
    assert "laptop" in [d["value"] for d in data["device_types"]]


def test_predict_valid_desktop():
    """Kiểm tra POST /predict với cấu hình Desktop hợp lệ."""
    payload = {
        "device_type": "desktop",
        "cpu_model": "Core i3-13100F",
        "gpu_model": "GeForce RTX 3060",
        "ram_gb": 16,
        "game": "Red Dead Redemption 2",
        "resolution": "1920x1080",
        "graphics_preset": "high",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Kiểm tra khối user_hardware
    assert data["user_hardware"]["cpu_score"] == 4750.0
    assert data["user_hardware"]["gpu_score"] > 0
    assert data["user_hardware"]["device_type"] == "desktop"

    # Kiểm tra khối rule_based
    assert data["rule_based"]["status"] in ("Dat_de_xuat", "Dat_toi_thieu_chua_dat_de_xuat")
    assert "cpu" in data["rule_based"]["components"]
    assert "gpu" in data["rule_based"]["components"]
    assert "ram" in data["rule_based"]["components"]

    # Kiểm tra khối machine_learning (chờ model thật)
    assert data["machine_learning"]["model_loaded"] is False
    assert data["machine_learning"]["prediction"] is None
    assert data["machine_learning"]["status"] == "waiting_for_user_model"


def test_predict_nonexistent_cpu_returns_400():
    """Kiểm tra CPU không tồn tại trả về lỗi HTTP 400 rõ ràng."""
    payload = {
        "device_type": "desktop",
        "cpu_model": "Fake Nonexistent CPU 9999",
        "gpu_model": "GeForce RTX 3060",
        "ram_gb": 16,
        "game": "Red Dead Redemption 2",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Không tìm thấy CPU" in response.json()["detail"]


def test_predict_nonexistent_gpu_returns_400():
    """Kiểm tra GPU không tồn tại trả về lỗi HTTP 400 rõ ràng."""
    payload = {
        "device_type": "desktop",
        "cpu_model": "Core i3-13100F",
        "gpu_model": "Fake Nonexistent GPU 9999",
        "ram_gb": 16,
        "game": "Red Dead Redemption 2",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Không tìm thấy GPU" in response.json()["detail"]


def test_predict_device_mismatch_returns_400():
    """Kiểm tra dùng GPU Desktop trên Laptop trả về lỗi HTTP 400 rõ ràng."""
    payload = {
        "device_type": "laptop",
        "cpu_model": "Core i3-13100F",
        "gpu_model": "GeForce RTX 3060",  # Card Desktop
        "ram_gb": 16,
        "game": "Red Dead Redemption 2",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "là card dành cho thiết bị Desktop" in response.json()["detail"]


def test_predict_nonexistent_game_returns_400():
    """Kiểm tra game không tồn tại trả về lỗi HTTP 400 rõ ràng."""
    payload = {
        "device_type": "desktop",
        "cpu_model": "Core i3-13100F",
        "gpu_model": "GeForce RTX 3060",
        "ram_gb": 16,
        "game": "Nonexistent Fake Game 2099",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Không tìm thấy cấu hình yêu cầu cho game" in response.json()["detail"]


def test_predict_invalid_ram_returns_422():
    """Kiểm tra RAM <= 0 trả về lỗi validation HTTP 422."""
    payload = {
        "device_type": "desktop",
        "cpu_model": "Core i3-13100F",
        "gpu_model": "GeForce RTX 3060",
        "ram_gb": 0,
        "game": "Red Dead Redemption 2",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_invalid_device_type_returns_422():
    """Kiểm tra device_type không hợp lệ trả về HTTP 422."""
    payload = {
        "device_type": "server",
        "cpu_model": "Core i3-13100F",
        "gpu_model": "GeForce RTX 3060",
        "ram_gb": 16,
        "game": "Red Dead Redemption 2",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
