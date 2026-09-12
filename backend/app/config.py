import os


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


DB_HOST = _env("DB_HOST", "127.0.0.1")
DB_PORT = int(_env("DB_PORT", "3306"))
DB_NAME = _env("DB_NAME", "boke_n")
DB_USER = _env("DB_USER", _env("SPRING_DATASOURCE_USERNAME", "root"))
DB_PASSWORD = _env("DB_PASSWORD", _env("SPRING_DATASOURCE_PASSWORD", ""))

JWT_SECRET = _env("APP_JWT_SECRET", "blog-secret-key-change-me-please-use-env")
JWT_EXPIRE_SECONDS = int(_env("APP_JWT_EXPIRE_SECONDS", "604800"))
