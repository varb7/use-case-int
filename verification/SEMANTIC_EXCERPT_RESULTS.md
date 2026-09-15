# Semantic-only retrieval and excerpt provenance

> Historical phase report. Duplicate excerpt editors were subsequently removed and commitment guards added. Current status: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

Date: 2026-09-15.

Implemented the approved switch from hybrid to semantic-only retrieval in the production engine builder, used for generation, retry and per-answer regeneration. The evaluation baselines remain available. Google embedding pacing, checkpoints and bounded retries are preserved.

The prompt requests concise verbatim supporting passages and copied answer-claim mappings. Citation validation now restricts references to retrieved candidates, rejects empty/whitespace/invented quotes and rejects claim mappings not present in the answer. Application-owned source snapshots retain original text and metadata. Review displays and edits excerpts/claim mappings, detects changed or removed sources before acceptance, and supports regeneration. The internal workbook adds metadata and uses saved source revisions; prospect output structure is unchanged.

## Actual verification

`python -m unittest test_semantic test_detailed -q`: **65 tests passed in 18.809 seconds**. Run outside the Windows sandbox with approval for temporary SQLite access.

- Production builder selects `SemanticRetriever`; keyword retrieval is patched to fail if accidentally invoked by it.
- Valid quotes preserve source snapshots and hashes; empty, whitespace and invented quotes are blocked.
- Citations outside a permitted candidate set are blocked.
- A source text change blocks review even when the old quote still occurs in the revised source.
- Editing away a mapped claim invalidates that mapping.
- A compound answer retains excerpts from two distinct sources.
- SQLite persistence and internal workbook export preserve the original filename/hash after the live source is renamed/changed.
- Existing provider, engine, revision-cache, rate-limit, review/export and Streamlit fixture tests remain green. The Streamlit fixture now exercises the production semantic-only builder with a controlled search result and fake drafting provider.

## Limits

No new live Google drafting run was performed: the user's key is in another PowerShell session. Prior real retrieval metrics justify the ranking choice but do not measure excerpt selection or answer quality. Tests use controlled embeddings/drafts. Prompt instructions request minimal passages and coverage of all material claims; Python checks provenance and mapped-text presence, not entailment or comprehensive claim coverage. No arbitrary excerpt length limit is imposed. Optional claim mappings preserve compatibility with legacy records, which may lack original source snapshots.

Existing saved answers are not bulk-regenerated or automatically unaccepted after file revisions. Snapshot metadata reflects the source at drafting/validation time; use regeneration and review for current-policy responses. Prospect exports keep the required format and historical citations. The original cumulative four-hour budget is not reconstructable from available history.
