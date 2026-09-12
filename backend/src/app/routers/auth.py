from fastapi import APIRouter, Depends

from app.api_response import ApiResponse
from app.deps import get_blog_service
from app.schemas import LoginRequest, RegisterRequest
from app.service import BlogService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(
    request: LoginRequest,
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    return ApiResponse.ok(await service.login(request.username, request.password))


@router.post("/register")
async def register(
    request: RegisterRequest,
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    return ApiResponse.ok(await service.register(request))
