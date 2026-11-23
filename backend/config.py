"""Configuration settings and data paths for the backend service."""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
MODELS_DIR = BASE_DIR / "models"

# Dataset paths
GAME_REQUIREMENTS_PATH = DATA_RAW_DIR / "game_requirements.csv"
GAMES_FPS_REFERENCE_PATH = DATA_RAW_DIR / "games_fps_reference.csv"
GAMING_TRAIN_DATASET_PATH = DATA_RAW_DIR / "gaming_train_dataset.csv"

# Server configuration
API_HOST = "127.0.0.1"
API_PORT = 8000

# CORS settings
CORS_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost",
    "http://127.0.0.1",
]
