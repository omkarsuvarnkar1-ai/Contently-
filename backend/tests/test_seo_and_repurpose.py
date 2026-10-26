def test_seo_analysis_density_calculation(client, demo_auth_headers):
    """Test SEO keyword density analysis, SERP preview, and score."""
    sample_text = (
        "AI in education is transforming modern higher learning institutions. "
        "With AI in education, universities can provide personalized tutoring loops. "
        "Students benefit from AI in education through real-time formative feedback."
    )

    resp = client.post(
        "/api/seo/analyze",
        headers=demo_auth_headers,
        json={
            "content": sample_text,
            "target_keyword": "AI in education",
            "tracked_keywords": ["personalized tutoring", "formative feedback"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["primary_target"]["keyword"] == "AI in education"
    assert data["primary_target"]["occurrences"] == 3
    assert data["primary_target"]["density_pct"] > 0
    assert "serp_preview" in data
    assert "seo_score" in data
    assert len(data["suggestions"]) >= 1


def test_seo_analysis_validation_short_content(client, demo_auth_headers):
    """Test rejection when content is too short to analyze."""
    resp = client.post(
        "/api/seo/analyze",
        headers=demo_auth_headers,
        json={"content": "Short"},
    )
    assert resp.status_code == 422


def test_repurpose_validation_short_content(client, demo_auth_headers):
    """Test validation when repurpose content is empty or invalid."""
    resp = client.post(
        "/api/repurpose",
        headers=demo_auth_headers,
        json={"raw_text": ""},
    )
    assert resp.status_code == 422
