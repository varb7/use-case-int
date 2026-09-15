import json
from pathlib import Path

import streamlit as st
from semantic import build_engine
from app_paths import data_directory
from secure_settings import (remove_settings, resolve_model, save_settings,
                             settings_status, test_connection)

from workflow import (
    JobStore,
    GeminiProvider,
    OUTPUT_COLUMNS,
    ProcessedAnswer,
    DraftProposal,
    WorkflowEngine,
    export_csv,
    export_review_xlsx,
    guarded_rows,
    load_evidence,
    parse_questionnaire,
    validate_draft,
)


ROOT = Path(__file__).parent
STORE = JobStore(data_directory(ROOT) / "questionnaire_jobs.sqlite3")
EVIDENCE = load_evidence(ROOT)
EVIDENCE_BY_ID = {item.ref_id: item for item in EVIDENCE}


st.set_page_config(page_title="Questionnaire review", layout="wide")
st.title("Guided questionnaire review")
st.caption("Synthetic case-study data only. Accepted means reviewed in this prototype, not formally approved.")

key_ready, model_ready, setting_source = settings_status()
with st.sidebar.expander("Google settings", expanded=not (key_ready and model_ready)):
    if key_ready and model_ready:
        st.success(f"Ready · credentials from {setting_source}")
    else:
        st.warning("Add a Google API key and generation model before drafting.")
    api_key_input = st.text_input(
        "Google API key", type="password", value="",
        placeholder="Already stored" if key_ready else "Paste key",
        help="The field is never populated with the saved key.",
    )
    try:
        configured_model = resolve_model() or ""
    except RuntimeError:
        configured_model = ""
    model_input = st.text_input("Generation model", value=configured_model,
                                placeholder="Model available to your Google project")
    if st.button("Save settings", use_container_width=True):
        try:
            save_settings(api_key_input or None, model_input or None)
            saved_key, saved_model, _ = settings_status()
            if not saved_key or not saved_model:
                st.error("Both an API key and generation model are required.")
            else:
                st.success("Saved securely for this Windows user.")
                st.rerun()
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
    if st.button("Test Google connection", use_container_width=True):
        try:
            with st.spinner("Checking the configured generation model"):
                name = test_connection()
            st.success(f"Connection succeeded · {name}")
        except Exception as exc:
            st.error(f"Connection failed: {exc}")
    if st.button("Remove saved settings", use_container_width=True):
        try:
            remove_settings()
            st.success("Saved settings removed. Environment variables, if set, still take precedence.")
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))

jobs = STORE.list_jobs()
job_options = {f"#{job['id']} · {job['filename']} · {job['state']}": job["id"] for job in jobs}
if job_options:
    selected = st.sidebar.selectbox("Saved jobs", list(job_options), index=0)
    st.session_state.setdefault("job_id", job_options[selected])
    if st.sidebar.button("Open selected job"):
        st.session_state.job_id = job_options[selected]

st.header("1 · Upload")
uploaded = st.file_uploader("Questionnaire CSV", type="csv")
if uploaded:
    raw = uploaded.getvalue()
    try:
        preview = parse_questionnaire(raw, uploaded.name)
        question_column = st.selectbox(
            "Question column",
            preview.headers,
            index=preview.headers.index(preview.question_column),
        )
        questionnaire = parse_questionnaire(raw, uploaded.name, question_column)
        st.write(f"Detected {len(questionnaire.rows)} questions · source pack: supplied synthetic pack")
        st.dataframe(questionnaire.rows[:5], width="stretch")
        if st.button("Generate draft", type="primary"):
            if not (key_ready and model_ready):
                st.error("Complete Google settings before generating. No questionnaire content was sent.")
            else:
                with st.spinner("Preparing evidence search"):
                    engine = build_engine(ROOT, EVIDENCE)
                job_id = STORE.create_job(questionnaire)
                st.session_state.job_id = job_id
                progress = st.progress(0, text="Starting")
                STORE.process_job(
                    job_id,
                    engine,
                    progress=lambda done, total: progress.progress(done / total, text=f"{done}/{total} questions"),
                )
                st.rerun()
    except Exception as exc:
        st.error(str(exc))

job_id = st.session_state.get("job_id")
if job_id:
    job = STORE.job(job_id)
    rows = guarded_rows(STORE, job_id, EVIDENCE)
    st.header("2 · Review")
    completed = [row for row in rows if row["result"]]
    failed = [row for row in completed if row["result"].processing_error]
    unresolved = [row for row in completed if row["result"].status == "Cannot answer" and not row["result"].processing_error]
    accepted = [row for row in rows if row["review_state"] == "Accepted"]
    st.write(
        f"{len(completed)}/{len(rows)} processed · {len(unresolved)} owner-routed · "
        f"{len(failed)} failed · {len(accepted)} accepted"
    )
    if failed and st.button("Retry failed rows"):
        if not (key_ready and model_ready):
            st.error("Complete Google settings before retrying.")
        else:
            try:
                with st.spinner("Preparing evidence search"):
                    engine = build_engine(ROOT, EVIDENCE)
                STORE.process_job(job_id, engine, failed_only=True)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    groups = {
        "All questions": rows,
        "Failed": failed,
        "Owner-routed": unresolved,
        "Needs review": [row for row in completed if row not in failed and row not in unresolved
                         and row["review_state"] != "Accepted"],
        "Accepted": accepted,
        "Not processed": [row for row in rows if not row["result"]],
    }
    review_filter = st.selectbox("Show questions", [name for name, items in groups.items() if items])
    visible_rows = groups[review_filter]
    owners = sorted({row["result"].owner for row in visible_rows if row["result"] and row["result"].owner})
    owner_filter = st.selectbox("Filter by owner", ["All owners", *owners])
    if owner_filter != "All owners":
        visible_rows = [row for row in visible_rows if row["result"] and row["result"].owner == owner_filter]
    st.dataframe([
        {
            "Row": row["row_index"] + 1,
            "Question": row["original"][job["question_column"]],
            "State": ("Not processed" if not row["result"] else
                      "Failed" if row["result"].processing_error else
                      "Owner-routed" if row["result"].status == "Cannot answer" else row["review_state"]),
            "Owner": row["result"].owner or "" if row["result"] else "",
            "Reason": (row["result"].processing_error or row["result"].escalation_reason
                       or row["result"].what_needs_checking) if row["result"] else "",
        } for row in visible_rows
    ], hide_index=True, width="stretch")
    st.caption("Routing records the responsible team locally; it does not send notifications. Filters do not limit exports.")
    labels = {
        f"{row['row_index'] + 1}: {row['original'][job['question_column']][:90]}": row["row_index"]
        for row in visible_rows
    }
    chosen_label = st.selectbox("Question", list(labels))
    chosen = rows[labels[chosen_label]]
    result: ProcessedAnswer | None = chosen["result"]
    st.markdown(f"**Original question:** {chosen['original'][job['question_column']]}")
    if result:
        if result.processing_error:
            st.error(result.processing_error)
        with st.form("review_form"):
            status = st.selectbox("Status", ["Yes", "No", "Partial", "Not applicable", "Cannot answer"],
                                  index=["Yes", "No", "Partial", "Not applicable", "Cannot answer"].index(result.status))
            answer = st.text_area("Answer", result.answer, height=130)
            owner_values = [None, "Security", "Legal", "Product", "Sales"]
            owner = st.selectbox(
                "Owner", owner_values, index=owner_values.index(result.owner),
                format_func=lambda value: value or "",
            )
            confidence_values = ["High", "Medium", "Low"]
            confidence = st.selectbox("Confidence", confidence_values, index=confidence_values.index(result.confidence))
            reviewer_note = st.text_area("Reviewer note", result.reviewer_note)
            save, accept = st.columns(2)
            save_clicked = save.form_submit_button("Save edit")
            accept_clicked = accept.form_submit_button(
                "Accept draft", type="primary", disabled=bool(result.processing_error)
            )
        if save_clicked or accept_clicked:
            proposal = DraftProposal(**result.model_dump(exclude={"validation_errors", "processing_error", "review_state"}))
            proposal = proposal.model_copy(update={
                "status": status, "answer": answer, "owner": owner,
                "confidence": confidence, "reviewer_note": reviewer_note,
            })
            edited = validate_draft(
                chosen["original"][job["question_column"]], proposal, EVIDENCE_BY_ID,
                allowed_refs=result.retrieved_refs or None,
                source_hashes={ref: source.content_hash for ref, source in result.source_snapshots.items()},
            )
            STORE.save_review(job_id, chosen["row_index"], edited, accept=accept_clicked, evidence=EVIDENCE)
            st.rerun()

        st.markdown("**Evidence and checks**")
        if st.button("Regenerate this answer"):
            try:
                with st.spinner("Retrieving current evidence and drafting"):
                    regenerated = build_engine(ROOT, EVIDENCE).process(chosen["original"][job["question_column"]])
                STORE.save_review(job_id, chosen["row_index"], regenerated, evidence=EVIDENCE)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        for use in result.evidence_uses:
            source = result.source_snapshots.get(use.ref_id) or EVIDENCE_BY_ID.get(use.ref_id)
            if source:
                with st.expander(source.citation):
                    st.write(use.quote)
                    if use.supported_claim:
                        st.write(f"Supports: {use.supported_claim}")
                    st.caption(f"File: {source.source_file or source.citation} | Section: {source.heading or 'not recorded'}")
                    st.caption(f"Revision fingerprint: {source.content_hash}")
                    st.caption(f"Source authority: {source.authority} (not approval of customer-specific terms)")
                    current = EVIDENCE_BY_ID.get(use.ref_id)
                    if not current or current.content_hash != source.content_hash:
                        st.warning("Source changed or was removed since drafting. Regenerate before accepting.")
                    if use.ref_id not in result.source_snapshots:
                        st.caption("Legacy answer: original source revision was not recorded.")
                    st.caption(f"Source date: {source.source_date or 'not supplied'} · Owner: {source.owner or 'not supplied'}")
        st.write(result.evidence_strength_reason or "No evidence-strength explanation supplied.")
        if result.what_needs_checking:
            st.info(result.what_needs_checking)
        if result.escalation_reason:
            st.warning(f"Routing reason: {result.escalation_reason}")
        if result.validation_errors:
            st.error("; ".join(result.validation_errors))
    else:
        st.warning("This row has not been processed.")

    st.header("3 · Export")
    if len(completed) != len(rows):
        st.warning("This job is partial. Unprocessed rows will remain present and blank in exports.")
    st.download_button(
        "Download prospect CSV",
        export_csv(STORE, job_id, EVIDENCE),
        file_name=f"{Path(job['filename']).stem}-answered.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download internal review workbook",
        export_review_xlsx(STORE, job_id, EVIDENCE),
        file_name=f"{Path(job['filename']).stem}-review.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
