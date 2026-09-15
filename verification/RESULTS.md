# Verification results

Run: `2026-09-15T13:50:37` with Python fixture provider (not a live Gemini call).

- Questionnaire parsing: Q1 25/25 rows, Q2 30/30 rows, Q3 20/20 rows; all question columns detected correctly.
- Gemini adapter contract: structured JSON/Pydantic request and response parsing passed without a network call.
- Complete Q1 plumbing: 25/25 processed, CSV 25/25 rows, review workbook 25/25 rows.
- Fixture statuses: Yes 18, No 3, Partial 1, Cannot answer 3.
- Validation: 0 citation/quote/format errors and 0 processing failures.
- Conflict behavior: Q14 routed to Legal because the supplied sources state both 12 and 36 months.
- Review behavior: acceptance persisted; a subsequent edit reset the row to Needs review.
- Partial/safe export: an unprocessed row remained present and a formula-leading input was escaped as text.

Limitations: this command deliberately uses test doubles, regardless of environment keys. Live drafting quality, API latency, token cost and live-model status distribution were not measured. This command checks Q2/Q3 parsing/mapping only; other suites cover retrieval and commitment rules. Fixture outputs are not prospect-ready model results. See `VERIFICATION_REPORT.md` for consolidated current coverage.
