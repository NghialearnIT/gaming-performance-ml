"""FPS inference for GPUs without a matching reference column."""

import math

import numpy as np
from threadpoolctl import threadpool_limits

from backend.fps_model import ANCHOR_COLUMNS, features, load_or_train, number_or_nan
from backend.schemas import MachineLearningResult


class MLService:
    def __init__(self, artifact=None):
        self._artifact = artifact

    def load(self):
        self._artifact = load_or_train()

    def predict(self, game_row, gpu_score):
        if self._artifact is None:
            return MachineLearningResult()

        artifact = self._artifact
        version = artifact["version"]
        min_score, max_score = artifact["gpu_score_range"]
        if not min_score <= gpu_score <= max_score:
            return MachineLearningResult(
                model_loaded=True,
                model_version=version,
                status="outside_gpu_score_range",
                message="Điểm GPU nằm ngoài phạm vi huấn luyện. Chưa có FPS ước tính cho GPU này.",
            )

        game_features = features(game_row, gpu_score)
        if not any(math.isfinite(value) for value in game_features[-len(ANCHOR_COLUMNS):]):
            return MachineLearningResult(
                model_loaded=True,
                model_version=version,
                status="missing_game_features",
                message="Thiếu FPS tham chiếu của game để dùng mô hình ước tính.",
            )

        # HistGradientBoosting uses OpenMP. Limit threads for small API requests.
        with threadpool_limits(limits=2, user_api="openmp"):
            estimate = float(artifact["model"].predict(np.asarray([game_features]))[0])
        cap = number_or_nan(game_row.get("engine_fps_cap"))
        ceiling = min(cap, artifact["max_reference_fps"]) if math.isfinite(cap) else artifact["max_reference_fps"]
        return MachineLearningResult(
            model_loaded=True,
            model_version=version,
            status="estimated",
            message="Ước tính từ điểm GPU và FPS tham chiếu của cùng game trên một số GPU.",
            prediction={"avg_fps": round(max(0.0, min(estimate, ceiling)), 1)},
        )

    def status(self, reason, message):
        return MachineLearningResult(
            model_loaded=self._artifact is not None,
            model_version=self._artifact["version"] if self._artifact else None,
            status=reason,
            message=message,
        )


ml_service = MLService()
