from fastapi import APIRouter

from app.api_response import ApiResponse
from app.schemas import LoginRequest, RegisterRequest
from app.service import BlogService

router = APIRouter(prefix="/api/auth", tags=["auth"])
service = BlogService()


@router.post("/login")
def login(request: LoginRequest) -> ApiResponse:
    return ApiResponse.ok(service.login(request.username, request.password))


@router.post("/register")
def register(request: RegisterRequest) -> ApiResponse:
    return ApiResponse.ok(service.register(request))
