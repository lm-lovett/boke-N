from __future__ import annotations

from datetime import datetime, timezone

import bcrypt

from app.jwt_service import JwtService
from app.repository import BlogRepository
from app.schemas import (
    ArticleRequest,
    AuthPrincipal,
    BannedWordRequest,
    CommentRequest,
    LoginResponse,
    RegisterRequest,
    ResourceRequest,
    RoleRequest,
    UserRequest,
)


class BlogService:
    def __init__(self, repo: BlogRepository | None = None, jwt_service: JwtService | None = None):
        self.repo = repo or BlogRepository()
        self.jwt_service = jwt_service or JwtService()

    def login(self, username: str, password: str) -> LoginResponse:
        if self._blank(username) or self._blank(password):
            raise ValueError("用户名和密码不能为空")
        user = self.repo.find_user_by_username(username)
        if not user or not self._verify_password(password, user["passwordHash"]):
            raise ValueError("用户名或密码错误")

        roles = self.repo.list_roles_by_ids(user["roleIds"])
        resource_ids = []
        seen = set()
        for role in roles:
            for resource_id in role["resourceIds"]:
                if resource_id not in seen:
                    seen.add(resource_id)
                    resource_ids.append(resource_id)
        resources = self.repo.list_resources_by_ids(resource_ids)
        is_admin = any(role["name"] == "admin" for role in roles)
        token = self.jwt_service.issue_token(user["id"], user["username"], user["roleIds"], is_admin)
        return LoginResponse(
            token=token,
            user=self._sanitize_user(user),
            roles=roles,
            resources=resources,
        )

    def register(self, request: RegisterRequest) -> dict:
        if self._blank(request.username) or self._blank(request.password):
            raise ValueError("用户名和密码不能为空")
        if self.repo.exists_user_by_username(request.username):
            raise ValueError("用户名已存在")

        reader = self.repo.find_role_by_name("reader")
        if not reader:
            raise ValueError("reader 角色不存在")

        user_id = self.repo.insert_user(
            request.username,
            request.nickname if not self._blank(request.nickname) else request.username,
            self._hash_password(request.password),
            [reader["id"]],
        )
        saved = self.repo.find_user_by_id(user_id)
        if not saved:
            raise RuntimeError("用户创建失败")
        return self._sanitize_user(saved)

    def list_roles(self) -> list[dict]:
        return self.repo.list_roles()

    def create_role(self, request: RoleRequest) -> dict:
        if self._blank(request.name):
            raise ValueError("角色名不能为空")
        if self.repo.exists_role_name(request.name):
            raise ValueError("角色名已存在")
        role_id = self.repo.insert_role(
            request.name,
            request.description or "",
            self._sanitize_long_list(request.resource_ids),
        )
        role = self.repo.find_role_by_id(role_id)
        if not role:
            raise RuntimeError("角色创建失败")
        return role

    def update_role(self, role_id: int, request: RoleRequest) -> dict:
        role = self.repo.find_role_by_id(role_id)
        if not role:
            raise ValueError("角色不存在")
        next_name = role["name"] if self._blank(request.name) else request.name
        next_desc = role["description"] if request.description is None else request.description
        self.repo.update_role(role_id, next_name, next_desc)
        if request.resource_ids is not None:
            self.repo.replace_role_resources(role_id, self._sanitize_long_list(request.resource_ids))
        updated = self.repo.find_role_by_id(role_id)
        if not updated:
            raise RuntimeError("角色更新失败")
        return updated

    def delete_role(self, role_id: int) -> None:
        if not self.repo.find_role_by_id(role_id):
            raise ValueError("角色不存在")
        self.repo.delete_role(role_id)

    def list_users(self) -> list[dict]:
        return [self._sanitize_user(user) for user in self.repo.list_users()]

    def create_user(self, request: UserRequest) -> dict:
        if self._blank(request.username) or self._blank(request.password):
            raise ValueError("用户名和密码不能为空")
        if self.repo.exists_user_by_username(request.username):
            raise ValueError("用户名已存在")
        user_id = self.repo.insert_user(
            request.username,
            request.nickname if not self._blank(request.nickname) else request.username,
            self._hash_password(request.password),
            self._sanitize_long_list(request.role_ids),
        )
        saved = self.repo.find_user_by_id(user_id)
        if not saved:
            raise RuntimeError("用户创建失败")
        return self._sanitize_user(saved)

    def update_user(self, user_id: int, request: UserRequest) -> dict:
        existing = self.repo.find_user_by_id(user_id)
        if not existing:
            raise ValueError("用户不存在")
        nickname = existing["nickname"] if request.nickname is None else request.nickname
        password_hash = existing["passwordHash"]
        if not self._blank(request.password):
            password_hash = self._hash_password(request.password)
        self.repo.update_user(user_id, nickname, password_hash)
        if request.role_ids is not None:
            self.repo.replace_user_roles(user_id, self._sanitize_long_list(request.role_ids))
        updated = self.repo.find_user_by_id(user_id)
        if not updated:
            raise RuntimeError("用户更新失败")
        return self._sanitize_user(updated)

    def delete_user(self, user_id: int) -> None:
        if not self.repo.find_user_by_id(user_id):
            raise ValueError("用户不存在")
        self.repo.delete_user(user_id)

    def list_resources(self) -> list[dict]:
        return self.repo.list_resources()

    def create_resource(self, request: ResourceRequest) -> dict:
        if self._blank(request.code) or self._blank(request.name):
            raise ValueError("资源编码和名称不能为空")
        resource_id = self.repo.insert_resource(request.code, request.name)
        resource = self.repo.find_resource_by_id(resource_id)
        if not resource:
            raise RuntimeError("资源创建失败")
        return resource

    def update_resource(self, resource_id: int, request: ResourceRequest) -> dict:
        existing = self.repo.find_resource_by_id(resource_id)
        if not existing:
            raise ValueError("资源不存在")
        next_code = existing["code"] if self._blank(request.code) else request.code
        next_name = existing["name"] if self._blank(request.name) else request.name
        self.repo.update_resource(resource_id, next_code, next_name)
        updated = self.repo.find_resource_by_id(resource_id)
        if not updated:
            raise RuntimeError("资源更新失败")
        return updated

    def delete_resource(self, resource_id: int) -> None:
        if not self.repo.find_resource_by_id(resource_id):
            raise ValueError("资源不存在")
        self.repo.delete_resource(resource_id)

    def list_admin_articles(self) -> list[dict]:
        return self.repo.list_admin_articles()

    def create_article(self, request: ArticleRequest, principal: AuthPrincipal) -> dict:
        if self._blank(request.title) or self._blank(request.content):
            raise ValueError("文章标题和内容不能为空")
        article_id = self.repo.insert_article(
            request.title,
            request.summary or "",
            request.content,
            principal.username if self._blank(request.author) else request.author,
            request.published if request.published is not None else True,
            datetime.now(timezone.utc).replace(tzinfo=None),
        )
        article = self.repo.find_article_by_id(article_id)
        if not article:
            raise RuntimeError("文章创建失败")
        return article

    def update_article(self, article_id: int, request: ArticleRequest) -> dict:
        existing = self.repo.find_article_by_id(article_id)
        if not existing:
            raise ValueError("文章不存在")
        self.repo.update_article(
            article_id,
            request.title if request.title is not None else existing["title"],
            request.summary if request.summary is not None else existing.get("summary"),
            request.content if request.content is not None else existing["content"],
            request.author if request.author is not None else existing.get("author"),
            request.published if request.published is not None else existing["published"],
        )
        updated = self.repo.find_article_by_id(article_id)
        if not updated:
            raise RuntimeError("文章更新失败")
        return updated

    def delete_article(self, article_id: int) -> None:
        if not self.repo.find_article_by_id(article_id):
            raise ValueError("文章不存在")
        self.repo.delete_article(article_id)

    def list_banned_words(self) -> list[dict]:
        return self.repo.list_banned_words()

    def create_banned_word(self, request: BannedWordRequest) -> dict:
        if self._blank(request.word):
            raise ValueError("违禁词不能为空")
        banned_word_id = self.repo.insert_banned_word(request.word)
        for item in self.repo.list_banned_words():
            if item["id"] == banned_word_id:
                return item
        raise RuntimeError("违禁词创建失败")

    def delete_banned_word(self, banned_word_id: int) -> None:
        if not any(item["id"] == banned_word_id for item in self.repo.list_banned_words()):
            raise ValueError("违禁词不存在")
        self.repo.delete_banned_word(banned_word_id)

    def list_admin_comments(self) -> list[dict]:
        return self.repo.list_admin_comments()

    def delete_comment(self, comment_id: int) -> None:
        if not self.repo.find_comment_by_id(comment_id):
            raise ValueError("评论不存在")
        self.repo.delete_comment(comment_id)

    def list_public_articles(self) -> list[dict]:
        return self.repo.list_public_articles()

    def top10_articles(self) -> list[dict]:
        return self.repo.top10_articles()

    def article_detail(self, article_id: int) -> dict:
        if not self.repo.find_published_article_by_id(article_id):
            raise ValueError("文章不存在")
        self.repo.increment_article_views(article_id)
        article = self.repo.find_published_article_by_id(article_id)
        if not article:
            raise ValueError("文章不存在")
        comments = self.repo.list_comments_by_article_id(article_id)
        return {"article": article, "comments": comments}

    def create_comment(
        self, article_id: int, request: CommentRequest, principal: AuthPrincipal
    ) -> dict:
        if self._blank(request.content):
            raise ValueError("评论内容不能为空")
        if not self.repo.find_published_article_by_id(article_id):
            raise ValueError("文章不存在")

        for word in self.repo.list_banned_words():
            if word["word"] in request.content:
                raise ValueError(f"评论包含违禁词: {word['word']}")

        user = self.repo.find_user_by_id(principal.user_id)
        if not user:
            raise ValueError("用户不存在")

        comment_id = self.repo.insert_comment(
            article_id,
            user["id"],
            user["username"],
            request.content,
            datetime.now(timezone.utc).replace(tzinfo=None),
        )
        comment = self.repo.find_comment_by_id(comment_id)
        if not comment:
            raise RuntimeError("评论创建失败")
        return comment

    def weather(self, city: str | None) -> dict:
        final_city = "上海市" if self._blank(city) else city
        now = datetime.now(timezone.utc)
        return {
            "city": final_city,
            "weather": "多云",
            "temperature": "18~24°C",
            "humidity": "62%",
            "tip": "当前为演示天气数据，可后续接入真实天气 API。",
            "updatedAt": now.isoformat().replace("+00:00", "Z"),
        }

    def parse_token(self, authorization_header: str | None) -> AuthPrincipal:
        if self._blank(authorization_header) or not authorization_header.startswith("Bearer "):
            raise PermissionError("未登录或登录已过期")
        token = authorization_header[len("Bearer ") :]
        try:
            return self.jwt_service.parse_token(token)
        except Exception:
            raise PermissionError("未登录或登录已过期")

    def require_admin(self, authorization_header: str | None) -> AuthPrincipal:
        principal = self.parse_token(authorization_header)
        if not principal.admin:
            raise PermissionError("需要管理员权限")
        return principal

    def _blank(self, value: str | None) -> bool:
        return value is None or value.strip() == ""

    def _sanitize_long_list(self, values: list[int] | None) -> list[int]:
        if not values:
            return []
        seen = set()
        result = []
        for value in values:
            if value is None or value <= 0 or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    def _sanitize_user(self, user: dict) -> dict:
        return {
            "id": user["id"],
            "username": user["username"],
            "nickname": user["nickname"],
            "roleIds": user["roleIds"],
        }

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
