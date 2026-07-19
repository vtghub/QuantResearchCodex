from fastapi.testclient import TestClient
from quantresearch_api.auth import auth_service, hash_password, verify_password
from quantresearch_api.main import create_app

client = TestClient(create_app())


def test_password_hash_verification() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong", hashed)


def test_can_login_seeded_admin_and_use_bearer_context() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@quantresearch.local", "password": "ChangeMe123!"},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.get("/api/v1/identity/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["role"] == "platform_admin"


def test_login_rejects_bad_password() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@quantresearch.local", "password": "bad"},
    )

    assert response.status_code == 401


def test_admin_can_register_researcher() -> None:
    email = "researcher.test@quantresearch.local"
    existing = auth_service.get_by_email(email)
    if existing is not None:
        return

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Research123!",
            "display_name": "Researcher Test",
            "role": "researcher",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "researcher"


def test_auth_provider_hooks_are_discoverable() -> None:
    response = client.get("/api/v1/auth/providers")

    assert response.status_code == 200
    assert response.json()[1]["type"] == "oidc"
