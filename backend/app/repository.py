from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


class BlogRepository:
    @contextmanager
    def _connection(self) -> Iterator[pymysql.connections.Connection]:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _placeholders(self, values: list[Any]) -> str:
        return ",".join(["%s"] * len(values))

    def _map_article(self, row: dict[str, Any]) -> dict[str, Any]:
        created_at = row.get("created_at")
        return {
            "id": row["id"],
            "title": row["title"],
            "summary": row.get("summary"),
            "content": row["content"],
            "author": row.get("author"),
            "views": int(row.get("views") or 0),
            "published": bool(row.get("published")),
            "createdAt": created_at.isoformat().replace("+00:00", "Z")
            if isinstance(created_at, datetime)
            else created_at,
        }

    def _map_comment(self, row: dict[str, Any]) -> dict[str, Any]:
        created_at = row.get("created_at")
        return {
            "id": row["id"],
            "articleId": row["article_id"],
            "userId": row["user_id"],
            "username": row["username"],
            "content": row["content"],
            "createdAt": created_at.isoformat().replace("+00:00", "Z")
            if isinstance(created_at, datetime)
            else created_at,
        }

    def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, nickname, password_hash FROM users WHERE username = %s",
                    (username,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                row["roleIds"] = self._list_role_ids_by_user_id(cur, row["id"])
                row["passwordHash"] = row.pop("password_hash")
                return row

    def find_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, nickname, password_hash FROM users WHERE id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                row["roleIds"] = self._list_role_ids_by_user_id(cur, row["id"])
                row["passwordHash"] = row.pop("password_hash")
                return row

    def exists_user_by_username(self, username: str) -> bool:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(1) AS cnt FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                return bool(row and row["cnt"] > 0)

    def list_users(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, nickname, password_hash FROM users ORDER BY id ASC"
                )
                rows = cur.fetchall()
                role_map = self._list_role_ids_by_user_ids(
                    cur, [row["id"] for row in rows]
                )
                users = []
                for row in rows:
                    users.append(
                        {
                            "id": row["id"],
                            "username": row["username"],
                            "nickname": row["nickname"],
                            "passwordHash": row["password_hash"],
                            "roleIds": role_map.get(row["id"], []),
                        }
                    )
                return users

    def insert_user(
        self, username: str, nickname: str, password_hash: str, role_ids: list[int]
    ) -> int:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, nickname, password_hash) VALUES (%s, %s, %s)",
                    (username, nickname, password_hash),
                )
                user_id = cur.lastrowid
                self._replace_user_roles(cur, user_id, role_ids)
                return int(user_id)

    def update_user(self, user_id: int, nickname: str, password_hash: str) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET nickname = %s, password_hash = %s WHERE id = %s",
                    (nickname, password_hash, user_id),
                )

    def replace_user_roles(self, user_id: int, role_ids: list[int]) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                self._replace_user_roles(cur, user_id, role_ids)

    def delete_user(self, user_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

    def list_roles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, description FROM roles ORDER BY id ASC")
                rows = cur.fetchall()
                resource_map = self._list_resource_ids_by_role_ids(
                    cur, [row["id"] for row in rows]
                )
                return [
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row.get("description"),
                        "resourceIds": resource_map.get(row["id"], []),
                    }
                    for row in rows
                ]

    def list_roles_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT id, name, description FROM roles WHERE id IN ({self._placeholders(ids)})",
                    ids,
                )
                rows = cur.fetchall()
                resource_map = self._list_resource_ids_by_role_ids(
                    cur, [row["id"] for row in rows]
                )
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

    def find_role_by_name(self, name: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, description FROM roles WHERE name = %s", (name,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                row["resourceIds"] = self._list_resource_ids_by_role_id(cur, row["id"])
                return row

    def find_role_by_id(self, role_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, description FROM roles WHERE id = %s", (role_id,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                row["resourceIds"] = self._list_resource_ids_by_role_id(cur, row["id"])
                return row

    def exists_role_name(self, name: str) -> bool:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(1) AS cnt FROM roles WHERE name = %s", (name,))
                row = cur.fetchone()
                return bool(row and row["cnt"] > 0)

    def insert_role(self, name: str, description: str, resource_ids: list[int]) -> int:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s)",
                    (name, description),
                )
                role_id = cur.lastrowid
                self._replace_role_resources(cur, role_id, resource_ids)
                return int(role_id)

    def update_role(self, role_id: int, name: str, description: str) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE roles SET name = %s, description = %s WHERE id = %s",
                    (name, description, role_id),
                )

    def replace_role_resources(self, role_id: int, resource_ids: list[int]) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                self._replace_role_resources(cur, role_id, resource_ids)

    def delete_role(self, role_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM roles WHERE id = %s", (role_id,))

    def list_resources(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, code, name FROM resources ORDER BY id ASC")
                return list(cur.fetchall())

    def list_resources_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT id, code, name FROM resources WHERE id IN ({self._placeholders(ids)})",
                    ids,
                )
                return list(cur.fetchall())

    def find_resource_by_id(self, resource_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, code, name FROM resources WHERE id = %s", (resource_id,)
                )
                return cur.fetchone()

    def insert_resource(self, code: str, name: str) -> int:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO resources (code, name) VALUES (%s, %s)", (code, name)
                )
                return int(cur.lastrowid)

    def update_resource(self, resource_id: int, code: str, name: str) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE resources SET code = %s, name = %s WHERE id = %s",
                    (code, name, resource_id),
                )

    def delete_resource(self, resource_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM resources WHERE id = %s", (resource_id,))

    def list_admin_articles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, summary, content, author, views, published, created_at "
                    "FROM articles ORDER BY created_at DESC"
                )
                return [self._map_article(row) for row in cur.fetchall()]

    def find_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, summary, content, author, views, published, created_at "
                    "FROM articles WHERE id = %s",
                    (article_id,),
                )
                row = cur.fetchone()
                return self._map_article(row) if row else None

    def find_published_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, summary, content, author, views, published, created_at "
                    "FROM articles WHERE id = %s AND published = 1",
                    (article_id,),
                )
                row = cur.fetchone()
                return self._map_article(row) if row else None

    def insert_article(
        self,
        title: str,
        summary: str,
        content: str,
        author: str,
        published: bool,
        created_at: datetime,
    ) -> int:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO articles (title, summary, content, author, views, published, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (title, summary, content, author, 0, published, created_at),
                )
                return int(cur.lastrowid)

    def update_article(
        self,
        article_id: int,
        title: str,
        summary: str,
        content: str,
        author: str,
        published: bool,
    ) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE articles SET title = %s, summary = %s, content = %s, author = %s, published = %s "
                    "WHERE id = %s",
                    (title, summary, content, author, published, article_id),
                )

    def increment_article_views(self, article_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE articles SET views = views + 1 WHERE id = %s", (article_id,)
                )

    def delete_article(self, article_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM articles WHERE id = %s", (article_id,))

    def list_public_articles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, summary, content, author, views, published, created_at "
                    "FROM articles WHERE published = 1 ORDER BY created_at DESC"
                )
                return [self._map_article(row) for row in cur.fetchall()]

    def top10_articles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, summary, content, author, views, published, created_at "
                    "FROM articles WHERE published = 1 ORDER BY views DESC LIMIT 10"
                )
                return [self._map_article(row) for row in cur.fetchall()]

    def list_banned_words(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, word FROM banned_words ORDER BY id ASC")
                return list(cur.fetchall())

    def insert_banned_word(self, word: str) -> int:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO banned_words (word) VALUES (%s)", (word,))
                return int(cur.lastrowid)

    def delete_banned_word(self, banned_word_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM banned_words WHERE id = %s", (banned_word_id,))

    def list_admin_comments(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, article_id, user_id, username, content, created_at "
                    "FROM comments ORDER BY created_at DESC"
                )
                return [self._map_comment(row) for row in cur.fetchall()]

    def list_comments_by_article_id(self, article_id: int) -> list[dict[str, Any]]:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, article_id, user_id, username, content, created_at "
                    "FROM comments WHERE article_id = %s ORDER BY created_at DESC",
                    (article_id,),
                )
                return [self._map_comment(row) for row in cur.fetchall()]

    def find_comment_by_id(self, comment_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, article_id, user_id, username, content, created_at "
                    "FROM comments WHERE id = %s",
                    (comment_id,),
                )
                row = cur.fetchone()
                return self._map_comment(row) if row else None

    def insert_comment(
        self,
        article_id: int,
        user_id: int,
        username: str,
        content: str,
        created_at: datetime,
    ) -> int:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO comments (article_id, user_id, username, content, created_at) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (article_id, user_id, username, content, created_at),
                )
                return int(cur.lastrowid)

    def delete_comment(self, comment_id: int) -> None:
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM comments WHERE id = %s", (comment_id,))

    def _list_role_ids_by_user_id(self, cur: DictCursor, user_id: int) -> list[int]:
        cur.execute(
            "SELECT role_id FROM user_roles WHERE user_id = %s ORDER BY role_id ASC",
            (user_id,),
        )
        return [int(row["role_id"]) for row in cur.fetchall()]

    def _list_role_ids_by_user_ids(
        self, cur: DictCursor, user_ids: list[int]
    ) -> dict[int, list[int]]:
        if not user_ids:
            return {}
        cur.execute(
            f"SELECT user_id, role_id FROM user_roles WHERE user_id IN ({self._placeholders(user_ids)})",
            user_ids,
        )
        role_map: dict[int, list[int]] = {}
        for row in cur.fetchall():
            role_map.setdefault(int(row["user_id"]), []).append(int(row["role_id"]))
        for role_ids in role_map.values():
            role_ids.sort()
        return role_map

    def _list_resource_ids_by_role_id(self, cur: DictCursor, role_id: int) -> list[int]:
        cur.execute(
            "SELECT resource_id FROM role_resources WHERE role_id = %s ORDER BY resource_id ASC",
            (role_id,),
        )
        return [int(row["resource_id"]) for row in cur.fetchall()]

    def _list_resource_ids_by_role_ids(
        self, cur: DictCursor, role_ids: list[int]
    ) -> dict[int, list[int]]:
        if not role_ids:
            return {}
        cur.execute(
            f"SELECT role_id, resource_id FROM role_resources WHERE role_id IN ({self._placeholders(role_ids)})",
            role_ids,
        )
        resource_map: dict[int, list[int]] = {}
        for row in cur.fetchall():
            resource_map.setdefault(int(row["role_id"]), []).append(int(row["resource_id"]))
        for resource_ids in resource_map.values():
            resource_ids.sort()
        return resource_map

    def _replace_user_roles(
        self, cur: DictCursor, user_id: int, role_ids: list[int]
    ) -> None:
        cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        for role_id in role_ids:
            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                (user_id, role_id),
            )

    def _replace_role_resources(
        self, cur: DictCursor, role_id: int, resource_ids: list[int]
    ) -> None:
        cur.execute("DELETE FROM role_resources WHERE role_id = %s", (role_id,))
        for resource_id in resource_ids:
            cur.execute(
                "INSERT INTO role_resources (role_id, resource_id) VALUES (%s, %s)",
                (role_id, resource_id),
            )
