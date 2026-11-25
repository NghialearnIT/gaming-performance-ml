"""Train and cache a 1080p High FPS regression model from the reference table."""

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from threadpoolctl import threadpool_limits

from backend.config import MODELS_DIR
from backend.services.fps_reference_service import fps_reference_service
from backend.services.hardware_service import hardware_service

MODEL_VERSION = "fps-1080p-high-v1"
MODEL_PATH = MODELS_DIR / f"{MODEL_VERSION}.joblib"
GAME_FEATURES = ("min_gpu_g3d", "rec_gpu_g3d", "release_year", "engine_fps_cap")
ANCHOR_COLUMNS = (
    "fps_1080p_high_gtx_1650",
    "fps_1080p_high_rtx_3060",
    "fps_1080p_high_rtx_4070",
)


def number_or_nan(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) and result > 0 else math.nan


def features(row, gpu_score):
    return [
        gpu_score,
        *(number_or_nan(row.get(key)) for key in GAME_FEATURES),
        *(number_or_nan(row.get(column)) for column in ANCHOR_COLUMNS),
    ]


def reference_gpus():
    """Use one hardware score per source FPS column to avoid alias duplicates."""
    devices = (
        ("laptop", "Radeon 780M"),
        ("desktop", "GeForce GTX 1650"),
        ("desktop", "GeForce GTX 1660 SUPER"),
        ("desktop", "GeForce RTX 3060"),
        ("desktop", "Radeon RX 7600"),
        ("desktop", "GeForce RTX 4060"),
        ("desktop", "GeForce RTX 5060"),
        ("desktop", "GeForce RTX 4070"),
        ("desktop", "Radeon RX 7800 XT"),
        ("desktop", "GeForce RTX 5070"),
        ("desktop", "GeForce RTX 4090"),
    )
    return {
        fps_reference_service.get_gpu_column(gpu, device)[0]:
        hardware_service.get_gpu_info(gpu, device)[2]
        for device, gpu in devices
    }


def training_data(gpus):
    inputs, targets, games, gpu_columns = [], [], [], []
    for row in fps_reference_service.iter_rows():
        game = "".join(char for char in row["name"].casefold() if char.isalnum())
        for column, score in gpus.items():
            if column in ANCHOR_COLUMNS:
                continue
            value = number_or_nan(row.get(column))
            if math.isfinite(value):
                inputs.append(features(row, score))
                targets.append(value)
                games.append(game)
                gpu_columns.append(column)
    return np.asarray(inputs), np.asarray(targets), np.asarray(games), np.asarray(gpu_columns)


def new_model():
    return HistGradientBoostingRegressor(
        learning_rate=0.1, max_iter=180, max_leaf_nodes=31, min_samples_leaf=25,
        monotonic_cst=[1] + [0] * (len(GAME_FEATURES) + len(ANCHOR_COLUMNS)), random_state=42,
    )


def metrics(observed, predicted):
    return {
        "rows": len(observed),
        "mae_fps": round(float(mean_absolute_error(observed, predicted)), 2),
        "rmse_fps": round(float(root_mean_squared_error(observed, predicted)), 2),
    }


def train():
    gpus = reference_gpus()
    inputs, targets, games, columns = training_data(gpus)
    train, test = next(GroupShuffleSplit(test_size=0.2, random_state=42).split(inputs, targets, games))
    held_out = np.isin(columns, ["fps_1080p_high_rtx_4060", "fps_1080p_high_rx_7800_xt"])
    train_other_gpus = train[~held_out[train]]
    test_unseen_gpus = test[held_out[test]]

    with threadpool_limits(limits=2):
        evaluation = new_model().fit(inputs[train], targets[train])
        baseline = DummyRegressor(strategy="median").fit(inputs[train], targets[train])
        unseen = new_model().fit(inputs[train_other_gpus], targets[train_other_gpus])
        unseen_baseline = DummyRegressor(strategy="median").fit(
            inputs[train_other_gpus], targets[train_other_gpus]
        )
        report = {
            "source_rows": len(targets),
            "target_gpu_columns": len(gpus) - len(ANCHOR_COLUMNS),
            "anchor_gpu_columns": list(ANCHOR_COLUMNS),
            "test_game_groups": len(set(games[test])),
            "model": metrics(targets[test], evaluation.predict(inputs[test])),
            "median_baseline": metrics(targets[test], baseline.predict(inputs[test])),
            "model_unseen_games_and_gpu_columns": metrics(
                targets[test_unseen_gpus], unseen.predict(inputs[test_unseen_gpus])
            ),
            "median_baseline_unseen_games_and_gpu_columns": metrics(
                targets[test_unseen_gpus], unseen_baseline.predict(inputs[test_unseen_gpus])
            ),
        }
        model = new_model().fit(inputs, targets)

    return {
        "model": model,
        "version": MODEL_VERSION,
        "gpu_score_range": [min(gpus.values()), max(gpus.values())],
        "max_reference_fps": float(max(targets)),
        "report": report,
    }


def cache_key():
    digest = hashlib.sha256(sklearn.__version__.encode())
    for path in (
        Path(__file__),
        fps_reference_service.dataset_path,
        hardware_service.dataset_path,
        Path(__file__).parent / "services" / "hardware_service.py",
        Path(__file__).parent / "services" / "fps_reference_service.py",
    ):
        with path.open("rb") as source:
            digest.update(hashlib.file_digest(source, "sha256").digest())
    return digest.hexdigest()


def load_or_train(path=MODEL_PATH, force=False):
    key = cache_key()
    if path.exists() and not force:
        try:
            cached = joblib.load(path)
            if cached.get("cache_key") == key:
                return cached
        except Exception:
            # A stale or damaged local cache can be rebuilt from the versioned data.
            pass

    artifact = train()
    artifact["cache_key"] = key
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        joblib.dump(artifact, temp_path, compress=3)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Retrain and overwrite the local model cache")
    print(json.dumps(load_or_train(force=parser.parse_args().force)["report"], indent=2))


if __name__ == "__main__":
    main()
