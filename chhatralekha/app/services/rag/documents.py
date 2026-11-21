"""Build the assistant's searchable corpus from reviewed sources.

Two kinds of source are indexed:

* the hand-reviewed multilingual answer catalogue in ``ai_assistant.py``;
* the Markdown documentation shipped with the repository, split by heading.

Both are turned into :class:`Document` values. A document carries the role
restriction of its source so a retrieval result can never widen what the
caller is allowed to read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

#: Files above this size are skipped: they are generated reports, not prose.
_MAX_FILE_BYTES = 200_000
#: A very long section is split into paragraph-sized chunks.
_MAX_CHUNK_CHARS = 1_400
#: Engineering process artefacts are not user guidance and swamp the index.
_EXCLUDED_DIRS = frozenset({"audits", "testing", "releases"})
#: Reviewed catalogue entries outrank incidental mentions in long docs.
_CATALOGUE_BOOST = 2.5

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
_HTML_RE = re.compile(r"<[^>]+>")
_EMPHASIS_RE = re.compile(r"[`*_]")


@dataclass(frozen=True)
class Document:
    """One searchable passage.

    ``roles`` is a whitelist. An empty tuple means the passage is public
    platform documentation; a non-empty tuple restricts it to those portals.
    """

    doc_id: str
    text: str
    section: str = ""
    source: str = ""
    roles: tuple[str, ...] = ()
    language: str = "en"
    actions: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    boost: float = 1.0

    def search_text(self) -> str:
        """The text vectorised for retrieval (identity + prose + section)."""
        return f"{self.section}\n{self.text}"

    def as_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "section": self.section,
            "source": self.source,
            "language": self.language,
            "text": self.text,
        }


def _clean_markdown(value: str) -> str:
    """Strip markup that would only add noise to the token stream."""
    value = _LINK_RE.sub(r"\1", value or "")
    value = _HTML_RE.sub(" ", value)
    value = _EMPHASIS_RE.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def chunk_markdown(
    text: str,
    *,
    doc_id: str,
    source: str = "",
    roles: Sequence[str] = (),
    max_chunk_chars: int = _MAX_CHUNK_CHARS,
) -> list[Document]:
    """Split Markdown into heading-scoped passages.

    The heading is kept as the section label, so every retrieved passage can
    be cited as ``source § section``. Fenced code blocks are kept verbatim but
    never treated as headings.
    """
    chunks: list[Document] = []
    buffer: list[str] = []
    heading = ""
    in_fence = False

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(buffer).strip()
        if body:
            chunks.append(
                Document(
                    doc_id=f"{doc_id}:{len(chunks)}",
                    text=body,
                    section=heading,
                    source=source or doc_id,
                    roles=tuple(roles),
                )
            )
        buffer = []

    for line in (text or "").splitlines():
        if _FENCE_RE.match(line):
            # Code samples contain example identifiers and add no guidance.
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = None if in_fence else _HEADING_RE.match(line)
        if match:
            flush()
            heading = _clean_markdown(match.group(2))
            continue
        buffer.append(line)
    flush()

    if max_chunk_chars <= 0:
        return chunks

    # Split oversized prose sections on blank lines while keeping the label.
    refined: list[Document] = []
    for chunk in chunks:
        if len(chunk.text) <= max_chunk_chars:
            refined.append(chunk)
            continue
        paragraph: list[str] = []
        for raw in chunk.text.split("\n"):
            candidate = "\n".join([*paragraph, raw]).strip()
            if paragraph and len(candidate) > max_chunk_chars:
                refined.append(
                    Document(
                        doc_id=f"{chunk.doc_id}.{len(refined)}",
                        text="\n".join(paragraph).strip(),
                        section=chunk.section,
                        source=chunk.source,
                        roles=chunk.roles,
                        language=chunk.language,
                    )
                )
                paragraph = []
            paragraph.append(raw)
        if paragraph:
            refined.append(
                Document(
                    doc_id=f"{chunk.doc_id}.{len(refined)}",
                    text="\n".join(paragraph).strip(),
                    section=chunk.section,
                    source=chunk.source,
                    roles=chunk.roles,
                    language=chunk.language,
                )
            )
    return refined


def knowledge_base_documents() -> list[Document]:
    """Turn the reviewed multilingual answer catalogue into documents."""
    from app.services.ai_assistant import KNOWLEDGE_BASE

    documents: list[Document] = []
    for article in KNOWLEDGE_BASE:
        keywords = " ".join(str(word) for word in article.get("keywords", []))
        languages = [code for code in ("en", "hi", "or") if article.get(code)]
        # One document per language: a short, focused passage scores higher
        # than a single long trilingual blob, and the language boost can pick
        # the article in the answer locale.
        for language in languages or ["en"]:
            documents.append(
                Document(
                    doc_id=f"kb:{article['id']}:{language}",
                    text=f"{keywords}\n{article[language]}".strip(),
                    section=str(article.get("id", "guide")),
                    source="ChhatraLekha knowledge base",
                    roles=tuple(article.get("roles", []) or ()),
                    language=language,
                    boost=_CATALOGUE_BOOST,
                    actions=tuple(
                        (str(action["label"]), str(action["url"]))
                        for action in article.get("actions", [])
                    ),
                )
            )
    return documents


def default_document_roots() -> tuple[Path, ...]:
    """Existing documentation directories, root first for stable ordering."""
    module = Path(__file__).resolve()
    backend_root = module.parents[3]  # chhatralekha/
    repository_root = module.parents[4]  # ChhatraLekha/
    candidates = (repository_root / "docs", backend_root / "docs")
    return tuple(path for path in candidates if path.is_dir())


def markdown_documents(roots: Iterable[Path] | None = None) -> list[Document]:
    """Chunk every Markdown file in the documentation trees.

    ``roots`` is injectable so tests can build a corpus from a temporary
    directory instead of the repository.
    """
    sources = tuple(roots) if roots is not None else default_document_roots()
    documents: list[Document] = []
    for root in sources:
        base = root.parent
        for path in sorted(root.rglob("*.md")):
            if _EXCLUDED_DIRS.intersection(path.relative_to(root).parts[:-1]):
                continue
            try:
                if path.stat().st_size > _MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            relative = path.relative_to(base).as_posix()
            documents.extend(
                chunk_markdown(text, doc_id=f"doc:{relative}", source=relative)
            )
    return documents


def all_documents(roots: Iterable[Path] | None = None) -> list[Document]:
    """The full default corpus: reviewed catalogue first, then documentation."""
    return [*knowledge_base_documents(), *markdown_documents(roots)]
