"""Tests of model support limits and inference for FPS estimates."""

import pytest

from backend.fps_model import ANCHOR_COLUMNS
from backend.services.ml_service import MLService


class FixedModel:
    def predict(self, values):
        assert values[0][0] == 17000
        return [110.5]


@pytest.fixture
def service():
    return MLService({
        "model": FixedModel(),
        "version": "test",
        "gpu_score_range": [7000, 38000],
        "max_reference_fps": 360,
    })


def test_unloaded_model_has_no_prediction():
    result = MLService().predict({}, 17000)
    assert result.model_loaded is False
    assert result.prediction is None


def test_fps_estimate_respects_game_cap(service):
    result = service.predict({ANCHOR_COLUMNS[0]: "80", "engine_fps_cap": "90"}, 17000)
    assert result.status == "estimated"
    assert result.prediction == {"avg_fps": 90}


def test_out_of_range_gpu_has_no_estimate(service):
    result = service.predict({ANCHOR_COLUMNS[0]: "80"}, 100)
    assert result.status == "outside_gpu_score_range"
    assert result.prediction is None


def test_missing_game_reference_has_no_estimate(service):
    result = service.predict({}, 17000)
    assert result.status == "missing_game_features"
    assert result.prediction is None
