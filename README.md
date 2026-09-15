# Questionnaire Review

An evidence-backed questionnaire workflow for Presales. It retrieves relevant excerpts from the supplied knowledge base, drafts answers with Google Gemini, validates the output, routes rows that need an owner or review, and exports completed CSV and Excel files.

## Open the application

> **Hosted application:** `[deployment URL to be added]`
>
> The hosted deployment is pending. This placeholder will be replaced with the private Streamlit URL after deployment and hosted acceptance testing.

Presales users do not install Python, download dependencies, or run terminal commands. When the hosted application is available:

1. Open the application link and sign in.
2. Upload the prospect's questionnaire CSV.
3. Select **Generate draft**.
4. Review the evidence, validation checks, failed rows, and owner-routed rows.
5. Download the completed CSV or review workbook.

API credentials and model configuration are deployment-administration concerns, not Presales setup steps. If the evaluation deployment uses bring-your-own-key mode, the landing page will request the key in a masked, session-only field.

## What the workflow does

- Parses and validates the uploaded questionnaire.
- Uses semantic retrieval over the supplied Markdown knowledge base and approved answers.
- Preserves source metadata so retrieved evidence identifies its document and location.
- Generates evidence-bounded drafts through one model provider: Google Gemini.
- Applies deterministic commitment guardrails before and after generation.
- Marks unsupported or failed answers instead of silently inventing content.
- Routes rows to the appropriate owner and exposes review queues.
- Exports the answer format required by the case-study brief.

The processing engine is implemented in `workflow.py` and remains separate from the Streamlit interface in `app.py`.

## Important operating boundaries

- Everything in the supplied data pack is synthetic and must not be treated as Usercentrics production information.
- Questions and selected evidence are sent to Google for embedding or generation.
- Live operation requires internet access, a permitted Gemini account, and available API quota.
- The hosted application must be private and must isolate each user's credentials and job data before real customer questionnaires are processed.
- Generated content still requires human review, especially commitments, contractual terms, security claims, and unsupported questions.

## Evidence and verification

- [Consolidated verification report](verification/VERIFICATION_REPORT.md)
- [Design and implementation decisions](DESIGN.md)
- [Design review](DESIGN_REVIEW.md)
- [Operating runbook](RUNBOOK.md)
- [Submission notes](SUBMISSION_NOTES.md)

The repository includes the supplied questionnaires, the synthetic knowledge base, retrieval measurements, guardrail results, detailed edge-case testing, and fixture exports. Tests use deterministic fakes unless explicitly identified as live Gemini evaluation.

## Developer and evaluator setup

This section is for developers and technical evaluators only. Presales users should use the hosted link above.

Tested source environment: Windows x64 with Python 3.13. The locked file contains the exact dependency set used for verification.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On local Windows, Google settings can be entered in the application and stored for the current user through Windows Credential Manager. Environment variables are also supported and take precedence:

```powershell
$env:GOOGLE_API_KEY = "your-google-ai-studio-key"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Never commit API keys, `.env` files, Streamlit secrets, generated SQLite databases, or customer questionnaires.

## Optional Windows desktop build

The desktop wrapper bundles the local Streamlit application, starts it automatically, opens the browser, and provides a system-tray shutdown control. See [desktop instructions](DESKTOP_GUIDE.md). The desktop edition is an optional local delivery route; the hosted web application is the primary nontechnical-user experience.

## Repository map

- `app.py` — Streamlit user interface.
- `workflow.py` — upload, drafting, validation, routing, review, persistence, and export engine.
- `semantic.py` — semantic indexing, metadata, and evidence retrieval.
- `commitments.py` — deterministic commitment-question guardrails.
- `secure_settings.py` — local Windows credential handling.
- `knowledge-base/` — supplied Markdown evidence sources.
- `questionnaires/` — supplied test questionnaires.
- `verification/` — test reports, retrieval evaluations, and fixture outputs.
- `test_*.py` — automated workflow, retrieval, guardrail, and desktop tests.
- `requirements.txt` / `requirements-lock.txt` — direct and reproducible source dependencies.

## Data-pack notice

All company facts, dates, vendor names, certificate numbers, policies, and questionnaire content in this repository are invented for the exercise. They do not describe Usercentrics' actual security posture, contracts, products, or systems.
