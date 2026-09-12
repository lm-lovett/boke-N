from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None

    @staticmethod
    def ok(data: T, message: str = "ok") -> "ApiResponse[T]":
        return ApiResponse(success=True, message=message, data=data)

    @staticmethod
    def fail(message: str) -> "ApiResponse[None]":
        return ApiResponse(success=False, message=message, data=None)
