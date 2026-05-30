import pytest


@pytest.mark.asyncio
async def test_register_login_me_flow(async_client):
    register = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "USER@example.com",
            "password": "correct horse battery staple",
            "name": "User",
        },
    )
    assert register.status_code == 201
    assert register.json()["user"]["email"] == "user@example.com"

    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "correct horse battery staple"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"
