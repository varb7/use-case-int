"""Step 1: persistent Google embeddings and independently testable semantic search."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from workflow import EvidenceSection, GeminiProvider, WorkflowEngine, load_evidence, retrieve
from secure_settings import resolve_api_key
from app_paths import data_directory

CHUNKING_VERSION = "markdown-h2-v1"


def unit_vector(values: list[float]) -> list[float]:
    if not values or not all(math.isfinite(x) for x in values):
        raise ValueError("Embedding must contain finite numbers")
    norm = math.hypot(*values)
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Embedding must have a finite, nonzero norm")
    return [x / norm for x in values]


class GoogleEmbeddings:
    def __init__(self):
        from google import genai
        from google.genai import types

        key = resolve_api_key()
        if not key:
            raise RuntimeError("Add a Google API key in Settings or set GEMINI_API_KEY/GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        self.types = types
        self._next_request = 0.0
        self.client = genai.Client(api_key=key, http_options=types.HttpOptions(
            timeout=30_000, retry_options=types.HttpRetryOptions(attempts=1)))

    def embed(self, text: str, task: str) -> list[float]:
        from google.genai.errors import APIError

        for attempt in range(3):
            # ponytail: one request/second per instance; shared limiter if concurrent workers are added.
            time.sleep(max(0.0, getattr(self, "_next_request", 0.0) - time.monotonic()))
            self._next_request = time.monotonic() + 1.0
            try:
                result = self.client.models.embed_content(
                    model=self.model, contents=text,
                    config=self.types.EmbedContentConfig(task_type=task),
                )
                break
            except APIError as exc:
                if exc.code not in (429, 500, 503) or attempt == 2:
                    raise
                delay = 60.0 if exc.code == 429 else float(2 ** attempt)
                payload = getattr(exc, "details", {}) or {}
                if not isinstance(payload, dict):
                    payload = {}
                for detail in payload.get("error", payload).get("details", []):
                    if detail.get("@type", "").endswith("RetryInfo"):
                        try:
                            delay = float(detail["retryDelay"].removesuffix("s")) + 1.0
                        except (KeyError, ValueError, AttributeError):
                            pass
                if not math.isfinite(delay) or delay < 0 or delay > 60:
                    raise  # Long-lived quota exhaustion needs an explicit later retry.
                time.sleep(delay)
        if not result.embeddings or len(result.embeddings) != 1:
            raise ValueError("Google returned no single embedding")
        return unit_vector(result.embeddings[0].values or [])


class SemanticIndex:
    def __init__(self, path: Path, provider):
        self.path, self.provider = path, provider
        self.sections: list[EvidenceSection] = []
        self.vectors: list[list[float]] = []

    def sync(self, sections: list[EvidenceSection]) -> dict[str, int]:
        """Publish a complete snapshot only after every required embedding succeeds."""
        if len({s.ref_id for s in sections}) != len(sections):
            raise ValueError("Duplicate evidence reference IDs")
        records, vectors = [], []
        reused = 0
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS evidence_embeddings (
                ref_id TEXT PRIMARY KEY, cache_key TEXT NOT NULL,
                content_hash TEXT NOT NULL, model TEXT NOT NULL,
                chunking_version TEXT NOT NULL, metadata TEXT NOT NULL,
                embedding TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS embedding_checkpoints (
                cache_key TEXT PRIMARY KEY, embedding TEXT NOT NULL)""")
            previous = dict(db.execute("SELECT ref_id, cache_key FROM evidence_embeddings"))
            for section in sections:
                # Hash the actual embedding input, so heading/location edits also invalidate it.
                text = f"{section.source_file}\n{section.heading}\n{section.text}"
                key = hashlib.sha256(json.dumps([
                    self.provider.model, CHUNKING_VERSION, "RETRIEVAL_DOCUMENT", text
                ]).encode("utf-8")).hexdigest()
                if previous.get(section.ref_id) == key:
                    row = db.execute("SELECT embedding FROM evidence_embeddings WHERE ref_id=?",
                                     (section.ref_id,)).fetchone()
                    vector = unit_vector(json.loads(row[0]))
                    reused += 1
                else:
                    checkpoint = db.execute("SELECT embedding FROM embedding_checkpoints WHERE cache_key=?", (key,)).fetchone()
                    if checkpoint:
                        vector = unit_vector(json.loads(checkpoint[0]))
                        reused += 1
                    else:
                        vector = unit_vector(self.provider.embed(text, "RETRIEVAL_DOCUMENT"))
                        db.execute("INSERT OR REPLACE INTO embedding_checkpoints VALUES (?, ?)",
                                   (key, json.dumps(vector)))
                        db.commit()  # Keep successful work if a subsequent API request fails.
                if vectors and len(vector) != len(vectors[0]):
                    raise ValueError("Embedding dimensions differ within the index")
                vectors.append(vector)
                records.append((section.ref_id, key, section.content_hash, self.provider.model,
                                CHUNKING_VERSION, section.model_dump_json(), json.dumps(vector)))
            # ponytail: replace one small corpus atomically; incremental writes if corpus grows.
            db.execute("DELETE FROM evidence_embeddings")
            db.executemany("INSERT INTO evidence_embeddings VALUES (?, ?, ?, ?, ?, ?, ?)", records)
            db.execute("DELETE FROM embedding_checkpoints")
        self.sections, self.vectors = list(sections), vectors
        return {"chunks": len(sections), "reused": reused, "generated": len(sections) - reused,
                "removed": len(set(previous) - {s.ref_id for s in sections})}

    def search(self, question: str, limit: int = 8) -> list[tuple[EvidenceSection, float]]:
        if not question.strip():
            raise ValueError("Question must not be empty")
        if limit < 1 or not self.sections:
            return []
        query = unit_vector(self.provider.embed(question, "RETRIEVAL_QUERY"))
        if len(query) != len(self.vectors[0]):
            raise ValueError("Query and document embedding dimensions differ")
        scored = [(section, sum(a * b for a, b in zip(query, vector)))
                  for section, vector in zip(self.sections, self.vectors)]
        return sorted(scored, key=lambda item: (-item[1], item[0].ref_id))[:limit]


def fuse_rankings(*rankings: list[EvidenceSection], limit: int = 8) -> list[EvidenceSection]:
    """Equal-weight reciprocal rank fusion, ranks start at one, k=60."""
    scores, sources = {}, {}
    for ranking in rankings:
        seen = set()
        for rank, section in enumerate(ranking, 1):
            if section.ref_id in seen:
                continue
            seen.add(section.ref_id)
            sources[section.ref_id] = section
            scores[section.ref_id] = scores.get(section.ref_id, 0) + 1 / (60 + rank)
    return [sources[ref] for ref in sorted(scores, key=lambda ref: (-scores[ref], ref))[:max(0, limit)]]


class HybridRetriever:
    def __init__(self, index: SemanticIndex):
        self.index = index

    def __call__(self, question: str, evidence: list[EvidenceSection]) -> list[EvidenceSection]:
        semantic = [section for section, score in self.index.search(question, limit=10) if score > 0]
        return fuse_rankings(retrieve(question, evidence, limit=10), semantic)


class SemanticRetriever:
    def __init__(self, index: SemanticIndex):
        self.index = index

    def __call__(self, question: str, evidence: list[EvidenceSection]) -> list[EvidenceSection]:
        return [section for section, score in self.index.search(question, limit=8) if score > 0]


def build_engine(root: Path, evidence: list[EvidenceSection]) -> WorkflowEngine:
    provider = GeminiProvider()  # Validate generation configuration before embedding calls.
    index = SemanticIndex(data_directory(root) / "evidence_embeddings.sqlite3", GoogleEmbeddings())
    index.sync(evidence)
    return WorkflowEngine(evidence, provider, retriever=SemanticRetriever(index))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Optional question to search after indexing")
    args = parser.parse_args()
    root = Path(__file__).parent
    index = SemanticIndex(root / "evidence_embeddings.sqlite3", GoogleEmbeddings())
    print(json.dumps(index.sync(load_evidence(root))))
    if args.query:
        for section, score in index.search(args.query):
            print(json.dumps({"score": score, "ref_id": section.ref_id,
                              "source_file": section.source_file, "heading": section.heading}))


if __name__ == "__main__":
    main()
