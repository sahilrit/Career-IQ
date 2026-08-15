"""Local, zero-cost semantic memory: derived from authoritative records.

No embedding API, paid or otherwise, is required. This indexes text with
a small TF-IDF model and ranks by cosine similarity — good enough to
answer "which past companies/notes are relevant to X" without any
external service. A future provider can implement the same
``SemanticIndex`` protocol on a real embedding model (Phase 46/47's
local-AI stack) without callers changing.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Protocol

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class SemanticIndex(Protocol):
    def index(self, record_id: str, text: str) -> None: ...
    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]: ...


class LocalTfidfIndex:
    """Pure-Python TF-IDF + cosine similarity index. No external services."""

    def __init__(self) -> None:
        self._documents: dict[str, Counter[str]] = {}

    def index(self, record_id: str, text: str) -> None:
        self._documents[record_id] = Counter(_tokenize(text))

    def remove(self, record_id: str) -> None:
        self._documents.pop(record_id, None)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        query_vector = Counter(_tokenize(query))
        if not query_vector or not self._documents:
            return []

        idf = self._idf()
        query_weights = self._tfidf_weights(query_vector, idf)
        scored = []
        for record_id, doc_vector in self._documents.items():
            doc_weights = self._tfidf_weights(doc_vector, idf)
            score = _cosine_similarity(query_weights, doc_weights)
            if score > 0:
                scored.append((record_id, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

    def _idf(self) -> dict[str, float]:
        num_docs = len(self._documents)
        term_doc_counts: Counter[str] = Counter()
        for doc in self._documents.values():
            term_doc_counts.update(doc.keys())
        return {
            term: math.log((1 + num_docs) / (1 + count)) + 1
            for term, count in term_doc_counts.items()
        }

    @staticmethod
    def _tfidf_weights(term_counts: Counter[str], idf: dict[str, float]) -> dict[str, float]:
        total = sum(term_counts.values()) or 1
        return {term: (count / total) * idf.get(term, 1.0) for term, count in term_counts.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    shared_terms = set(a) & set(b)
    numerator = sum(a[term] * b[term] for term in shared_terms)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)
