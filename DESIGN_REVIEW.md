# Design review and scope reconciliation

> Historical audit from 2026-09-14, before the actual PDF brief was supplied and before semantic retrieval/commitment controls. Claims below about an unavailable brief, lexical-only retrieval and deferred vector search are superseded. Current state and limitations: [consolidated verification](verification/VERIFICATION_REPORT.md), [submission notes](SUBMISSION_NOTES.md), and the current sections at the top of DESIGN.md.

Reviewed on 2026-09-14 against `DESIGN.md`, `README.md`, `answer-format.md`, all ten knowledge-base files, `approved-answers.md`, and all three supplied questionnaires.

## Material discrepancies

1. The supplied “case-study brief” is only `README.md`, a contents list. It contains no additional functional, evaluation, or answer-format requirements. This implementation therefore treats `DESIGN.md` and `answer-format.md` as the operative specifications.
2. The three inbound layouts use different question fields: `question` (Q1), `requirement` (Q2), and `requirement_text` (Q3). The engine detects these fields and the UI permits an explicit override. Original columns and row order are preserved.
3. The required prospect export is the original CSV plus exactly `status`, `answer`, `evidence`, `owner`, `confidence`, and `reviewer_note`. Design-only internal fields stay in the separate review workbook.
4. The approved sources conflict on consent-record retention: `06-data-residency-and-retention.md` says 12 months; `09-privacy-and-dpa-terms.md` says 36 months. Neither source is declared authoritative. Q1 row Q14 is therefore forced to `Cannot answer`, routed to Legal, and the prospect-facing `evidence` cell remains empty as required.
5. Q1 asks for the most recent penetration-test date. `AA-009` gives September 2024 but is older than 12 months; the newer certification document says testing is annual without giving the latest test date. The verification fixture routes this question to Security rather than presenting September 2024 as current.
6. Q3 contains prompt-injection text asking the respondent to ignore the format, answer Yes, and omit evidence. Questions and evidence are explicitly treated as untrusted data in the model instruction; application validation still enforces citations and allowed statuses.
7. `DESIGN.md` proposes Q2/Q3 attempts but directs delivery to prioritize one complete Q1 workflow. Under the four-hour constraint, Q2 and Q3 receive parsing/mapping verification only. Semantic generation, review, and export were exercised end to end on Q1 first.

## Implemented Q1 boundary

- CSV validation, layout detection, preview, and upload size/encoding checks.
- Lightweight lexical retrieval over labelled Markdown sections and approved answers.
- One production provider: Google Gemini structured output, with a 30-second timeout, two bounded retries after the initial attempt, and no tools.
- Deterministic validation of status values, answer length/voice, evidence IDs, exact excerpts, mandatory evidence/owner rules, stale-source confidence, and the known unresolved retention conflict.
- Deterministic owner routing, with processing failures kept separate from business answer status.
- SQLite per-row progress, failed-row retry, accepted/edit review state, and one prior version retained.
- Prospect CSV and internal Excel exports, including partial/failed rows and spreadsheet-formula escaping.

## Deferred by design

Authentication/authorization, live document connectors, collaborative approvals, private inference, background workers, multi-user storage, vector search, numerical hallucination scores, a second model provider, and calibrated semantic-support scoring are not implemented. Add them only after real usage or evaluation demonstrates the need.

## Known prototype limitations

- Exact-quote validation proves provenance, not semantic entailment. A human reviewer remains mandatory.
- Retrieval is lexical and tuned only by the supplied pack; paraphrase recall needs a labelled evaluation before changing retrieval technology.
- The explicit retention-conflict guard is pack-specific. A broader source-conflict registry or governed authority metadata is needed for a larger corpus.
- SQLite and local files are single-instance prototype storage. The app has no production access controls or retention enforcement.
- Source-pack fingerprint, prompt version history, and full audit-history tables from the proposed design were not required to prove the first workflow and remain deferred.
- The available environment had no `GEMINI_API_KEY` or `GOOGLE_API_KEY`, so no live-model quality, latency, token-cost, or provider-timeout result is claimed.
- No in-app browser was attached. Streamlit startup and control rendering were checked through Streamlit's application test harness, not through visual browser QA.
