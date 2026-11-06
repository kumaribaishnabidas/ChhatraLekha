"""AI Assistant endpoints.

The assistant has two jobs: explain the platform, and answer questions about
the caller's own authorised records. The role and identity used for the second
job always come from the authenticated session - never from the request body.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.api.deps import (
    Principal,
    client_ip,
    enforce_rate_limit,
    get_db,
    get_optional_principal,
)
from app.audit import writer
from app.repositories.audit import AuditRepository
from app.services.ai_assistant import get_quick_prompts_for_role
from app.services.ai_grounding import build_grounded_response

router = APIRouter(prefix="/ai", tags=["ai-assistant"])


class ChatRequest(BaseModel):
    """A chat turn.

    ``role`` and ``context`` are accepted for backwards compatibility with the
    first version of the drawer, but they are ignored: role and scope are read
    from the bearer token instead.
    """

    message: str = Field(..., min_length=1, max_length=1000)
    language: Optional[str] = "en"
    role: Optional[str] = Field(None, deprecated=True)
    context: Optional[Dict[str, Any]] = Field(None, deprecated=True)


class ActionChip(BaseModel):
    label: str
    url: str


class Citation(BaseModel):
    label: str
    collection: str = ""
    scope: str = ""


class ChatResponse(BaseModel):
    reply: str
    actions: List[ActionChip] = []
    source: str
    confidence: float
    grounded: bool = False
    intent: str = "help"
    language: str = "en"
    data: Optional[Dict[str, Any]] = None
    citations: List[Citation] = []
    followups: List[str] = []


class PromptsResponse(BaseModel):
    role: str
    prompts: List[str]


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the ChhatraLekha assistant a question",
    dependencies=[Depends(enforce_rate_limit)],
)
async def chat(
    payload: ChatRequest,
    request: Request,
    principal: Optional[Principal] = Depends(get_optional_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ChatResponse:
    """Answer from reviewed guidance, or from the caller's authorised records.

    A grounded answer is written to the audit trail as an ``AI_GROUNDED_QUERY``
    entry. The user's question text is deliberately not logged - only the
    intent and the fact that record data was read.
    """
    result = await build_grounded_response(
        db=db,
        principal=principal,
        query=payload.message,
        language=payload.language,
    )

    if result.get("grounded") and principal is not None:
        await writer.log(
            AuditRepository(db["audit_events"]),
            actor=principal.subject,
            actor_role=principal.role,
            action="AI_GROUNDED_QUERY",
            subject=principal.apaar_id or principal.subject,
            details=(
                f"Assistant answered intent '{result['intent']}' from authorised records. "
                "Question text was not stored."
            ),
            category="AI",
            ip_address=client_ip(request),
        )

    return ChatResponse(**result)


@router.get("/prompts", response_model=PromptsResponse, summary="Get quick question prompts")
async def get_prompts(
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> PromptsResponse:
    """Return suggested prompt chips tailored to the authenticated role."""
    role = principal.role if principal is not None else "student"
    return PromptsResponse(role=role, prompts=get_quick_prompts_for_role(role))
