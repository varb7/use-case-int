# Embedding rate-limit recovery

> Historical focused test run. Current full-suite status: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

2026-09-15: The user's live Google error identifies `EmbedContentRequestsPerMinutePerUserPerProjectPerModel-FreeTier`, limit 100, with a seven-second retry delay. The cold index needs 109 document requests, followed by 81 evaluation query requests. The prior adapter had no pacing, and partial document builds were not saved.

Implemented one-second per-instance request spacing, at most three total attempts for 429/500/503, structured server retry delay plus one second (60-second fallback for 429), and immediate document checkpoint commits. Requests requiring waits above 60 seconds are surfaced. Other client errors are not retried. A later index failure leaves the previous active snapshot intact and completed vectors available to the next run. Checkpoints are removed atomically when a complete snapshot is published.

Verification: `python -m unittest test_semantic test_detailed -q` — **62 tests passed in 17.895 seconds**. New tests simulate a 429 followed by success, verify the server delay and pacing, enforce the three-attempt cap, reject retrying HTTP 400, and verify partial indexing resumes without repeating completed requests. Sleep is mocked in the rate-limit test. Existing cache revision, hybrid pipeline, Streamlit and export tests also pass.

No live API run was performed by the agent: the key remains scoped to the user's other PowerShell window. Per-instance pacing does not coordinate concurrent processes or guarantee sufficient daily/token quota. The user's original unsaved vectors cannot be recovered. Google rate-limit reference: https://ai.google.dev/gemini-api/docs/rate-limits
