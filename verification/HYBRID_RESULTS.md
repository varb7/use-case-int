# Hybrid retrieval implementation and evaluation

> Historical evaluation report. Production is now semantic-only. Current status: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

Date: 2026-09-15.

## Completed live run — supersedes pending status below

Inspected the user's `retrieval_live.json`: model `gemini-embedding-001`, 81 cases, zero recorded processing errors. No new API requests were made during this inspection.

| Method | Q1 coverage@8 | Q2 coverage@8 | Q3 coverage@8 | Supported extra cases |
|---|---:|---:|---:|---:|
| Semantic | 100% | 96.67% | 98.33% | 100% |
| Keyword + semantic | 100% | 95.00% | 94.83% | 100% |
| BM25 + semantic | 100% | 95.00% | 94.83% | 100% |

Semantic found every designated source for 24/24 labelled Q1 rows, 29/30 Q2 rows and 19/20 Q3 rows. Each hybrid did so for 24/24, 28/30 and 17/20 respectively. These are evidence-target metrics, not correct-answer counts.

Row inspection explains the difference: hybrid ranking loses the hosting-regions section for Q2 row 26, authorisation/offboarding for Q3 row 2, and change-management for Q3 row 10. Semantic retrieves those sources. All three miss the designated not-held/PHI section for Q2 row 3 (HIPAA/BAA) and the designated certification table for Q3 row 1. Other returned evidence could partially cover those topics; missing a designated target does not itself prove an incorrect answer.

Decision: retain BM25 as an experiment; it has not demonstrated an improvement over keyword hybrid. Semantic-only ranking is the leading candidate based on this run. The app's hybrid default was not modified in this reporting step. All three semantic-based methods return candidates for the unsupported Q1 row and both unsupported extra cases, so answerability and unsupported-claim behavior need generated-answer review before claiming end-to-end improvement.

Earlier sections preserve the offline implementation/testing history. References there to pending live evaluation describe the state before this completed user run.

## Actual test results

`python -m unittest test_semantic test_detailed -q`: **60 tests passed in 7.288 seconds** (13 semantic/hybrid tests and 47 existing workflow tests). Executed outside the Windows sandbox with approval because temporary SQLite directory access is restricted inside it.

Checks include revision caching, vector validation, reciprocal-rank fusion and deduplication, embedding failures preserved as processing errors, conflict detection independent of rankings, generation-model configuration, Q1 processing/review/export and Streamlit upload-to-export with controlled retrieval and drafting fixtures. The former generation-default assertion now tests the configured model; missing configuration raises an actionable error before a client is created. The UI fixture was updated to mock the new embedding boundary, so tests cannot send real data or write a production embedding cache.

These tests are offline. Controlled embeddings/rankings establish mechanics, not semantic relevance or live answer quality.

## Actual lexical evaluation

Executed `python evaluate_retrieval.py`. Detailed results are in `retrieval_offline.json`, including the question, designated targets, top-eight references and timings for every row.

| Supplied questionnaire | Keyword target coverage@8 | Experimental BM25 | All targets found: keyword / BM25 |
|---|---:|---:|---:|
| Q1 (24 labelled rows; 1 unsupported) | 95.83% | 93.75% | 23/24 / 22/24 |
| Q2 (30 labelled rows) | 93.33% | 95.00% | 28/30 / 28/30 |
| Q3 (20 labelled rows) | 84.83% | 86.50% | 13/20 / 13/20 |
| Extra cases (4 labelled; 2 unsupported) | 25.00% | 25.00% | 1/4 / 1/4 |

Coverage is the mean fraction of designated source IDs retrieved per labelled question. Labels were selected from reading the supplied KB before measuring scores. They are not exhaustive relevance judgments: a valid approved answer may be returned instead of a designated KB section. Some targets document an evidence gap or an owner-routing restriction, rather than support a substantive answer. These metrics cannot be called answer accuracy or precision. No LLM judge or generated-answer evaluation was used.

Observed gaps:

- Q1 row 16: both methods omit the designated stored-data section; alternative evidence may still be present.
- Q1 row 24: BM25 omits the designated current-subprocessor list, a regression versus keyword scoring.
- Q2 row 3: neither retrieves the designated framework/PHI evidence. That evidence does not establish agreement to sign a BAA.
- Q2 row 26: keyword misses designated backup and hosting sections; BM25 retrieves the backup section but misses hosting.
- Q3 row 4: keyword misses both conflicting retention sections; BM25 retrieves one. The engine's existing narrow consent-conflict trigger is not a general compound-question conflict detector; this narrative wording still requires model/human assessment.
- Both lexical methods miss the chosen evidence for the stored-information and departing-colleague paraphrases and the compensation request.
- The unsupported Q1 legal-entity question and one of the two unsupported extra cases still return candidates. Nonempty retrieval is not proof that an answer exists.

## Live evaluation and adoption decision

Hybrid retrieval is implemented and wired into generation/retry, but live semantic comparison remains pending. The Google key is configured in the user's separate PowerShell session; it is absent from the agent process and Windows persistent variables. No live embeddings or draft answers were generated here.

Run `python evaluate_retrieval.py --live` in that configured terminal. It evaluates all 81 cases, reuses one real semantic result for both hybrid variants, and saves `retrieval_live.json`. API failures are recorded per question; initial indexing failures stop the command. Inspect errors before interpreting metrics. Query embedding latency includes the API request; lexical latency is local CPU work.

**BM25 has not been adopted in the app.** Offline results are mixed and include a Q1 regression. A decision between the two hybrid variants needs the live comparison and review of regressions, particularly conflict sources and compound questions. No semantic quality, cost savings, calibrated threshold, or full Q2/Q3 answer-quality claim is made.

The original four-hour cumulative task budget is not reconstructable from the available historical records; no total-budget compliance claim is made.
