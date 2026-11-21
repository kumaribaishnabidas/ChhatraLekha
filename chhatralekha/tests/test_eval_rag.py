"""Tests for the reproducible RAG evaluation harness."""

from __future__ import annotations

from pathlib import Path

from app.scripts.eval_rag import evaluate, load_questions, render_markdown
from app.services.rag import Document, TfidfRetriever, get_default_retriever

QUESTIONS = [
    {
        "question": "How do I check my attendance?",
        "kind": "guidance",
        "expected_doc": "kb:attendance",
        "language": "en",
        "role": "student",
    },
    {
        "question": "How do I change the language?",
        "kind": "guidance",
        "expected_doc": "kb:language_and_voice",
        "language": "en",
        "role": "student",
    },
    {
        "question": "Show my timetable",
        "kind": "record",
        "expected_intent": "timetable",
        "language": "en",
        "role": "student",
    },
]


def test_load_questions_from_repository():
    questions = load_questions()

    assert len(questions) >= 30
    assert all({"question", "kind", "role"} <= set(item) for item in questions)


def test_load_questions_from_an_injected_path(tmp_path: Path):
    source = tmp_path / "questions.json"
    source.write_text('[{"question": "hi", "kind": "guidance"}]', encoding="utf-8")

    assert load_questions(source)[0]["question"] == "hi"


def test_evaluate_perfect_corpus():
    retriever = TfidfRetriever(
        [
            Document(
                doc_id="kb:attendance:en",
                text="Attendance is checked in the attendance tab.",
                roles=("student",),
            ),
            Document(
                doc_id="kb:language_and_voice:en",
                text="Change the language with the language selector.",
                roles=("student",),
            ),
        ]
    )

    report = evaluate(QUESTIONS, retriever)

    assert report["retrieval_hit_rate"] == 1.0
    assert report["mean_reciprocal_rank"] == 1.0
    assert report["intent_accuracy"] == 1.0
    assert report["role_isolation_pass_rate"] == 1.0
    assert report["pii_leak_count"] == 0
    assert report["failures"] == []


def test_evaluate_reports_misses():
    unknown = [{"question": "zzz qwerty blorptastic", "kind": "guidance", "expected_doc": "kb:help"}]
    report = evaluate(QUESTIONS + unknown, TfidfRetriever([]))

    assert report["retrieval_hit_rate"] == 0.0
    assert len(report["failures"]) == 3


def test_render_markdown_contains_all_metrics():
    report = evaluate(QUESTIONS, TfidfRetriever([]))
    markdown = render_markdown(report)

    assert "Retrieval hit rate" in markdown
    assert "Missed questions" in markdown
    assert "PII leaks" in markdown


def test_repository_golden_set_scores_well():
    report = evaluate(load_questions(), get_default_retriever())

    assert report["retrieval_hit_rate"] >= 0.9
    assert report["intent_accuracy"] == 1.0
    assert report["role_isolation_pass_rate"] == 1.0
    assert report["pii_leak_count"] == 0
