import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from semantic import GoogleEmbeddings, SemanticIndex, HybridRetriever, SemanticRetriever, build_engine, fuse_rankings, unit_vector
from workflow import EvidenceSection, GeminiProvider, WorkflowEngine, load_evidence, parse_questionnaire

ROOT = Path(__file__).parent


class FakeEmbeddings:
    model = "test-embedding-v1"

    def __init__(self):
        self.calls = []

    def embed(self, text, task):
        self.calls.append((text, task))
        return [1.0, 0.0] if "encrypt" in text else [0.0, 1.0]


def chunk(ref="one", text="We encrypt data."):
    return EvidenceSection(ref_id=ref, citation=ref, text=text,
                           source_file="test.md", heading=ref)


class SemanticTests(unittest.TestCase):
    def test_production_uses_semantic_without_keyword_ranking(self):
        index = SimpleNamespace(sync=lambda sections: None,
                                search=lambda q, limit: [(chunk("semantic"), 0.8)])
        with patch("semantic.GoogleEmbeddings"), patch("semantic.GeminiProvider"), patch("semantic.SemanticIndex", return_value=index):
            engine = build_engine(ROOT, [chunk()])
        self.assertIsInstance(engine.retriever, SemanticRetriever)
        with patch("semantic.retrieve", side_effect=AssertionError("Keyword search must not run")):
            self.assertEqual(engine.retriever("query", [chunk()])[0].ref_id, "semantic")

    def test_excerpt_validation_retrieval_boundary_and_revision(self):
        from workflow import DraftProposal, EvidenceUse, validate_draft
        source = chunk()
        draft = DraftProposal(status="Yes", answer="We encrypt data.", confidence="High",
                              evidence_uses=[EvidenceUse(ref_id="one", quote="We encrypt data.", supported_claim="We encrypt data.")])
        result = validate_draft("Encryption?", draft, {"one": source}, allowed_refs=["one"])
        self.assertFalse(result.validation_errors)
        self.assertEqual(result.source_snapshots["one"].content_hash, source.content_hash)
        for quote in ["", "   ", "Invented quote"]:
            bad = draft.model_copy(update={"evidence_uses": [EvidenceUse(ref_id="one", quote=quote)]})
            self.assertTrue(validate_draft("Encryption?", bad, {"one": source}).validation_errors)
        self.assertTrue(validate_draft("Encryption?", draft, {"one": source}, allowed_refs=[]).validation_errors)
        changed = source.model_copy(update={"text": source.text + " New policy."})
        self.assertTrue(validate_draft("Encryption?", draft, {"one": changed},
                                      source_hashes={"one": source.content_hash}).validation_errors)
        edited = draft.model_copy(update={"answer": "We retain records."})
        self.assertTrue(validate_draft("Encryption?", edited, {"one": source}).validation_errors)

    def test_compound_excerpts_persist_provenance_in_export(self):
        import io
        from openpyxl import load_workbook
        from workflow import DraftProposal, EvidenceUse, JobStore, validate_draft, export_review_xlsx
        first, second = chunk(), chunk("two", "We rotate keys every 90 days.")
        draft = DraftProposal(status="Yes", answer="We encrypt data. We rotate keys every 90 days.", confidence="High",
            evidence_uses=[EvidenceUse(ref_id=s.ref_id, quote=s.text, supported_claim=s.text) for s in [first, second]])
        result = validate_draft("Encryption and rotation?", draft, {s.ref_id:s for s in [first,second]}, allowed_refs=["one","two"])
        store = JobStore(Path(self.directory.name) / "review.sqlite3")
        job = store.create_job(parse_questionnaire(b"question\nEncryption and rotation?\n", "q.csv"))
        store.save_review(job, 0, result)
        changed = first.model_copy(update={"source_file":"renamed.md", "text":"Different revision"})
        workbook = load_workbook(io.BytesIO(export_review_xlsx(store, job, [changed,second])))
        rows = list(workbook.active.values)
        metadata = json.loads(rows[1][rows[0].index("evidence_metadata")])
        self.assertEqual(metadata[0]["source_file"], "test.md")
        self.assertEqual(metadata[0]["content_hash"], first.content_hash)
        self.assertTrue(metadata[0]["snapshot_recorded"])
        self.assertIn(second.text, rows[1][rows[0].index("evidence_excerpts")])
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=ROOT / "verification")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "cache.sqlite3"
        self.provider = FakeEmbeddings()
        self.index = SemanticIndex(self.path, self.provider)

    def test_revision_restart_metadata_and_deletion(self):
        first, second = chunk(), chunk("two", "We retain records.")
        self.assertEqual(self.index.sync([first, second])["generated"], 2)
        self.index = SemanticIndex(self.path, self.provider)
        self.assertEqual(self.index.sync([first, second])["reused"], 2)
        edited = first.model_copy(update={"text": "We encrypt with AES-256."})
        self.assertNotEqual(first.content_hash, edited.content_hash)
        self.assertEqual(self.index.sync([edited, second])["generated"], 1)
        renamed = edited.model_copy(update={"heading": "Encryption"})
        self.assertEqual(self.index.sync([renamed, second])["generated"], 1)
        metadata_only = renamed.model_copy(update={"owner": "Legal"})
        result = self.index.sync([metadata_only])
        self.assertEqual((result["reused"], result["removed"]), (1, 1))
        with closing(sqlite3.connect(self.path)) as db:
            metadata = json.loads(db.execute("SELECT metadata FROM evidence_embeddings").fetchone()[0])
        self.assertEqual(metadata["owner"], "Legal")

    def test_model_and_chunking_invalidate_cache(self):
        self.index.sync([chunk()])
        self.provider.model = "test-embedding-v2"
        self.assertEqual(self.index.sync([chunk()])["generated"], 1)
        with patch("semantic.CHUNKING_VERSION", "v2"):
            self.assertEqual(self.index.sync([chunk()])["generated"], 1)

    def test_failed_revision_preserves_previous_snapshot(self):
        self.index.sync([chunk()])
        with patch.object(self.provider, "embed", side_effect=RuntimeError("timeout")):
            with self.assertRaises(RuntimeError):
                self.index.sync([chunk(text="Changed")])
        self.assertEqual(self.index.sections[0].text, "We encrypt data.")
        self.assertEqual(self.index.sync([chunk()])["reused"], 1)

    def test_query_ranking_and_validation(self):
        self.index.sync([chunk("retention", "We retain records."), chunk()])
        hits = self.index.search("encrypt information", 1)
        self.assertEqual(hits[0][0].ref_id, "one")
        self.assertEqual(hits[0][1], 1.0)
        self.assertEqual(self.provider.calls[-1][1], "RETRIEVAL_QUERY")
        with self.assertRaises(ValueError):
            self.index.search(" ")
        with patch.object(self.provider, "embed", return_value=[1, 2, 3]):
            with self.assertRaises(ValueError):
                self.index.search("question")
        for invalid in ([], [0, 0], [float("nan")], [float("inf")]):
            with self.assertRaises(ValueError):
                unit_vector(invalid)

    def test_duplicate_ids_and_empty_corpus(self):
        with self.assertRaises(ValueError):
            self.index.sync([chunk(), chunk()])
        self.index.sync([chunk()])
        self.assertEqual(self.index.sync([])["removed"], 1)
        self.assertEqual(self.index.search("question"), [])

    def test_supplied_pack_and_questionnaires_offline(self):
        evidence = load_evidence(ROOT)
        self.assertEqual(len(evidence), 109)
        self.assertEqual(len({s.ref_id for s in evidence}), len(evidence))
        for section in evidence:
            self.assertTrue((ROOT / section.source_file).is_file())
            self.assertTrue(section.heading)
            self.assertEqual(len(section.content_hash), 64)
        self.assertEqual(self.index.sync(evidence)["generated"], 109)
        self.assertEqual(self.index.sync(evidence)["reused"], 109)
        count = 0
        for path in sorted((ROOT / "questionnaires").glob("*.csv")):
            questionnaire = parse_questionnaire(path.read_bytes(), path.name)
            for row in questionnaire.rows:
                hits = self.index.search(row[questionnaire.question_column])
                self.assertEqual(len(hits), 8)
                count += 1
        self.assertEqual(count, 75)

    def test_google_adapter_request_and_empty_response(self):
        from google.genai import types
        provider = GoogleEmbeddings.__new__(GoogleEmbeddings)
        provider.model, provider.types = "test-model", types
        with patch("google.genai.Client") as client:
            provider.client = client.return_value
            call = provider.client.models.embed_content
            call.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[3, 4])])
            self.assertEqual(provider.embed("text", "RETRIEVAL_DOCUMENT"), [0.6, 0.8])
            self.assertEqual(call.call_args.kwargs["config"].task_type, "RETRIEVAL_DOCUMENT")
            call.return_value = SimpleNamespace(embeddings=[])
            with self.assertRaises(ValueError):
                provider.embed("text", "RETRIEVAL_QUERY")

    def test_fusion_deduplication_and_deterministic_ties(self):
        a, b, c = chunk("a"), chunk("b"), chunk("c")
        fused = fuse_rankings([a, b], [c, b])
        self.assertEqual([s.ref_id for s in fused], ["b", "a", "c"])
        self.assertEqual(fuse_rankings([a, a], [b], limit=1)[0].ref_id, "a")
        self.assertEqual(fuse_rankings([], []), [])

    def test_embedding_failure_is_retryable_processing_error(self):
        self.index.sync([chunk()])
        provider = SimpleNamespace(draft=lambda *args: self.fail("Must not draft on retrieval failure"))
        engine = WorkflowEngine([chunk()], provider, HybridRetriever(self.index))
        with patch.object(self.provider, "embed", side_effect=RuntimeError("embedding unavailable")):
            result = engine.process("encrypt")
        self.assertIn("embedding unavailable", result.processing_error)
        self.assertEqual(result.owner, "Security")

    def test_conflict_guard_survives_changed_rankings(self):
        evidence = load_evidence(ROOT)
        engine = WorkflowEngine(evidence, None, lambda *args: [])
        result = engine.process("How long are consent records retained?")
        self.assertEqual(result.status, "Cannot answer")
        self.assertEqual(result.owner, "Legal")
        self.assertFalse(result.processing_error)
        self.assertIn("36 months", result.reviewer_note)

    def test_generation_model_required_before_client(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test", "GEMINI_MODEL": ""}):
            with patch("workflow.resolve_model", return_value=None), patch("google.genai.Client") as client:
                with self.assertRaisesRegex(RuntimeError, "GEMINI_MODEL"):
                    GeminiProvider()
                client.assert_not_called()

    def test_hybrid_q1_review_export_offline(self):
        from workflow import JobStore, export_csv, export_review_xlsx
        from verify import Q1FixtureProvider
        evidence = load_evidence(ROOT)
        self.index.sync(evidence)
        # Feed lexical rankings as a controlled semantic ranking. This is an
        # integration fixture, not an evaluation of embedding relevance.
        from workflow import retrieve
        self.index.search = lambda q, limit=8: [(s, 1.0) for s in retrieve(q, evidence, limit)]
        engine = WorkflowEngine(evidence, Q1FixtureProvider(), HybridRetriever(self.index))
        store = JobStore(Path(self.directory.name) / "jobs.sqlite3")
        path = ROOT / "questionnaires" / "questionnaire-1-standard.csv"
        job = store.create_job(parse_questionnaire(path.read_bytes(), path.name))
        store.process_job(job, engine)
        rows = store.rows(job)
        self.assertEqual(len(rows), 25)
        self.assertFalse([r for r in rows if r["result"].processing_error])
        store.save_review(job, 4, rows[4]["result"], accept=True)
        self.assertEqual(store.rows(job)[4]["review_state"], "Accepted")
        self.assertIn(b"Q25", export_csv(store, job, evidence))
        self.assertTrue(export_review_xlsx(store, job, evidence).startswith(b"PK"))

    def test_bm25_rare_terms_and_empty_query(self):
        from evaluate_retrieval import BM25
        search = BM25([chunk("a", "general policy security"), chunk("b", "FedRAMP status")])
        self.assertEqual(search.search("FedRAMP")[0].ref_id, "b")
        self.assertEqual(search.search(""), [])

    def test_partial_index_resumes_without_repeating_completed_requests(self):
        sections = [chunk("one"), chunk("two", "retain")]
        with patch.object(self.provider, "embed", side_effect=[[1, 0], RuntimeError("quota")]):
            with self.assertRaisesRegex(RuntimeError, "quota"):
                self.index.sync(sections)
        restarted = SemanticIndex(self.path, self.provider)
        self.provider.calls.clear()
        result = restarted.sync(sections)
        self.assertEqual((result["generated"], result["reused"]), (1, 1))
        self.assertEqual(len(self.provider.calls), 1)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM embedding_checkpoints").fetchone()[0], 0)

    def test_rate_limit_pacing_retry_delay_and_bounds(self):
        from google.genai import types
        from google.genai.errors import ClientError
        provider = GoogleEmbeddings.__new__(GoogleEmbeddings)
        provider.model, provider.types = "test", types
        limited = ClientError(429, {"error": {"code": 429, "message": "quota", "details": [
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "7s"}]}})
        with patch("google.genai.Client") as client, patch("semantic.time.sleep") as sleep, patch("semantic.time.monotonic", return_value=100):
            provider.client = client.return_value
            request = provider.client.models.embed_content
            request.side_effect = [limited, SimpleNamespace(embeddings=[SimpleNamespace(values=[1, 0])])]
            self.assertEqual(provider.embed("query", "RETRIEVAL_QUERY"), [1, 0])
            sleep.assert_any_call(8.0)
            sleep.assert_any_call(1.0)
            self.assertEqual(request.call_count, 2)
            request.reset_mock()
            request.side_effect = limited
            with self.assertRaises(ClientError):
                provider.embed("query", "RETRIEVAL_QUERY")
            self.assertEqual(request.call_count, 3)
            request.reset_mock()
            request.side_effect = ClientError(400, {"error": {"code": 400, "message": "invalid"}})
            with self.assertRaises(ClientError):
                provider.embed("query", "RETRIEVAL_QUERY")
            self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
