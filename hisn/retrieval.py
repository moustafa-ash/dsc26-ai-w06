"""Runbook search over hisn/data/runbooks. You write this file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer


@lru_cache(maxsize=1)
def _index():
    runbooks = []
    for path in sorted(Path(__file__).with_name("data").glob("runbooks/*.md")):
        _, headers, body = path.read_text(encoding="utf-8").split("---", 2)
        metadata = dict(line.split(": ", 1) for line in headers.strip().splitlines())
        snippet = next(line for line in body.splitlines() if line.strip() and not line.startswith("#"))
        runbooks.append((metadata["id"], metadata["title"], snippet, body))
    vectorizers = (
        TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True),
    )
    corpus = [f"{title} {title} {body}" for _, title, _, body in runbooks]
    indexes = [(vectorizer, vectorizer.fit_transform(corpus)) for vectorizer in vectorizers]
    return runbooks, indexes


def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Search Hisn's SOC runbooks.

    Returns up to `k` results, each `{"id", "title", "snippet", "score"}`, best first, ties
    broken by ID ascending. `k` is clamped to 1-10. A blank (empty or whitespace-only) query
    returns `[]`. Any method is fine (TF-IDF, BM25, …); it must run offline and return the
    right runbook for clear queries. See README.md for the ten runbook IDs and topics.
    """
    if not query.strip():
        return []
    runbooks, indexes = _index()
    lexical, character = [(matrix @ vectorizer.transform([query]).T).toarray().ravel()
                          for vectorizer, matrix in indexes]
    scores = 0.65 * lexical + 0.35 * character
    results = [
        {"id": book_id, "title": title, "snippet": snippet, "score": float(score)}
        for (book_id, title, snippet, _), score in zip(runbooks, scores)
    ]
    return sorted(results, key=lambda item: (-item["score"], item["id"]))[:max(1, min(k, 10))]
