from fastapi import APIRouter, Header

from app.api_response import ApiResponse
from app.schemas import ArticleRequest, BannedWordRequest, ResourceRequest, RoleRequest, UserRequest
from app.service import BlogService

router = APIRouter(prefix="/api/admin", tags=["admin"])
service = BlogService()


@router.get("/roles")
def roles(authorization: str | None = Header(default=None, alias="Authorization")) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.list_roles())


@router.post("/roles")
def create_role(
    request: RoleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.create_role(request))


@router.put("/roles/{role_id}")
def update_role(
    role_id: int,
    request: RoleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.update_role(role_id, request))


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    service.delete_role(role_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/users")
def users(authorization: str | None = Header(default=None, alias="Authorization")) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.list_users())


@router.post("/users")
def create_user(
    request: UserRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.create_user(request))


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: UserRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.update_user(user_id, request))


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    service.delete_user(user_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/resources")
def resources(authorization: str | None = Header(default=None, alias="Authorization")) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.list_resources())


@router.post("/resources")
def create_resource(
    request: ResourceRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.create_resource(request))


@router.put("/resources/{resource_id}")
def update_resource(
    resource_id: int,
    request: ResourceRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.update_resource(resource_id, request))


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    service.delete_resource(resource_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/articles")
def articles(authorization: str | None = Header(default=None, alias="Authorization")) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.list_admin_articles())


@router.post("/articles")
def create_article(
    request: ArticleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    principal = service.require_admin(authorization)
    return ApiResponse.ok(service.create_article(request, principal))


@router.put("/articles/{article_id}")
def update_article(
    article_id: int,
    request: ArticleRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.update_article(article_id, request))


@router.delete("/articles/{article_id}")
def delete_article(
    article_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    service.delete_article(article_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/banned-words")
def banned_words(authorization: str | None = Header(default=None, alias="Authorization")) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.list_banned_words())


@router.post("/banned-words")
def create_banned_word(
    request: BannedWordRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.create_banned_word(request))


@router.delete("/banned-words/{banned_word_id}")
def delete_banned_word(
    banned_word_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    service.delete_banned_word(banned_word_id)
    return ApiResponse.ok(None, message="删除成功")


@router.get("/comments")
def comments(authorization: str | None = Header(default=None, alias="Authorization")) -> ApiResponse:
    service.require_admin(authorization)
    return ApiResponse.ok(service.list_admin_comments())


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ApiResponse:
    service.require_admin(authorization)
    service.delete_comment(comment_id)
    return ApiResponse.ok(None, message="删除成功")
