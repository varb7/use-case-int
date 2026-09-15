# Consolidated verification report

Status: 2026-09-15. This is the current verification entry point. Older phase reports in the working directory are historical, not cumulative pass counts. Current implementation: semantic-only Google RAG, excerpt provenance, review/routing and three commitment guards.

## Evidence and actual results

| Evidence | Actual result | What it establishes |
|---|---|---|
| Latest development regression run | 94 passed, 0 failures/errors, 21.098 seconds | 23 commitment tests + 18 semantic tests + 53 detailed tests; no live Google calls |
| Supplied input layouts | Q1 25, Q2 30, Q3 20 rows parsed | Original CSV schemas/order preserved; three question-column names supported |
| Q1 deterministic fixture | 25 processed/exported; 18 Yes, 3 No, 1 Partial, 3 Cannot answer | Upload/review/persistence/CSV/XLSX mechanics; not live answer quality |
| Commitment question gate | Q1 0/25, Q2 5/30, Q3 0/20 pre-routed | Q2 data rows 3, 6, 20, 22, 23 route Legal; other rows may still need model/human routing |
| Historical real Google embedding evaluation | 81 cases, no recorded processing errors; `gemini-embedding-001` | Retrieval target coverage only, not generated answers |
| Previous clean candidate environment | Windows 11, CPython 3.13.1; 91 passed, 0 failures/errors in 22.028 seconds; pip check and Q1 fixture passed | Predates Credential Manager support; retained only as packaging history |
| Final submission validation | Exact final archive result recorded in adjacent `*.validation.json` | Separate final extraction/install/test, identified by archive SHA-256 |

Development test detail: [named test log](commitment-tests.txt), [machine-readable results and all 75 question decisions](commitment-results.json), [guardrail plan and edge cases](commitment-guardrails.md). The package-validation sidecar is separate so it can record the tested archive's SHA-256 without a self-referential hash. Only a sidecar with `passed: true` is a successful clean-package run. Fresh-venv results may have different timings from the development run above.

## Real retrieval evaluation (historical, not rerun for packaging)

| Group | Semantic mean target coverage@8 | All designated targets found | Unsupported rows returning candidates |
|---|---:|---:|---:|
| Q1 | 100% | 24/24 labelled rows | 1 |
| Q2 | 96.67% | 29/30 | 0 |
| Q3 | 98.33% | 19/20 | 0 |
| Extra cases | 100% | 4/4 | 2 |

Source: [retrieval_live.json](retrieval_live.json), a prior user-run real embedding evaluation. There are 75 supplied questions plus six extra cases; unsupported cases are not included in labelled coverage denominators. Coverage averages the fraction of designated source IDs found in the top eight, not correct answers. Labels are not exhaustive relevance judgments. Missing targets included the designated HIPAA/PHI section for Q2 row 3 and certification section for Q3 row 1.

Semantic-only exceeded both tested hybrid variants on Q2/Q3 target coverage; BM25 did not establish an improvement over keyword hybrid. That supports the current ranking choice, not a claim of lower cost or better generated answers. The three unsupported cases returning semantic candidates demonstrate that retrieval alone is not an answerability gate. Offline comparison remains available in [retrieval_offline.json](retrieval_offline.json).

## Requirement coverage and remaining gaps

| Requirement | Implemented/tested | Limit |
|---|---|---|
| Upload and original CSV layout | UTF-8, size/header/row validation, mapping, original column/row order | CSV only; invalid input stops before generation |
| Required output | Exactly six appended prospect fields; valid statuses; 1–4 sentences and plural voice; owner/evidence rules | Sentence/voice checks are heuristics; no independent language-quality scoring |
| Evidence-backed draft | Retrieved-reference boundary, exact quote checks, claim-text presence, source snapshots/hashes | Exact matches do not prove entailment or coverage of every claim |
| Source conflicts/freshness | Known 12/36-month consent-retention guard; stale-source notes/confidence ceiling | Conflict guard is pack-specific, not an exhaustive compound-question detector |
| Commitment control | Pre-question rules, pinned authority, post-draft/review/export checks | Bounded English rules can miss paraphrases and overblock legitimate future-tense facts |
| Owner routing/review | Local assignment, reasons, filters, accept/edit behavior; legacy-output checks | No notification, authenticated approver or actual contract approval |
| Failures and retry | Per-row processing errors, bounded retries/pacing, checkpointed embeddings | Project-wide quotas and model availability remain external; no multi-process limiter |
| Exports | Whole-job CSV/XLSX, internal metadata, spreadsheet formula escaping | Partial/unreviewed jobs can export; human send approval required |
| Separation/provider | Engine independent of Streamlit; one Google provider | Single-user local prototype, not hosted production |
| First-run setup | Masked settings form; save/load/remove; environment precedence; model metadata test | Windows-only credential target; connection test still depends on Google availability |

## Windows Credential Manager verification

`secure_settings.py` is the only saved-credential boundary used by both generation and embedding adapters. The UI never prepopulates its password field. Three focused tests verify save/load/remove behavior with a fake keyring, environment-variable precedence, and that connection testing passes the secret to the Google client without returning it. The full suite passed without writing a real credential. Read-only backend inspection on the development machine returned `keyring.backends.Windows.WinVaultKeyring`. The clean-package validator separately asserts the same backend class after the locked install.

No live Google connection test was run because the agent process has no key. Windows Credential Manager encryption does not prevent another process running under the same Windows account from requesting the credential; this is safer at-rest storage than `.env`, not an application authentication boundary.

## Why an answer is not generated or is withheld

1. **Run does not start:** malformed/oversized/non-UTF-8 CSV, blank questions, bad headers; absent key/model; initial corpus indexing failure. Correct input/configuration or resolve the service error. Engine startup can still index before per-question commitment checks.
2. **Intentional business routing:** recognized new commitment; known retention conflict; no relevant candidates; model reports insufficient evidence. `Cannot answer` is not an API failure. Legal/Sales/Security/Product must supply evidence or resolve the request.
3. **Processing failure:** timeout, exhausted retries, invalid/empty JSON, unavailable model, quota/network/service error. The UI keeps the failure visible and supports retry. Mock tests cover adapter behavior; no new live quota/load test was performed.
4. **Validation blocks text:** unknown/nonretrieved source, nonexact/empty quote, changed source revision, lost mapped claim, unsupported recognized promise, missing evidence/owner or format violation. Correct/regenerate and re-review. A matching citation alone does not authorize a commitment.

Tested edge cases include source replacement/removal, stale/missing/future source dates, forged authority metadata, mixed commitment questions, Legal-vs-Sales precedence, negated and affirmative promise clauses, all five statuses, legacy accepted answers, failures distinct from routing, partial exports and spreadsheet formulas. See the named tests rather than treating each parameterized input as a separate test count.

## Packaging and reproducibility

Python 3.13/Windows x64 is the lock target. `requirements.txt` records four direct pins; `requirements-lock.txt` additionally pins transitive packages and hashes. uv generated the lock; pip installs it without uv. See [Astral's lockfile documentation](https://docs.astral.sh/uv/pip/compile/). Docker was not added. A Python venv isolates dependencies, not the operating system; a fresh venv on this host is not a separate clean VM.

The builder uses an explicit file allowlist, rejects symlink escapes and common credential formats, checks ZIP integrity, and records SHA-256 per file. It excludes saved job/vector databases, credentials, `.env`, virtual environments, bytecode, logs unrelated to verification, temporary directories and old phase reports. Original user state and historical reports remain untouched in the working directory. This is a scoped hygiene check, not an exhaustive secret-scanner certification.

## Limitations and submission honesty

No new live Gemini drafting, production cost/latency measurement, calibrated hallucination scoring, exhaustive prompt-injection/commitment robustness, visual browser inspection or cross-platform install test is claimed. Streamlit's automated harness tests interaction paths but not pixel-level layout. Saved Q1 sample exports are clearly named fixtures. No production security review or cumulative four-hour-budget compliance claim is made. Docker/MCP and other deferred features were not implemented.
