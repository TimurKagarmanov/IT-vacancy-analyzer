from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORAGE_DIR = ROOT / "storage"


def ensure_storage() -> Path:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return STORAGE_DIR
