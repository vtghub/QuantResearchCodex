from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from quantresearch_api.security import (
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    ROLE_PLATFORM_ADMIN,
)

TOKEN_SECRET = b"local-development-secret"


@dataclass(frozen=True)
class LocalUser:
    id: str
    email: str
    display_name: str
    role: str
    tenant_id: UUID
    workspace_id: UUID
    password_hash: str
    status: str = "active"


class LocalAuthService:
    def __init__(self) -> None:
        self._users_by_email: dict[str, LocalUser] = {}
        self.register(
            email="admin@quantresearch.local",
            password="ChangeMe123!",
            display_name="Platform Admin",
            role=ROLE_PLATFORM_ADMIN,
        )

    def register(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str,
        tenant_id: UUID = DEFAULT_TENANT_ID,
        workspace_id: UUID = DEFAULT_WORKSPACE_ID,
    ) -> LocalUser:
        normalized_email = email.strip().lower()
        if normalized_email in self._users_by_email:
            raise ValueError("User already exists")
        user = LocalUser(
            id=str(uuid4()),
            email=normalized_email,
            display_name=display_name.strip(),
            role=role,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            password_hash=hash_password(password),
        )
        self._users_by_email[normalized_email] = user
        return user

    def authenticate(self, email: str, password: str) -> LocalUser | None:
        user = self._users_by_email.get(email.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def get_by_email(self, email: str) -> LocalUser | None:
        return self._users_by_email.get(email.strip().lower())


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or hashlib.sha256(uuid4().bytes).digest()[:16]
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256${base64.urlsafe_b64encode(salt).decode()}${digest.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    _algorithm, encoded_salt, expected_digest = encoded_hash.split("$", maxsplit=2)
    salt = base64.urlsafe_b64decode(encoded_salt.encode())
    actual = hash_password(password, salt).split("$", maxsplit=2)[2]
    return hmac.compare_digest(actual, expected_digest)


def issue_token(user: LocalUser, expires_delta: timedelta = timedelta(hours=8)) -> str:
    payload = {
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id),
        "workspace_id": str(user.workspace_id),
        "exp": int((datetime.now(UTC) + expires_delta).timestamp()),
    }
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode().rstrip("=")
    signature = hmac.new(TOKEN_SECRET, encoded_payload.encode(), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_token(token: str) -> dict[str, str]:
    encoded_payload, signature = token.split(".", maxsplit=1)
    expected_signature = hmac.new(
        TOKEN_SECRET,
        encoded_payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token signature")
    padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
    if int(payload["exp"]) < int(datetime.now(UTC).timestamp()):
        raise ValueError("Token expired")
    return payload


auth_service = LocalAuthService()
