# Detailed application test results

> Historical phase report. Current status, failure behavior and test counts: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

Run date: 2026-09-14

## Executive result

- Automated checks after the Gemini owner-schema fix: **47 passed, 0 failed, 0 errors, 0 skipped** in 7.091 seconds.
- Q1 workflow: completed through Streamlit upload, preview, mocked Gemini drafting, validation, SQLite persistence, review, CSV export, and Excel export.
- Supplied layouts: Q1 25/25, Q2 30/30, and Q3 20/20 rows parsed with their expected question columns.
- Knowledge pack: 109 evidence sections loaded, including all 42 approved answers.
- Local Streamlit server: started successfully on port 8501 and stopped cleanly.
- Live Gemini: **not tested**, because neither `GEMINI_API_KEY` nor `GOOGLE_API_KEY` was visible to the test process.
- Visual browser QA: **not performed**, because no in-app browser was attached. Five Streamlit application-harness tests passed instead.

The raw named-test output is saved in `verification/DETAILED_TEST_OUTPUT.txt`.

## Coverage

| Area | Checks | Result |
|---|---:|---|
| CSV parsing and input validation | 12 | Passed |
| Evidence loading, retrieval, conflicts, routing | 7 | Passed |
| Gemini adapter and engine failures | 6 | Passed offline |
| SQLite, retry, review, CSV/Excel exports | 7 | Passed |
| Streamlit startup and interaction paths | 5 | Passed with native harness |
| Draft and citation validation | 10 | Passed |
| **Total** | **47** | **Passed** |

## Actual supplied-pack retrieval results

Lexical retrieval produced at least one candidate for every supplied row:

| Questionnaire | Rows | Zero-candidate rows | Weak top score (<=2) |
|---|---:|---:|---:|
| Q1 standard | 25 | 0 | 2 |
| Q2 enterprise | 30 | 0 | 8 |
| Q3 narrative | 20 | 0 | 0 |

A nonzero candidate count does not prove relevant evidence. The weak Q1 rows were the legal-entity/address request and RTO/RPO. Weak Q2 rows included C5, HIPAA/BAA, FedRAMP, TISAX, on-premise deployment, SSO, on-site audit rights, and backup location/retention.

## When the application does not generate an answer

There are three different outcomes. They should not be confused.

### 1. The questionnaire run does not start

| Reason | Current behavior | Recovery |
|---|---|---|
| `GEMINI_API_KEY` and `GOOGLE_API_KEY` are both absent | Generate button displays an error; no job is created and no data is sent | Set one key in the same shell that launches Streamlit |
| File exceeds 5 MB | Upload is rejected | Reduce/split the CSV |
| File is not UTF-8 | Upload is rejected | Save as UTF-8 CSV |
| Empty file or missing/duplicate headers | Upload is rejected | Correct the header row |
| Blank question row | Upload is rejected | Populate or remove the row |
| Extra fields or malformed CSV quoting | Upload is rejected | Correct CSV structure |
| No recognized question-column name | Upload is rejected before generation | Rename to `question`, `requirement`, or `requirement_text` |

### 2. A row intentionally becomes `Cannot answer` without calling Gemini

| Reason | Current behavior | Recovery |
|---|---|---|
| No lexical token overlap with any evidence section | `Cannot answer`; deterministic owner routing; no provider call | Add relevant approved evidence or improve retrieval |
| Word-form mismatch, such as `encryption` versus `encrypt` in a minimal corpus | Same no-evidence path | Add stemming/synonyms only if measured failures justify it |
| Consent-retention question finds the known 12-month/36-month conflict | `Cannot answer`, routed to Legal, conflict shown | Legal must establish the authoritative retention value |

This is not a processing failure. It is the safe business result when usable evidence is unavailable or conflicting.

### 3. Gemini is called but the row becomes a processing failure

The engine records a `processing_error`, keeps the row visible, and allows retry. It does not present the failure as a factual business answer.

Tested failure causes:

- Provider timeout or exception.
- Empty model response.
- Invalid JSON or output that does not match the Pydantic schema.

Expected but not live-tested causes:

- Invalid, expired, or restricted API key.
- Configured model unavailable to the Google project.
- Quota exhaustion or rate limiting.
- Network, DNS, TLS, proxy, or firewall failure.
- Google service failure after the configured three total attempts.

### 4. Gemini returns text, but validation blocks the proposed answer

The proposed content is replaced with a safe `Cannot answer`, assigned to an owner, and marked with validation errors when any of these occur:

- Unknown evidence ID.
- Quoted excerpt is not an exact substring of the source.
- Yes, No, Partial, or Not applicable has no evidence.
- Cannot answer has no owner.
- Answer is not written in first-person plural.
- Answer contains zero or more than four sentences.
- Status or another structured field is outside its allowed schema.

Stale evidence does not suppress the answer by itself. Evidence older than 12 months downgrades High confidence to Medium and adds a reviewer note.

## Findings and limitations

### F-01 — Manual column mapping is unreachable for unknown layouts (Medium)

The engine supports an explicit custom question column, but `app.py` first calls `parse_questionnaire` without a mapping. An unknown layout is therefore rejected before the dropdown can be displayed. The documented workaround is to rename the question column to one of the three recognized names. This was observed and preserved as a passing characterization test; it was not fixed because this task requested testing rather than feature modification.

### F-02 — Lexical retrieval can miss synonyms or return weak false positives (Medium)

Retrieval uses exact lower-case tokens with no stemming, synonyms, embeddings, or minimum relevance threshold. A morphology test demonstrated that `encryption` can miss a section containing only `encrypt`. Conversely, every supplied row returned something, but ten rows had a weak top score. Human evidence review remains necessary.

### F-03 — “Most recent” freshness is not deterministically blocked (Medium)

Stale evidence is downgraded and flagged, but the validator does not automatically reject every “most recent” answer based on stale evidence. The Q1 deterministic fixture safely routes the penetration-test-date question to Security; live-model behavior still needs evaluation.

### F-04 — Live Gemini behavior remains unverified (Medium)

The adapter request/response contract, missing-key behavior, key alias, empty output, invalid JSON, and provider exceptions passed offline. Actual authentication, model entitlement, quota, latency, retries, cost, and semantic quality require a real key in the test process.

### F-05 — Visual browser inspection unavailable (Low)

No browser backend was attached. Streamlit's native harness verified startup, invalid upload feedback, valid Q1 preview, missing-key gating, and a complete mocked Q1 run through the review and export controls.

### F-06 — Sandbox-only Streamlit cleanup warning (Low/environmental)

After successful harness runs, Streamlit attempted to change permissions on its temporary directory and Windows returned `Access denied`. This occurred after all tests completed and did not change the 47/47 result. It has not been observed as an application runtime failure.

## Resolved Gemini schema error

The live API previously rejected `owner` because its enum contained an empty string. `owner` now uses `null` for the unassigned state, while CSV and Excel exports still write a blank cell. The generated schema was inspected directly and a permanent regression test confirms that no enum contains `""`.

## Defects corrected during testing

- SQLite retry coverage was corrected to exercise a genuinely retrieved question; this also revealed and documented the morphology limitation.
- Streamlit's removed `use_container_width` argument was replaced with `width="stretch"`.
- Deprecated openpyxl alignment copying was replaced with a supported `Alignment` assignment.
- UI tests now isolate their SQLite database and preserve required system environment settings.

## Reproduce

```powershell
cd C:\path\to\data-pack-ai-enablement-engineer
python test_detailed.py
python verify.py
```

For live Gemini coverage, set `GEMINI_API_KEY` in that PowerShell session before launching Streamlit. Do not put the key in test output or source control.
