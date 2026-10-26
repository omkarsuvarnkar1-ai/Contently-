def test_cannot_access_other_users_content(client, demo_auth_headers, second_user_auth_headers):
    """Verify that User B cannot read User A's content item."""
    # User A (demo user) creates a private draft
    create_resp = client.post(
        "/api/content",
        headers=demo_auth_headers,
        json={
            "title": "User A Private Architecture Doc",
            "body": "Confidential technical details for User A only.",
            "format": "Long-form Guide",
            "platform": "Blog",
        },
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    # User B tries to read User A's item -> MUST BE 404 (isolation enforced)
    get_resp = client.get(f"/api/content/{item_id}", headers=second_user_auth_headers)
    assert get_resp.status_code == 404
    assert "not found or access denied" in get_resp.json()["detail"].lower()


def test_cannot_modify_other_users_content(client, demo_auth_headers, second_user_auth_headers):
    """Verify that User B cannot update User A's content item."""
    create_resp = client.post(
        "/api/content",
        headers=demo_auth_headers,
        json={"title": "Original Title by User A", "body": "Body content."},
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    # User B tries to modify User A's item
    update_resp = client.put(
        f"/api/content/{item_id}",
        headers=second_user_auth_headers,
        json={"title": "Hacked Title by User B"},
    )
    assert update_resp.status_code == 404

    # Verify User A's item remains unchanged
    verify_resp = client.get(f"/api/content/{item_id}", headers=demo_auth_headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["title"] == "Original Title by User A"


def test_cannot_delete_other_users_content(client, demo_auth_headers, second_user_auth_headers):
    """Verify that User B cannot delete User A's content item."""
    create_resp = client.post(
        "/api/content",
        headers=demo_auth_headers,
        json={"title": "User A Content to Delete", "body": "Body"},
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    # User B tries to delete User A's item
    del_resp = client.delete(f"/api/content/{item_id}", headers=second_user_auth_headers)
    assert del_resp.status_code == 404

    # User A still has the item
    check_resp = client.get(f"/api/content/{item_id}", headers=demo_auth_headers)
    assert check_resp.status_code == 200


def test_content_list_strictly_isolated(client, demo_auth_headers, second_user_auth_headers):
    """Verify that User B's library list only contains their own items, never User A's."""
    # User B creates 1 item
    client.post(
        "/api/content",
        headers=second_user_auth_headers,
        json={"title": "User B Solo Post", "body": "Only for User B."},
    )

    # User B lists content
    list_resp = client.get("/api/content", headers=second_user_auth_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "User B Solo Post"


def test_unauthenticated_requests_rejected(client):
    """Verify that unauthenticated requests to protected endpoints return 401."""
    assert client.get("/api/content").status_code == 401
    assert client.post("/api/content", json={"title": "X", "body": "Y"}).status_code == 401
    assert client.get("/api/dashboard/stats").status_code == 401
    assert client.get("/api/brand-kit").status_code == 401
    assert client.get("/api/planner/posts").status_code == 401
