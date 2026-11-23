"""Unit tests for MLService adapter."""
import pytest
from backend.services.ml_service import MLService, ml_service


def test_ml_service_initial_state():
    """Kiểm tra ML Service ở trạng thái chờ mô hình thật."""
    assert ml_service.is_model_loaded() is False
    result = ml_service.predict({"feature": 123})
    assert result.model_loaded is False
    assert result.prediction is None
    assert result.status == "waiting_for_user_model"
    assert "Chưa tích hợp mô hình ML" in result.message


def test_ml_service_no_fake_predictions():
    """Đảm bảo không bao giờ sinh kết quả giả lập khi chưa có model."""
    service = MLService()
    assert service.is_model_loaded() is False
    res = service.predict({"cpu_score": 5000, "gpu_score": 10000})
    assert res.prediction is None
    assert res.model_version is None
