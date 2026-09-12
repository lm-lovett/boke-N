from fastapi import Request

from app.d1_repository import D1BlogRepository
from app.service import BlogService
from app.sqlite_repository import SqliteBlogRepository


def get_blog_service(request: Request) -> BlogService:
    env = request.scope.get("env")
    if env is not None and getattr(env, "MY_DB", None) is not None:
        return BlogService(D1BlogRepository(env.MY_DB))
    return BlogService(SqliteBlogRepository())
