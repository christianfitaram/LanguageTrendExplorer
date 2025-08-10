# core/paths.py
from pathlib import Path
import os


def models_dir(cli_override: str | None = None) -> Path:
    # Priority: CLI flag > ENV > repo default
    if cli_override:
        return Path(cli_override).resolve()
    if (env := os.getenv("MODELS_DIR")):
        return Path(env).resolve()
    # default: repo_root/models
    here = Path(__file__).resolve().parent
    return (here / ".." / "models").resolve()


def hf_cache_dir(models_root: Path) -> Path:
    return models_root / "transformers"
