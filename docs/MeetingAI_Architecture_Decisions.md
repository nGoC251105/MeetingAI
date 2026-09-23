# MeetingAI architecture decisions — Phase 1.6

Date: 2026-09-23. Documentation review only; no database, model, migration, API, frontend, authentication or AI implementation.

## Authority and evidence

All six canonical workbooks (54 worksheets), [AGENTS.md](../AGENTS.md), and [Database Mapping](MeetingAI_Database_Mapping.md) were reread. The workbook content is unchanged from Phase 1.5.

References below use these abbreviations, in descending authority:

1. **FD** — [Master Function Dataset](MeetingAI_Master_Function_Dataset.xlsx): canonical functional scope.
2. **UC** — [Use Case Specification](MeetingAI_Master_Use_Case_Specification.xlsx): flows and exceptions.
3. **DB** — [Database Design](MeetingAI_Master_Database_Design.xlsx): schema and relationships.
4. **API** — [API Contract](MeetingAI_Master_API_Contract.xlsx): backend interface.
5. **UI** — [UI Page Flow](MeetingAI_Master_UI_Page_Flow.xlsx): screens and user interactions.
6. **AI** — [AI IO Contract](MeetingAI_Master_AI_IO_Contract.xlsx): model inputs, outputs and mapping.
7. **AGENTS** — [AGENTS.md](../AGENTS.md): stack, architecture and coding rules.

Worksheet row numbers are Excel row numbers including the header row. Where a source defines only an outcome, this review does not treat that as evidence for an unstated storage/locking protocol. Source priority resolves a conflict; absence of a field alone does not authorize discarding a functional requirement.

**RESOLVED** means a complete decision for the record's stated scope is supported, including an explicitly permitted alternative. **NEEDS HUMAN DECISION** means the supported constraints are recorded but at least one material policy/storage choice remains open. Partial sub-rules do not inflate the resolved count.

## Outcome

Of the **12 original Decisions Required items**, **2 are RESOLVED (D01, D02)** and **10 NEED HUMAN DECISION (D03–D12)**. Supplemental S01 documents the requested nullable-owner/deadline behavior as RESOLVED; it is not counted as an original open item. Across all 13 records: 3 resolved and 10 requiring human decision.

| ID | Topic | Confidence |
| --- | --- | --- |
| D01 | Missing transcript timestamps | RESOLVED |
| D02 | KEY_POINTS-only regeneration | RESOLVED |
| D03 | Durable schema-version and model provenance | NEEDS HUMAN DECISION |
| D04 | ASR model/version provenance | NEEDS HUMAN DECISION |
| D05 | Missing ai_run foreign-key deletion policies | NEEDS HUMAN DECISION |
| D06 | Selecting active results across full and section runs | NEEDS HUMAN DECISION |
| D07 | Confirmed minutes, transcript edits and task updates | NEEDS HUMAN DECISION |
| D08 | Effective transcript, empty edits, reset and concurrency | NEEDS HUMAN DECISION |
| D09 | Primary evidence selection and optional full-reference retention | NEEDS HUMAN DECISION |
| D10 | Processing concurrency, checkpoints and restart recovery | NEEDS HUMAN DECISION |
| D11 | Timezone, relative deadlines and overdue dates | NEEDS HUMAN DECISION |
| D12 | Database/file deletion and failure recovery | NEEDS HUMAN DECISION |
| S01 | Nullable action owners and deadlines (supplemental) | RESOLVED |

## Proposed schema changes and remaining contradictions

The only settled schema amendment proposed by this review is D01: make transcript_segments.start_ms and end_ms nullable with NULL defaults, keeping INT UNSIGNED. This changes two existing column definitions, not the **11-table** count. Known intervals still require strict start < end. No new field, table, enum value, index, or FK action is selected.

D02 preserves run_type and narrows lower-priority section-only API lists to the three MVP sections named by FD/UC. Standalone key-point regeneration is not substituted with a misleading FULL run. F073 full-analysis generation and key-point CRUD remain required; advanced risks/open questions and minute_versions remain future scope.

The six workbooks are not edited. Their stale/conflicting annotations therefore remain visible and must be aligned separately before dependent implementation:

- **D01:** FD's nullable/strict-time behavior versus DB/API/AI non-null timing, and AI allowing equal bounds.
- **D02:** FD/UC's three section types and DB enum versus broader API section lists.
- **D03:** the AI per-run schema-version promise versus an unspecified durable prompt/schema encoding or linkage.
- **D07:** confirmed-content immutability versus required mutable task workflows and editable transcript evidence.
- **D09:** higher-priority nullable evidence versus mandatory-ref AI validation.
- **D11:** FD overdue status != DONE versus API excluding both DONE and CANCELLED; timezone itself remains unspecified.
- **S01:** preserve ambiguous stated deadline text under UC BR11; do not follow a lower AI example that would discard it. Unknown-owner confidence must respect FD F076 rather than imposing a HIGH-confidence example.

D04–D06, D08, D10 and D12 additionally contain missing designs, rather than conflicts that source precedence alone can resolve. Do not implement their unchosen solutions by inference.

## D01 — Missing transcript timestamps

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D01 |
| 2. Problem | F042 permits missing timestamps to be nullable or handled by a fallback. The database, API and AI contracts instead require numeric timestamps; the AI contract also permits zero-duration intervals. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F042 (row 30), F060; UC / USE_CASE_SPECS UC10 (row 7); DB / COLUMNS transcript_segments.start_ms and end_ms (rows 50–51); API / RESPONSE_SCHEMAS TranscriptSegment timestamps (rows 24–25) and Evidence timestamps (rows 56–57); AI / INPUT_SCHEMA rows 15–16; UI / PAGE_COMPONENTS C062 and C074. |
| 4. Source priority used | FD's explicit nullable exception and strict start < end rule outrank DB, API and AI. UC timestamp/order validation is compatible. Choose the nullable alternative explicitly permitted by F042; do not invent a numeric fallback. |
| 5. Chosen design | Represent each unavailable boundary as NULL and preserve any valid known boundary. Retain nonnegative millisecond integers for known values. Whenever both boundaries exist, require start_ms < end_ms. Keep the segment, its text, speaker/ref and segment_index even when timing is missing. Preserve transcript order; NULL timing is absence of information, not time zero. Propose nullable columns with NULL defaults so an omitted boundary cannot become a fabricated zero. |
| 6. Reason | This uses a stated functional alternative, preserves full transcript/evidence content, and avoids fabricated timestamps or dropping untimed speech. A real start of 0 remains valid when its end is greater than 0. |
| 7. Database impact | Proposed change to transcript_segments.start_ms and end_ms only: retain INT UNSIGNED, change nullable to YES and default to NULL. Keep existing indexes and segment_index uniqueness. A zero default is no longer a missing-value sentinel. Validation enforces strict ordering when both bounds are known. |
| 8. API impact | TranscriptSegment and Evidence start_ms/end_ms must allow null in the future contract implementation. Do not coerce null to 0 or omit the segment. Known reversed/equal bounds remain invalid. Canonical workbook non-null annotations remain a recorded contradiction until separately revised. |
| 9. AI/pipeline impact | AI input timestamp fields must permit null while retaining segment_ref, text and chronology. Do not supply fabricated timing to satisfy the older input schema. Align supported schema/version validation before using this exception in inference; D03 still governs durable version provenance. Evidence can refer to a segment without a complete playback range. |
| 10. Edge cases | Both missing; exactly one missing; valid 0-to-positive interval; known equal or reversed bounds; untimed segment between timed segments; evidence without a seekable range. No timestamp seeking can be derived from an unknown boundary; audio seeking itself remains advanced scope. |
| 11. Changes the 11-table MVP schema? | YES — two nullability/default changes within transcript_segments are proposed. The table count remains 11; no new field or table. No actual database/workbook modification in this phase. |
| 12. Confidence | RESOLVED |

## D02 — KEY_POINTS-only regeneration

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D02 |
| 2. Problem | API A080 includes key_points among regeneratable sections, but the canonical run_type enum has no KEY_POINTS value. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F094 (row 60), F073 and F081–F082; UC / USE_CASE_SPECS UC19 (row 16, alternative flow); DB / COLUMNS ai_runs.run_type (row 61); API / API_ENDPOINTS A080 (row 45), REQUEST_FIELDS A080 (row 23), A063 sections (row 15), A100–A102; UI / PAGE_COMPONENTS C076. |
| 4. Source priority used | FD explicitly scopes F094 to Summary/Decision/Action Items; UC19 repeats Summary/Decisions/Tasks. These and DB's concrete enum outrank the broader API section list. |
| 5. Chosen design | For MVP section-specific regeneration, support summary -> SUMMARY, decisions -> DECISIONS and action_items -> ACTION_ITEMS. Do not add KEY_POINTS or label a key-points-only run FULL. Keep F073 key-point extraction during full analysis and the existing manual key-point CRUD design. Standalone key-point regeneration is outside this narrowed MVP branch; revisiting it requires an explicit later contract decision. Risk/open-question extraction remains advanced. |
| 6. Reason | All specifically named F094 behavior remains available, and the existing run_type enum can represent it accurately. Removing a lower-priority API expansion does not remove F073 generation or human editing. |
| 7. Database impact | No schema change. Preserve the existing enum, including advanced values already documented; their presence does not make the advanced workflows MVP. |
| 8. API impact | Future A080 accepted MVP section values are summary, decisions, action_items. Its documented INVALID_SECTION outcome applies to unsupported selections. Apply the same scope consistently if A063 exposes selected-section reanalysis; full reanalysis still generates key points. The broader workbook lists are explicitly superseded for MVP by the higher-priority scope, not silently implemented. |
| 9. AI/pipeline impact | Single-section requests invoke only their declared analysis task and use the matching run_type. Full analysis includes key_points. ASR must not rerun for text-only regeneration. |
| 10. Edge cases | A key_points-only request; a full run with key_points=[]; a mixed request containing unsupported selections; human-added key points; advanced risks/open_questions disabled. Do not mislabel unsupported subsets as FULL or delete unrelated sections. |
| 11. Changes the 11-table MVP schema? | NO — 11 tables and run_type values remain as documented. |
| 12. Confidence | RESOLVED |

## D03 — Durable schema-version and model provenance

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D03 |
| 2. Problem | The AI README says each inference records schema_version via ai_runs; no separate schema_version column exists. The previous mapping also overlooked that prompt_version is described as a prompt/schema version. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F085, F143, F150–F152; UC / BUSINESS_RULES BR17 (row 18); DB / COLUMNS ai_runs.model_name/model_version/dataset_version/prompt_version (rows 62–65, prompt_version description: 'Version prompt/schema.'); AI / README row 11, OUTPUT_SCHEMA row 2, DB_MAPPING row 12, VERSIONING rows 2 and 6, VALIDATION_RULES V002. |
| 4. Source priority used | FD/UC require truthful model provenance; DB defines current fields and explicitly permits prompt/schema meaning for prompt_version. AI adds distinct schema-version and prompt-version semantics, but does not define their durable encoding/link. |
| 5. Chosen design | No complete storage design selected. Supported decisions: validate schema_version in input/output JSON against supported config; source model_name/model_version and prompt/dataset metadata from backend configuration, not model-generated claims; retain the existing DB fields. Human decision: does prompt_version identify a joint prompt/schema artifact, encode both versions, or link to an immutable compatibility record, or is a dedicated field needed? No such encoding/registry is defined here. |
| 6. Reason | The DB description means prompt/schema use is not categorically forbidden; the prior blanket 'do not overload' statement is corrected. However, the documents do not establish a recoverable link from an old run to its exact schema after configuration changes. Choosing an encoding or adding a field without that policy would guess. |
| 7. Database impact | Existing model_name/model_version remain required; dataset_version/prompt_version retain canonical nullability. Potential storage change is undecided. Do not add schema_version or metadata JSON, reinterpret existing values, or invent a version registry in this phase. |
| 8. API impact | No chosen API extension. Run metadata must remain truthful. Supported/unsupported schema validation remains required; no new public schema field is assumed. |
| 9. AI/pipeline impact | Keep schema and prompt semantics distinct; reject unsupported schemas. Durable linkage must work across prompt-only and schema-only changes before claiming per-run schema provenance is complete. |
| 10. Edge cases | Two prompts share one schema; schema changes without a model change; old runs after deployment; unavailable historical config; unknown dataset version; model-supplied fake metadata. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — no schema change proposed as a settled decision; a joint version policy might fit the 11 existing tables, while another policy might change ai_runs. The table count is not expanded here. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D04 — ASR model/version provenance

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D04 |
| 2. Problem | F041 requires storing ASR model/version, but transcript_segments has no provenance columns and ai_runs.run_type describes NLP inference scopes. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F041 (row 29), F085, F152; UC / USE_CASE_SPECS UC10; DB / COLUMNS transcript_segments rows 46–58, ai_runs rows 59–71, processing_jobs.job_type row 30; AI / INFERENCE_FLOW and VERSIONING. |
| 4. Source priority used | F041's ASR provenance requirement is mandatory. DB supplies no explicit ASR-to-provenance mapping. A processing job type TRANSCRIBE is not itself a model/version record. |
| 5. Chosen design | No complete storage design selected. Preserve the requirement to identify the actual ASR model/version for transcript production. Human decision: specify its durable association with a transcription attempt/segments using an approved existing-field interpretation or schema amendment. Do not put ASR into an NLP FULL/SUMMARY run merely to satisfy the enum. |
| 6. Reason | Model provenance cannot be reconstructed reliably from current global configuration after retries or model changes. The documents do not choose a storage location or granularity. |
| 7. Database impact | No model/version columns, ASR enum value, job metadata field, or new run table added. The future association and schema impact remain undecided. |
| 8. API impact | No invented ASR provenance response. Any later exposure must identify the model that actually produced the stored transcript. |
| 9. AI/pipeline impact | Keep ASR and subsequent summarization provenance separate. Text-only reanalysis must not change which ASR model produced raw_text. |
| 10. Edge cases | ASR retry with another model; partial transcript before failure; user-edited text; no subsequent NLP run; multiple ASR attempts for one meeting. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — existing-table amendment may be needed. No expansion beyond the 11-table MVP is selected. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D05 — Missing ai_run foreign-key deletion policies

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D05 |
| 2. Problem | Three nullable ai_run_id FKs exist without ON DELETE behavior in RELATIONSHIPS: key_points, decisions and action_items. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F034, F085, F116; UC / USE_CASE_SPECS UC20 and UC25; DB / COLUMNS key_points.ai_run_id row 81, decisions.ai_run_id row 89, action_items.ai_run_id row 99; RELATIONSHIPS row 10 (summaries.ai_run_id SET NULL) and meeting-child CASCADE rows; API / API_ENDPOINTS A024 and A071. |
| 4. Source priority used | Functional preservation/provenance and deletion requirements constrain the design; DB explicitly defines some referential actions but omits these three. Similarity and nullable types do not establish the missing actions. |
| 5. Chosen design | No action selected for these three FKs. Preserve every explicitly documented CASCADE/SET NULL action elsewhere. Human decision: specify SET NULL, restriction, or another approved policy for deletion of an ai_runs row and explain its effect on retained output provenance. |
| 6. Reason | Copying summaries' SET NULL policy would be an inference. Defaulting to database restriction would also choose an unspecified design. The absence of a run-delete endpoint does not define the underlying FK policy. |
| 7. Database impact | The three FKs remain mapped but their ON DELETE clauses are unresolved. No cascade is invented. Meeting deletion must still remove required child data under UC25. |
| 8. API impact | No independent run-delete endpoint is added. A024 meeting deletion must continue to satisfy its canonical behavior; A071 history should not imply unsupported run deletion. |
| 9. AI/pipeline impact | Deleting provenance must not silently delete or orphan usable results under an unchosen policy. Retry is not permission to delete prior runs/results. |
| 10. Edge cases | Deleting a run with human-edited outputs; meeting-wide cascade; failed run with partial data; references already null; mixed summary/key-point/action dependencies. |
| 11. Changes the 11-table MVP schema? | UNDECIDED for three referential actions; NO additional columns/tables are proposed. The 11-table count remains fixed. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D06 — Selecting active results across full and section runs

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D06 |
| 2. Problem | Output tables can hold several runs, including section-only regeneration and human rows with nullable ai_run_id, but no authoritative current-result selector or replacement boundary is defined. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F064, F090–F094, F096; UC / USE_CASE_SPECS UC19 row 16 and UC20 row 17; DB / TABLES_OVERVIEW summaries row 8, COLUMNS output ai_run_id/is_user_edited fields, INDEXES idx_summaries_meeting; API / API_ENDPOINTS A072/A080, RESPONSE_SCHEMAS MeetingMinutes; AI / DB_MAPPING row 2 and INFERENCE_FLOW steps 9–10. |
| 4. Source priority used | FD requires failure preservation and confirmation before replacing user edits; UC preserves AI origin and current results on failure. DB's multiple-run storage/indexes do not establish active-section semantics. A 'latest' index is not authority for replacement. |
| 5. Chosen design | No complete selection policy selected. Supported boundaries: a failed regeneration preserves the current result; successful persistence alone cannot override a required user replacement confirmation; section regeneration must not replace unrelated sections; retain AI origin for edited items. Human decision: define current membership per section, manual-row membership, empty successful results, preview/acceptance, and atomic switching without forcing advanced minute_versions into MVP. |
| 6. Reason | MAX(id), latest created_at, or latest COMPLETED run cannot by itself represent mixed-section acceptance, manual rows, and a deliberate empty result. A pointer/snapshot/current flag is not authorized merely because it would solve the problem. |
| 7. Database impact | No active_run_id, is_current, acceptance flag, or mandatory snapshot table is introduced. Existing multiple-run relationships remain; the eventual design may affect fields or constraints. |
| 8. API impact | A072 must return a coherent current result. A063/A080 must not silently replace user edits. No acceptance endpoint or request property is invented; its exact contract is part of the human decision. |
| 9. AI/pipeline impact | Separate successful inference from accepted/current output. Persist validated output and task-owner rows transactionally without rolling back previously successful transcript stages. |
| 10. Edge cases | New decisions=[] replacing old decisions; human-added row with null ai_run_id; equal created_at values; failed/latest run; successful but unaccepted preview; concurrent user edit; summary and tasks from different accepted runs. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — the 11 tables remain the baseline; no pointer, flag or version table is selected. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D07 — Confirmed minutes, transcript edits and task updates

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D07 |
| 2. Problem | Read-only confirmed minutes are permitted, but a blanket lock would conflict with required task editing/status tracking. There is no separate confirmed/final transcript state or immutable minutes snapshot in the MVP. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F061, F093 (row 59), F095 (row 61), F096, F101 (row 64); UC / USE_CASE_SPECS UC19–UC22 (rows 16–19), BUSINESS_RULES BR15; DB / COLUMNS meetings.review_status row 16, transcript_segments rows 46–58, action_items.task_status row 103; API / STATE_TRANSITIONS Review row 9, A081 and A091; UI / PAGE_STATES Minutes CONFIRMED row 13. |
| 4. Source priority used | F095 permits locking or edit-with-version by policy; F093/F101 still require task workflows without a stated DRAFT precondition. UC21/UI place post-confirmation draft/version editing later, but do not settle the shared-table task/transcript boundary. |
| 5. Chosen design | No complete post-confirmation policy selected. Supported rules: confirmation marks minutes review_status, not transcript finality; show the confirmed state and do not silently overwrite confirmed content. Human decision: define what is frozen, whether live task status/content may change, and what transcript edits/reanalysis do to confirmation and evidence. Do not add a final transcript flag or lock the entire meeting by assumption. |
| 6. Reason | Simply declaring all shared output rows immutable would weaken F093/F101; allowing changes while leaving an immutable-looking confirmed view would choose another unapproved policy. F096 snapshots are advanced and cannot be made a hidden MVP prerequisite. |
| 7. Database impact | No transcript.finalized flag, new review enum, snapshot requirement, or automatic CONFIRMED-to-DRAFT transition is selected. |
| 8. API impact | A061, task CRUD/A091, and A080 need an agreed post-confirmation boundary. A081 confirmation remains explicit. No new unconfirm/reopen endpoint or error code is invented. |
| 9. AI/pipeline impact | Do not overwrite confirmed outputs because an inference succeeded. A transcript correction is not a new ASR run and must not silently imply approval of regenerated minutes. |
| 10. Edge cases | Marking a confirmed meeting task DONE; correcting a speaker/transcript used as evidence; changing a deadline; regenerating a confirmed summary; repeated confirmation; viewing confirmed minutes after task edits. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — a content-boundary policy may fit existing fields; immutable snapshots would change scope. No schema change is selected. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D08 — Effective transcript, empty edits, reset and concurrency

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D08 |
| 2. Problem | Raw-versus-edited semantics are clear, but empty-edit acceptance, reset-to-raw input, and concurrent update behavior are not specified. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F043 (row 31), F061 (row 36), F064; UC / BUSINESS_RULES BR05–BR06, USE_CASE_SPECS UC17 row 14, EXCEPTION_MATRIX EX11; DB / COLUMNS raw_text/edited_text/is_user_edited/updated_at rows 52–58; API / API_ENDPOINTS A061/A063, REQUEST_FIELDS A061 row 14; AI / INPUT_SCHEMA row 17; UI / FORM_FIELDS row 13. |
| 4. Source priority used | FD/UC require raw preservation and saved corrections. DB explicitly says edited_text NULL means use raw_text. API leaves empty acceptance conditional; no higher source supplies its missing policy or a conflict protocol. |
| 5. Chosen design | No complete mutation policy selected. Resolved sub-rule: effective text is edited_text when it is not NULL, otherwise raw_text; keep raw_text immutable under user editing and update edit metadata. Initial effective text must equal the ASR text. An empty string is not a NULL fallback. Human decision: allow/reject blank or whitespace-only edits, define whether/how reset-to-raw is exposed, and decide stale-edit detection/handling. |
| 6. Reason | Truthiness-based fallback could discard an intentionally empty edit. A nullable storage field does not make null a valid API reset request: A061 currently requires a string. updated_at exists but no precondition token/comparison contract is defined. |
| 7. Database impact | Keep canonical raw_text, edited_text, is_user_edited and updated_at. Do not add a version counter or impose an unchosen reset representation. |
| 8. API impact | A061 currently accepts edited_text as a required string. Do not infer null acceptance, a reset endpoint, If-Match semantics, or last-write-wins from silence. Failed saves retain last saved values under EX11. |
| 9. AI/pipeline impact | Build effective transcript with a NULL check and use corrections in reanalysis without rerunning ASR. Treatment of blank/all-blank effective input follows the pending edit policy; do not invent raw fallback. |
| 10. Edge cases | Never-edited segment; edited_text equal to raw_text; empty/whitespace edit; reset attempt; two browser tabs editing the same segment; reanalysis while an edit is pending. |
| 11. Changes the 11-table MVP schema? | NO settled schema change. Any optimistic-lock amendment is conditional on the unresolved policy; table count remains 11. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D09 — Primary evidence selection and optional full-reference retention

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D09 |
| 2. Problem | MVP stores one primary evidence FK, while AI can return many refs. Some selection guidance exists, but decision selection and deterministic tie-breaking do not. Lower AI rules are also stricter than the functional nullable-evidence rule. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F079 (row 49), F083; UC / BUSINESS_RULES BR09 and EXCEPTION_MATRIX EX12; DB / COLUMNS evidence_segment_id fields and RELATIONSHIPS evidence SET NULL rows; AI / DB_MAPPING rows 3–4, 6 and 9, MERGE_RULES MG07, OUTPUT_SCHEMA evidence_refs fields, VALIDATION_RULES V004; API / RESPONSE_SCHEMAS Evidence.text row 59. |
| 4. Source priority used | F079 permits unclear evidence to be null/low-confidence and F083 still forbids hallucinations. UC/DB support nullable evidence. Lower AI requirements for at least one ref cannot force fabricated refs or universally reject otherwise grounded records solely because a direct ref is unavailable. |
| 5. Chosen design | No complete deterministic selector selected. Resolved sub-rules: store one nullable primary FK; use the first valid key-point evidence ref as explicitly mapped; action evidence should support task/final state most clearly; validate same-meeting membership; preserve all needed refs during merge. Human decision: define decision selection and ties, whether optional full refs are retained and where, and current-versus-inference-time evidence text after transcript edits. |
| 6. Reason | Cardinality is already documented and needs no join table. 'Clearest' does not specify a repeatable scoring/tie rule. Full-ref run logging is optional ('if needed'); neither a log format nor an immutable evidence snapshot is defined. |
| 7. Database impact | Keep nullable primary evidence_segment_id and explicit SET NULL actions. No evidence join table, snapshot JSON or full-ref log column is added. |
| 8. API impact | Evidence may be null. A valid segment may have null timing under D01. The Evidence.text current/raw policy remains an explicit decision; do not claim historical evidence is immutable when it points to an editable segment. |
| 9. AI/pipeline impact | Drop invalid cross-meeting/nonexistent refs; never fabricate one. Distinguish genuinely ungrounded claims from grounded but unlinked/uncertain evidence cases allowed by F079. Reconcile stricter AI validation with higher-priority null policy before implementation. |
| 10. Edge cases | Several equally relevant refs; corrected owner/deadline across chunks; no surviving valid ref; human-created item without evidence; deleted source segment; untimed source; later transcript edit changes a linked statement. |
| 11. Changes the 11-table MVP schema? | NO primary-cardinality change; optional full-reference persistence remains UNDECIDED. No additional table is proposed. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D10 — Processing concurrency, checkpoints and restart recovery

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D10 |
| 2. Problem | The documents require checkpoint retry and no conflicting jobs, but do not specify atomic job claiming, proof of complete checkpoints, normalized-artifact identity, or recovery after process interruption. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F030–F034 (rows 23–27), F040 and F132; UC / USE_CASE_SPECS UC15 row 12, FLOW_STEPS UC15 rows 18–19, BUSINESS_RULES BR13–BR14, SCENARIO_CHECKLIST SC009; DB / TABLES_OVERVIEW processing_jobs row 4, COLUMNS rows 28–38; API / A040–A042, STATE_TRANSITIONS row 8; UI / PAGE_CATALOG P006 and USER_FLOWS UF02. |
| 4. Source priority used | FD/UC mandate outcomes and preservation. DB supplies job/status/error fields; API/UI describe retry and leaving the page. None selects a locking/worker mechanism or establishes that any existing segment row proves a complete ASR checkpoint. |
| 5. Chosen design | No complete recovery design selected. Supported rules: return promptly and process in background; do not run conflicting jobs for one meeting; preserve committed successful stages; retry creates a new job from the nearest valid checkpoint; reuse a valid transcript after AI failure; missing checkpoint falls back to the nearest usable earlier stage. Human decision: define claim atomicity, checkpoint validity/artifact identity, interrupted-job recovery, and the duplicate-result boundary. |
| 6. Reason | A queue, lock, manifest, lease, or new checkpoint column would be a design choice without sufficient canonical evidence. Closing a browser tab is explicitly supported; automatic recovery after worker/process death is not fully specified by that statement. |
| 7. Database impact | Retain processing_jobs and meeting status/error fields. Do not introduce a unique-active-job index, lease, checkpoint table or normalized-file column without a decision. A status field alone is not proof of durable stage completion. |
| 8. API impact | Preserve A040/A042 202 behavior and existing JOB_ALREADY_RUNNING/NOT_RETRYABLE outcomes. Network polling failure must not be reported as job failure. No new cancellation/recovery endpoint or retry parameter is invented. |
| 9. AI/pipeline impact | ASR success plus NLP failure must keep the transcript. Do not mistake partially inserted ASR segments for a validated complete transcript; the completeness rule remains to be decided. Retry must not duplicate results uncontrollably. |
| 10. Edge cases | Two simultaneous starts; queued versus running conflict; worker dies before/after stage persistence; lost normalized file; partial transcript; retry fails again; browser closes; database unavailable during status update. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — no new column/index/table is selected. The documented 11-table baseline remains. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D11 — Timezone, relative deadlines and overdue dates

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D11 |
| 2. Problem | meeting_date is timezone-less DATETIME, API timestamps use ISO 8601, and no canonical storage/display/meeting timezone defines relative deadlines or 'today'. There is also a narrower task-status predicate disagreement. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F078 (row 48), F102 (row 65); UC / BUSINESS_RULES BR11, SCENARIO_CHECKLIST SC016; DB / COLUMNS meetings.meeting_date row 13 and action_items.deadline_normalized row 102; API / README time row 7, REQUEST_FIELDS meeting_date row 7, RESPONSE_SCHEMAS ActionItem.overdue row 51; AI / INPUT_SCHEMA meeting_date row 6, VALIDATION_RULES V009–V010, HARD_CASE_EXPECTATIONS HC17. |
| 4. Source priority used | FD governs deadline grounding and its stated overdue rule. DB/API define types but no timezone. The developer machine timezone is environment context, not a canonical business policy. |
| 5. Chosen design | No timezone selected. Preserve deadline_raw and use NULL when normalization lacks sufficient context; a DATE remains a calendar date, not an invented midnight timestamp. Human decision: define datetime storage/API-offset conversion, the timezone used to interpret meeting-relative phrases, and the calendar used for 'today'. Resolved source-priority sub-rule: F102 says deadline < today and status != DONE, with null deadline not overdue; the lower API exclusion of CANCELLED cannot silently replace that predicate. |
| 6. Reason | UTC, Asia/Bangkok, a Vietnamese default or per-user timezones would all be guesses here. The status discrepancy is separate from timezone: if CANCELLED should also be excluded, the canonical functional rule needs explicit clarification. |
| 7. Database impact | No timezone column or datatype conversion selected. Keep nullable DATE for normalized deadlines and the documented DATETIME pending policy. |
| 8. API impact | ISO 8601 formatting alone does not define how offset-free values are interpreted or which offsets to emit. Do not prescribe a Z suffix or a default zone without evidence. The API overdue annotation excluding CANCELLED remains inconsistent with F102. |
| 9. AI/pipeline impact | Use meeting context for relative deadlines only when sufficient; no anchor means no guessed calendar date. Absolute/relative dates near a day boundary must use the eventual chosen policy. |
| 10. Edge cases | Meeting near midnight; users in different zones; offset-bearing input saved into DATETIME; missing meeting_date; ambiguous 'Friday'; DST if relevant to the chosen zone; null deadline; CANCELLED task past its deadline. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — policy may use existing fields or require a future amendment; no new table/column is proposed. |
| 12. Confidence | NEEDS HUMAN DECISION |

## D12 — Database/file deletion and failure recovery

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D12 |
| 2. Problem | Meeting deletion must remove database children and audio safely, but the sources do not define an atomic/recoverable protocol across MySQL and filesystem operations. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F116–F117 (rows 73–74), F142, F144; UC / USE_CASE_SPECS UC25 row 22, FLOW_STEPS rows 35–38, BUSINESS_RULES BR16, EXCEPTION_MATRIX EX15; DB / RELATIONSHIPS meeting cascades, COLUMNS meetings.audio_path/audio_deleted_at; API / API_ENDPOINTS A024 row 17; UI / USER_FLOWS UF09. |
| 4. Source priority used | F116/F117 require confirmation, access removal and safe file removal; UC25 narrows MVP to blocking busy meetings and requires recoverable failure handling. Its happy-path sequence does not specify transaction commit timing or compensating behavior. |
| 5. Chosen design | No complete failure protocol selected. Supported behavior: check ownership and confirmation, reject deletion while processing under the MVP busy rule, delete required DB children and associated private audio, never remove a path outside the allowed upload/storage boundary, and tolerate/log an already-missing file. Human decision: define operation/commit ordering and recovery when either deletion fails or the process stops between them. |
| 6. Reason | A database rollback cannot restore an already-unlinked file. Conversely, committing DB deletion first can lose the only file reference. A quarantine move, outbox, soft-delete field or deletion journal would require an unchosen persistence/recovery policy. |
| 7. Database impact | Keep documented cascades. Do not use audio_deleted_at as an invented deletion-workflow state, introduce soft-delete/outbox tables, or add a deletion status enum. |
| 8. API impact | A024 success must satisfy the documented deletion outcome and return deleted_id. Do not claim complete success while required audio remains, or invent a new partial-success contract. Error/retry behavior for an interrupted deletion needs agreement. |
| 9. AI/pipeline impact | No new processing may race deletion; exact race prevention depends on D10. Completed/failed intermediate artifacts need an agreed safe cleanup boundary; no retention scheduler is made MVP. |
| 10. Edge cases | Audio already absent; file locked/access denied; DB rollback after file deletion; DB commit followed by crash before unlink; path traversal; associated derived audio; simultaneous process start; repeated delete after an uncertain response. |
| 11. Changes the 11-table MVP schema? | UNDECIDED — no recovery field/table or schema change is selected. Keep 11 tables unless a later decision explicitly amends the design. |
| 12. Confidence | NEEDS HUMAN DECISION |

## S01 — Nullable action owners and deadlines (supplemental)

| Record field | Decision |
| --- | --- |
| 1. Decision ID | S01 |
| 2. Problem | An ownerless task must coexist with non-null owner_name on actual owner rows, and missing/ambiguous deadlines must not force fabricated data. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F076–F078, F083, F093; UC / BUSINESS_RULES BR07, BR11–BR12; DB / COLUMNS action_items.deadline_raw/deadline_normalized rows 101–102, action_item_owners rows 109–113; API / REQUEST_FIELDS owners/deadlines rows 19–21, RESPONSE_SCHEMAS ActionItem.owners/Owner; AI / OUTPUT_SCHEMA owners/deadline fields, DB_MAPPING row 8, FINAL_STATE_RULES FS05–FS08. |
| 4. Source priority used | FD/UC explicitly allow unknown owners/deadlines and 0..N owners; DB defines normalized storage. API/AI concrete array contracts refine the null/empty alternatives without changing the requirement. |
| 5. Chosen design | Represent unknown owners as owners=[] and zero action_item_owners rows. Every actual owner row has a grounded, non-empty owner_name; speaker_id may be NULL when a named owner cannot be mapped to a speaker. Map an unknown/blank owner input to no owner row rather than a fake 'unknown' person. Preserve multiple real owners. Keep deadline_raw and deadline_normalized independently nullable; retain an ambiguous stated raw phrase while normalized stays NULL. |
| 6. Reason | Zero child rows represent absence without weakening NOT NULL owner_name on real owners. This uses the documented relationship and avoids new owner columns/tables or placeholder people. |
| 7. Database impact | No change to action_items or action_item_owners. Keep nullable speaker FK, required owner_name, nullable deadline fields and 0..N owner relation. |
| 8. API impact | Return owners=[] for an ownerless task, not a fabricated owner object. A present owner object still requires its name. Return nullable date fields as null; no empty-string date sentinel. Same-meeting speaker validation remains required. |
| 9. AI/pipeline impact | Do not assign the nearest speaker by proximity or invent a deadline. Model owner name maps to owner_name and valid speaker_ref to speaker_id. Preserve reassignment/final-state rules and multiple collaborative owners. Retain a stated ambiguous deadline under BR11 even if a lower AI annotation example permits dropping it. Do not force HIGH confidence for an unknown owner merely from an AI example when F076 calls for uncertainty/low confidence. |
| 10. Edge cases | Explicit task but no assignee; team/external owner not in speakers; two owners; owner reassigned; 'do it soon'; absent meeting_date for relative deadline; no action items at all. |
| 11. Changes the 11-table MVP schema? | NO — the canonical 11-table schema already supports this behavior. |
| 12. Confidence | RESOLVED |

## Scope and review checks

- Original D01–D12 IDs are retained; each has all 12 requested decision fields.
- S01 is supplemental, so it does not change the denominator of the original decision review.
- Only this decision document and the Decisions Required section of the mapping are changed in Phase 1.6.
- The rest of the Phase 1.5 mapping remains historical text. Its old list of blockers must be read together with the updated Decisions Required status; it is not permission to implement unresolved items.
- No source workbook, model, migration, runtime code or actual database is changed.
- Source hashes are retained for reproducibility.

## Canonical workbook fingerprints

| Workbook | SHA-256 |
| --- | --- |
| MeetingAI_Master_AI_IO_Contract.xlsx | 91D8323D0E5F9A639A4C5378604E2F10DCB231B9797A64FA0807523D78BF8758 |
| MeetingAI_Master_API_Contract.xlsx | 4F40DB01C7679E81BF94416F0F95B44157BF67AFA033EFDEF13714B80B7CB04E |
| MeetingAI_Master_Database_Design.xlsx | 60BD53385B1640F4F06B565DDA1B2B810600523BC15A6B760E5C82C33111E227 |
| MeetingAI_Master_Function_Dataset.xlsx | 32325DC1FD80F6C51FADFD11F95869B4BC4007AB60D7D41D48F84C7C4F27922F |
| MeetingAI_Master_UI_Page_Flow.xlsx | 61E60E0291CAEC9C83FECBC25709DB7030CCBB355E8AAB1C9CAB76B7250CD159 |
| MeetingAI_Master_Use_Case_Specification.xlsx | 28D2AB9FAA489D55A0BCA8B4B9A0AEDA269DF08E68E1758E1A6D37932F883822 |

