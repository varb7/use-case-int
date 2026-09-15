# Semantic retrieval step 1 — actual results

> Historical phase report. The old model-default test failure was subsequently fixed; production is now semantic-only. Current status: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

Date: 2026-09-15. Environment: Windows, Python 3.13, installed project dependencies.

## Implemented

`semantic.py` provides Google embeddings, a separate persistent SQLite cache, revision invalidation and command-line cosine search. Evidence retains its citation IDs and gains source filename, heading and a computed content hash. Design and runbook document the staged rollout. Streamlit drafting still uses keyword retrieval; hybrid ranking and BM25 are not implemented in this step.

## Executed checks

| Command/check | Actual result |
|---|---|
| `python -m unittest test_semantic -v` | 7 tests passed in 7.126 seconds |
| Supplied evidence metadata | 109 sections; unique IDs, existing source paths, populated headings and 64-character hashes |
| Offline indexing | 109 fake document embeddings on first sync; all 109 reused on second sync |
| Questionnaire search wiring | All 75 supplied question rows processed with fake embeddings and eight valid candidate records per row |
| Revision tests | Changed text/heading re-embedded; unchanged vectors reused across index reconstruction; owner-only edit refreshed metadata; deleted IDs pruned |
| Cache configuration tests | Model and chunking-version changes invalidated vectors |
| Failure tests | Provider failure preserved previous persisted and in-memory snapshot; duplicate IDs, empty query, invalid vectors and dimension mismatch rejected; empty corpus supported |
| Google adapter mock | Verified document task configuration, vector normalization and rejection of missing response embeddings |
| `python -m unittest test_detailed -q` | 46 passed, 1 failed; 47 tests in 12.633 seconds |

The existing failure is `ProviderAndEngineTests.test_google_api_key_alias_is_accepted_without_printing_key`: line 247 expects `gemini-2.5-flash`, but the inspected current drafting adapter sets `model or os.getenv("GEMINI_MODEL")`, which is `None` in this session. That generation-model logic was already present before this change and was not modified. The runbook now accurately instructs users to set `GEMINI_MODEL`.

Initial sandbox runs encountered Windows access-denied errors opening/cleaning temporary directories. Both suites were rerun outside the sandbox with tool approval; the results above are from those reruns. Test SQLite connections are explicitly closed. No saved production review database was used by the new semantic tests.

## Limits and next step

Neither `GEMINI_API_KEY` nor `GOOGLE_API_KEY` was configured in the execution environment. No live Google embeddings were requested and no production embedding cache was built. Fake embeddings verify mechanics only: eight returned hits do not demonstrate relevant retrieval. API availability, real vector dimensions, semantic quality, latency and billing were not measured.

Run `python semantic.py --query "How is stored customer information protected?"` in a shell with a configured Google key to build the real cache and inspect source references. This reads environment variables, not a `.env` file.

Step 2 is combining semantic and keyword rankings; step 3 is labelled evaluation on supplied questions and edge cases. No BM25 adoption decision is justified by these offline tests. A relevance threshold is intentionally unset for the diagnostic command and must be evaluated before treating semantic hits as sufficient evidence.

The original four-hour total budget cannot be reconstructed from the available historical timing. This report does not assert compliance with that cumulative budget.
