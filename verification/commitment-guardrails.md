# Commitment guardrails: implementation and verification

## Stepwise plan and completion

1. Define deterministic new-commitment patterns and factual counterexamples — implemented in `commitments.py`, with Unicode/whitespace normalization and explicit Legal/Sales precedence.
2. Apply the question gate before per-question retrieval/generation — implemented in `WorkflowEngine`; a mixed factual/commitment question routes as a whole.
3. Attach application-owned authority metadata — implemented as an `EvidenceSection` computed field; never taken from model output. The registry is pinned to reviewed section content hashes.
4. Validate generated answers, reviewer edits and saved-result output — shared policy checks in validation, review save, and a common in-memory projection for UI/CSV/XLSX. Saved jobs are not migrated or silently rewritten.
5. Test supplied questionnaires, counterexamples, source revisions and workflow boundaries; preserve reports — implemented in `test_commitments.py`, alongside the existing semantic and detailed suites.

## What each guard does

| Guard | Decision | Result |
|---|---|---|
| C1: question | Recognized request to accept/sign/guarantee/commit, or nonstandard on-site audit rights | Cannot answer; Legal or Sales; no per-row retrieval/model call |
| Source authority | Registered ref + exact section hash; all others default factual-only | Two existing-standard-term sections; three negotiation-only sections; no blanket authority |
| C3: draft | Recognized affirmative promise without an exact authorized standard statement and supporting current excerpt | Safe Cannot answer; owner and validation reason; acceptance blocked |

Registered standard terms: the supplied standard liability cap and Enterprise audit rights. Their only exempted output sentences preserve the original scope and qualifiers. Registered negotiation-only material: availability/SLA discussion, DPA modifications, and insurance. Other sections remain usable as factual evidence. These classifications are derived from the supplied documents, not independent Legal approval.

## Supplied questionnaire results

The report records all 75 original questions and their pre-guard decisions. Row numbers below are one-based data rows, excluding headers.

| Questionnaire | Rows inspected | C1 routed | Interpretation |
|---|---:|---:|---|
| Standard | 25 | 0 | Existing-policy questions continue; existing retention conflict guard remains separate |
| Enterprise | 30 | 5 | Rows 3, 6, 20, 22, 23 route to Legal |
| Narrative | 20 | 0 | Factual descriptions/positions continue; this is not proof that generated drafts cannot contain promises |

Enterprise examples: HIPAA plus signing a BAA; 99.99% SLA with credits; unlimited liability; accepting the customer's DPA; on-site audit rights. The standard questionnaire's “Within what timeframe will you notify us…” is intentionally not classified as a new commitment.

The complete 25-row Q1 fixture workflow also runs without processing or validation errors attributable to the new guards. It uses deterministic test responses, not live Gemini. Existing tests exercise parsing, persistence, review, exports, semantic retrieval adapters, retries/pacing and the Streamlit test harness.

## Edge cases covered

- Mixed factual plus new-commitment question routes the whole row.
- Case, whitespace and full-width Unicode variants normalize consistently.
- Price-only commitments route Sales; liability/DPA/BAA overrides that to Legal.
- “Please provide your SOC 2 report” and factual policy/target questions are not preblocked.
- Negative statements do not automatically count as affirmative promises; a subsequent affirmative clause still triggers.
- Yes/No/Partial/Not applicable/Cannot answer cannot hide a promise in the answer text.
- Negotiation-only material cannot authorize an SLA promise even with a genuine exact quote.
- Forged authority metadata is ignored; changed section text loses registered authority.
- Stale, missing, future-dated, undated or wrong-excerpt standard evidence cannot authorize an exemption.
- Modified numbers, removed qualifiers or an extra promise do not inherit a standard statement's exemption.
- A valid standard-term exception still requires normal retrieved-reference and citation checks.
- Direct review saves and legacy accepted records cannot bypass commitment checks; CSV and workbook output are safe and newly changed results need review.
- Accepted safe routing decisions remain accepted; processing failures are not relabelled as successful business routing.

## Reproduction and actual-run artifacts

Guardrail milestone run on 2026-09-15: **91 tests passed, 0 failures, 0 errors, 18.534 seconds** — 23 new guardrail tests plus 68 then-existing tests. Later consolidated runs include additional credential-setting tests; see `VERIFICATION_REPORT.md`. Parameterized subcases cover multiple questions/answer variants within those test methods.

From the project directory, with existing requirements installed, run `python test_commitments.py`. It runs all three unittest modules and writes `commitment-tests.txt` and `commitment-results.json` here. These files contain actual counts, duration, failure details and questionnaire-level decisions; the script exits nonzero if any test fails. There are no live Google calls in this test run.

The first sandboxed regression attempt encountered Windows temporary-directory access/SQLite errors (68 tests attempted, 28 reported errors). Running with normal local Windows filesystem permissions resolved those environment failures. Streamlit emits expected missing-ScriptRunContext warnings under its offline harness.

## Limitations and operational meaning

- This is a bounded English ruleset, not a semantic classifier or comprehensive legal safety guarantee. It can miss indirect/passive language such as “A full refund is assured,” unseen paraphrases, deliberate obfuscation and non-English wording. Human review remains mandatory.
- Conservative post-validation can route an otherwise factual future-tense sentence such as “We will notify customers…”; describing existing policy in present tense can avoid that wording issue, but must never be used to disguise a new commitment.
- Only two exact standard statements have exemptions. Other legitimate paraphrases can be routed for review. Matching citations still does not prove every other factual claim is supported.
- A section-level hash is a revision check, not a signature or document-wide approval. The local trusted source files and code-owned registry remain a trust boundary. Do not let uploaded questionnaires redefine that registry.
- Source freshness is checked at validation/output time. The supplied liability source is dated 2025-09-18 and is near the 365-day limit on the 2026-09-15 test date; once stale, its exemption stops working until owner-reviewed current evidence is supplied.
- Corpus embedding initialization still happens before processing rows in the app. The C1 guarantee is zero per-question retrieval/generation calls after engine construction, not zero startup calls.
- No live Gemini behavior, production API quota usage, exhaustive adversarial detection, external owner notification or negotiated-contract approval was tested or implemented. Semantic-only retrieval and the single Google provider remain unchanged. No MCP work was included.
- No claim is made about the original four-hour cumulative task budget: prior total elapsed time was not recorded.
