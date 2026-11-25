"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Kiểm tra health check GET /."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "options" in data["endpoints"]["catalog"]


def test_get_options_catalog(client):
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


def test_predict_valid_desktop(client):
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

    assert data["avg_fps"] == 93
    assert data["fps_source"] == "reference"
    assert data["machine_learning"]["model_loaded"] is True
    assert data["machine_learning"]["prediction"] is None
    assert data["machine_learning"]["status"] == "reference_available"


def test_predict_nonexistent_cpu_returns_400(client):
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


def test_predict_nonexistent_gpu_returns_400(client):
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


def test_predict_device_mismatch_returns_400(client):
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


def test_predict_nonexistent_game_returns_400(client):
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


def test_predict_invalid_ram_returns_422(client):
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


def test_predict_invalid_device_type_returns_422(client):
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


@pytest.fixture
def desktop_payload():
    return {
        "device_type": "desktop",
        "cpu_model": "Intel Core i5-12400F",
        "gpu_model": "NVIDIA RTX 3060",
        "game": "Red Dead Redemption 2",
        "ram_gb": 16,
    }


@pytest.mark.parametrize("overrides", [
    {"resolution": "2560x1440"},
    {"graphics_preset": "potato"},
    {"gpu_tgp_w": 0},
])
def test_predict_rejects_invalid_settings(client, desktop_payload, overrides):
    response = client.post("/predict", json=desktop_payload | overrides)
    assert response.status_code == 422


@pytest.mark.parametrize("preset", ["low", "medium"])
def test_predict_only_returns_fps_for_supported_presets(client, desktop_payload, preset):
    response = client.post("/predict", json=desktop_payload | {"graphics_preset": preset})
    assert response.status_code == 200
    data = response.json()
    assert data["avg_fps"] is None
    assert data["fps_source"] is None
    assert data["fps_reference"]["has_reference"] is False
    assert "1080p High" in data["fps_message"]


def test_predict_under_minimum_has_separate_reference(client, desktop_payload):
    response = client.post("/predict", json=desktop_payload | {"ram_gb": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["rule_based"]["status"] == "Khong_dat_toi_thieu"
    assert data["avg_fps"] is None
    assert data["fps_reference"]["reference_fps"] == 93


@pytest.mark.parametrize(("device", "gpu", "cpu"), [
    ("desktop", "Radeon RX 6600", "Ryzen 5 5600"),
    ("laptop", "NVIDIA RTX 4060 Laptop GPU", "Intel Core i7-12700H"),
])
def test_predict_estimates_fps_for_gpus_missing_from_reference(client, desktop_payload, device, gpu, cpu):
    response = client.post("/predict", json=desktop_payload | {
        "device_type": device, "gpu_model": gpu, "cpu_model": cpu,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["fps_source"] == "ml_estimate"
    assert data["fps_reference"]["has_reference"] is False
    assert data["machine_learning"]["status"] == "estimated"
    assert data["avg_fps"] == data["machine_learning"]["prediction"]["avg_fps"]
    assert 0 < data["avg_fps"] <= 360
    assert data["one_percent_low_fps"] is None


@pytest.mark.parametrize(("game", "name", "fps"), [
    ("Valorant", "Valorant", 251),
    ("cs2", "Counter-Strike 2", 248),
    ("lol", "League of Legends", 360),
])
def test_reference_only_games_are_in_options_and_can_return_fps(client, desktop_payload, game, name, fps):
    options = client.get("/options").json()
    assert name in [item["value"] for item in options["games"]]
    assert options["fps_presets"] == ["high"]
    response = client.post("/analyze", json=desktop_payload | {"game": game})
    assert response.status_code == 200
    data = response.json()
    assert data["avg_fps"] == fps
    assert data["rule_based"]["status"] == "Partial_minimum"
    assert data["rule_based"]["components"]["gpu"]["passed_min"]
    assert data["rule_based"]["game_requirements"]["min_cpu_description"]
    assert client.post("/predict", json=desktop_payload | {"game": game, "ram_gb": 1}).json()["avg_fps"] is None


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5501", "http://localhost:5501"])
def test_cors_from_frontend_port_5501(client, origin):
    response = client.options("/predict", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_fastapi_serves_frontend(client):
    assert "Dự đoán FPS" in client.get("/app/").text
    assert client.get("/app/app.js").status_code == 200
