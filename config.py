import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
MODELS_DIR = BASE_DIR / "models"

for directory in [TEMP_DIR, OUTPUT_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Default transcription settings
DEFAULT_WHISPER_MODEL = "base"  # options: tiny, base, small, medium, large-v3
DEVICE = "cuda"                 # RTX 3050 has 6GB VRAM, perfect for cuda
COMPUTE_TYPE = "float16"        # Fast half-precision on Tensor Cores

# Target clip duration defaults (seconds)
DEFAULT_MIN_DURATION = 20
DEFAULT_MAX_DURATION = 60
TARGET_ASPECT_RATIO = "9:16"  # 1080x1920 for YouTube Shorts, TikTok, Instagram Reels
