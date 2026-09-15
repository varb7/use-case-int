# Submission notes

## Delivered

One local, single-user workflow: CSV upload and mapping → evidence retrieval → drafting → deterministic validation and owner routing → human review → prospect CSV and internal XLSX. The engine (`workflow.py`, `semantic.py`, `commitments.py`) is separate from the Streamlit shell (`app.py`). Google is the only production model provider.

The knowledge base is the supplied ten Markdown files plus 42 approved answers, parsed into 109 labelled sections. Production retrieval embeds document sections and questions with Google, stores vectors and source metadata in SQLite, and ranks by cosine similarity. It is semantic-only RAG; a separate vector database is unnecessary at this corpus size. Keyword, BM25 and hybrid variants remain evaluation tools, not production defaults.

Retrieved excerpts retain file/section/date/owner and revision hashes. Drafts cite exact quotes; application-owned snapshots preserve their source revision. Validation checks provenance, output shape and mapped claim text, not complete semantic entailment. Human evidence review remains mandatory. Known conflicting retention values route to Legal. Three bounded commitment guards pre-route recognized requests, restrict source authority by reviewed hashes, and block recognized unsupported promises in drafts/review/exports.

## Evidence and results

The consolidated report distinguishes offline workflow tests, historical real embedding retrieval results and clean-package validation. Q1 sample CSV/XLSX files are deterministic fixtures, **not live Gemini answers or prospect-ready submissions**. Q2/Q3 parsing, retrieval and guard decisions were tested; complete live answer quality was not systematically measured. No claims are made about time savings, costs or production readiness.

## Reproducibility decision

Use the supplied hash-pinned requirements lock and Python 3.13 virtual environment. uv was used as a maintainer tool to resolve the lock; recipients can use ordinary pip. Docker would introduce another runtime and require a separately tested image, ports and persistent volumes without addressing Google account/model/quota variability. It is deferred unless container deployment becomes a real requirement. The tested target is Windows x64, not a universal cross-platform guarantee.

## Deliberate limitations

No authentication, shared approval roles, external notifications, background jobs, source connectors, full audit history, MCP server or production retention controls. Rules do not detect every commitment paraphrase or source conflict. Retrieved text can be relevant without answering the question. Local storage and API processing are suitable only for the supplied synthetic pack until governance is approved.

Setup is in README/RUNBOOK. First-run settings can save the Google key in Windows Credential Manager; environment variables remain available for automation. Use a Google model available to your project; API keys, user job databases, vector caches, virtual environments and temporary files are excluded. The original cumulative four-hour budget cannot be reconstructed, so no compliance claim is made. These concise notes are Markdown; no rendered two-page PDF deliverable is claimed.
