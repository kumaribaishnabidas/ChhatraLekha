"""Evaluate the assistant's retrieval quality against a golden question set.

Run offline, with no model and no network::

    python -m app.scripts.eval_rag
    python -m app.scripts.eval_rag --write

The report measures retrieval, not generation: whether the right reviewed
passage is found, whether citations point at real passages, whether role
restrictions hold, and how slow the local index is.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from app.services.ai_grounding import detect_intent
from app.services.rag.guardrails import contains_sensitive_identifier
from app.services.rag.retriever import (
    RetrievedChunk,
    TfidfRetriever,
    canonical_role,
    get_default_retriever,
)

_RESOURCE = Path(__file__).resolve().parents[1] / "resources" / "rag_eval_questions.json"
_REPORT_PATH = Path(__file__).resolve().parents[3] / "docs" / "ai" / "EVALUATION.md"


def load_questions(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the golden question set from disk."""
    source = path or _RESOURCE
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("The RAG evaluation set must be a JSON array")
    return data


def _rank(expected: str | None, chunks: Sequence[RetrievedChunk]) -> int:
    if not expected:
        return 0
    for index, chunk in enumerate(chunks, start=1):
        if chunk.doc_id.startswith(expected):
            return index
    return 0


def evaluate(
    questions: Sequence[dict[str, Any]],
    retriever: TfidfRetriever,
    *,
    top_k: int = 4,
) -> dict[str, Any]:
    """Compute retrieval, citation, safety and latency metrics."""
    hits = 0
    reciprocal_ranks: list[float] = []
    citation_hits = 0
    intent_hits = 0
    isolation_passes = 0
    pii_leaks = 0
    latencies: list[float] = []
    failures: list[dict[str, Any]] = []
    guidance_count = 0
    record_count = 0

    for item in questions:
        question = str(item.get("question", ""))
        role = canonical_role(str(item.get("role") or "student"))
        language = str(item.get("language") or "en")

        started = time.perf_counter()
        chunks = retriever.retrieve(question, top_k=top_k, role=role, language=language)
        latencies.append((time.perf_counter() - started) * 1000)

        if item.get("kind") == "record":
            record_count += 1
            actual_intent, _ = detect_intent(question)
            if actual_intent == item.get("expected_intent"):
                intent_hits += 1
            continue

        guidance_count += 1
        expected = item.get("expected_doc")
        rank = _rank(expected, chunks)
        if expected:
            if rank:
                hits += 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                failures.append(
                    {
                        "question": question,
                        "expected_doc": expected,
                        "retrieved": [chunk.doc_id for chunk in chunks],
                    }
                )
            if chunks:
                citation_hits += 1
        if all(not chunk.roles or role in chunk.roles for chunk in chunks):
            isolation_passes += 1
        for chunk in chunks:
            if contains_sensitive_identifier(chunk.text):
                pii_leaks += 1

    def rate(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 4) if denominator else 0.0

    ordered = sorted(latencies)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corpus_size": len(retriever.documents),
        "question_count": len(questions),
        "top_k": top_k,
        "guidance_count": guidance_count,
        "record_count": record_count,
        "retrieval_hit_rate": rate(
            hits, sum(1 for item in questions if item.get("expected_doc"))
        ),
        "mean_reciprocal_rank": round(statistics.fmean(reciprocal_ranks), 4)
        if reciprocal_ranks
        else 0.0,
        "citation_coverage": rate(
            citation_hits, sum(1 for item in questions if item.get("expected_doc"))
        ),
        "intent_accuracy": rate(intent_hits, record_count),
        "role_isolation_pass_rate": rate(isolation_passes, guidance_count),
        "pii_leak_count": pii_leaks,
        "latency_p50_ms": round(statistics.median(ordered), 4) if ordered else 0.0,
        "latency_p95_ms": round(ordered[max(0, int(len(ordered) * 0.95) - 1)], 4)
        if ordered
        else 0.0,
        "failures": failures,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a report as the Markdown artefact used for the project report."""
    lines = [
        "# ChhatraLekha — RAG Evaluation Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "This report measures the **local retrieval layer**, not an external "
        "model. It is reproducible offline with "
        "`python -m app.scripts.eval_rag`.",
        "",
        "## Configuration",
        "",
        "| Setting | Value |",
        "| :--- | ---: |",
        f"| Corpus passages | {report['corpus_size']} |",
        f"| Questions | {report['question_count']} |",
        f"| Guidance / record | {report['guidance_count']} / {report['record_count']} |",
        f"| top-k | {report['top_k']} |",
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
        f"| Retrieval hit rate | {report['retrieval_hit_rate']:.0%} |",
        f"| Mean reciprocal rank | {report['mean_reciprocal_rank']:.4f} |",
        f"| Citation coverage | {report['citation_coverage']:.0%} |",
        f"| Intent accuracy | {report['intent_accuracy']:.0%} |",
        f"| Role isolation pass rate | {report['role_isolation_pass_rate']:.0%} |",
        f"| PII leaks | {report['pii_leak_count']} |",
        f"| Retrieval latency p50 | {report['latency_p50_ms']:.3f} ms |",
        f"| Retrieval latency p95 | {report['latency_p95_ms']:.3f} ms |",
        "",
    ]
    if report["failures"]:
        lines.extend(
            [
                "## Missed questions",
                "",
                "| Question | Expected | Retrieved |",
                "| :--- | :--- | :--- |",
            ]
        )
        for failure in report["failures"]:
            retrieved = ", ".join(failure["retrieved"]) or "none"
            lines.append(
                f"| {failure['question']} | `{failure['expected_doc']}` | {retrieved} |"
            )
        lines.append("")
    else:
        lines.extend(["All golden questions retrieved their expected passage.", ""])
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write docs/ai/EVALUATION.md")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args(argv)

    # Windows consoles default to cp1252; the golden set contains Indic text.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    report = evaluate(load_questions(), get_default_retriever(), top_k=args.top_k)
    rendered = render_markdown(report)
    print(rendered)

    if args.write:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text(rendered, encoding="utf-8")
        print(f"Wrote {_REPORT_PATH}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
