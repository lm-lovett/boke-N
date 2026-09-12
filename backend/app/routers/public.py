from fastapi import APIRouter, Header

from app.api_response import ApiResponse
from app.schemas import CommentRequest
from app.service import BlogService

router = APIRouter(prefix="/api", tags=["public"])
service = BlogService()


@router.get("/health")
def health() -> ApiResponse:
    return ApiResponse.ok({"ok": True})


@router.get("/articles")
def articles() -> ApiResponse:
    return ApiResponse.ok(service.list_public_articles())


@router.get("/articles/top10")
def top10() -> ApiResponse:
    return ApiResponse.ok(service.top10_articles())


@router.get("/articles/{article_id}")
def article_detail(article_id: int) -> ApiResponse:
    return ApiResponse.ok(service.article_detail(article_id))


@router.post("/articles/{article_id}/comments")
def create_comment(
    article_id: int,
    request: CommentRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    principal = service.parse_token(authorization)
    return ApiResponse.ok(service.create_comment(article_id, request, principal))


@router.get("/weather")
def weather(city: str | None = None) -> ApiResponse:
    return ApiResponse.ok(service.weather(city))
