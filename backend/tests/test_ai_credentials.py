from unittest.mock import patch

from backend.app.core.config import settings


def test_missing_openai_key_returns_clear_actionable_error(client, demo_auth_headers):
    """Verify that calling generation without AI credentials returns a clear 503 error, not fake success."""
    with patch.object(settings, "OPENAI_API_KEY", ""):
        resp = client.post(
            "/api/ai/generate",
            headers=demo_auth_headers,
            json={
                "promptTopic": "Autonomous AI agent architectures in 2026",
                "channel": "linkedin",
                "provider": "openai",
            },
        )
        assert resp.status_code == 503
        data = resp.json()
        assert "OPENAI_API_KEY" in data["detail"]
        assert "https://platform.openai.com/api-keys" in data["detail"]


def test_missing_gemini_key_returns_clear_actionable_error(client, demo_auth_headers):
    """Verify that calling Gemini without credentials returns clear 503 error with link to Google AI Studio."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        resp = client.post(
            "/api/ai/generate",
            headers=demo_auth_headers,
            json={
                "promptTopic": "Autonomous AI agent architectures in 2026",
                "channel": "linkedin",
                "provider": "gemini",
            },
        )
        assert resp.status_code == 503
        data = resp.json()
        assert "GEMINI_API_KEY" in data["detail"]
        assert "https://aistudio.google.com" in data["detail"]


def test_missing_anthropic_key_returns_clear_actionable_error(client, demo_auth_headers):
    """Verify that calling Anthropic without credentials returns clear 503 error with link to Anthropic Console."""
    with patch.object(settings, "ANTHROPIC_API_KEY", ""):
        resp = client.post(
            "/api/ai/generate",
            headers=demo_auth_headers,
            json={
                "promptTopic": "Autonomous AI agent architectures in 2026",
                "channel": "linkedin",
                "provider": "anthropic",
            },
        )
        assert resp.status_code == 503
        data = resp.json()
        assert "ANTHROPIC_API_KEY" in data["detail"]
        assert "https://console.anthropic.com" in data["detail"]


def test_ai_generation_with_configured_adapter(client, demo_auth_headers):
    """Verify that when the provider returns valid response, generation succeeds and is saved in history."""
    mock_payload = {
        "generated_text": "Autonomous AI agents in 2026 are replacing SaaS glue. Key takeaways: 1. Speed. 2. Resilience.",
        "model_used": "OpenAI (gpt-4o-mini)",
        "tokens_used": 180,
        "word_count": 22,
        "read_time_mins": 0.4,
        "brand_match_pct": 98.9,
    }

    with patch("backend.app.services.ai_service.AiService.generate_content", return_value=mock_payload):
        resp = client.post(
            "/api/ai/generate",
            headers=demo_auth_headers,
            json={
                "promptTopic": "Autonomous AI agents",
                "channel": "linkedin",
                "tone": "Analytical & Direct",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["generated_text"] == mock_payload["generated_text"]
        assert data["brand_match_pct"] == mock_payload["brand_match_pct"]

        # Verify saved in history
        history_resp = client.get("/api/ai/history", headers=demo_auth_headers)
        assert history_resp.status_code == 200
        hist_data = history_resp.json()
        assert hist_data["total"] >= 1
        assert hist_data["items"][0]["prompt_topic"] == "Autonomous AI agents"


def test_ai_status_endpoint(client):
    """Verify that /api/ai/status returns provider readiness and active models."""
    resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "default_provider" in data
    assert "providers" in data
    assert "openai" in data["providers"]
    assert "gemini" in data["providers"]
    assert "anthropic" in data["providers"]


def test_ai_config_update(client, demo_auth_headers):
    """Verify that authorized users can update their AI provider configuration."""
    resp = client.post(
        "/api/ai/config",
        headers=demo_auth_headers,
        json={
            "default_provider": "gemini",
            "gemini_api_key": "AIzaSyTestKey123456",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["default_provider"] == "gemini"
    assert data["providers"]["gemini"]["configured"] is True

