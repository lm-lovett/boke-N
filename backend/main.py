import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from app.database import init_database
from app.factory import create_app


@asynccontextmanager
async def lifespan(_):
    init_database()
    yield


app = create_app(lifespan=lifespan)
