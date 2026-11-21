"""Top-k retrieval over the assistant's local documentation corpus."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Mapping, Sequence

from app.core.config import get_settings
from app.services.ai_assistant import ROLE_PROMPT_ALIASES
from app.services.rag.documents import Document, all_documents
from app.services.rag.embeddings import TfidfVectorizer, cosine, tokenize

#: Below this cosine score a passage is not evidence for an answer.
_RELEVANCE_FLOOR = 0.05
#: A small boost when the passage is written in the answer language.
_LANGUAGE_BOOST = 1.05


@dataclass(frozen=True)
class RetrievedChunk:
    """A passage returned by retrieval, ready to be cited by the API."""

    doc_id: str
    section: str
    text: str
    score: float
    source: str
    #: Kept for evaluation only; never serialised into the chat response.
    roles: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "section": self.section,
            "text": self.text,
            "score": round(self.score, 4),
            "source": self.source,
        }


def canonical_role(role: str | None) -> str:
    """Map a portal-specific role onto the role used by the knowledge base."""
    value = (role or "student").strip().lower()
    if value in {"anonymous", "public", "guest", "none"}:
        return "student"
    return ROLE_PROMPT_ALIASES.get(value, value)


class TfidfRetriever:
    """Rank the corpus against a query with a local TF-IDF model."""

    def __init__(self, documents: Sequence[Document]) -> None:
        self.documents = list(documents)
        self.vectorizer = TfidfVectorizer()
        self.vectors = self.vectorizer.fit_transform(
            [document.search_text() for document in self.documents]
        )

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 4,
        role: str | None = None,
        language: str | None = None,
        min_score: float = _RELEVANCE_FLOOR,
    ) -> list[RetrievedChunk]:
        """Return the best passages the caller is allowed to read."""
        if top_k <= 0 or not self.documents:
            return []
        query_vector = self.vectorizer.transform(tokenize(query))
        if not query_vector:
            return []

        allowed_role = canonical_role(role)
        answer_language = (language or "en").strip().lower()
        scored: list[RetrievedChunk] = []
        for document, vector in zip(self.documents, self.vectors, strict=True):
            if document.roles and allowed_role not in document.roles:
                continue
            score = cosine(query_vector, vector) * document.boost
            if score <= 0:
                continue
            if answer_language and answer_language in document.language:
                score *= _LANGUAGE_BOOST
            if score < min_score:
                continue
            scored.append(
                RetrievedChunk(
                    doc_id=document.doc_id,
                    section=document.section,
                    text=document.text,
                    score=score,
                    source=document.source,
                    roles=document.roles,
                )
            )
        scored.sort(key=lambda chunk: (-chunk.score, chunk.doc_id))
        return scored[:top_k]


@lru_cache(maxsize=1)
def get_default_retriever() -> TfidfRetriever:
    """Build (and cache) the retriever over the shipped documentation."""
    return TfidfRetriever(all_documents())


def invalidate_default_retriever() -> None:
    """Rebuild the corpus on the next call — used after docs change in tests."""
    get_default_retriever.cache_clear()


def retrieve_context(
    query: str,
    *,
    top_k: int | None = None,
    role: str | None = None,
    language: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve passages as JSON-safe dictionaries for the chat response."""
    limit = top_k if top_k is not None else get_settings().ai_top_k
    return [
        chunk.as_dict()
        for chunk in get_default_retriever().retrieve(
            query, top_k=limit, role=role, language=language
        )
    ]


def chunks_to_citations(
    chunks: Iterable[RetrievedChunk | Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Map passages onto the ``Citation`` schema returned by ``/api/ai/chat``."""
    citations: list[dict[str, str]] = []
    for chunk in chunks:
        data = chunk.as_dict() if isinstance(chunk, RetrievedChunk) else dict(chunk)
        citations.append(
            {
                "label": str(data.get("section") or data.get("doc_id") or "Reference"),
                "collection": str(data.get("source") or "ChhatraLekha documentation"),
                "scope": str(data.get("doc_id") or ""),
            }
        )
    return citations
