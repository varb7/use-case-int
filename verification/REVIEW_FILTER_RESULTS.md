# Review simplification and routing visibility

> Historical focused test run. Current full-suite status: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

2026-09-15. Removed the duplicate excerpt and supported-claim editing fields. Evidence remains read-only under Evidence and checks, with stored metadata and validation intact. Added review-group and owner filters and an overview table showing original row number, question, state, owner and reason. Filters do not restrict exports or the job-wide retry-failed action. No external notifications were added.

Verification: `python -m unittest test_detailed.StreamlitShellTests -q` — **6 tests passed in 14.479 seconds**. Used approved execution outside the Windows sandbox for SQLite test access. The new test checks that failures remain separate from owner-routed rows, filtering Legal selects the correct original row and reason, returning to All restores access, duplicate editors are absent, Evidence and checks remains, and both downloads remain available with all four test rows in CSV export. Existing startup, upload validation, key gate and controlled Q1 generation/export UI tests also pass. No live model calls were made.
