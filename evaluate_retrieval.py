"""Retrieval evaluation; BM25 remains an experiment, never the app default."""
import argparse
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

from semantic import GoogleEmbeddings, SemanticIndex, fuse_rankings
from workflow import STOP_WORDS, load_evidence, parse_questionnaire, retrieve

ROOT = Path(__file__).parent

# Designated evidence sections, selected by reading the supplied KB before scoring.
# These measure target coverage, not exhaustive relevance or semantic answer support.
TARGETS = {
    "questionnaire-1-standard.csv": [
        [], ["07#current"], ["07#current"], ["01#security-team"], ["02#data-at-rest"],
        ["02#data-in-transit"], ["02#key-management"], ["02#key-management"],
        ["07#penetration-testing", "AA-009"], ["10#vulnerability-management", "07#penetration-testing"],
        ["03#authentication"], ["03#authorisation"], ["03#authorisation"],
        ["06#retention", "09#retention"], ["06#hosting-regions"], ["06#what-data-is-stored"],
        ["06#deletion-on-termination"], ["04#customer-notification"], ["04#history"],
        ["04#detection"], ["08#recovery-objectives"], ["08#dr-testing"],
        ["09#data-protection-officer"], ["05#current-subprocessors", "05#changes-to-the-list"], ["AA-033"],
    ],
    "questionnaire-2-enterprise.csv": [
        ["07#not-held"], ["07#not-held"], ["07#not-held"], ["07#not-held"], ["07#not-held"],
        ["08#availability-commitment"], ["08#availability"], ["08#status-communication"],
        ["10#hosting"], ["10#hosting"], ["10#secure-development"], ["10#environments"],
        ["03#customer-access"], ["03#customer-access"], ["03#privileged-access"], ["03#remote-access"],
        ["01#personnel-security"], ["01#personnel-security"], ["01#personnel-security"],
        ["09#liability"], ["09#insurance"], ["09#data-processing-agreement"], ["07#customer-audit"],
        ["06#what-data-is-stored"], ["06#retention"], ["08#backups", "06#hosting-regions"],
        ["09#data-subject-rights"], ["04#process"], ["04#testing"], ["05#supplier-assessment"],
    ],
    "questionnaire-3-narrative.csv": [
        ["01#scope", "01#risk-management", "07#current"], ["01#personnel-security", "03#authorisation"],
        ["09#roles", "09#data-processing-agreement"], ["06#what-data-is-stored", "06#retention", "09#retention"],
        ["05#data-transfers"], ["09#data-subject-rights"],
        ["02#data-in-transit", "02#data-at-rest", "02#key-management"],
        ["03#authentication", "03#authorisation", "03#customer-access"],
        ["03#privileged-access", "10#logging-and-monitoring", "04#detection"],
        ["10#secure-development", "10#change-management", "10#vulnerability-management", "07#penetration-testing", "AA-009"],
        ["08#recovery-objectives", "08#backups", "08#dr-testing"],
        ["08#availability", "08#availability-commitment"], ["08#status-communication", "04#customer-notification"],
        ["04#process", "04#customer-notification", "04#post-incident", "04#history"], ["04#detection"],
        ["05#current-subprocessors", "05#changes-to-the-list"], ["05#supplier-assessment"],
        ["07#current", "07#penetration-testing", "07#customer-audit"], ["07#not-held"],
        ["09#insurance", "09#liability"],
    ],
}
EDGES = [
    ("How is stored customer information protected?", ["02#data-at-rest"]),
    ("Can a departing colleague still sign into production the next day?", ["03#authorisation"]),
    ("How long do you keep consent records?", ["06#retention", "09#retention"]),
    ("Will you promise 99.99% uptime and pay compensation?", ["08#availability-commitment"]),
    ("What is your office cafeteria's weekly menu?", []),
    ("Do you manufacture rocket engines?", []),
]


def resolve(target, evidence):
    if target.startswith("AA-"):
        matches = [s.ref_id for s in evidence if s.ref_id == target]
    else:
        document, heading = target.split("#")
        matches = [s.ref_id for s in evidence if s.ref_id.startswith("KB:" + document + "-")
                   and s.ref_id.split("#", 1)[1].startswith(heading)]
        exact = [ref for ref in matches if ref.split("#", 1)[1] == heading]
        matches = exact or matches
    if len(matches) != 1:
        raise ValueError(f"Ambiguous/missing evaluation target: {target}: {matches}")
    return matches[0]


def terms(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP_WORDS]


class BM25:
    """Experimental Okapi BM25: k1=1.5, b=0.75, positive Robertson IDF."""
    def __init__(self, evidence):
        self.evidence = evidence
        self.counts = [Counter(terms(s.text + " " + s.citation)) for s in evidence]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / max(1, len(evidence)) or 1
        self.df = Counter(word for count in self.counts for word in count)

    def search(self, question, limit=8):
        scores = []
        for section, counts, length in zip(self.evidence, self.counts, self.lengths):
            score = 0
            for word in set(terms(question)):
                frequency = counts[word]
                if frequency:
                    idf = math.log(1 + (len(self.evidence) - self.df[word] + 0.5) / (self.df[word] + 0.5))
                    score += idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * length / self.average))
            if score > 0:
                scores.append((section, score))
        return [s for s, _ in sorted(scores, key=lambda item: (-item[1], item[0].ref_id))[:limit]]


def run(live=False):
    evidence = load_evidence(ROOT)
    bm25 = BM25(evidence)
    index = None
    cache = None
    if live:
        index = SemanticIndex(ROOT / "evidence_embeddings.sqlite3", GoogleEmbeddings())
        cache = index.sync(evidence)
    cases = []
    for filename, targets in TARGETS.items():
        questionnaire = parse_questionnaire((ROOT / "questionnaires" / filename).read_bytes(), filename)
        if len(targets) != len(questionnaire.rows):
            raise ValueError("Questionnaire changed; update labels before evaluating")
        cases.extend((filename, i + 1, row[questionnaire.question_column], target)
                     for i, (row, target) in enumerate(zip(questionnaire.rows, targets)))
    cases.extend(("edge-cases", i + 1, query, target) for i, (query, target) in enumerate(EDGES))
    records = []
    for filename, row, query, targets in cases:
        expected = {resolve(t, evidence) for t in targets}
        started = time.perf_counter()
        keyword = retrieve(query, evidence, limit=10)
        keyword_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        bm = bm25.search(query, limit=10)
        bm_ms = (time.perf_counter() - started) * 1000
        rankings = {"keyword": keyword[:8], "bm25_experiment": bm[:8]}
        timings = {"keyword": keyword_ms, "bm25_experiment": bm_ms}
        error = ""
        if index:
            try:
                started = time.perf_counter()
                hits = index.search(query, limit=10)
                semantic = [s for s, score in hits if score > 0]
                timings["semantic_with_api"] = (time.perf_counter() - started) * 1000
                rankings.update(semantic=semantic[:8], hybrid=fuse_rankings(keyword, semantic),
                                bm25_hybrid_experiment=fuse_rankings(bm, semantic))
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
        records.append({"file": filename, "row": row, "question": query,
                        "expected": sorted(expected), "rankings": {k: [s.ref_id for s in v] for k, v in rankings.items()},
                        "latency_ms": timings, "processing_error": error})
    summary = {}
    for name in sorted({name for r in records for name in r["rankings"]}):
        summary[name] = {}
        for group in [*TARGETS, "edge-cases"]:
            rows = [r for r in records if r["file"] == group]
            labelled = [r for r in rows if r["expected"]]
            summary[name][group] = {
                "target_recall_at_8": sum(len(set(r["expected"]) & set(r["rankings"].get(name, []))) / len(r["expected"]) for r in labelled) / len(labelled),
                "all_targets_found": sum(set(r["expected"]) <= set(r["rankings"].get(name, [])) for r in labelled),
                "labelled_rows": len(labelled),
                "missing_rankings": sum(name not in r["rankings"] for r in rows),
                "unsupported_rows_returning_candidates": sum(not r["expected"] and bool(r["rankings"].get(name)) for r in rows),
            }
    return {"live_google": live, "embedding_model": index.provider.model if index else None,
            "cache": cache, "note": "Target coverage only; designated labels are not exhaustive relevance judgements. No answer generation or precision claims.",
            "summary": summary, "rows": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Call Google for real semantic/hybrid comparison")
    args = parser.parse_args()
    result = run(args.live)
    output = ROOT / "verification" / ("retrieval_live.json" if args.live else "retrieval_offline.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Saved {output}")
