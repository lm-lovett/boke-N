from fastapi import APIRouter, Depends, Header

from app.api_response import ApiResponse
from app.deps import get_blog_service
from app.schemas import CommentRequest
from app.service import BlogService

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/health")
async def health() -> ApiResponse:
    return ApiResponse.ok({"ok": True})


@router.get("/articles")
async def articles(service: BlogService = Depends(get_blog_service)) -> ApiResponse:
    return ApiResponse.ok(await service.list_public_articles())


@router.get("/articles/top10")
async def top10(service: BlogService = Depends(get_blog_service)) -> ApiResponse:
    return ApiResponse.ok(await service.top10_articles())


@router.get("/articles/{article_id}")
async def article_detail(
    article_id: int,
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    return ApiResponse.ok(await service.article_detail(article_id))


@router.post("/articles/{article_id}/comments")
async def create_comment(
    article_id: int,
    request: CommentRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    principal = service.parse_token(authorization)
    return ApiResponse.ok(await service.create_comment(article_id, request, principal))


@router.get("/weather")
async def weather(
    city: str | None = None,
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    return ApiResponse.ok(await service.weather(city))
