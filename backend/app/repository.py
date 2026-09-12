from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from app.config import get_sqlite_path


class BlogRepository:
    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _row_dict(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return dict(row)

    def _placeholders(self, values: list[Any]) -> str:
        return ",".join(["?"] * len(values))

    def _format_datetime(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
        return value

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
            "createdAt": created_at,
        }

    def _map_comment(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "articleId": row["article_id"],
            "userId": row["user_id"],
            "username": row["username"],
            "content": row["content"],
            "createdAt": row.get("created_at"),
        }

    def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, nickname, password_hash FROM users WHERE username = ?",
                (username,),
            )
            row = self._row_dict(cur.fetchone())
            if not row:
                return None
            row["roleIds"] = self._list_role_ids_by_user_id(cur, row["id"])
            row["passwordHash"] = row.pop("password_hash")
            return row

    def find_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, nickname, password_hash FROM users WHERE id = ?",
                (user_id,),
            )
            row = self._row_dict(cur.fetchone())
            if not row:
                return None
            row["roleIds"] = self._list_role_ids_by_user_id(cur, row["id"])
            row["passwordHash"] = row.pop("password_hash")
            return row

    def exists_user_by_username(self, username: str) -> bool:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) AS cnt FROM users WHERE username = ?", (username,))
            row = self._row_dict(cur.fetchone())
            return bool(row and row["cnt"] > 0)

    def list_users(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, username, nickname, password_hash FROM users ORDER BY id ASC")
            rows = [self._row_dict(row) for row in cur.fetchall()]
            role_map = self._list_role_ids_by_user_ids(cur, [row["id"] for row in rows])
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
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, nickname, password_hash) VALUES (?, ?, ?)",
                (username, nickname, password_hash),
            )
            user_id = cur.lastrowid
            self._replace_user_roles(cur, user_id, role_ids)
            return int(user_id)

    def update_user(self, user_id: int, nickname: str, password_hash: str) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET nickname = ?, password_hash = ? WHERE id = ?",
                (nickname, password_hash, user_id),
            )

    def replace_user_roles(self, user_id: int, role_ids: list[int]) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            self._replace_user_roles(cur, user_id, role_ids)

    def delete_user(self, user_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def list_roles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, description FROM roles ORDER BY id ASC")
            rows = [self._row_dict(row) for row in cur.fetchall()]
            resource_map = self._list_resource_ids_by_role_ids(cur, [row["id"] for row in rows])
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
            cur = conn.cursor()
            cur.execute(
                f"SELECT id, name, description FROM roles WHERE id IN ({self._placeholders(ids)})",
                ids,
            )
            rows = [self._row_dict(row) for row in cur.fetchall()]
            resource_map = self._list_resource_ids_by_role_ids(cur, [row["id"] for row in rows])
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
            cur = conn.cursor()
            cur.execute("SELECT id, name, description FROM roles WHERE name = ?", (name,))
            row = self._row_dict(cur.fetchone())
            if not row:
                return None
            row["resourceIds"] = self._list_resource_ids_by_role_id(cur, row["id"])
            return row

    def find_role_by_id(self, role_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, description FROM roles WHERE id = ?", (role_id,))
            row = self._row_dict(cur.fetchone())
            if not row:
                return None
            row["resourceIds"] = self._list_resource_ids_by_role_id(cur, row["id"])
            return row

    def exists_role_name(self, name: str) -> bool:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) AS cnt FROM roles WHERE name = ?", (name,))
            row = self._row_dict(cur.fetchone())
            return bool(row and row["cnt"] > 0)

    def insert_role(self, name: str, description: str, resource_ids: list[int]) -> int:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO roles (name, description) VALUES (?, ?)",
                (name, description),
            )
            role_id = cur.lastrowid
            self._replace_role_resources(cur, role_id, resource_ids)
            return int(role_id)

    def update_role(self, role_id: int, name: str, description: str) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE roles SET name = ?, description = ? WHERE id = ?",
                (name, description, role_id),
            )

    def replace_role_resources(self, role_id: int, resource_ids: list[int]) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            self._replace_role_resources(cur, role_id, resource_ids)

    def delete_role(self, role_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM roles WHERE id = ?", (role_id,))

    def list_resources(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, code, name FROM resources ORDER BY id ASC")
            return [self._row_dict(row) for row in cur.fetchall()]

    def list_resources_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT id, code, name FROM resources WHERE id IN ({self._placeholders(ids)})",
                ids,
            )
            return [self._row_dict(row) for row in cur.fetchall()]

    def find_resource_by_id(self, resource_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, code, name FROM resources WHERE id = ?", (resource_id,))
            return self._row_dict(cur.fetchone())

    def insert_resource(self, code: str, name: str) -> int:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO resources (code, name) VALUES (?, ?)", (code, name))
            return int(cur.lastrowid)

    def update_resource(self, resource_id: int, code: str, name: str) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE resources SET code = ?, name = ? WHERE id = ?",
                (code, name, resource_id),
            )

    def delete_resource(self, resource_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM resources WHERE id = ?", (resource_id,))

    def list_admin_articles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, summary, content, author, views, published, created_at "
                "FROM articles ORDER BY created_at DESC"
            )
            return [self._map_article(self._row_dict(row)) for row in cur.fetchall()]

    def find_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, summary, content, author, views, published, created_at "
                "FROM articles WHERE id = ?",
                (article_id,),
            )
            row = self._row_dict(cur.fetchone())
            return self._map_article(row) if row else None

    def find_published_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, summary, content, author, views, published, created_at "
                "FROM articles WHERE id = ? AND published = 1",
                (article_id,),
            )
            row = self._row_dict(cur.fetchone())
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
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO articles (title, summary, content, author, views, published, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    title,
                    summary,
                    content,
                    author,
                    0,
                    1 if published else 0,
                    self._format_datetime(created_at),
                ),
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
            cur = conn.cursor()
            cur.execute(
                "UPDATE articles SET title = ?, summary = ?, content = ?, author = ?, published = ? "
                "WHERE id = ?",
                (title, summary, content, author, 1 if published else 0, article_id),
            )

    def increment_article_views(self, article_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE articles SET views = views + 1 WHERE id = ?", (article_id,))

    def delete_article(self, article_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))

    def list_public_articles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, summary, content, author, views, published, created_at "
                "FROM articles WHERE published = 1 ORDER BY created_at DESC"
            )
            return [self._map_article(self._row_dict(row)) for row in cur.fetchall()]

    def top10_articles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, summary, content, author, views, published, created_at "
                "FROM articles WHERE published = 1 ORDER BY views DESC LIMIT 10"
            )
            return [self._map_article(self._row_dict(row)) for row in cur.fetchall()]

    def list_banned_words(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, word FROM banned_words ORDER BY id ASC")
            return [self._row_dict(row) for row in cur.fetchall()]

    def insert_banned_word(self, word: str) -> int:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO banned_words (word) VALUES (?)", (word,))
            return int(cur.lastrowid)

    def delete_banned_word(self, banned_word_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM banned_words WHERE id = ?", (banned_word_id,))

    def list_admin_comments(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, article_id, user_id, username, content, created_at "
                "FROM comments ORDER BY created_at DESC"
            )
            return [self._map_comment(self._row_dict(row)) for row in cur.fetchall()]

    def list_comments_by_article_id(self, article_id: int) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, article_id, user_id, username, content, created_at "
                "FROM comments WHERE article_id = ? ORDER BY created_at DESC",
                (article_id,),
            )
            return [self._map_comment(self._row_dict(row)) for row in cur.fetchall()]

    def find_comment_by_id(self, comment_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, article_id, user_id, username, content, created_at "
                "FROM comments WHERE id = ?",
                (comment_id,),
            )
            row = self._row_dict(cur.fetchone())
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
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO comments (article_id, user_id, username, content, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (article_id, user_id, username, content, self._format_datetime(created_at)),
            )
            return int(cur.lastrowid)

    def delete_comment(self, comment_id: int) -> None:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM comments WHERE id = ?", (comment_id,))

    def _list_role_ids_by_user_id(self, cur: sqlite3.Cursor, user_id: int) -> list[int]:
        cur.execute(
            "SELECT role_id FROM user_roles WHERE user_id = ? ORDER BY role_id ASC",
            (user_id,),
        )
        return [int(row["role_id"]) for row in cur.fetchall()]

    def _list_role_ids_by_user_ids(
        self, cur: sqlite3.Cursor, user_ids: list[int]
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

    def _list_resource_ids_by_role_id(self, cur: sqlite3.Cursor, role_id: int) -> list[int]:
        cur.execute(
            "SELECT resource_id FROM role_resources WHERE role_id = ? ORDER BY resource_id ASC",
            (role_id,),
        )
        return [int(row["resource_id"]) for row in cur.fetchall()]

    def _list_resource_ids_by_role_ids(
        self, cur: sqlite3.Cursor, role_ids: list[int]
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
        self, cur: sqlite3.Cursor, user_id: int, role_ids: list[int]
    ) -> None:
        cur.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        for role_id in role_ids:
            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id),
            )

    def _replace_role_resources(
        self, cur: sqlite3.Cursor, role_id: int, resource_ids: list[int]
    ) -> None:
        cur.execute("DELETE FROM role_resources WHERE role_id = ?", (role_id,))
        for resource_id in resource_ids:
            cur.execute(
                "INSERT INTO role_resources (role_id, resource_id) VALUES (?, ?)",
                (role_id, resource_id),
            )
