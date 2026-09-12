from datetime import datetime, timedelta, timezone

import jwt

from app.config import JWT_EXPIRE_SECONDS, JWT_SECRET
from app.schemas import AuthPrincipal


def _secret_key() -> str:
    if len(JWT_SECRET) >= 32:
        return JWT_SECRET
    return (JWT_SECRET + "00000000000000000000000000000000")[:32]


class JwtService:
    def issue_token(
        self,
        user_id: int,
        username: str,
        role_ids: list[int],
        is_admin: bool,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": username,
            "userId": user_id,
            "roleIds": role_ids,
            "isAdmin": is_admin,
            "iat": now,
            "exp": now + timedelta(seconds=JWT_EXPIRE_SECONDS),
        }
        return jwt.encode(payload, _secret_key(), algorithm="HS256")

    def parse_token(self, token: str) -> AuthPrincipal:
        payload = jwt.decode(token, _secret_key(), algorithms=["HS256"])
        role_ids = []
        for value in payload.get("roleIds") or []:
            if isinstance(value, (int, float)):
                role_ids.append(int(value))
        user_id = payload.get("userId")
        if user_id is None:
            raise ValueError("token userId invalid")
        return AuthPrincipal(
            user_id=int(user_id),
            username=payload.get("sub", ""),
            role_ids=role_ids,
            admin=bool(payload.get("isAdmin")),
        )
