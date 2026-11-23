"""Machine Learning Adapter Service.

Thiết kế theo dạng Adapter Pattern để tích hợp mô hình do bạn trực tiếp huấn luyện:
- Không tự huấn luyện mô hình.
- Không tự sinh file model.
- Không giả lập số liệu hoặc nhãn dự đoán.
- Luôn trả về prediction = None và status = 'waiting_for_user_model' khi chưa nạp model thật.
"""
from typing import Any, Dict, Optional

from backend.schemas import MachineLearningResult


class MLService:
    """Adapter interface for Machine Learning model prediction."""

    def __init__(self):
        self._model: Optional[Any] = None
        self._model_path: Optional[str] = None
        self._model_version: Optional[str] = None

    def is_model_loaded(self) -> bool:
        """Kiểm tra model đã được nạp hay chưa."""
        return self._model is not None

    def load_model(self, model_path: str, version: str = "1.0.0") -> None:
        """Nạp file model thật do bạn cung cấp (joblib, pickle, onnx,...).

        Chỉ được gọi khi bạn xác nhận và bàn giao file model.
        """
        # Sẵn sàng nạp mô hình thật trong tương lai
        import joblib
        self._model = joblib.load(model_path)
        self._model_path = model_path
        self._model_version = version

    def predict(self, features: Dict[str, Any]) -> MachineLearningResult:
        """Dự đoán hiệu năng hoặc phân loại cấu hình bằng mô hình Machine Learning.

        Khi chưa có model từ bạn:
        - Luôn trả về model_loaded: False, prediction: None.
        - Tuyệt đối không sinh số giả hoặc giả lập kết quả.
        """
        if not self.is_model_loaded():
            return MachineLearningResult(
                model_loaded=False,
                model_version=None,
                status="waiting_for_user_model",
                message="Chưa tích hợp mô hình ML (hệ thống sẵn sàng nhận model từ bạn)",
                prediction=None,
            )

        # Khi model thật được nạp:
        # result = self._model.predict(...)
        # return MachineLearningResult(model_loaded=True, model_version=self._model_version, prediction=result)
        raise NotImplementedError("Model chưa được cấu hình.")


# Singleton instance
ml_service = MLService()
