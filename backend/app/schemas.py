from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class LoginRequest(CamelModel):
    username: str
    password: str


class RegisterRequest(CamelModel):
    username: str
    nickname: str | None = None
    password: str


class RoleRequest(CamelModel):
    name: str | None = None
    description: str | None = None
    resource_ids: list[int] | None = Field(default=None, alias="resourceIds")


class UserRequest(CamelModel):
    username: str | None = None
    nickname: str | None = None
    password: str | None = None
    role_ids: list[int] | None = Field(default=None, alias="roleIds")


class ResourceRequest(CamelModel):
    code: str | None = None
    name: str | None = None


class ArticleRequest(CamelModel):
    title: str | None = None
    summary: str | None = None
    content: str | None = None
    author: str | None = None
    published: bool | None = None


class BannedWordRequest(CamelModel):
    word: str | None = None


class CommentRequest(CamelModel):
    content: str


class Resource(CamelModel):
    id: int
    code: str
    name: str


class Role(CamelModel):
    id: int
    name: str
    description: str | None = None
    resource_ids: list[int] = Field(default_factory=list, alias="resourceIds")


class Article(CamelModel):
    id: int
    title: str
    summary: str | None = None
    content: str
    author: str | None = None
    views: int
    published: bool
    created_at: datetime | None = Field(default=None, alias="createdAt")


class BannedWord(CamelModel):
    id: int
    word: str


class Comment(CamelModel):
    id: int
    article_id: int = Field(alias="articleId")
    user_id: int = Field(alias="userId")
    username: str
    content: str
    created_at: datetime | None = Field(default=None, alias="createdAt")


class ArticleDetailResponse(CamelModel):
    article: Article
    comments: list[Comment]


class LoginResponse(CamelModel):
    token: str
    user: dict[str, Any]
    roles: list[Role]
    resources: list[Resource]


class AuthPrincipal:
    def __init__(self, user_id: int, username: str, role_ids: list[int], admin: bool):
        self.user_id = user_id
        self.username = username
        self.role_ids = role_ids
        self.admin = admin
