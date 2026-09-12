from __future__ import annotations

from datetime import datetime
from typing import Any

from app.repository_base import format_datetime, map_article, map_comment, placeholders


class D1BlogRepository:
    def __init__(self, db: Any):
        self.db = db

    async def _all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        stmt = self.db.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        result = await stmt.all()
        return list(result.results or [])

    async def _first(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        stmt = self.db.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        row = await stmt.first()
        return dict(row) if row else None

    async def _run(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        stmt = self.db.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        return await stmt.run()

    def _last_row_id(self, result: Any) -> int:
        meta = result.meta
        if isinstance(meta, dict):
            return int(meta.get("last_row_id") or 0)
        return int(getattr(meta, "last_row_id", 0))

    async def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        row = await self._first(
            "SELECT id, username, nickname, password_hash FROM users WHERE username = ?",
            (username,),
        )
        if not row:
            return None
        row["roleIds"] = await self._list_role_ids_by_user_id(row["id"])
        row["passwordHash"] = row.pop("password_hash")
        return row

    async def find_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        row = await self._first(
            "SELECT id, username, nickname, password_hash FROM users WHERE id = ?",
            (user_id,),
        )
        if not row:
            return None
        row["roleIds"] = await self._list_role_ids_by_user_id(row["id"])
        row["passwordHash"] = row.pop("password_hash")
        return row

    async def exists_user_by_username(self, username: str) -> bool:
        row = await self._first("SELECT COUNT(1) AS cnt FROM users WHERE username = ?", (username,))
        return bool(row and row["cnt"] > 0)

    async def list_users(self) -> list[dict[str, Any]]:
        rows = await self._all("SELECT id, username, nickname, password_hash FROM users ORDER BY id ASC")
        role_map = await self._list_role_ids_by_user_ids([row["id"] for row in rows])
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "nickname": row["nickname"],
                "passwordHash": row["password_hash"],
                "roleIds": role_map.get(row["id"], []),
            }
            for row in rows
        ]

    async def insert_user(
        self, username: str, nickname: str, password_hash: str, role_ids: list[int]
    ) -> int:
        result = await self._run(
            "INSERT INTO users (username, nickname, password_hash) VALUES (?, ?, ?)",
            (username, nickname, password_hash),
        )
        user_id = self._last_row_id(result)
        await self._replace_user_roles(user_id, role_ids)
        return user_id

    async def update_user(self, user_id: int, nickname: str, password_hash: str) -> None:
        await self._run(
            "UPDATE users SET nickname = ?, password_hash = ? WHERE id = ?",
            (nickname, password_hash, user_id),
        )

    async def replace_user_roles(self, user_id: int, role_ids: list[int]) -> None:
        await self._replace_user_roles(user_id, role_ids)

    async def delete_user(self, user_id: int) -> None:
        await self._run("DELETE FROM users WHERE id = ?", (user_id,))

    async def list_roles(self) -> list[dict[str, Any]]:
        rows = await self._all("SELECT id, name, description FROM roles ORDER BY id ASC")
        resource_map = await self._list_resource_ids_by_role_ids([row["id"] for row in rows])
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row.get("description"),
                "resourceIds": resource_map.get(row["id"], []),
            }
            for row in rows
        ]

    async def list_roles_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        rows = await self._all(
            f"SELECT id, name, description FROM roles WHERE id IN ({placeholders(ids)})",
            tuple(ids),
        )
        resource_map = await self._list_resource_ids_by_role_ids([row["id"] for row in rows])
        roles = [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row.get("description"),
                "resourceIds": resource_map.get(row["id"], []),
            }
            for row in rows
        ]
        roles.sort(key=lambda item: item["id"])
        return roles

    async def find_role_by_name(self, name: str) -> dict[str, Any] | None:
        row = await self._first("SELECT id, name, description FROM roles WHERE name = ?", (name,))
        if not row:
            return None
        row["resourceIds"] = await self._list_resource_ids_by_role_id(row["id"])
        return row

    async def find_role_by_id(self, role_id: int) -> dict[str, Any] | None:
        row = await self._first(
            "SELECT id, name, description FROM roles WHERE id = ?",
            (role_id,),
        )
        if not row:
            return None
        row["resourceIds"] = await self._list_resource_ids_by_role_id(row["id"])
        return row

    async def exists_role_name(self, name: str) -> bool:
        row = await self._first("SELECT COUNT(1) AS cnt FROM roles WHERE name = ?", (name,))
        return bool(row and row["cnt"] > 0)

    async def insert_role(self, name: str, description: str, resource_ids: list[int]) -> int:
        result = await self._run(
            "INSERT INTO roles (name, description) VALUES (?, ?)",
            (name, description),
        )
        role_id = self._last_row_id(result)
        await self._replace_role_resources(role_id, resource_ids)
        return role_id

    async def update_role(self, role_id: int, name: str, description: str) -> None:
        await self._run(
            "UPDATE roles SET name = ?, description = ? WHERE id = ?",
            (name, description, role_id),
        )

    async def replace_role_resources(self, role_id: int, resource_ids: list[int]) -> None:
        await self._replace_role_resources(role_id, resource_ids)

    async def delete_role(self, role_id: int) -> None:
        await self._run("DELETE FROM roles WHERE id = ?", (role_id,))

    async def list_resources(self) -> list[dict[str, Any]]:
        return await self._all("SELECT id, code, name FROM resources ORDER BY id ASC")

    async def list_resources_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        return await self._all(
            f"SELECT id, code, name FROM resources WHERE id IN ({placeholders(ids)})",
            tuple(ids),
        )

    async def find_resource_by_id(self, resource_id: int) -> dict[str, Any] | None:
        return await self._first(
            "SELECT id, code, name FROM resources WHERE id = ?",
            (resource_id,),
        )

    async def insert_resource(self, code: str, name: str) -> int:
        result = await self._run(
            "INSERT INTO resources (code, name) VALUES (?, ?)",
            (code, name),
        )
        return self._last_row_id(result)

    async def update_resource(self, resource_id: int, code: str, name: str) -> None:
        await self._run(
            "UPDATE resources SET code = ?, name = ? WHERE id = ?",
            (code, name, resource_id),
        )

    async def delete_resource(self, resource_id: int) -> None:
        await self._run("DELETE FROM resources WHERE id = ?", (resource_id,))

    async def list_admin_articles(self) -> list[dict[str, Any]]:
        rows = await self._all(
            "SELECT id, title, summary, content, author, views, published, created_at "
            "FROM articles ORDER BY created_at DESC"
        )
        return [map_article(row) for row in rows]

    async def find_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        row = await self._first(
            "SELECT id, title, summary, content, author, views, published, created_at "
            "FROM articles WHERE id = ?",
            (article_id,),
        )
        return map_article(row) if row else None

    async def find_published_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        row = await self._first(
            "SELECT id, title, summary, content, author, views, published, created_at "
            "FROM articles WHERE id = ? AND published = 1",
            (article_id,),
        )
        return map_article(row) if row else None

    async def insert_article(
        self,
        title: str,
        summary: str,
        content: str,
        author: str,
        published: bool,
        created_at: datetime,
    ) -> int:
        result = await self._run(
            "INSERT INTO articles (title, summary, content, author, views, published, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                summary,
                content,
                author,
                0,
                1 if published else 0,
                format_datetime(created_at),
            ),
        )
        return self._last_row_id(result)

    async def update_article(
        self,
        article_id: int,
        title: str,
        summary: str,
        content: str,
        author: str,
        published: bool,
    ) -> None:
        await self._run(
            "UPDATE articles SET title = ?, summary = ?, content = ?, author = ?, published = ? "
            "WHERE id = ?",
            (title, summary, content, author, 1 if published else 0, article_id),
        )

    async def increment_article_views(self, article_id: int) -> None:
        await self._run("UPDATE articles SET views = views + 1 WHERE id = ?", (article_id,))

    async def delete_article(self, article_id: int) -> None:
        await self._run("DELETE FROM articles WHERE id = ?", (article_id,))

    async def list_public_articles(self) -> list[dict[str, Any]]:
        rows = await self._all(
            "SELECT id, title, summary, content, author, views, published, created_at "
            "FROM articles WHERE published = 1 ORDER BY created_at DESC"
        )
        return [map_article(row) for row in rows]

    async def top10_articles(self) -> list[dict[str, Any]]:
        rows = await self._all(
            "SELECT id, title, summary, content, author, views, published, created_at "
            "FROM articles WHERE published = 1 ORDER BY views DESC LIMIT 10"
        )
        return [map_article(row) for row in rows]

    async def list_banned_words(self) -> list[dict[str, Any]]:
        return await self._all("SELECT id, word FROM banned_words ORDER BY id ASC")

    async def insert_banned_word(self, word: str) -> int:
        result = await self._run("INSERT INTO banned_words (word) VALUES (?)", (word,))
        return self._last_row_id(result)

    async def delete_banned_word(self, banned_word_id: int) -> None:
        await self._run("DELETE FROM banned_words WHERE id = ?", (banned_word_id,))

    async def list_admin_comments(self) -> list[dict[str, Any]]:
        rows = await self._all(
            "SELECT id, article_id, user_id, username, content, created_at "
            "FROM comments ORDER BY created_at DESC"
        )
        return [map_comment(row) for row in rows]

    async def list_comments_by_article_id(self, article_id: int) -> list[dict[str, Any]]:
        rows = await self._all(
            "SELECT id, article_id, user_id, username, content, created_at "
            "FROM comments WHERE article_id = ? ORDER BY created_at DESC",
            (article_id,),
        )
        return [map_comment(row) for row in rows]

    async def find_comment_by_id(self, comment_id: int) -> dict[str, Any] | None:
        row = await self._first(
            "SELECT id, article_id, user_id, username, content, created_at "
            "FROM comments WHERE id = ?",
            (comment_id,),
        )
        return map_comment(row) if row else None

    async def insert_comment(
        self,
        article_id: int,
        user_id: int,
        username: str,
        content: str,
        created_at: datetime,
    ) -> int:
        result = await self._run(
            "INSERT INTO comments (article_id, user_id, username, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (article_id, user_id, username, content, format_datetime(created_at)),
        )
        return self._last_row_id(result)

    async def delete_comment(self, comment_id: int) -> None:
        await self._run("DELETE FROM comments WHERE id = ?", (comment_id,))

    async def _list_role_ids_by_user_id(self, user_id: int) -> list[int]:
        rows = await self._all(
            "SELECT role_id FROM user_roles WHERE user_id = ? ORDER BY role_id ASC",
            (user_id,),
        )
        return [int(row["role_id"]) for row in rows]

    async def _list_role_ids_by_user_ids(self, user_ids: list[int]) -> dict[int, list[int]]:
        if not user_ids:
            return {}
        rows = await self._all(
            f"SELECT user_id, role_id FROM user_roles WHERE user_id IN ({placeholders(user_ids)})",
            tuple(user_ids),
        )
        role_map: dict[int, list[int]] = {}
        for row in rows:
            role_map.setdefault(int(row["user_id"]), []).append(int(row["role_id"]))
        for role_ids in role_map.values():
            role_ids.sort()
        return role_map

    async def _list_resource_ids_by_role_id(self, role_id: int) -> list[int]:
        rows = await self._all(
            "SELECT resource_id FROM role_resources WHERE role_id = ? ORDER BY resource_id ASC",
            (role_id,),
        )
        return [int(row["resource_id"]) for row in rows]

    async def _list_resource_ids_by_role_ids(self, role_ids: list[int]) -> dict[int, list[int]]:
        if not role_ids:
            return {}
        rows = await self._all(
            f"SELECT role_id, resource_id FROM role_resources WHERE role_id IN ({placeholders(role_ids)})",
            tuple(role_ids),
        )
        resource_map: dict[int, list[int]] = {}
        for row in rows:
            resource_map.setdefault(int(row["role_id"]), []).append(int(row["resource_id"]))
        for resource_ids in resource_map.values():
            resource_ids.sort()
        return resource_map

    async def _replace_user_roles(self, user_id: int, role_ids: list[int]) -> None:
        await self._run("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        for role_id in role_ids:
            await self._run(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id),
            )

    async def _replace_role_resources(self, role_id: int, resource_ids: list[int]) -> None:
        await self._run("DELETE FROM role_resources WHERE role_id = ?", (role_id,))
        for resource_id in resource_ids:
            await self._run(
                "INSERT INTO role_resources (role_id, resource_id) VALUES (?, ?)",
                (role_id, resource_id),
            )
