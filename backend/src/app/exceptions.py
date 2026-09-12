from fastapi import Request
from fastapi.responses import JSONResponse

from app.api_response import ApiResponse


async def illegal_argument_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ApiResponse.fail(str(exc)).model_dump(),
    )


async def security_handler(_: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=ApiResponse.fail(str(exc)).model_dump(),
    )


async def generic_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail(f"服务器异常: {exc}").model_dump(),
    )
