"""Local, dependency-free retrieval for the grounded AI assistant.

The assistant already has a reviewed answer catalogue and role-scoped record
handlers. This package adds the missing retrieval layer: the documentation is
chunked, embedded with a small TF-IDF vectoriser written in pure Python, and
searched at query time. No model download, API key or network call is needed
for the default path, so the demo works completely offline.
"""

from app.services.rag.documents import (
    Document,
    chunk_markdown,
    default_document_roots,
    knowledge_base_documents,
    markdown_documents,
)
from app.services.rag.generation import (
    GenerationResult,
    generate_grounded_answer,
    get_provider,
)
from app.services.rag.retriever import (
    RetrievedChunk,
    TfidfRetriever,
    chunks_to_citations,
    get_default_retriever,
    invalidate_default_retriever,
    retrieve_context,
)

__all__ = [
    "Document",
    "GenerationResult",
    "RetrievedChunk",
    "TfidfRetriever",
    "chunk_markdown",
    "chunks_to_citations",
    "default_document_roots",
    "generate_grounded_answer",
    "get_default_retriever",
    "get_provider",
    "invalidate_default_retriever",
    "knowledge_base_documents",
    "markdown_documents",
    "retrieve_context",
]
