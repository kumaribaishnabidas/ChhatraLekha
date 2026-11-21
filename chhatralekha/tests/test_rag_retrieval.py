"""Tests for the local retrieval layer behind the AI assistant.

These cover the properties that matter for a grounded system: the right
passage is ranked first, restricted passages cannot be retrieved by the wrong
role, unknown questions return no evidence, and retrieval data fits the chat
API contract.
"""

from __future__ import annotations

import pytest

from app.services.rag import (
    Document,
    chunk_markdown,
    chunks_to_citations,
    get_default_retriever,
    invalidate_default_retriever,
    knowledge_base_documents,
    markdown_documents,
    retrieve_context,
)
from app.services.rag.retriever import TfidfRetriever, canonical_role


def _corpus() -> list[Document]:
    return [
        Document(
            doc_id="kb:attendance",
            text="Mark daily class attendance in the teacher workspace. Present absent late.",
            section="attendance",
            source="knowledge base",
            roles=("teacher", "student"),
        ),
        Document(
            doc_id="doc:library.md:0",
            text="The digital library catalogue lists books, due dates and stock availability.",
            section="Library catalogue",
            source="docs/library.md",
        ),
        Document(
            doc_id="kb:admin",
            text="Preview the impact of a record correction before applying it.",
            section="admin_operations",
            source="knowledge base",
            roles=("institution_admin",),
        ),
    ]


def test_chunk_markdown_keeps_headings_as_sections():
    text = "# Guide\n\nIntro paragraph.\n\n## Attendance\n\nMark the register daily.\n"

    chunks = chunk_markdown(text, doc_id="doc:guide.md", source="docs/guide.md")

    assert [chunk.section for chunk in chunks] == ["Guide", "Attendance"]
    assert "Mark the register daily." in chunks[1].text
    assert chunks[0].doc_id == "doc:guide.md:0"


def test_chunk_markdown_does_not_treat_fenced_code_as_heading():
    text = "## Example\n\nShort explanation.\n\n```md\n# not a heading\n```\n"

    chunks = chunk_markdown(text, doc_id="doc:code.md")

    assert len(chunks) == 1
    assert chunks[0].section == "Example"
    assert "# not a heading" not in chunks[0].text


def test_tfidf_ranks_the_relevant_passage_first():
    retriever = TfidfRetriever(_corpus())

    results = retriever.retrieve("How do I mark attendance?", top_k=2, role="teacher")

    assert results
    assert results[0].doc_id == "kb:attendance"
    assert results[0].score > 0


def test_role_filter_hides_restricted_passages():
    retriever = TfidfRetriever(_corpus())

    as_student = retriever.retrieve("record correction impact", role="student")
    as_admin = retriever.retrieve("record correction impact", role="institution_admin")

    assert all(chunk.doc_id != "kb:admin" for chunk in as_student)
    assert any(chunk.doc_id == "kb:admin" for chunk in as_admin)


def test_unknown_question_returns_no_evidence():
    retriever = TfidfRetriever(_corpus())

    assert retriever.retrieve("zzyzx qwertyuiop blorptastic", top_k=3) == []


def test_retrieved_passage_has_api_ready_shape():
    result = TfidfRetriever(_corpus()).retrieve("library books", top_k=1)[0]

    data = result.as_dict()
    assert set(data) == {"doc_id", "section", "text", "score", "source"}
    assert isinstance(data["score"], float)


def test_citations_match_the_chat_response_schema():
    chunks = TfidfRetriever(_corpus()).retrieve("library books", top_k=1)

    citations = chunks_to_citations(chunks)

    assert citations == [
        {
            "label": "Library catalogue",
            "collection": "docs/library.md",
            "scope": "doc:library.md:0",
        }
    ]


def test_knowledge_base_documents_are_multilingual_and_role_scoped():
    documents = knowledge_base_documents()

    assert documents
    assert {doc.language for doc in documents} >= {"en", "hi", "or"}
    assert all(doc.roles for doc in documents)


def test_canonical_role_maps_portal_aliases():
    assert canonical_role("school_admin") == "institution_admin"
    assert canonical_role("university_admin") == "aicte_admin"
    assert canonical_role(None) == "student"


def test_markdown_documents_accept_an_injected_root(tmp_path):
    (tmp_path / "guide.md").write_text("# Help\n\nVoice commands are described here.\n", encoding="utf-8")

    documents = markdown_documents([tmp_path])

    assert documents
    assert all(doc.doc_id.startswith("doc:") for doc in documents)
    assert any("Voice commands" in doc.text for doc in documents)


def test_default_retriever_is_cached_until_invalidated():
    first = get_default_retriever()
    assert get_default_retriever() is first

    invalidate_default_retriever()
    assert get_default_retriever() is not first


def test_retrieve_context_returns_json_safe_passages():
    chunks = retrieve_context("How do I change my language?", role="student", language="en")

    assert chunks
    assert all(isinstance(chunk["score"], float) for chunk in chunks)
    assert all(isinstance(chunk["text"], str) for chunk in chunks)


@pytest.mark.asyncio
async def test_guidance_answer_carries_retrieval_and_citations(client):
    response = await client.post(
        "/api/ai/chat",
        json={"message": "How do I change my language?", "language": "en"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["retrieval"]["provider"] == "tfidf-local"
    assert payload["retrieval"]["chunks"]
    assert payload["citations"]
    assert payload["grounded"] is False


@pytest.mark.asyncio
async def test_record_intent_does_not_gain_document_retrieval(client):
    response = await client.post(
        "/api/ai/chat",
        json={"message": "What is my attendance?", "language": "en"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["retrieval"] is None
    assert payload["citations"] == []
