import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "app" / "models"
RULES_CONFIG_PATH = BASE_DIR / "app" / "compliance" / "rules_config.json"

# App & Model Settings
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.2")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
