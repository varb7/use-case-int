"""Resource and writable-state paths for source and desktop launches."""
import os
from pathlib import Path


def data_directory(source_directory: Path) -> Path:
    configured = os.getenv("QUESTIONNAIRE_DATA_DIR")
    path = Path(configured).expanduser().resolve() if configured else source_directory
    path.mkdir(parents=True, exist_ok=True)
    return path


def desktop_directory() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if not base:
        raise RuntimeError("Windows could not locate your local application data folder.")
    return Path(base) / "QuestionnaireReview"
