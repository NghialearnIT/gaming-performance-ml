"""Paths and runtime settings for the FPS application."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
MODELS_DIR = BASE_DIR / "models"
FRONTEND_DIR = BASE_DIR / "frontend"

GAME_REQUIREMENTS_PATH = DATA_RAW_DIR / "game_requirements.csv"
GAMES_FPS_REFERENCE_PATH = DATA_RAW_DIR / "games_fps_reference.csv"
GAMING_TRAIN_DATASET_PATH = DATA_RAW_DIR / "gaming_train_dataset.csv"

FPS_RESOLUTION = "1920x1080"
FPS_PRESET = "high"
API_HOST = "127.0.0.1"
API_PORT = 8000

CORS_ORIGINS = [
    f"http://{host}:{port}"
    for host in ("127.0.0.1", "localhost")
    for port in (5500, 5501, API_PORT)
]
CORS_ORIGINS.extend(["http://localhost", "http://127.0.0.1"])
CORS_ORIGINS.extend(
    origin.strip() for origin in os.environ.get("FPS_CORS_ORIGINS", "").split(",") if origin.strip()
)
