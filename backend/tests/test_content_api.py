def test_content_crud_flow(client, demo_auth_headers):
    """Test creating, reading, updating, and deleting content items."""
    # 1. Create
    create_resp = client.post(
        "/api/content",
        headers=demo_auth_headers,
        json={
            "title": "Autonomous AI Agent Architectures in 2026",
            "body": "Detailed technical analysis examining state machines and token latency.",
            "format": "Long-form Guide",
            "platform": "Blog",
            "status": "Draft",
        },
    )
    assert create_resp.status_code == 201
    item = create_resp.json()
    item_id = item["id"]
    assert item["title"] == "Autonomous AI Agent Architectures in 2026"
    assert item["word_count"] > 0
    assert item["voice_match_pct"] == 98.0
    assert item["is_favorite"] is False

    # 2. Read detail
    detail_resp = client.get(f"/api/content/{item_id}", headers=demo_auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == item_id

    # 3. Update
    update_resp = client.put(
        f"/api/content/{item_id}",
        headers=demo_auth_headers,
        json={"title": "Updated Title: Autonomous AI Agent Architectures", "status": "Saved"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Title: Autonomous AI Agent Architectures"
    assert update_resp.json()["status"] == "Saved"

    # 4. Toggle Favorite
    fav_resp = client.post(f"/api/content/{item_id}/favorite", headers=demo_auth_headers)
    assert fav_resp.status_code == 200
    assert fav_resp.json()["is_favorite"] is True

    # 5. Delete
    del_resp = client.delete(f"/api/content/{item_id}", headers=demo_auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify deleted
    get_after_del = client.get(f"/api/content/{item_id}", headers=demo_auth_headers)
    assert get_after_del.status_code == 404


def test_content_filtering_and_search(client, demo_auth_headers):
    """Test keyword search, status filtering, category filtering, and empty states."""
    # List seeded content
    resp = client.get("/api/content", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 4
    assert len(data["items"]) >= 4

    # Search keyword match
    search_resp = client.get("/api/content?search=Education", headers=demo_auth_headers)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    assert any("education" in it["title"].lower() for it in search_data["items"])

    # Search non-existent keyword -> empty state
    empty_resp = client.get("/api/content?search=NonExistentKeywordXYZ999", headers=demo_auth_headers)
    assert empty_resp.status_code == 200
    assert empty_resp.json()["total"] == 0
    assert len(empty_resp.json()["items"]) == 0

    # Filter by status: Saved
    saved_resp = client.get("/api/content?status=Saved", headers=demo_auth_headers)
    assert saved_resp.status_code == 200
    for it in saved_resp.json()["items"]:
        assert it["status"] == "Saved"

    # Filter by category: LinkedIn
    linkedin_resp = client.get("/api/content?category=LinkedIn", headers=demo_auth_headers)
    assert linkedin_resp.status_code == 200
    for it in linkedin_resp.json()["items"]:
        assert "linkedin" in it["platform"].lower()


def test_content_bulk_action(client, demo_auth_headers):
    """Test bulk action on content items."""
    # Create 2 items
    i1 = client.post("/api/content", headers=demo_auth_headers, json={"title": "Bulk 1", "body": "B1"}).json()["id"]
    i2 = client.post("/api/content", headers=demo_auth_headers, json={"title": "Bulk 2", "body": "B2"}).json()["id"]

    # Bulk favorite
    bulk_fav = client.post(
        "/api/content/bulk-action",
        headers=demo_auth_headers,
        json={"action": "favorite", "content_ids": [i1, i2]},
    )
    assert bulk_fav.status_code == 200
    assert bulk_fav.json()["affected"] == 2

    # Verify both are favorited
    assert client.get(f"/api/content/{i1}", headers=demo_auth_headers).json()["is_favorite"] is True
    assert client.get(f"/api/content/{i2}", headers=demo_auth_headers).json()["is_favorite"] is True

    # Bulk delete
    bulk_del = client.post(
        "/api/content/bulk-action",
        headers=demo_auth_headers,
        json={"action": "delete", "content_ids": [i1, i2]},
    )
    assert bulk_del.status_code == 200
    assert bulk_del.json()["affected"] == 2
    assert client.get(f"/api/content/{i1}", headers=demo_auth_headers).status_code == 404
