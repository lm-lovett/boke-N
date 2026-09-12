import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app.database import init_database


@pytest.fixture(scope="session", autouse=True)
def prepare_sqlite_database(tmp_path_factory: pytest.TempPathFactory) -> None:
    db_path = tmp_path_factory.mktemp("sqlite") / "test_boke.db"
    os.environ["SQLITE_PATH"] = str(db_path)
    init_database(db_path)
