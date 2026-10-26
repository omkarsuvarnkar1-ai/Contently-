from datetime import UTC, datetime, timedelta


def test_brand_kit_operations(client, demo_auth_headers):
    """Test brand voice settings, sliders, and keyword governance."""
    # 1. Get
    resp = client.get("/api/brand-kit", headers=demo_auth_headers)
    assert resp.status_code == 200
    kit = resp.json()
    assert "formality_pct" in kit
    assert "preferred_keywords" in kit
    assert len(kit["preferred_keywords"]) >= 1

    # 2. Update sliders
    update_resp = client.put(
        "/api/brand-kit",
        headers=demo_auth_headers,
        json={"formality_pct": 80, "edge_pct": 95, "positioning_statement": "New positioning anchor"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["formality_pct"] == 80
    assert updated["edge_pct"] == 95
    assert updated["positioning_statement"] == "New positioning anchor"

    # 3. Add preferred keyword
    add_kw_resp = client.post(
        "/api/brand-kit/keywords/preferred",
        headers=demo_auth_headers,
        json={"keyword": "autonomous loops"},
    )
    assert add_kw_resp.status_code == 200
    assert "autonomous loops" in add_kw_resp.json()["preferred_keywords"]

    # 4. Remove preferred keyword
    rem_kw_resp = client.delete(
        "/api/brand-kit/keywords/preferred/autonomous%20loops",
        headers=demo_auth_headers,
    )
    assert rem_kw_resp.status_code == 200
    assert "autonomous loops" not in rem_kw_resp.json()["preferred_keywords"]

    # 5. Add forbidden cliché
    add_forb = client.post(
        "/api/brand-kit/keywords/forbidden",
        headers=demo_auth_headers,
        json={"keyword": "synergy"},
    )
    assert add_forb.status_code == 200
    assert "synergy" in add_forb.json()["forbidden_keywords"]


def test_planner_scheduled_posts(client, demo_auth_headers):
    """Test calendar planner scheduling, listing, rescheduling, and deletion."""
    # 1. List
    list_resp = client.get("/api/planner/posts", headers=demo_auth_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 2. Create post
    target_time = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    create_resp = client.post(
        "/api/planner/posts",
        headers=demo_auth_headers,
        json={
            "title": "Autonomous Agent Launch Thread",
            "platform": "X / Twitter",
            "scheduled_time": target_time,
            "time_slot_label": "04:30 PM",
        },
    )
    assert create_resp.status_code == 201
    post = create_resp.json()
    post_id = post["id"]
    assert post["title"] == "Autonomous Agent Launch Thread"
    assert post["platform"] == "X / Twitter"

    # 3. Update / Reschedule
    new_time = (datetime.now(UTC) + timedelta(days=8)).isoformat()
    patch_resp = client.patch(
        f"/api/planner/posts/{post_id}",
        headers=demo_auth_headers,
        json={"scheduled_time": new_time, "time_slot_label": "05:00 PM"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["time_slot_label"] == "05:00 PM"

    # 4. Delete
    del_resp = client.delete(f"/api/planner/posts/{post_id}", headers=demo_auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


def test_templates_catalog(client):
    """Test templates catalog listing, search, and usage counter."""
    # List all
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5

    # Filter by category
    social_resp = client.get("/api/templates?category=social")
    assert social_resp.status_code == 200
    for t in social_resp.json()["items"]:
        assert "social" in t["category"].lower()

    # Get single template
    t_id = data["items"][0]["id"]
    single_resp = client.get(f"/api/templates/{t_id}")
    assert single_resp.status_code == 200
    assert single_resp.json()["id"] == t_id


def test_profile_and_settings(client, demo_auth_headers):
    """Test profile and settings endpoints."""
    # Profile get
    resp = client.get("/api/profile", headers=demo_auth_headers)
    assert resp.status_code == 200
    assert "email" in resp.json()

    # Profile update
    up_resp = client.put(
        "/api/profile",
        headers=demo_auth_headers,
        json={"bio": "Updated bio text for creator.", "handle": "omkar_prime"},
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["bio"] == "Updated bio text for creator."
    assert up_resp.json()["handle"] == "omkar_prime"

    # Settings get & update
    set_resp = client.get("/api/profile/settings", headers=demo_auth_headers)
    assert set_resp.status_code == 200

    set_update = client.put(
        "/api/profile/settings",
        headers=demo_auth_headers,
        json={"creativity_temperature": 0.85, "auto_save_drafts": True},
    )
    assert set_update.status_code == 200
    assert set_update.json()["creativity_temperature"] == 0.85
