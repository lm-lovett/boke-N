from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_database
from app.exceptions import generic_handler, illegal_argument_handler, security_handler
from app.routers import admin, auth, public


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(title="boke-N API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(ValueError, illegal_argument_handler)
app.add_exception_handler(PermissionError, security_handler)
app.add_exception_handler(Exception, generic_handler)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(admin.router)
