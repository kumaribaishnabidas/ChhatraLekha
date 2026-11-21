"""A small, deterministic TF-IDF vectoriser.

The goal here is reproducible retrieval rather than semantic novelty: the
corpus is a few hundred reviewed passages, so a pure-Python vectoriser is
fast enough, has no model download, and produces identical rankings on every
machine. It also handles the Devanagari and Odia passages in the knowledge
base because it tokenises on Unicode word boundaries.
"""

from __future__ import annotations

import math
import unicodedata
from collections import Counter
from typing import Iterable, Sequence

_APOSTROPHES = frozenset("'\u2019-")

#: Function words add noise to every query and carry no retrieval signal.
_STOPWORDS = frozenset(
    """
    a an and are as at be by can do does for from how i in into is it me my
    of on or our show tell that the their there these this to use using what
    when where which who why will with you your please about
    """.split()
)


def _is_token_character(character: str) -> bool:
    """Keep letters, digits and combining marks (Indic vowel signs)."""
    return character.isalnum() or unicodedata.category(character).startswith("M")


def tokenize(text: str) -> list[str]:
    """Lower-case Unicode word tokens, without stopwords or single letters.

    A regex based on ``\\w`` breaks Devanagari and Odia words at their vowel
    marks. Scanning by Unicode category keeps ``भाषा`` and ``ଉପସ୍ଥାନ`` intact.
    """
    tokens: list[str] = []
    current: list[str] = []
    for character in (text or "").lower():
        if _is_token_character(character):
            current.append(character)
        elif character in _APOSTROPHES and current:
            current.append(character)
        else:
            if current:
                tokens.append("".join(current).strip("'\u2019-"))
            current = []
    if current:
        tokens.append("".join(current).strip("'\u2019-"))
    return [token for token in tokens if len(token) > 1 and token not in _STOPWORDS]


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Dot product of two L2-normalised sparse vectors."""
    if len(a) > len(b):
        a, b = b, a
    return sum(weight * b.get(term, 0.0) for term, weight in a.items())


class TfidfVectorizer:
    """Fit IDF weights on a corpus, then vectorise queries with the same IDF."""

    def __init__(self) -> None:
        self.idf_: dict[str, float] = {}

    def fit_transform(self, documents: Sequence[str]) -> list[dict[str, float]]:
        """Tokenise the raw passages, learn IDF, and vectorise them."""
        token_lists = [tokenize(document) for document in documents]
        total = len(token_lists)
        document_frequency: Counter[str] = Counter()
        for tokens in token_lists:
            document_frequency.update(set(tokens))
        self.idf_ = {
            term: math.log((1 + total) / (1 + frequency)) + 1.0
            for term, frequency in document_frequency.items()
        }
        return [self.transform(tokens) for tokens in token_lists]

    def transform(self, tokens: Iterable[str]) -> dict[str, float]:
        counts = Counter(token for token in tokens if token in self.idf_)
        if not counts:
            return {}
        vector = {
            term: (1.0 + math.log(count)) * self.idf_[term]
            for term, count in counts.items()
        }
        norm = math.sqrt(sum(weight * weight for weight in vector.values()))
        if norm:
            vector = {term: weight / norm for term, weight in vector.items()}
        return vector
