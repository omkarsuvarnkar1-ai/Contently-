def test_get_auth_providers(client):
    response = client.get("/api/auth/providers")
    assert response.status_code == 200
    data = response.json()
    assert "google" in data
    assert "github" in data
    assert "enabled" in data["google"]
    assert "enabled" in data["github"]


def test_google_signup_and_login_flow(client):
    # 1. New Google user signs up
    signup_payload = {
        "provider": "google",
        "email": "alex.creator@gmail.com",
        "name": "Alex Creator",
        "avatar_url": "https://lh3.googleusercontent.com/test-avatar",
        "provider_id": "google-sub-123456",
    }
    res = client.post("/api/auth/oauth", json=signup_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["is_new"] is True
    assert data["token"]
    assert data["user"]["email"] == "alex.creator@gmail.com"
    assert data["user"]["name"] == "Alex Creator"
    assert data["user"]["role"] == "Pro Creator"
    assert data["user"]["oauth_provider"] == "google"

    token = data["token"]

    # 2. Verify /api/auth/me works with this token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "alex.creator@gmail.com"

    # 3. Subsequent Google login with same email/provider
    login_payload = {
        "provider": "google",
        "email": "alex.creator@gmail.com",
        "provider_id": "google-sub-123456",
    }
    res2 = client.post("/api/auth/oauth", json=login_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is True
    assert data2["is_new"] is False
    assert data2["user"]["id"] == data["user"]["id"]


def test_github_signup_and_login_flow(client):
    # 1. New GitHub user signs up
    signup_payload = {
        "provider": "github",
        "email": "developer@github.com",
        "name": "Dev User",
        "avatar_url": "https://avatars.githubusercontent.com/u/987654",
        "provider_id": "gh-987654",
    }
    res = client.post("/api/auth/oauth", json=signup_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["is_new"] is True
    assert data["user"]["email"] == "developer@github.com"
    assert data["user"]["oauth_provider"] == "github"

    # 2. Login existing GitHub user
    res2 = client.post("/api/auth/oauth", json={
        "provider": "github",
        "email": "developer@github.com",
        "provider_id": "gh-987654",
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_new"] is False


def test_invalid_oauth_provider(client):
    res = client.post("/api/auth/oauth", json={
        "provider": "unsupported_provider",
        "email": "test@example.com",
    })
    assert res.status_code == 400
    assert "Unsupported OAuth provider" in res.json()["detail"]


def test_oauth_missing_email(client):
    res = client.post("/api/auth/oauth", json={
        "provider": "google",
        "email": "",
    })
    assert res.status_code == 422
