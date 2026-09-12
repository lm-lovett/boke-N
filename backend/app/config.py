import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_SQLITE_PATH = BACKEND_ROOT / "data" / "boke_n.db"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def get_sqlite_path() -> Path:
    return Path(_env("SQLITE_PATH", str(DEFAULT_SQLITE_PATH)))

JWT_SECRET = _env("APP_JWT_SECRET", "blog-secret-key-change-me-please-use-env")
JWT_EXPIRE_SECONDS = int(_env("APP_JWT_EXPIRE_SECONDS", "604800"))
