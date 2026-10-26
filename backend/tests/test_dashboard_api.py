def test_dashboard_stats(client, demo_auth_headers):
    """Test dashboard metrics calculation."""
    resp = client.get("/api/dashboard/stats", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "content_created" in data
    assert data["content_created"]["value"] >= 4
    assert "saved_content" in data
    assert "scheduled" in data
    assert "ai_generations" in data

    # Voice calibration dial
    assert "voice_calibration" in data
    vc = data["voice_calibration"]
    assert "directness_pct" in vc
    assert "hook_potency_pct" in vc
    assert "story_resonance_pct" in vc

    # AI recommendation
    assert "ai_recommendation" in data
    assert "Ready to create?" in data["ai_recommendation"]["headline"]


def test_dashboard_recent_content(client, demo_auth_headers):
    """Test dashboard recent items table endpoint."""
    resp = client.get("/api/dashboard/recent", headers=demo_auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) >= 4
    assert "title" in items[0]
    assert "platform" in items[0]
    assert "status" in items[0]


def test_dashboard_overview(client, demo_auth_headers):
    """Test combined dashboard overview endpoint."""
    resp = client.get("/api/dashboard/overview", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert "recent_content" in data
