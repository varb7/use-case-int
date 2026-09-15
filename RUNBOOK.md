# Q1 workflow runbook

Current results are consolidated in [verification/VERIFICATION_REPORT.md](verification/VERIFICATION_REPORT.md). Older phase reports are historical. Start with README for the shortest submission setup path.

### First-run Google settings

Open **Google settings** in the sidebar. Enter the Google API key and a generation model available to the Google project, select **Save settings**, then **Test Google connection**. The password field intentionally stays blank after saving. The key and model are stored for the current Windows user via Windows Credential Manager; they are not written to `.env`, SQLite, logs or exports. **Remove saved settings** deletes both saved values. Environment variables still take precedence and are not deleted by that button.

Credential Manager protects the key at rest but does not isolate it from other processes running as the same Windows user. Use a dedicated, restricted Google key, rotate it if the machine/user profile is compromised, and never include it in a submission. Connection testing makes a Google metadata request but sends no questionnaire content.

## Commitment guardrails

Restart Streamlit after updating. No new package, API key, database migration or embedding-cache reset is required for these guards.

New commitment requests are routed before per-row search/model calls. Use **Owner-routed** and **Filter by owner** to find them; the reason begins `C1-`. Unsupported promises in a draft or reviewer edit are replaced with a safe `Cannot answer` result and a `C3-` validation reason. Both routes leave prospect evidence blank. A C3 result cannot be accepted; correct/regenerate the answer. Accepting a safe C1 escalation acknowledges its routing only. The app cannot approve negotiated terms or notify Legal/Sales automatically.

Evidence now shows **Source authority**. `factual_policy` permits factual description, not a new guarantee. `negotiation_only` identifies restricted/mixed material that cannot authorize a commitment. `existing_standard_term` is limited to the explicitly supported standard wording and scope, not all text in the section.

When a registered source section changes, its hash no longer matches and it defaults to factual-only authority. A maintainer must review the revised text and update the hash, classification and exact allowed statement/supporting excerpt in `commitments.py` after the appropriate owner review. Do not automatically refresh hashes as approvals. Missing, future-dated or older-than-365-day evidence cannot authorize an exempted standard-term statement. Human review is still required for other facts and unrecognized phrasing.

Old saved drafts are rechecked when displayed/exported. Newly blocked results appear as Needs review with their owner and reason, while the original stored job is preserved until an explicit review save/regeneration. Processing errors remain failures. CSV and XLSX use the same guard projection, so the review view matches the exported business answer.

Reproduce offline tests and save a fresh machine-readable report and verbose log:

```powershell
python test_commitments.py
```

This runs the new guard tests plus both existing suites, without a live Gemini request. Reports: `verification/commitment-results.json`, `verification/commitment-tests.txt`; explanation and limitations: `verification/commitment-guardrails.md`. Corpus indexing at engine startup still requires the existing Google configuration; pre-routing saves per-question requests, not startup initialization.

## Semantic retrieval and evidence review

### Generation request pacing

Gemini drafting requests are serialized and start at least 4.1 seconds apart within one app process, which stays below the observed free-tier limit of 15 generation requests per minute. HTTP 429, 500 and 503 receive at most three total attempts; Google's structured retry delay is respected with a one-second margin. SDK retries are disabled so request counts remain bounded. Restart the app after updating this code.

`GEMINI_GENERATION_INTERVAL_SECONDS` optionally changes the interval for a different verified quota. Keep the default for the reported free-tier limit. A value of zero disables pacing and is appropriate only when the configured project quota supports it. Quotas apply per Google project, so two app processes can still exceed a shared limit. Pacing a 25-row questionnaire adds roughly 98 seconds before provider latency and retry waits.

Production drafting, retry and **Regenerate this answer** now use semantic-only top-eight retrieval. Hybrid/BM25 commands remain comparison tools. Restart Streamlit to use the changed code, keeping both the Google key and `GEMINI_MODEL` configured in the launching PowerShell session.

For each new draft, inspect the read-only excerpt and its supported answer text in **Evidence and checks**. The review view shows filename, heading, owner, source date and revision fingerprint taken from application records. Duplicate evidence editing fields have been removed. If the source changed or disappeared, or an answer edit invalidates its claim mapping, regenerate the answer before accepting it. Regeneration clears acceptance. Claim-to-quote matching still needs human judgment.

Use **Show questions** to select Failed or Owner-routed, then **Filter by owner** to inspect a team's questions. Only groups and owners with matching rows are offered. The overview table shows each question's original row number, state, owner and reason. Failures remain distinct from business escalations. **Retry failed rows** retries all failed rows in the job, irrespective of the view filter. Exports always include the whole job. Routing records a responsible team locally; it does not notify that team automatically.

The internal workbook includes `evidence_metadata` with source IDs, filenames, headings, dates, owners, content hashes and whether original snapshots were recorded. Saved snapshots preserve the original revision when files change. Older saved answers may lack snapshots and are labelled accordingly. Prospect CSV fields are unchanged. Existing saved answers are not automatically regenerated or unaccepted when source files change.

### Rate limits and recovery

Embedding calls are spaced at least one second apart per provider instance. HTTP 429, 500 and 503 receive at most three total attempts. For 429, the client waits for Google's structured retry delay plus one second, or 60 seconds if no delay is provided. A requested delay over 60 seconds is surfaced for a later manual retry. Persistent quota errors remain visible; this does not increase your Google quota. Avoid running multiple embedding processes concurrently because project usage is shared.

Successful new document vectors are checkpointed immediately. A failed run preserves the previous complete index and resumes from checkpoints on rerun. Checkpoints are cleared after the new complete snapshot commits. No database deletion is needed. A cold 109-document plus 81-query evaluation takes at least roughly three minutes with pacing, plus API latency and any retry waits.

If you encounter the reported 100-requests-per-minute error, wait a minute and rerun `python evaluate_retrieval.py --live` in the terminal containing your Google key. Earlier failures from the pre-checkpoint version cannot recover vectors that were never saved.

After installing the dependencies below, configure your Google key in the same PowerShell session:

```powershell
$env:GEMINI_API_KEY = "your-google-ai-studio-key"
$env:GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
python semantic.py
python semantic.py --query "How is stored customer information protected?"
python -m unittest test_semantic -v
```

The first command embeds the supplied 109 sections and writes `evidence_embeddings.sqlite3`. Later runs reuse unchanged embeddings and print generated/reused/removed counts. Search prints scores, evidence IDs, filenames and headings; it does not draft an answer. Document text and the query are sent to Google. This command reads process environment variables; it does not load a `.env` file automatically. Keep the cache out of Git; it contains source text as well as vectors.

`GEMINI_EMBEDDING_MODEL` is independent of `GEMINI_MODEL`. Its initial default uses the document/query task conventions of `gemini-embedding-001`; verify those conventions before selecting a different embedding model. Access errors should be resolved with a model available to your account. Streamlit uses the cached semantic index for generation and retry. Automated semantic tests use fake embeddings; the separate user-run live retrieval evaluation established target coverage, not generated-answer quality.

Run the following in the **same PowerShell window** where you assigned `$env:GOOGLE_API_KEY` (or `$env:GEMINI_API_KEY`). PowerShell variables are not automatically shared with other already-running terminals or the coding agent.

```powershell
python evaluate_retrieval.py
python evaluate_retrieval.py --live
python -m unittest test_semantic test_detailed -q
```

The first command saves `verification/retrieval_offline.json`; the second saves `verification/retrieval_live.json`. Live evaluation requires an embedding key/model but no generation model: it compares retrieval only, with no draft-generation charges. The first live run embeds 109 sections, then makes 81 query-embedding requests (75 supplied rows plus six extra cases). Subsequent runs reuse unchanged document vectors but repeat query embeddings. These are application-level request counts; provider retries may add requests. Inspect any `processing_error` and `missing_rankings` before comparing scores. Existing report files are replaced on rerun.

Labels identify particular evidence sections; equivalent approved answers may be useful even when a designated section is absent. Scores do not measure answer correctness. BM25 is an evaluation-only implementation and has not replaced the app's keyword scorer.

## Clean-machine setup (Windows PowerShell)

Validated lock target: Windows x64 and Python 3.13 (development interpreter 3.13.1). Other targets are not clean-install verified. Internet access to PyPI is required.

```powershell
cd C:\path\to\data-pack-ai-enablement-engineer
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe test_commitments.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL shown by Streamlit. Upload `questionnaires/questionnaire-1-standard.csv`, confirm the detected `question` column, and select **Generate draft**. Review evidence before accepting any row, resolve routed items with their owners, then download the prospect CSV and internal review workbook.

For scripted operation, `GOOGLE_API_KEY` or `GEMINI_API_KEY` is accepted and overrides the saved key. The drafting adapter has no default generation model; `GEMINI_MODEL` similarly overrides the saved model:

```powershell
$env:GEMINI_MODEL = "an-approved-gemini-model"
```

The API receives each question and a small set of retrieved excerpts from this synthetic pack. Do not use real questionnaire data until model processing, access control, storage, logging, and retention arrangements are approved.

## Repeatable verification

```powershell
python verify.py
python test_detailed.py
```

These legacy commands check input mappings and Q1 using test doubles and regenerate phase-specific reports/fixture exports. For all current tests use `.\.venv\Scripts\python.exe test_commitments.py`; use the consolidated verification report as the current entry point. In the commands elsewhere in this document, substitute `.\.venv\Scripts\python.exe` for `python` unless you activated the environment. Fixture exports are not live-model or prospect-ready outputs.

For a live check, set `GEMINI_API_KEY`, run the app, process Q1, and record model, elapsed time, edits, escalations, citation failures, processing failures, and token usage. Do not infer time savings without a manual baseline.

## Operational notes

- Local state is stored in `questionnaire_jobs.sqlite3` beside the app.
- A provider failure leaves the row visible as a processing failure; use **Retry failed rows**.
- Editing always resets the accepted state. `Accepted` is prototype review, not production approval.
- Partial jobs can be exported; unprocessed and failed rows remain visible.
- Delete local prototype data according to your approved handling process; this prototype does not automate retention.
