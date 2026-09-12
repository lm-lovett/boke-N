from contextlib import AbstractAsyncContextManager
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import generic_handler, illegal_argument_handler, security_handler
from app.routers import admin, auth, public


def create_app(
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
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
    return app
