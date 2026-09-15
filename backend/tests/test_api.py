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
    assert {item["code"] for item in login_data["resources"]} == {
        "role:manage",
        "user:manage",
        "resource:manage",
        "article:manage",
        "bannedword:manage",
        "comment:manage",
    }

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert {item["code"] for item in me.json()["data"]["resources"]} == {
        item["code"] for item in login_data["resources"]
    }

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


def test_limited_role_only_sees_assigned_resources(client: TestClient):
    admin_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    admin_token = admin_login.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resources = client.get("/api/admin/resources", headers=admin_headers)
    assert resources.status_code == 200
    article_resource = next(item for item in resources.json()["data"] if item["code"] == "article:manage")

    role = client.post(
        "/api/admin/roles",
        headers=admin_headers,
        json={
            "name": "pinpai",
            "description": "品牌子账号",
            "resourceIds": [article_resource["id"]],
        },
    )
    assert role.status_code == 200
    role_id = role.json()["data"]["id"]

    user = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "username": "pinpai",
            "nickname": "品牌账号",
            "password": "Pinpai123!",
            "roleIds": [role_id],
        },
    )
    assert user.status_code == 200

    pinpai_login = client.post(
        "/api/auth/login",
        json={"username": "pinpai", "password": "Pinpai123!"},
    )
    assert pinpai_login.status_code == 200
    pinpai_data = pinpai_login.json()["data"]
    assert {item["code"] for item in pinpai_data["resources"]} == {"article:manage"}
    pinpai_headers = {"Authorization": f"Bearer {pinpai_data['token']}"}

    allowed = client.get("/api/admin/articles", headers=pinpai_headers)
    assert allowed.status_code == 200

    forbidden = client.get("/api/admin/roles", headers=pinpai_headers)
    assert forbidden.status_code == 403
    assert "没有权限" in forbidden.json()["message"]

    demo_login = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "Demo123!"},
    )
    demo_token = demo_login.json()["data"]["token"]
    denied = client.get(
        "/api/admin/articles",
        headers={"Authorization": f"Bearer {demo_token}"},
    )
    assert denied.status_code == 403
