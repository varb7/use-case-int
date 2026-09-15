Guided Questionnaire Review App — Design Document
Version 0.6 | Deterministic commitment guardrails

### Additional Windows distribution

`desktop_launcher.py` wraps the existing Streamlit app in a tray process. It starts a hidden server child on a selected 127.0.0.1 port, waits for health readiness, and opens the default browser. Open/Exit tray actions reopen the UI or send a shutdown message over the child stdin pipe. EOF requests shutdown if the parent disappears. A per-data-directory file lock prevents duplicate desktop instances. Shutdown waits up to 30 seconds before terminating an unresponsive child.

`app_paths.py` provides a single writable-path override. The desktop launcher sets it to `%LOCALAPPDATA%/QuestionnaireReview`; ordinary source launches retain their existing adjacent databases. The packaged knowledge base stays with the executable. Existing source jobs are not copied or overwritten. The same Credential Manager settings serve both launch modes.

PyInstaller builds a one-folder executable with Python, dependencies, static UI resources and the supplied data. Inno Setup installs it for the current user with Start Menu and optional Desktop shortcuts. Uninstall preserves user data and credential entries. Build requirements are separately hash-locked. The portable zip and installer are unsigned; test evidence and remaining gaps are recorded in `verification/DESKTOP_RESULTS.md`.

Submission entry points: [concise notes](SUBMISSION_NOTES.md), [consolidated verification](verification/VERIFICATION_REPORT.md), and [clean setup](README.md). Historical design proposals below do not imply implemented or verified functionality.

### First-run credential setup

The Streamlit sidebar provides a masked Google API-key field, generation-model field, save, connection-test and removal actions. `secure_settings.py` is the single credential boundary used by both generation and embeddings. Environment variables take precedence for automation; otherwise the API key and model are read from the current Windows user's Credential Manager through `keyring`. The saved key is never returned to the UI field. Connection testing requests model metadata only and sends no questionnaire content. Credential Manager protects at-rest storage, not against other processes running as the same Windows user.

### Commitment protection (current implementation)

Implementation sequence: (1) define question rules and factual counterexamples; (2) pre-route new commitments; (3) pin source authority to reviewed section hashes; (4) validate generated/reviewer text and legacy exports; (5) run questionnaire and regression tests and save results. Implementation and test details are in `verification/commitment-guardrails.md`.

Three guards live in the processing engine, not Streamlit:

1. **Question gate (C1):** normalized English patterns for agreeing, accepting, signing, guaranteeing, indemnifying and similar requests route the whole row to `Cannot answer`, blank evidence and Legal (Sales for price/discount-only requests). On-site audit-right requests also route. This executes before per-question retrieval and generation. Existing policy questions, including the supplied breach-notification timing question, continue normally. Corpus indexing/provider initialization still happens when the app builds its engine.
2. **Evidence authority:** application-derived `authority` is `factual_policy` by default. A code-owned registry pins two existing-standard-term sections and three negotiation-only sections to exact section hashes. Changed/unregistered sections cannot grant commitment authority. Mixed sections are deliberately restricted: a standard-term label does not authorize the entire section or customer-specific negotiation. The registry describes the supplied source material; it is not actual approval of a customer's contract.
3. **Draft gate (C3):** recognized affirmative promises are blocked regardless of the proposed status. Only two exact standard-term statements can be exempted, with the pinned current source, exact supporting excerpt and source date no older than 365 days. Other citation, retrieval-boundary and format checks still apply. A match becomes a routed safe answer with a visible validation reason, never an automatic second model call.

Review submission enforces the same commitment policy. Acceptance cannot override C3; it may acknowledge a safe C1 routing decision, not approve new terms. UI and both exports recheck legacy saved answers in memory, marking newly blocked content Needs review without rewriting saved jobs. Processing failures remain distinct. Source authority is visible with evidence and included in internal workbook metadata; prospect CSV columns are unchanged.

These deterministic rules are conservative pattern checks, not exhaustive semantic understanding. Unseen paraphrases, passive promises, obfuscation and non-English requests can be missed; ordinary factual hallucinations still require human evidence review. Legitimate future-tense descriptions can be overblocked. No LLM judge, MCP, new provider, dependency, external notification or contract-approval system was added. This scoped extension does not assert compliance with the original cumulative four-hour budget, whose prior elapsed time is not recorded.

### Generation rate-limit correction

The live app hit Google's free-tier generation quota of 15 requests per minute for `gemini-3.1-flash-lite`. The Gemini adapter now serializes generation starts within the process and spaces them by 4.1 seconds by default. Temporary 429/500/503 responses receive at most three total attempts, with a one-second margin added to Google's structured retry delay. SDK-level retries are set to one attempt so application behavior is bounded. The interval is configurable through `GEMINI_GENERATION_INTERVAL_SECONDS`; zero disables it. This process-local gate does not coordinate multiple app processes sharing the same Google project.

### Review UI simplification

The approved UI now keeps evidence read-only in **Evidence and checks**; the duplicate **Exact source excerpt** and **Supported answer text** editors have been removed. Quotes, claim mappings and source snapshots remain persisted and validated. If editing an answer invalidates its claim mapping, regenerate the answer; the application does not silently rewrite evidence to fit an edited claim.

Review now has filters for available groups (All questions, Failed, Owner-routed, Needs review, Accepted, Not processed) and owners present in the selected group. A table lists row number, question, state, owner and failure/routing reason. Processing failures are excluded from the Owner-routed group even though failures have a responsible owner. Selecting a filtered question retains the original row identity. Filters affect review only; exports still contain every row. Owner routing is local assignment, not automatic email or ticket delivery.

### Approved implementation: semantic-only and relevant excerpts

Following user approval, production `build_engine` now selects `SemanticRetriever` for generation, retry and single-answer regeneration. It returns up to eight positive-cosine matches without keyword fusion. Keyword and BM25/hybrid methods remain evaluation baselines only. This supersedes historical statements below describing hybrid as the app default. The existing known retention-conflict guard runs before retrieval and remains independent of ranking.

The drafting prompt requests the shortest sufficient verbatim excerpt for every material factual claim, keeping qualifications and exceptions and using multiple sources for compound answers. Each evidence use includes a `supported_claim` excerpt from the answer. The application checks nonempty exact source quotes, that citations came from this question's retrieved candidates, and that any supplied claim text actually occurs in the answer. It does not enforce an arbitrary quote-length cap or claim that matching text proves semantic support. Older fixtures/records may omit claim mappings; the model instruction requests them for new drafts. Comprehensive automated entailment and claim-coverage validation remain unimplemented.

Application-generated `source_snapshots` preserve the cited section's text, ID, filename, heading, owner and date alongside the answer, with a deterministic content hash available for revision checks. `retrieved_refs` records the allowed candidate references for later review validation. The model supplies references/quotes/claim text only, not authoritative metadata. Review displays excerpts, claims, filename, heading, source date, owner and revision fingerprint. On review, changed source content or deleted sources blocks acceptance; original evidence stays available in saved snapshots until regeneration. Legacy answers explicitly disclose that their original revision was not recorded.

Reviewers may edit the claim mapping and exact quote within existing citations, and regenerate an individual answer using current semantic evidence. Regeneration resets acceptance and retains the previous result through the existing review-history field. The internal workbook adds `evidence_metadata` and shows supported claims alongside excerpts; saved snapshots take precedence over current documents. Required prospect CSV columns and citation formatting remain unchanged. Exporting an existing accepted answer after a document update does not automatically revoke its saved acceptance: snapshots preserve historical provenance, and reviewers must regenerate/review current answers when policies change.

### Live evaluation decision (2026-09-15)

The user's live `gemini-embedding-001` run is saved in `verification/retrieval_live.json` and was inspected: all 81 cases have rankings and zero processing errors. This supersedes the pending-live statements in the earlier implementation notes below. It evaluates retrieval only, not generated answers.

Designated-source coverage@8 for semantic / keyword-hybrid / BM25-hybrid is Q1 100% / 100% / 100%, Q2 96.67% / 95% / 95%, Q3 98.33% / 94.83% / 94.83%, and the four labelled extra cases 100% for all three. Semantic retrieves all designated targets for 72/74 labelled supplied questions, versus 69/74 for either hybrid. The unsupported supplied row is excluded from that denominator.

Do not adopt BM25: it provides no aggregate target-coverage gain over the existing hybrid. Semantic-only retrieval is the strongest candidate on this small evaluation; equal-weight fusion pushes designated hosting, offboarding and change-management evidence out of the top eight. This finding contradicts the earlier hypothesis that hybrid ranking necessarily improves this corpus. The app still uses the implemented keyword hybrid; no default change has been made solely from this aggregate result. Before changing it, compare the actual drafts and handling of unsupported/compound questions.

All three semantic-based methods return candidates for both unsupported extra cases. That is not proof of a fabricated answer, but it means retrieval does not establish answerability. The existing prompt, citation validation and human review do not substitute for evaluating claim support. Labels are designated sections, not exhaustive acceptable evidence, and this small development set is not a held-out benchmark.

### Rate-limit recovery correction

The live user run hit Google's embedding free-tier limit of 100 requests per minute. Embeddings are now paced at one request per second per adapter instance, with three bounded attempts on 429/500/503. Structured retry delays are respected with a one-second margin; delays above 60 seconds and exhausted attempts are surfaced rather than retried indefinitely. SDK internal retries are disabled so the application controls request counts. Concurrent processes still share project quota and require coordination if introduced.

An `embedding_checkpoints` table now persists each successful new document vector by cache identity immediately. A failed build retains these reusable checkpoints while leaving the active `evidence_embeddings` snapshot and in-memory index unchanged. The next build reuses checkpoints as well as active vectors; publishing the complete snapshot and clearing checkpoints occur in the same transaction. This corrects the original all-or-nothing cache behavior that repeated successful API calls after an interrupted first build.

## Retrieval upgrade status (2026-09-15)

Steps 1 and 2 are implemented in `semantic.py`: Google document/query embeddings, persistent SQLite caching, explicit source metadata, cosine search and hybrid ranking. Streamlit generation and retry now build the hybrid engine. Offline integration and lexical evaluation have run; live semantic relevance and answer-quality improvements have not yet been measured.

1. **Embeddings and metadata (implemented):** reuse the Markdown `##` sections and approved-answer rows. Preserve existing citation IDs; add `source_file`, `heading`, and a SHA-256 content hash. Existing owner and source date remain attached. Markdown has no page numbers. A heading rename changes its KB reference ID, so the old record is removed and the new section is embedded.
2. **Hybrid retrieval (implemented):** combine the top ten keyword and positive-cosine semantic candidates using equal-weight reciprocal rank fusion, k=60, returning eight unique references with deterministic ID tie-breaking. Similarity scores are not directly added to lexical scores. Generation and retry share `build_engine`; core callers may still explicitly use the original keyword baseline. Index setup errors display before a new job is created; per-question retrieval errors are persisted as retryable processing failures. The known consent-retention conflict is checked against the entire current pack before retrieval, so ranking cannot hide it. This remains a narrow keyword-triggered conflict guard, not general semantic conflict detection.
3. **Questionnaire evaluation (partially executed):** `evaluate_retrieval.py` compares keyword and experimental BM25 on all 75 supplied questions and six additional cases. Designated source labels were chosen by reading the pack before scoring. They include routing evidence, stale evidence and both conflict sources, not necessarily sufficient support for an answer. Metrics are designated-source coverage@8, not exhaustive relevance recall or answer accuracy. Per-row candidates, missed targets derivable from those candidates, and timings are saved. `--live` adds real Google semantic, hybrid and BM25-hybrid rankings using the same query vector per case. No live call ran in this agent environment because the user's key is scoped to another PowerShell window. No calibrated relevance cutoff or answer-quality claim is established.
4. **BM25 experiment (not adopted):** offline designated-target coverage was keyword/BM25: Q1 95.83%/93.75%, Q2 93.33%/95.00%, Q3 84.83%/86.50%. BM25 loses a designated subprocessor-list source on Q1. Both lexical methods cover only 25% of the four supported extra cases. Keep BM25 confined to the evaluation script until the real hybrid comparison establishes an improvement without unacceptable regressions.

### Step 1 storage and revision handling

Use a separate generated `evidence_embeddings.sqlite3` file beside the app to isolate the retrieval cache from saved review jobs. SQLite stores reference ID, full chunk metadata/text, content hash, model, chunking version, cache identity and vector JSON. This file should be excluded from version control. The original Markdown remains the source of truth.

The cache identity hashes the exact embedding input (source filename, heading and text), embedding model, document task type and chunking version. Unchanged records reuse vectors across restarts. Text or heading changes regenerate affected vectors; owner/date-only changes refresh metadata without unnecessary embeddings. A model or chunking-version change rebuilds affected records. Removed IDs are pruned only after the complete new snapshot succeeds. Failed embedding requests leave the previous snapshot intact and propagate an error. Hashes detect changes but do not retain revision history.

Google is the only model provider. The initial adapter uses `gemini-embedding-001` with `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`, configurable via `GEMINI_EMBEDDING_MODEL` for compatible models. This variable is separate from the drafting model. Follow Google's embedding documentation when changing models: task conventions and dimensions may differ. API access is account-dependent and must be verified live.

The index loads cached document vectors into memory and calculates exact cosine similarity. Query vectors are generated per search and not persisted. Invalid, zero, non-finite or dimensionally inconsistent vectors raise errors. The standalone semantic command returns diagnostic top-eight results. Hybrid retrieval excludes nonpositive semantic scores, but zero is only a mathematical filter, not a calibrated relevance threshold. Weak positive candidates may still reach the drafter. Human review and the existing evidence-only prompting and citation validation remain necessary; quote provenance alone does not prove answer support.

The staged upgrade uses the existing dependencies and keeps retrieval outside Streamlit. This implementation does not claim that the original four-hour case-study budget has been remeasured; remaining evaluation and documentation effort must be accounted for before expanding scope.

#1. Purpose and intended outcome

Build a simple application that helps Solutions Engineers prepare accurate, evidence-backed responses to prospect questionnaires.

The application will process a whole questionnaire, produce a draft in the required format, show the exact evidence supporting each answer, and route questions that require a decision from Security, Legal, or Product.

The intended benefit is less time spent searching and drafting, with a clear review process before answers are shared externally. Success means reducing review effort while avoiding unsupported claims and unauthorized commitments.

#2. Scope of the first version

The first version will support:

* Uploading the supplied CSV questionnaires.
* Previewing questions and mapping columns when layouts differ.
* Using only the supplied knowledge documents and approved answers.
* Generating structured answers with specific evidence references.
* Showing supporting excerpts and review reasons.
* Routing unresolved questions to an appropriate owner.
* Exporting the required questionnaire output.
* Producing an internal Excel review workbook.
* Saving processing progress and retrying failed questions.

Q1 is the required end-to-end implementation. Q2 and Q3 will be attempted, with their actual coverage and limitations documented.

The first version will use one tested model provider. Company sign-in, live document connectors, collaborative approvals, and private model hosting are future enhancements.

The supplied data pack is available and the CSV workflow is implemented. The original design sections below describe intent; `DESIGN_REVIEW.md` and verification reports track actual coverage and limitations. The retrieval status section above describes the current staged upgrade.

3. User experience

The application will have three steps: Upload, Review, and Export.

Upload

The Solutions Engineer uploads a questionnaire and sees a preview, detected question count, and selected knowledge-pack version.

For recognized layouts, the app selects the question column automatically. Otherwise, the user chooses it from a dropdown. The app preserves original columns, row order, and identifiers.

The user selects “Generate draft.” Progress shows how many questions have completed and whether any failed.

Review

The app displays a summary of answers awaiting review, questions requiring an owner, and processing failures.

The reviewer can filter these groups and select a question. Its detail view contains:

* Original question.
* Proposed status and answer.
* Exact supporting excerpts.
* Source document, section, and available version information.
* Evidence-strength explanation.
* Missing information or applicable limitations.
* Assigned owner and escalation reason.

The user can accept a draft, edit it, or mark it for an owner. Editing an answer resets its review state and requires validation again.

“Accepted” means the reviewer accepted the draft within this prototype. It does not represent a production approval workflow.

Export

The app provides the questionnaire draft in the required format and a separate internal review workbook.

Export remains available for partially completed work, but unresolved and failed rows must remain visible. The application must never silently omit them or present a partial run as complete.

4. Answering policy

Each question must receive either a supported response or “Cannot answer” with a routed owner.

The permitted answer statuses will follow the supplied specification: Yes, No, Partial, Not applicable, and Cannot answer.

The following rules apply:

Yes requires evidence supporting the requested capability.

No requires evidence establishing a negative. Missing evidence alone does not justify No.

Partial requires evidence of a genuinely partial capability. It must not conceal an unanswered material part of the question.

Not applicable requires an evidenced reason.

Cannot answer applies when material evidence is missing, conflicting, insufficiently scoped, or otherwise unusable.

Requests for new commitments are routed to the relevant owner. The application must not turn an existing policy statement into a new promise.

Compound questions must be assessed across their material parts. An excerpt supporting one part must not be treated as support for the entire question.

5. Evidence and uncertainty

Evidence will be stored with application-generated identifiers. Each source section will retain its document name, section location, text, and available date or version metadata.

The model will select evidence identifiers and supporting text. Application code will verify that references exist and that quoted excerpts match their source.

These checks prove that an excerpt exists. They do not prove that the excerpt supports the answer, so claim support also requires semantic checking and human review.

The internal review view will explain evidence strength using categories such as Strong, Limited, and Blocked. The required exported confidence marker will follow the data-pack specification.

A separate “What needs checking?” field will describe actionable uncertainty, for example:

“The source covers one deployment region. Confirm that this is the region relevant to the prospect.”

The first version will not produce a numerical falseness probability. Such a score would require calibration against representative, labelled examples.

Conflicting sources will trigger review unless an explicit authority rule resolves the conflict. A newer date alone will not establish authority. Missing freshness metadata will be visible rather than replaced with an invented expiry rule.

6. Technical design

The application will be a single Python project with a Streamlit interface and separate processing modules.

Streamlit will manage uploads, previews, review controls, and downloads.

The processing engine will manage parsing, evidence selection, model calls, validation, routing, and export. This separation allows the same engine to support another interface later.

Pydantic will define and validate structured records. CSV utilities will preserve questionnaire structure, and an Excel-writing library will generate the internal workbook.

SQLite will store local job progress and review records for the prototype. It provides restart recovery without requiring a separate database service. This is a single-instance design, not the final shared deployment architecture.

A small model adapter will isolate provider-specific request and response handling. Only one adapter needs to be implemented and tested initially.

7. Processing sequence

The engine will:

1. Validate the uploaded file and map its columns.
2. Assign internal row identifiers while retaining original identifiers.
3. Load and identify the approved source sections.
4. Select relevant evidence for each question.
5. Generate a structured draft using that evidence.
6. Validate fields, references, quotations, and answer-policy compliance.
7. Record the result or a processing error.
8. Present results for review and export.

For the small supplied corpus, the initial evidence approach will use labelled source sections with lightweight text retrieval. Where practical, the complete pack can be evaluated as a baseline.

Retrieval settings must be checked against representative questions, including paraphrases and conflicts. Failure to retrieve evidence means “no sufficient evidence found,” not that the company lacks the capability.

A vector database is deferred until corpus size or measured retrieval quality justifies it.

8. Records and state

Each job will record its input fingerprint, column mapping, source-pack fingerprint, model configuration, prompt version, timestamps, and processing state.

Each answer will record its question, status, explanation, evidence references, evidence-strength reason, owner, escalation reason, and review state.

Processing state and business answer status will remain separate.

For example, a provider timeout is a processing failure. It must not be converted into an evidence-based “Cannot answer.”

Results will be saved after each completed question. Retrying a failed question will not regenerate already completed answers unless explicitly requested.

An edited answer will retain its previous version and lose its accepted state until reviewed again.

9. Failure handling and security

The app will reject malformed inputs with a useful explanation before generation begins.

Model calls will have timeouts and bounded retries. The initial implementation can process sequentially; bounded concurrency can be added once correctness is established.

Questionnaires and source documents will be treated as untrusted content. Instructions embedded inside them must not control application behavior. The model will have no tools for sending messages, modifying external systems, or accessing arbitrary files.

Exported untrusted text will be handled as text to avoid spreadsheet formula execution.

API credentials will remain outside source code. Routine logs will record job identifiers, timing, and error categories without duplicating questionnaire contents or evidence text.

The prototype will use synthetic data. A live deployment requires authentication, authorization, retention rules, protected storage, and an approved model-processing arrangement.

10. Scalability and adaptability

The first version addresses the workload with recoverable processing and a reusable engine.

For multiple users, the next architecture step is a shared database, protected object storage, and a background job queue. The browser will submit jobs and display saved results while workers perform generation.

Worker concurrency will be limited according to provider quotas, latency, and cost. Increasing worker count must not bypass those limits.

Input adapters will accommodate new questionnaire layouts. Source adapters can later load approved documents from company systems. A model adapter allows provider changes, subject to regression evaluation.

A future Claude/Cowork integration could invoke the same processing service. The review and validation rules should remain in the engine so behavior stays consistent across interfaces.

For private inference, a company-managed model service could replace the hosted provider. Privacy would still require protection of retrieval, storage, logs, and exports.

11. Evaluation and acceptance criteria

The initial evaluation will cover straightforward supported answers, missing evidence, explicit negative evidence, compound questions, source conflicts, requested commitments, and processing failures.

Acceptance criteria are:

* Q1 runs from upload through export.
* Original question rows and required structure are preserved.
* Every substantive answer has a specific, valid citation.
* Unsupported questions receive Cannot answer and an owner.
* Requested commitments are routed without inventing promises.
* Failed rows remain visible and can be retried.
* Editing an answer invalidates its previous review state.
* A nontechnical user can upload, inspect evidence, and export without writing prompts.
* Q2 and Q3 results and limitations are reported honestly.

Record generation time, reviewer edits, escalation frequency, citation validity, and unsupported claims found during review. Do not claim time savings until the workflow has been compared with a manual baseline.

12. Delivery and enablement

Implementation will prioritize one complete Q1 workflow, then evidence checks and failure handling, followed by Q2/Q3 adaptation and final verification.

The deliverables will include the runnable application, setup instructions, actual questionnaire outputs, the brief’s two-page design note, and a short handover. This working design can be condensed into that submission note after implementation decisions are verified.

The enablement session will demonstrate upload, a supported answer, an unresolved question, a commitment escalation, and export. The participant will then inspect one answer’s evidence themselves.

This makes the session demonstrate both the application’s behavior and the Solutions Engineer’s responsibility: verify supported drafts, resolve uncertainty through the right owner, and prepare the final response for the prospect.
