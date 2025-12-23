from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SCENES_DIR = DATA_DIR / "scenes"
INDEX_DIR = DATA_DIR / "index"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"

YOUTUBE_QUERY = "super mario movie trailer"
VIDEO_PATH = RAW_DIR / "video.mp4"
