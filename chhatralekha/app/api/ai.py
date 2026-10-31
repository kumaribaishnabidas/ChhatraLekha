"""AI Assistant endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.security import decode_token
from app.services.ai_assistant import find_grounded_answer, get_quick_prompts_for_role

router = APIRouter(prefix="/ai", tags=["ai-assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: Optional[str] = "en"
    context: Optional[Dict[str, Any]] = None


class ActionChip(BaseModel):
    label: str
    url: str


class ChatResponse(BaseModel):
    reply: str
    actions: List[ActionChip] = []
    source: str
    confidence: float


class PromptsResponse(BaseModel):
    role: str
    prompts: List[str]


def _get_optional_principal(request: Request) -> Optional[Dict[str, Any]]:
    """Decode bearer token if present; otherwise return None without raising 401."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    try:
        payload = decode_token(token)
        return {
            "user_id": payload.get("sub"),
            "role": payload.get("role", "student"),
            "institution_id": payload.get("institution_id"),
            "apaar_id": payload.get("apaar_id"),
        }
    except Exception:
        return None


@router.post("/chat", response_model=ChatResponse, summary="Ask the ChhatraLekha AI assistant a question")
async def chat(
    payload: ChatRequest,
    request: Request,
) -> ChatResponse:
    """Answer a user query with grounded knowledge and role-aware navigation actions."""
    principal = _get_optional_principal(request)
    role = principal.get("role", "student") if principal else "student"
    user_context = None
    if principal:
        user_context = {
            "user_id": principal.get("user_id"),
            "role": principal.get("role"),
            "student_id": principal.get("apaar_id"),
            "institution_id": principal.get("institution_id"),
        }

    result = find_grounded_answer(
        query=payload.message,
        role=role,
        language=payload.language or "en",
        user_context=user_context,
    )
    return ChatResponse(
        reply=result["reply"],
        actions=[ActionChip(**a) for a in result.get("actions", [])],
        source=result.get("source", "ChhatraLekha Knowledge Base"),
        confidence=result.get("confidence", 0.8),
    )


@router.get("/prompts", response_model=PromptsResponse, summary="Get quick question prompt suggestions")
async def get_prompts(
    request: Request,
) -> PromptsResponse:
    """Return suggested prompt chips tailored to the current user's role."""
    principal = _get_optional_principal(request)
    role = principal.get("role", "student") if principal else "student"
    prompts = get_quick_prompts_for_role(role)
    return PromptsResponse(role=role, prompts=prompts)
