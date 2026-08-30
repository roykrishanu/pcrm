
from tests.conftest import unique_slug


async def _register_org(client, slug=None):
    slug = slug or unique_slug()
    resp = await client.post("/api/v1/auth/register-organization", json={
        "organization_name": "Test Realty",
        "slug": slug,
        "owner_name": "Owner One",
        "owner_email": f"owner-{slug}@example.com",
        "owner_password": "Sup3rSecret!",
    })
    assert resp.status_code == 201, resp.text
    return slug, resp.json()


async def test_register_organization_creates_owner(client):
    slug, data = await _register_org(client)
    assert data["slug"] == slug


async def test_duplicate_slug_rejected(client):
    slug, _ = await _register_org(client)
    resp = await client.post("/api/v1/auth/register-organization", json={
        "organization_name": "Other",
        "slug": slug,
        "owner_name": "Someone",
        "owner_email": "someone@example.com",
        "owner_password": "Sup3rSecret!",
    })
    assert resp.status_code == 409


async def test_login_success_and_me(client):
    slug, _ = await _register_org(client)
    resp = await client.post("/api/v1/auth/login", json={
        "email": f"owner-{slug}@example.com", "password": "Sup3rSecret!", "organization_slug": slug,
    })
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == f"owner-{slug}@example.com"
    assert me.json()["role_name"] == "Organization Owner"


async def test_login_wrong_password_fails_generically(client):
    slug, _ = await _register_org(client)
    resp = await client.post("/api/v1/auth/login", json={
        "email": f"owner-{slug}@example.com", "password": "WrongPassword1", "organization_slug": slug,
    })
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


async def test_login_unknown_email_same_error_as_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "WrongPassword1",
    })
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid email or password."


async def test_account_locks_after_repeated_failures(client):
    slug, _ = await _register_org(client)
    email = f"owner-{slug}@example.com"
    for _ in range(5):
        await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong", "organization_slug": slug})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Sup3rSecret!", "organization_slug": slug})
    assert resp.status_code == 401
    assert "locked" in resp.json()["error"]["message"].lower()


async def test_refresh_rotates_token(client):
    slug, _ = await _register_org(client)
    login = await client.post("/api/v1/auth/login", json={
        "email": f"owner-{slug}@example.com", "password": "Sup3rSecret!", "organization_slug": slug,
    })
    old_refresh = login.json()["refresh_token"]
    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != old_refresh

    # old refresh token must now be dead (rotation)
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401


async def test_protected_route_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_unverified_email_flow(client):
    slug, _ = await _register_org(client)
    resp = await client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})
    assert resp.status_code == 401
