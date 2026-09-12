import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture(scope="module")
def client() -> TestClient:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from main import app

    return TestClient(app)


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["ok"] is True


def test_admin_login_and_article_flow(client: TestClient):
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    assert login.status_code == 200
    login_data = login.json()["data"]
    token = login_data["token"]
    assert login_data["user"]["username"] == "admin"
    assert any(role["name"] == "admin" for role in login_data["roles"])

    articles = client.get("/api/articles")
    assert articles.status_code == 200
    assert len(articles.json()["data"]) >= 1

    top10 = client.get("/api/articles/top10")
    assert top10.status_code == 200

    detail = client.get("/api/articles/1")
    assert detail.status_code == 200
    assert "article" in detail.json()["data"]

    weather = client.get("/api/weather", params={"city": "上海市"})
    assert weather.status_code == 200
    assert weather.json()["data"]["city"] == "上海市"

    admin_articles = client.get(
        "/api/admin/articles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert admin_articles.status_code == 200


def test_demo_user_comment_and_banned_word(client: TestClient):
    login = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "Demo123!"},
    )
    token = login.json()["data"]["token"]

    comment = client.post(
        "/api/articles/1/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "Python 后端评论测试"},
    )
    assert comment.status_code == 200

    blocked = client.post(
        "/api/articles/1/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "这条评论包含赌博词"},
    )
    assert blocked.status_code == 400
    assert "违禁词" in blocked.json()["message"]


def test_register(client: TestClient):
    username = f"pyuser_{os.getpid()}"
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "Test1234!", "nickname": "Py User"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["username"] == username
