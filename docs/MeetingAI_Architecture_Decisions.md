# MeetingAI architecture decisions — Phase 1.6 reconciliation

Reviewed: 2026-09-30. This update changes internal Markdown only. Existing models and migration are implementation evidence; approved service/pipeline behavior is not automatically implemented by its database fields.

## Authority and evidence

The explicit human-approved D01–D12 and S01 decisions govern the amendments recorded here. Otherwise resolve requirements in this order:

1. **FD** — [Master Function Dataset](MeetingAI_Master_Function_Dataset.xlsx), canonical functional scope.
2. **UC** — [Use Case Specification](MeetingAI_Master_Use_Case_Specification.xlsx), business flows and exceptions.
3. **DB** — [Database Design](MeetingAI_Master_Database_Design.xlsx), tables/columns/relationships.
4. **API** — [API Contract](MeetingAI_Master_API_Contract.xlsx), backend interface.
5. **UI** — [UI Page Flow](MeetingAI_Master_UI_Page_Flow.xlsx), screens/navigation.
6. **AI** — [AI IO Contract](MeetingAI_Master_AI_IO_Contract.xlsx), AI input/output.
7. [AGENTS.md](../AGENTS.md), architecture and coding rules.

All six workbooks / 54 worksheets were read without modification. Source references below are retained from the decision review; worksheet row numbers include the header. The [Database Mapping](MeetingAI_Database_Mapping.md) contains all 86 function mappings, current field inventories and actual FK actions.

Implementation reference: [models](../app/models/__init__.py), [initial migration a2be71a104a2](../migrations/versions/a2be71a104a2_create_initial_meetingai_schema.py), and read-only MySQL inspection. Applied revision is a2be71a104a2 (head); model/live schema comparison reports no upgrade operations.

## Outcome

**D01–D12: 12 RESOLVED, 0 NEEDS HUMAN DECISION. S01: RESOLVED.** D03–D12 changed from unresolved to resolved through explicit human approval; D01, D02 and S01 remain resolved. Across all 13 records, 13 are resolved.

RESOLVED denotes an approved design, not completion of its runtime implementation. The remaining implementation work below does not reopen these decisions.

| ID | Topic | Confidence |
| --- | --- | --- |
| D01 | Missing transcript timestamps | RESOLVED |
| D02 | KEY_POINTS-only regeneration | RESOLVED |
| D03 | Separate schema-version provenance | RESOLVED |
| D04 | ASR provenance on transcription jobs | RESOLVED |
| D05 | AI-run foreign-key deletion behavior | RESOLVED |
| D06 | Accepted AI results per section | RESOLVED |
| D07 | Confirmed-review content lock | RESOLVED |
| D08 | Raw/effective text, reset and optimistic concurrency | RESOLVED |
| D09 | One primary evidence reference | RESOLVED |
| D10 | Job locking, checkpoints and recovery | RESOLVED |
| D11 | UTC storage and business timezone | RESOLVED |
| D12 | Filesystem quarantine for meeting deletion | RESOLVED |
| S01 | Nullable action owners and deadlines | RESOLVED |

## Schema amendment reconciliation

The canonical MVP inventory contains 112 columns. The approved additions are already in the current models and initial migration:

| Table | Added field | Implemented MySQL definition | Decision |
| --- | --- | --- | --- |
| processing_jobs | asr_model_name | VARCHAR(120) NULL | D04 |
| processing_jobs | asr_model_version | VARCHAR(120) NULL | D04 |
| processing_jobs | checkpoint_stage | VARCHAR(64) NULL | D10 |
| processing_jobs | checkpoint_data | JSON NULL | D10 |
| processing_jobs | heartbeat_at | DATETIME NULL | D10 |
| ai_runs | schema_version | VARCHAR(50) NULL | D03 |
| ai_runs | is_accepted | TINYINT(1) NOT NULL DEFAULT 0 (Boolean false) | D06 |
| ai_runs | accepted_at | DATETIME NULL | D06 |

**112 + 5 + 3 = 120 application columns in exactly 11 application tables.** D01 changes two existing timestamp bounds to nullable without adding columns; D05 supplies three SET NULL policies without adding columns. All other decisions use existing fields or application behavior. alembic_version is migration bookkeeping and is excluded. No new migration or schema change is proposed by this reconciliation.

The summary model now uses the explicit MySQL LONGTEXT variant. The historical migration expresses it as Text(length=4294967295); the installed MySQL column is LONGTEXT and matches the repaired model. The migration is unchanged.

## D01 — Missing transcript timestamps

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D01 |
| 2. Problem | Missing timestamps must coexist with strict ordering for known intervals. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F042 (row 30), F060; UC / USE_CASE_SPECS UC10 (row 7); DB / COLUMNS transcript_segments.start_ms and end_ms (rows 50–51); API / RESPONSE_SCHEMAS TranscriptSegment timestamps (rows 24–25) and Evidence timestamps (rows 56–57); AI / INPUT_SCHEMA rows 15–16; UI / PAGE_COMPONENTS C062 and C074. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | FD > UC > DB > API > UI > AI; the human reaffirmed the nullable choice. |
| 5. Chosen design | Use nullable start_ms/end_ms, retaining each known boundary. Require start_ms < end_ms when both are known; never fabricate zero timestamps. A real start of zero is valid with a positive end. |
| 6. Reason | FD F042 permits missing bounds and requires strict ordering; this preserves speech without inventing timing. |
| 7. Database impact | Both INT UNSIGNED columns are nullable in the model and initial migration, with no zero server default. This changes nullability/defaults only, adding no columns. Strict ordering is an application requirement, not an existing SQL CHECK. |
| 8. API impact | Transcript and evidence timestamps permit null; reject equal/reversed known bounds when validation is implemented. |
| 9. AI/pipeline impact | Preserve segment order/text/refs for untimed speech; do not fabricate times to satisfy older AI input schemas. |
| 10. Edge cases | Both missing; exactly one missing; valid 0-to-positive interval; known equal or reversed bounds; untimed segment between timed segments; evidence without a seekable range. No timestamp seeking can be derived from an unknown boundary; audio seeking itself remains advanced scope. |
| 11. Changes the 11-table MVP schema? | YES relative to the workbook: two existing column definitions; 11 tables unchanged. |
| 12. Confidence | RESOLVED |

## D02 — KEY_POINTS-only regeneration

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D02 |
| 2. Problem | Lower-priority API section lists exceed the MVP regeneration scope and available run types. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F094 (row 60), F073 and F081–F082; UC / USE_CASE_SPECS UC19 (row 16, alternative flow); DB / COLUMNS ai_runs.run_type (row 61); API / API_ENDPOINTS A080 (row 45), REQUEST_FIELDS A080 (row 23), A063 sections (row 15), A100–A102; UI / PAGE_COMPONENTS C076. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | FD/UC section scope and DB enum outrank broader API lists; human reaffirmed. |
| 5. Chosen design | MVP section-only regeneration supports SUMMARY, DECISIONS and ACTION_ITEMS. Key points come from FULL runs or manual management. Do not add KEY_POINTS or disguise a key-points-only operation as FULL. RISKS and OPEN_QUESTIONS remain advanced even though their enum values exist. |
| 6. Reason | Preserves FD F094 and UC19 scope without silently removing full-run key points or manual CRUD. |
| 7. Database impact | No schema change. ai_runs.run_type currently contains FULL, SUMMARY, DECISIONS, ACTION_ITEMS, RISKS, OPEN_QUESTIONS, and no KEY_POINTS. |
| 8. API impact | Future A080 and selected-section A063 validation must follow the three supported MVP section types; unsupported values use the contract's invalid-section behavior. |
| 9. AI/pipeline impact | Text-only regeneration uses the effective transcript without rerunning ASR; failed regeneration preserves accepted output. |
| 10. Edge cases | A key_points-only request; a full run with key_points=[]; a mixed request containing unsupported selections; human-added key points; advanced risks/open_questions disabled. Do not mislabel unsupported subsets as FULL or delete unrelated sections. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## D03 — Separate schema-version provenance

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D03 |
| 2. Problem | Runs need durable schema provenance independent of model, dataset and prompt versions. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F085, F143, F150–F152; UC / BUSINESS_RULES BR17 (row 18); DB / COLUMNS ai_runs.model_name/model_version/dataset_version/prompt_version (rows 62–65, prompt_version description: 'Version prompt/schema.'); AI / README row 11, OUTPUT_SCHEMA row 2, DB_MAPPING row 12, VERSIONING rows 2 and 6, VALIDATION_RULES V002. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Explicit human amendment resolves the DB prompt/schema wording; FD/UC provenance requirements remain controlling. |
| 5. Chosen design | Store ai_runs.schema_version VARCHAR(50) NULL. prompt_version identifies the prompt, schema_version the input/output schema, model_version the model artifact, and dataset_version the dataset. Never overload one to stand for another. |
| 6. Reason | An explicit field preserves recoverable schema identity across independent prompt/model/schema changes. |
| 7. Database impact | schema_version exists in model and migration: one added nullable column. Existing model_name/model_version and nullable dataset_version/prompt_version are retained. |
| 8. API impact | No new endpoint is implied. Any exposed provenance must reflect the actual run and supported schema. |
| 9. AI/pipeline impact | Record truthful versions from the actual backend configuration/artifacts; validate supported schemas rather than trusting model-generated provenance. |
| 10. Edge cases | Two prompts share one schema; schema changes without a model change; old runs after deployment; unavailable historical config; unknown dataset version; model-supplied fake metadata. |
| 11. Changes the 11-table MVP schema? | YES relative to the workbook: one column in ai_runs; no table added. |
| 12. Confidence | RESOLVED |

## D04 — ASR provenance on transcription jobs

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D04 |
| 2. Problem | ASR provenance needs persistence without misclassifying transcription as NLP inference. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F041 (row 29), F085, F152; UC / USE_CASE_SPECS UC10; DB / COLUMNS transcript_segments rows 46–58, ai_runs rows 59–71, processing_jobs.job_type row 30; AI / INFERENCE_FLOW and VERSIONING. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human selects the storage location required by FD F041; actual models/migration establish the VARCHAR(120) widths. |
| 5. Chosen design | Store the actual ASR model name and version on processing_jobs for TRANSCRIBE jobs. Do not represent ASR as an ai_runs NLP run. |
| 6. Reason | Associates provenance with transcription attempts while keeping ASR and downstream NLP distinct. |
| 7. Database impact | asr_model_name and asr_model_version both exist as VARCHAR(120) NULL in model/migration. Two added columns; no segment/run FK or ASR run_type added. |
| 8. API impact | No additional provenance endpoint is introduced by this decision. |
| 9. AI/pipeline impact | Record provenance for the transcription attempt. Text-only reanalysis must not rewrite raw ASR provenance. Producing these records is future pipeline work. |
| 10. Edge cases | ASR retry with another model; partial transcript before failure; user-edited text; no subsequent NLP run; multiple ASR attempts for one meeting. |
| 11. Changes the 11-table MVP schema? | YES relative to the workbook: two columns in processing_jobs; no table added. |
| 12. Confidence | RESOLVED |

## D05 — AI-run foreign-key deletion behavior

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D05 |
| 2. Problem | The workbook omits delete actions for three nullable output ai_run_id foreign keys. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F034, F085, F116; UC / USE_CASE_SPECS UC20 and UC25; DB / COLUMNS key_points.ai_run_id row 81, decisions.ai_run_id row 89, action_items.ai_run_id row 99; RELATIONSHIPS row 10 (summaries.ai_run_id SET NULL) and meeting-child CASCADE rows; API / API_ENDPOINTS A024 and A071. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Explicit human choice fills DB RELATIONSHIPS omissions; all other documented delete actions remain. |
| 5. Chosen design | Use ON DELETE SET NULL for key_points.ai_run_id, decisions.ai_run_id and action_items.ai_run_id. summaries.ai_run_id already uses SET NULL. Removing a run preserves output rows; deleting the meeting still cascades through its owned rows. |
| 6. Reason | Preserves usable results when run provenance is removed while retaining meeting-wide deletion. |
| 7. Database impact | All four nullable output ai_run_id FKs use SET NULL in models, migration and live MySQL. No new columns; no output cascade from an AI run. |
| 8. API impact | No run-delete endpoint is implied. A null run link is not proof that a row was human-created: SET NULL can also remove a generated row's provenance. |
| 9. AI/pipeline impact | Retry/failure is not permission to remove accepted runs. Preserve independent manual rows under D06. |
| 10. Edge cases | Deleting a run with human-edited outputs; meeting-wide cascade; failed run with partial data; references already null; mixed summary/key-point/action dependencies. |
| 11. Changes the 11-table MVP schema? | YES relative to incomplete workbook relationship specifications: three FK actions selected; no count change. |
| 12. Confidence | RESOLVED |

## D06 — Accepted AI results per section

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D06 |
| 2. Problem | Multiple full/section runs must not let a failed or unaccepted attempt displace accepted content. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F064, F090–F094, F096; UC / USE_CASE_SPECS UC19 row 16 and UC20 row 17; DB / TABLES_OVERVIEW summaries row 8, COLUMNS output ai_run_id/is_user_edited fields, INDEXES idx_summaries_meeting; API / API_ENDPOINTS A072/A080, RESPONSE_SCHEMAS MeetingMinutes; AI / DB_MAPPING row 2 and INFERENCE_FLOW steps 9–10. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human selects acceptance storage/semantics; FD F064/F094 and UC failure preservation/replacement confirmation still apply. |
| 5. Chosen design | Use is_accepted NOT NULL DEFAULT false and nullable accepted_at. Select the newest accepted eligible run separately for each meeting section: summary FULL/SUMMARY; key_points FULL; decisions FULL/DECISIONS; action_items FULL/ACTION_ITEMS. Failed or unaccepted runs never replace current results. Human-created rows with ai_run_id NULL remain independent. |
| 6. Reason | Separates successful inference from acceptance and preserves mixed-section results and manual content. |
| 7. Database impact | is_accepted is physically TINYINT(1) NOT NULL DEFAULT 0 (the Boolean false representation); accepted_at is DATETIME NULL. Both exist. No active-run pointer, snapshot, or version table. No database check currently enforces acceptance/status consistency. |
| 8. API impact | Current-minute reads must apply section eligibility; replacement still respects user-edited content confirmation and D07. This decision does not invent an acceptance endpoint. |
| 9. AI/pipeline impact | Persist validated section output and task owners transactionally; accept only eligible nonfailed results. Select the run before reading its rows, so an accepted empty decisions/tasks/key-points result does not fall back to older nonempty AI output. |
| 10. Edge cases | New decisions=[] replacing old decisions; human-added row with null ai_run_id; equal created_at values; failed/latest run; successful but unaccepted preview; concurrent user edit; summary and tasks from different accepted runs. |
| 11. Changes the 11-table MVP schema? | YES relative to the workbook: two ai_runs columns; no table added. |
| 12. Confidence | RESOLVED |

## D07 — Confirmed-review content lock

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D07 |
| 2. Problem | Confirmation must protect content while allowing task execution tracking. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F061, F093 (row 59), F095 (row 61), F096, F101 (row 64); UC / USE_CASE_SPECS UC19–UC22 (rows 16–19), BUSINESS_RULES BR15; DB / COLUMNS meetings.review_status row 16, transcript_segments rows 46–58, action_items.task_status row 103; API / STATE_TRANSITIONS Review row 9, A081 and A091; UI / PAGE_STATES Minutes CONFIRMED row 13. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human chooses the F095 locking policy and its task-status exception; advanced F096 remains deferred. |
| 5. Chosen design | When meetings.review_status = CONFIRMED, block summary/key-point/decision editing, transcript editing, and AI regeneration/reanalysis. Action-item execution status may still change. Do not silently mutate confirmed content; this status exception does not grant permission to rewrite task content/owners/deadlines. Post-confirmation version editing is advanced scope. |
| 6. Reason | Uses the approved read-only option without disabling ongoing action-item execution. |
| 7. Database impact | Uses existing meetings.review_status and action_items.task_status. No transcript-final flag, final-transcript table, minute-version table, or automatic reopen state added. |
| 8. API impact | Future mutation services must enforce the boundary, including concurrent publication; no new unconfirm/version endpoint or invented error contract is declared here. |
| 9. AI/pipeline impact | A late-completing run cannot silently replace confirmed content. Confirmation is a review state, separate from processing status. |
| 10. Edge cases | Marking a confirmed meeting task DONE; correcting a speaker/transcript used as evidence; changing a deadline; regenerating a confirmed summary; repeated confirmation; viewing confirmed minutes after task edits. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## D08 — Raw/effective text, reset and optimistic concurrency

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D08 |
| 2. Problem | Transcript edits must preserve raw ASR output and avoid silent stale overwrites. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F043 (row 31), F061 (row 36), F064; UC / BUSINESS_RULES BR05–BR06, USE_CASE_SPECS UC17 row 14, EXCEPTION_MATRIX EX11; DB / COLUMNS raw_text/edited_text/is_user_edited/updated_at rows 52–58; API / API_ENDPOINTS A061/A063, REQUEST_FIELDS A061 row 14; AI / INPUT_SCHEMA row 17; UI / FORM_FIELDS row 13. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human supplies the missing mutation/concurrency policy; FD/UC raw preservation and DB NULL semantics remain. |
| 5. Chosen design | raw_text is immutable. Effective text = edited_text when edited_text IS NOT NULL, else raw_text. Reject blank/whitespace-only edits. Explicit reset_to_raw=true sets edited_text=NULL and is_user_edited=false. Compare expected_updated_at for optimistic conflicts; stale writes return HTTP 409. Do not add a version column. |
| 6. Reason | Preserves original evidence and intentional reset semantics while protecting concurrent edits. |
| 7. Database impact | Existing raw_text, edited_text, is_user_edited and updated_at suffice. TranscriptSegment.effective_text already implements the NULL check; mutation validation/reset/conflict detection are not implemented. |
| 8. API impact | A061 must implement explicit reset and expected_updated_at in addition to text editing; this approved extension supersedes the workbook's older string-only request description. D07 blocks edits/resets after confirmation. |
| 9. AI/pipeline impact | Reanalysis consumes effective saved text without rerunning ASR. Do not use truthiness fallback for a legacy empty-string value. |
| 10. Edge cases | Never-edited segment; edited_text equal to raw_text; empty/whitespace edit; reset attempt; two browser tabs editing the same segment; reanalysis while an edit is pending. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## D09 — One primary evidence reference

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D09 |
| 2. Problem | AI may emit many refs while the MVP persists one nullable primary reference. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F079 (row 49), F083; UC / BUSINESS_RULES BR09 and EXCEPTION_MATRIX EX12; DB / COLUMNS evidence_segment_id fields and RELATIONSHIPS evidence SET NULL rows; AI / DB_MAPPING rows 3–4, 6 and 9, MERGE_RULES MG07, OUTPUT_SCHEMA evidence_refs fields, VALIDATION_RULES V004; API / RESPONSE_SCHEMAS Evidence.text row 59. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human defines the selector/text policy; FD F079/F083 and UC nullable evidence outrank stricter AI minimum-ref examples. |
| 5. Chosen design | AI evidence refs are ordered strongest-first. Backend validates existence, trustworthiness and same-meeting membership, and persists the first valid same-meeting ref; if none is trustworthy, store NULL. Never fabricate evidence. API evidence text uses current effective transcript text. |
| 6. Reason | Fits the canonical primary-FK representation while preserving grounded output without invented evidence. |
| 7. Database impact | Existing nullable evidence_segment_id on key_points, decisions and action_items suffices; all use ON DELETE SET NULL. No evidence table, full-reference column, or historical text snapshot. |
| 8. API impact | Return nullable evidence and nullable bounds under D01. Linked text reflects subsequent valid transcript edits, not a frozen inference-time quote. |
| 9. AI/pipeline impact | Drop invalid/cross-meeting candidates and keep strongest-first ordering. Grounded but unlinked cases may store null; hallucinated claims remain invalid. |
| 10. Edge cases | Several equally relevant refs; corrected owner/deadline across chunks; no surviving valid ref; human-created item without evidence; deleted source segment; untimed source; later transcript edit changes a linked statement. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## D10 — Job locking, checkpoints and recovery

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D10 |
| 2. Problem | Retries and interrupted workers need persistent checkpoints and atomic conflict prevention. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F030–F034 (rows 23–27), F040 and F132; UC / USE_CASE_SPECS UC15 row 12, FLOW_STEPS UC15 rows 18–19, BUSINESS_RULES BR13–BR14, SCENARIO_CHECKLIST SC009; DB / TABLES_OVERVIEW processing_jobs row 4, COLUMNS rows 28–38; API / A040–A042, STATE_TRANSITIONS row 8; UI / PAGE_CATALOG P006 and USER_FLOWS UF02. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human chooses meeting-row locks and existing-table checkpoint storage; FD/UC preservation/retry requirements remain. |
| 5. Chosen design | Keep processing_jobs. Use transactional locking of the meeting row to prevent conflicting active jobs. Checkpoint stages: UPLOADED, AUDIO_NORMALIZED, TRANSCRIBED, DIARIZED, ANALYZED. Retry from the nearest valid checkpoint; stale RUNNING jobs become interrupted/failed and may be retried. |
| 6. Reason | Preserves successful work without a second queue/checkpoint table or uncontrolled duplicate results. |
| 7. Database impact | checkpoint_stage VARCHAR(64) NULL, checkpoint_data JSON NULL and heartbeat_at DATETIME NULL already exist. Stage names are application values, not a database enum. Job status has FAILED, not INTERRUPTED; interruption must be represented without claiming an extra enum value. |
| 8. API impact | Preserve A040/A042 asynchronous behavior, busy/retry checks and failure-safe status reporting. No additional worker-control endpoint is implied. |
| 9. AI/pipeline impact | Checkpoint validity must include required artifacts/results, not merely a stage string or one segment row. Preserve committed earlier stages; missing/invalid checkpoints fall back to a valid earlier stage. Locking, heartbeat updates, retry and recovery remain to implement. |
| 10. Edge cases | Two simultaneous starts; queued versus running conflict; worker dies before/after stage persistence; lost normalized file; partial transcript; retry fails again; browser closes; database unavailable during status update. |
| 11. Changes the 11-table MVP schema? | YES relative to the workbook: three processing_jobs columns; no table added. |
| 12. Confidence | RESOLVED |

## D11 — UTC storage and business timezone

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D11 |
| 2. Problem | Timezone-less storage and relative calendar rules need a consistent application policy. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F078 (row 48), F102 (row 65); UC / BUSINESS_RULES BR11, SCENARIO_CHECKLIST SC016; DB / COLUMNS meetings.meeting_date row 13 and action_items.deadline_normalized row 102; API / README time row 7, REQUEST_FIELDS meeting_date row 7, RESPONSE_SCHEMAS ActionItem.overdue row 51; AI / INPUT_SCHEMA meeting_date row 6, VALIDATION_RULES V009–V010, HARD_CASE_EXPECTATIONS HC17. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human selects UTC/Asia/Ho_Chi_Minh; FD F102 status != DONE outranks API's extra CANCELLED exclusion. |
| 5. Chosen design | Store application DATETIME values as UTC. API timestamp inputs/outputs use ISO-8601 with offsets. APP_TIMEZONE = Asia/Ho_Chi_Minh for MVP business-time interpretation; relative deadlines and today use that zone. deadline_normalized remains DATE. Overdue = deadline < today AND status != DONE; a null deadline is not overdue. |
| 6. Reason | Separates absolute instants from local calendar dates and preserves the approved higher-priority overdue rule, including overdue CANCELLED tasks. |
| 7. Database impact | No timezone column or type conversion. Existing TIMESTAMP audit fields remain TIMESTAMP; their database session conversion must be handled consistently rather than assumed to be UTC. No fields added. |
| 8. API impact | Normalize offset-bearing input to UTC; return timestamp offsets. Do not append a UTC label to an unverified local timestamp. The existing /api/auth/me created_at lacks an offset and remains a code gap. |
| 9. AI/pipeline impact | Ground relative deadlines using sufficient meeting context in APP_TIMEZONE; preserve ambiguous raw phrases and null normalized dates when context is insufficient. |
| 10. Edge cases | Meeting near midnight; users in different zones; offset-bearing input saved into DATETIME; missing meeting_date; ambiguous 'Friday'; DST if relevant to the chosen zone; null deadline; CANCELLED task past its deadline. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## D12 — Filesystem quarantine for meeting deletion

| Record field | Decision |
| --- | --- |
| 1. Decision ID | D12 |
| 2. Problem | Database rollback alone cannot recover an already-unlinked audio file. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F116–F117 (rows 73–74), F142, F144; UC / USE_CASE_SPECS UC25 row 22, FLOW_STEPS rows 35–38, BUSINESS_RULES BR16, EXCEPTION_MATRIX EX15; DB / RELATIONSHIPS meeting cascades, COLUMNS meetings.audio_path/audio_deleted_at; API / API_ENDPOINTS A024 row 17; UI / USER_FLOWS UF09. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | Human chooses quarantine/commit ordering; FD/UC safe deletion, privacy and recovery constraints remain. |
| 5. Chosen design | Validate every path stays under the configured storage root. Move audio to private storage/temp/deleting before transactional DB deletion. After commit unlink quarantined audio; on rollback restore it. Startup recovery scans quarantine: meeting exists -> restore; meeting absent -> remove quarantined file. No soft-delete/deletion-log table. |
| 6. Reason | Provides the approved compensating filesystem protocol using the existing database ownership graph. |
| 7. Database impact | Retain existing cascades and audio path fields; audio_deleted_at is not repurposed as a deletion journal. No additional table/column. Database cascades alone do not implement file deletion or recovery. |
| 8. API impact | Keep ownership/confirmation and processing-busy checks from UC25/A024; tolerate an already-missing file as documented. No new partial-success endpoint contract is invented. |
| 9. AI/pipeline impact | Coordinate deletion with job conflict prevention. File operations, post-commit cleanup and startup recovery are future implementation, not effects of SQLAlchemy relationships. |
| 10. Edge cases | Audio already absent; file locked/access denied; DB rollback after file deletion; DB commit followed by crash before unlink; path traversal; associated derived audio; simultaneous process start; repeated delete after an uncertain response. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## S01 — Nullable action owners and deadlines

| Record field | Decision |
| --- | --- |
| 1. Decision ID | S01 |
| 2. Problem | Unknown owners/deadlines must not produce fake people or guessed dates. |
| 3. Relevant canonical sources | FD / FUNCTION_DATASET F076–F078, F083, F093; UC / BUSINESS_RULES BR07, BR11–BR12; DB / COLUMNS action_items.deadline_raw/deadline_normalized rows 101–102, action_item_owners rows 109–113; API / REQUEST_FIELDS owners/deadlines rows 19–21, RESPONSE_SCHEMAS ActionItem.owners/Owner; AI / OUTPUT_SCHEMA owners/deadline fields, DB_MAPPING row 8, FINAL_STATE_RULES FS05–FS08. Human-approved D01–D12/S01 supplied in the project instructions. |
| 4. Source priority used | FD/UC unknown-owner, deadline-preservation and multiple-owner requirements outrank contradictory lower AI examples; human reaffirmed. |
| 5. Chosen design | Unknown owner means owners=[] and zero action_item_owners rows. Real owner_name is non-empty; speaker_id may be NULL. Support multiple grounded owners. deadline_raw and deadline_normalized are independently nullable; preserve ambiguous raw deadline phrases even when no normalized date can be grounded. |
| 6. Reason | Represents missing information with existing nullable fields and zero child rows instead of fabricated data. |
| 7. Database impact | Existing action_item_owners.owner_name is NOT NULL, speaker_id nullable; both deadline fields nullable. Non-empty/grounding validation is future service work, not an existing SQL CHECK. |
| 8. API impact | Return owners=[] for unknown ownership, not a fake Unknown person. A real owner object requires a name; date absence uses null. |
| 9. AI/pipeline impact | Do not infer an owner from the nearest speaker or force deadline normalization. Keep final-state/reassignment rules and uncertainty required by FD. |
| 10. Edge cases | Explicit task but no assignee; team/external owner not in speakers; two owners; owner reassigned; 'do it soon'; absent meeting_date for relative deadline; no action items at all. |
| 11. Changes the 11-table MVP schema? | NO. |
| 12. Confidence | RESOLVED |

## Approved behavior versus current implementation

| Area | Current evidence / remaining implementation work |
| --- | --- |
| D01 intervals | Nullable unsigned bounds exist. Neither model nor migration enforces start_ms < end_ms when both are known. Future validation must enforce it; nullability alone is not compliance. |
| D02–D04 provenance/scope | Enum and version columns exist. Regeneration scope validation and ASR/NLP provenance writing are not implemented. |
| D05 deletion | All specified FK actions exist. User.meetings, Meeting child collections and ActionItem.owners use passive_deletes="all", so MySQL cascades also handle loaded children. SET NULL relationships use passive_deletes=True. Loaded ORM objects can need expiration after database-side deletion; services must not reuse stale objects as persisted results. File deletion is separate under D12. |
| D06 accepted output | Acceptance fields exist; section selection/publication, acceptance timestamps and replacement-confirmation logic do not. "Newest accepted eligible run" is the approved rule; no implemented ordering/tie-break algorithm or acceptance API is claimed. SET NULL can erase a generated row's run link, so NULL alone does not prove human origin. |
| D07 review lock | review_status exists; confirmed-content locks and the execution-status exception are not implemented by any meeting/minutes service. |
| D08 transcript mutations | effective_text property correctly checks IS NOT NULL. Raw immutability, nonblank validation, reset_to_raw, expected_updated_at and HTTP 409 behavior are still absent. updated_at is currently second-precision TIMESTAMP; future concurrency implementation must demonstrate that same-second edits cannot silently evade stale-write detection without adding a version column. |
| D09 evidence | Single nullable FKs and SET NULL exist. Same-meeting/trust validation, strongest-first selection and effective-text API projection are not implemented; a simple FK does not enforce meeting identity. |
| D10 recovery | Checkpoint/heartbeat fields exist; transactional job claiming, stage validation, heartbeat/stale-job handling and checkpoint recovery do not. JSON structure, artifact validation and stale timing need concrete implementation/verification; no undocumented durable fields or extra status enums are claimed. |
| D11 time | config.py has no APP_TIMEZONE; inspected MySQL session time_zone is SYSTEM. UTC conversion/session discipline is not configured. auth_service.user_data emits created_at.isoformat() without an offset. DATETIME/TIMESTAMP type declarations alone do not guarantee the approved policy. |
| D12 quarantine | Cascades exist; containment checks, quarantine/rollback restore, post-commit unlink and startup recovery do not. The filesystem association needed to restore a quarantined file must be implemented and tested without adding a table. |
| S01 validation | Nullable deadlines/speaker FK and zero owner rows are supported. Non-empty owner names and grounded deadline/owner validation are not SQL constraints and remain service/pipeline work. |
| Workbook index annotations | DB COLUMNS marks summaries.is_user_edited and key_points.sort_order as indexed, but no corresponding indexes exist in models/migration/live MySQL. This discrepancy is recorded, not silently represented as implemented. Optional full-text indexes are also not implemented and remain optional. |

These are implementation gaps or unchanged workbook differences, not unresolved D01–D12 approvals. This documentation-only task does not add enforcement, choose new API endpoints, modify schema, or start Phase 3B.

## Remaining canonical differences

The Excel sources remain unchanged. Apply the approved decisions rather than their superseded annotations:

- D01: DB/API/AI non-null timestamps and AI equal-bound allowance conflict with nullable bounds and strict known start < end.
- D02: broader API section lists conflict with MVP SUMMARY/DECISIONS/ACTION_ITEMS-only regeneration.
- D03/D04/D06/D10: workbook inventories omit the eight approved additions; DB's combined prompt/schema description is superseded by separate version meanings.
- D05: workbook RELATIONSHIPS omits three output-to-run actions now explicitly SET NULL.
- D07: broad editing workflows are constrained after confirmation; only action-item execution status is exempt. Advanced version editing is not an MVP workaround.
- D08: older A061 request fields omit the approved reset_to_raw and expected_updated_at semantics.
- D09: stricter AI minimum-evidence examples cannot force fabricated references or override nullable evidence.
- D11: API's extra CANCELLED exclusion conflicts with FD F102 and the approved status != DONE rule. UTC/APP_TIMEZONE policy fills the prior timezone omission.
- S01: preserve ambiguous deadline_raw under UC BR11; lower-priority examples must not discard it or fabricate owners/force unjustified confidence.

No new table, column or unapproved feature is introduced to hide these differences.

## Validation and scope

The mapping inventories were compared with all model columns, migration create_table declarations and live MySQL metadata. The 11-table / 120-column totals exclude alembic_version. All D01–D12 and S01 records retain the twelve review fields. Only the two internal Markdown files are updated; no workbooks, models, migrations, routes, services, tests or application behavior are changed.

## Canonical workbook fingerprints

| Workbook | SHA-256 |
| --- | --- |
| MeetingAI_Master_AI_IO_Contract.xlsx | 91D8323D0E5F9A639A4C5378604E2F10DCB231B9797A64FA0807523D78BF8758 |
| MeetingAI_Master_API_Contract.xlsx | 4F40DB01C7679E81BF94416F0F95B44157BF67AFA033EFDEF13714B80B7CB04E |
| MeetingAI_Master_Database_Design.xlsx | 60BD53385B1640F4F06B565DDA1B2B810600523BC15A6B760E5C82C33111E227 |
| MeetingAI_Master_Function_Dataset.xlsx | 32325DC1FD80F6C51FADFD11F95869B4BC4007AB60D7D41D48F84C7C4F27922F |
| MeetingAI_Master_UI_Page_Flow.xlsx | 61E60E0291CAEC9C83FECBC25709DB7030CCBB355E8AAB1C9CAB76B7250CD159 |
| MeetingAI_Master_Use_Case_Specification.xlsx | 28D2AB9FAA489D55A0BCA8B4B9A0AEDA269DF08E68E1758E1A6D37932F883822 |
