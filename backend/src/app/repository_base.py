from __future__ import annotations

from datetime import datetime
from typing import Any


def placeholders(values: list[Any]) -> str:
    return ",".join(["?"] * len(values))


def format_datetime(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    return value


def map_article(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "summary": row.get("summary"),
        "content": row["content"],
        "author": row.get("author"),
        "views": int(row.get("views") or 0),
        "published": bool(row.get("published")),
        "createdAt": row.get("created_at"),
    }


def map_comment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "articleId": row["article_id"],
        "userId": row["user_id"],
        "username": row["username"],
        "content": row["content"],
        "createdAt": row.get("created_at"),
    }
