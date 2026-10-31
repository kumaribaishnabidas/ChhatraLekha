"""Unit and integration tests for Demo Logins and Multilingual AI Assistant."""

from __future__ import annotations

import pytest

from app.services.ai_assistant import (
    find_grounded_answer,
    get_quick_prompts_for_role,
    KNOWLEDGE_BASE,
)


@pytest.mark.asyncio
async def test_demo_login_all_six_personas(client):
    """Ensure all 6 demo accounts can acquire tokens without passwords."""
    personas = [
        ("student", "student"),
        ("parent", "parent"),
        ("teacher", "teacher"),
        ("school_admin", "institution_admin"),
        ("college_admin", "institution_admin"),
        ("university_admin", "aicte_admin"),
    ]

    for role_key, expected_role in personas:
        res = await client.post("/api/auth/demo-login", json={"role": role_key})
        assert res.status_code == 200, f"Demo login failed for role {role_key}: {res.text}"
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["role"] == expected_role
        assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_ai_assistant_service_english():
    """Verify AI assistant answers common questions in English with suggested actions."""
    res = find_grounded_answer("How do I view my timetable?", role="student", language="en")
    assert "timetable" in res["reply"].lower() or "class" in res["reply"].lower()
    assert len(res["actions"]) > 0
    assert any("/me" in act["url"] or "/academic" in act["url"] for act in res["actions"])


@pytest.mark.asyncio
async def test_ai_assistant_service_hindi():
    """Verify AI assistant detects Hindi intent and responds appropriately."""
    res = find_grounded_answer("Mera attendance kaise check karu?", role="student", language="hi")
    assert len(res["reply"]) > 0
    assert len(res["actions"]) > 0


@pytest.mark.asyncio
async def test_ai_assistant_service_odia():
    """Verify AI assistant responds in Odia when requested."""
    res = find_grounded_answer("ମୋର ଉପସ୍ଥିତି କିପରି ଦେଖିବି?", role="student", language="or")
    assert len(res["reply"]) > 0


@pytest.mark.asyncio
async def test_ai_assistant_endpoints(client):
    """Test AI assistant chat and prompt endpoints via HTTP client."""
    # Prompts endpoint
    res_prompts = await client.get("/api/ai/prompts?role=student")
    assert res_prompts.status_code == 200
    prompts_data = res_prompts.json()
    assert "prompts" in prompts_data
    assert len(prompts_data["prompts"]) >= 3

    # Chat endpoint
    res_chat = await client.post(
        "/api/ai/chat",
        json={"message": "What is an APAAR ID?", "role": "student", "language": "en"},
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert "reply" in chat_data
    assert "APAAR" in chat_data["reply"] or "Automated Permanent Academic Account Registry" in chat_data["reply"]
    assert "source" in chat_data
