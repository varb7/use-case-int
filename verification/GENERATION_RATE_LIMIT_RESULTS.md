# Generation request pacing

> Historical focused test run. Current full-suite status: [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

2026-09-15. The reported live error identified a 15 requests-per-minute free-tier quota for `gemini-3.1-flash-lite`. Added a process-shared lock and a default 4.1-second minimum interval between generation request starts. Added at most three total attempts for 429/500/503, honoring structured retry delays with a one-second margin; SDK retries are disabled. The interval can be changed with `GEMINI_GENERATION_INTERVAL_SECONDS` after verifying the project's quota.

The focused test simulates a 429 with a seven-second server delay, successful retry and a subsequent draft. It verifies three total API calls, the eight-second retry wait and cumulative request pacing without real sleeps. Configuration validation rejects a nonnumeric interval.

Actual result: `python -m unittest test_semantic test_detailed -q` completed with **68 tests passed in 19.398 seconds**. The Streamlit warnings about a missing script context are expected in its bare-mode test runner. No live Google requests were made, so the user's next real questionnaire run remains the live confirmation of quota behavior.
