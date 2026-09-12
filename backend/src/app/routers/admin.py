from fastapi import APIRouter, Depends, Header

from app.api_response import ApiResponse
from app.deps import get_blog_service
from app.schemas import ArticleRequest, BannedWordRequest, ResourceRequest, RoleRequest, UserRequest
from app.service import BlogService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/roles")
async def roles(
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.list_roles())


@router.post("/roles")
async def create_role(
    request: RoleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.create_role(request))


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    request: RoleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.update_role(role_id, request))


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    await service.delete_role(role_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/users")
async def users(
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.list_users())


@router.post("/users")
async def create_user(
    request: UserRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.create_user(request))


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: UserRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.update_user(user_id, request))


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    await service.delete_user(user_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/resources")
async def resources(
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.list_resources())


@router.post("/resources")
async def create_resource(
    request: ResourceRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.create_resource(request))


@router.put("/resources/{resource_id}")
async def update_resource(
    resource_id: int,
    request: ResourceRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.update_resource(resource_id, request))


@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    await service.delete_resource(resource_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/articles")
async def articles(
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.list_admin_articles())


@router.post("/articles")
async def create_article(
    request: ArticleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    principal = service.require_admin(authorization)
    return ApiResponse.ok(await service.create_article(request, principal))


@router.put("/articles/{article_id}")
async def update_article(
    article_id: int,
    request: ArticleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.update_article(article_id, request))


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    await service.delete_article(article_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/banned-words")
async def banned_words(
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.list_banned_words())


@router.post("/banned-words")
async def create_banned_word(
    request: BannedWordRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.create_banned_word(request))


@router.delete("/banned-words/{banned_word_id}")
async def delete_banned_word(
    banned_word_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    await service.delete_banned_word(banned_word_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/comments")
async def comments(
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(await service.list_admin_comments())


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service: BlogService = Depends(get_blog_service),
) -> ApiResponse:
    service.require_admin(authorization)
    await service.delete_comment(comment_id)
    return ApiResponse.ok(None, message="删除成功")
