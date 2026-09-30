# MeetingAI database mapping — Phase 1.6 reconciliation

Reviewed: 2026-09-30. Documentation-only reconciliation with approved decisions, current SQLAlchemy models, initial migration a2be71a104a2 and live MySQL. The schema is already implemented; service/pipeline rules below are requirements unless explicitly identified as working code. No application code or database changes are made in this task.

## Sources and precedence

Reread on 2026-09-30, including all 54 worksheets. Resolve functional scope before implementation detail:

1. [Master Function Dataset](MeetingAI_Master_Function_Dataset.xlsx) — FUNCTION_DATASET: 86 functions, 74 MVP and 12 advanced.
2. [Use Case Specification](MeetingAI_Master_Use_Case_Specification.xlsx) — business flows, BUSINESS_RULES, EXCEPTION_MATRIX.
3. [Database Design](MeetingAI_Master_Database_Design.xlsx) — TABLES_OVERVIEW, COLUMNS, RELATIONSHIPS, ENUMS, INDEXES, MIGRATION_ORDER.
4. [API Contract](MeetingAI_Master_API_Contract.xlsx) — API_ENDPOINTS, REQUEST_FIELDS, RESPONSE_SCHEMAS, STATE_TRANSITIONS.
5. [UI Page Flow](MeetingAI_Master_UI_Page_Flow.xlsx) — page/component actions and states.
6. [AI IO Contract](MeetingAI_Master_AI_IO_Contract.xlsx) — inputs, outputs, validation, mapping and versioning.

[AGENTS.md](../AGENTS.md) governs the fixed stack and existing layered architecture. Explicit human-approved D01–D12 and S01 amend the derived design as recorded in [Architecture Decisions](MeetingAI_Architecture_Decisions.md). Otherwise the source priority above applies. This document distinguishes actual schema from approved future runtime behavior. Source hashes appear below.

## Model-file mapping and schema boundary

Exactly 11 application tables exist. Speaker is implemented in participant.py with table speakers; TranscriptSegment is in transcript.py. There is no participants table. All classes are registered in app/models/__init__.py and imported by the app factory before migration initialization, using db from app/extensions.py.

| Table | Class | Model file | Original columns | Approved additions | Current columns |
| --- | --- | --- | --- | --- | --- |
| users | User | app/models/user.py | 7 | 0 | 7 |
| meetings | Meeting | app/models/meeting.py | 19 | 0 | 19 |
| processing_jobs | ProcessingJob | app/models/processing_job.py | 11 | 5 | 16 |
| speakers | Speaker | app/models/participant.py | 7 | 0 | 7 |
| transcript_segments | TranscriptSegment | app/models/transcript.py | 13 | 0 | 13 |
| ai_runs | AIRun | app/models/ai_run.py | 13 | 3 | 16 |
| summaries | Summary | app/models/summary.py | 7 | 0 | 7 |
| key_points | KeyPoint | app/models/key_point.py | 8 | 0 | 8 |
| decisions | Decision | app/models/decision.py | 10 | 0 | 10 |
| action_items | ActionItem | app/models/action_item.py | 12 | 0 | 12 |
| action_item_owners | ActionItemOwner | app/models/action_item_owner.py | 5 | 0 | 5 |
| **Total** | **11 application tables** | All implemented | **112** | **8** | **120** |

alembic_version is migration bookkeeping and is not included. The applied revision is [a2be71a104a2](../migrations/versions/a2be71a104a2_create_initial_meetingai_schema.py) (head). No migration is required by this documentation update.

Advanced risks, open_questions, minute_versions and password_reset_tokens tables are deferred and do not exist in the MVP. No separate participants, transcript-final/version, evidence, queue/checkpoint, deletion-log, sessions or deadline table is introduced.

## Approved schema amendments already implemented

| Table | Column / constraint | Current definition | Decision |
| --- | --- | --- | --- |
| processing_jobs | asr_model_name | VARCHAR(120) NULL | D04 |
| processing_jobs | asr_model_version | VARCHAR(120) NULL | D04 |
| processing_jobs | checkpoint_stage | VARCHAR(64) NULL | D10 |
| processing_jobs | checkpoint_data | JSON NULL | D10 |
| processing_jobs | heartbeat_at | DATETIME NULL | D10 |
| ai_runs | schema_version | VARCHAR(50) NULL | D03 |
| ai_runs | is_accepted | TINYINT(1) NOT NULL DEFAULT 0; Boolean false | D06 |
| ai_runs | accepted_at | DATETIME NULL | D06 |
| transcript_segments | start_ms, end_ms | INT UNSIGNED NULL; no fabricated zero default | D01; no new columns |
| key_points, decisions, action_items | ai_run_id foreign keys | ON DELETE SET NULL | D05; no new columns |

The eight additions produce 112 + 5 + 3 = 120 columns. D01's strict interval rule remains to be enforced by application validation; no existing CHECK is claimed. All other decisions fit existing columns and require runtime behavior rather than extra schema.

## Function-to-database mapping

One row per canonical function, retaining its scope. Tables omitted from a function's shorthand DB column are included when a higher-level flow and the canonical database require them (for example processing_jobs for retry, ai_runs for regeneration, and action_item_owners for multiple owners). These are traceability mappings, not additional schema.

The fields column names the principal fields for the function. Every MVP field's type, nullability, default, keys and FK target is listed in the table inventories below. Relationship references R(table) and constraint references C(table) refer to those table sections; they are part of each row's mapping. For deferred tables only, R(table) and C(table) refer to Database Design / RELATIONSHIPS and COLUMNS; no advanced table inventory or model is proposed in this phase. Global service constraints apply in addition to SQL constraints.

| Function ID | Function / scope | Table(s) | Fields | Relationships | Constraints | Model file(s) |
| --- | --- | --- | --- | --- | --- | --- |
| F001 | Xem Landing Page — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không hiển thị dữ liệu riêng tư. | None — UI/service/config responsibility |
| F002 | Đăng ký tài khoản — MVP | users | users.id, full_name, email, password_hash, is_active | R(users) | Email unique; password không lưu plain text.; C(users) | app/models/user.py |
| F003 | Đăng nhập — MVP | users | users.id, full_name, email, password_hash, is_active | R(users) | Không tiết lộ email có tồn tại hay không qua lỗi chi tiết.; C(users) | app/models/user.py |
| F004 | Đăng xuất — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Sau logout không truy cập được trang riêng tư. | None — UI/service/config responsibility |
| F005 | Bảo vệ route theo session — MVP | users | users.id, full_name, email, password_hash, is_active | R(users) | Áp dụng cho mọi meeting/history/profile API.; C(users) | app/models/user.py |
| F006 | Xem/cập nhật hồ sơ — MVP | users | users.id, full_name, email, password_hash, is_active | R(users) | Không cho sửa user_id; email unique.; C(users) | app/models/user.py |
| F007 | Đổi mật khẩu — MVP | users | users.id, full_name, email, password_hash, is_active | R(users) | Hash password; yêu cầu độ dài tối thiểu.; C(users) | app/models/user.py |
| F008 | Quên mật khẩu — Nâng cao | users, password_reset_tokens | Deferred: users.email; password_reset_tokens.token_hash, expires_at, used_at, user_id | R(users); R(password_reset_tokens) | Token có thời hạn, dùng 1 lần.; C(users); C(password_reset_tokens) | app/models/user.py; Deferred: no MVP model |
| F010 | Xem Dashboard — MVP | meetings, action_items | meetings.user_id, status, created_at; action_items.meeting_id, task_status, deadline_normalized | R(meetings); R(action_items) | Chỉ dữ liệu của user hiện tại.; C(meetings); C(action_items) | app/models/meeting.py; app/models/action_item.py |
| F011 | Thống kê cuộc họp — MVP | meetings | meetings.user_id, title, status, created_at | R(meetings) | Không tính meeting của user khác.; C(meetings) | app/models/meeting.py |
| F012 | Xem cuộc họp gần đây — MVP | meetings | meetings.user_id, title, status, created_at | R(meetings) | Giới hạn số bản ghi hiển thị.; C(meetings) | app/models/meeting.py |
| F013 | Tạo cuộc họp mới từ Dashboard — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | - | None — UI/service/config responsibility |
| F020 | Tạo bản ghi cuộc họp — MVP | meetings | meetings.user_id, title, meeting_date, language, description, status, updated_at | R(meetings) | meeting thuộc user hiện tại.; C(meetings) | app/models/meeting.py |
| F021 | Sửa metadata / đổi tên cuộc họp — MVP | meetings | meetings.user_id, title, meeting_date, language, description, status, updated_at | R(meetings) | Không cho sửa owner user_id.; C(meetings) | app/models/meeting.py |
| F022 | Upload audio bằng chọn file/kéo thả — MVP | meetings | meetings.original_filename, stored_filename, audio_path, mime_type, file_size_bytes, duration_seconds, status, error_code, failed_step | R(meetings) | Không dùng trực tiếp tên file user làm tên lưu.; C(meetings) | app/models/meeting.py |
| F023 | Kiểm tra định dạng file — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Whitelist MP3/WAV; M4A nếu bật. | None — UI/service/config responsibility |
| F024 | Kiểm tra kích thước file — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Giới hạn cấu hình bằng .env/config. | None — UI/service/config responsibility |
| F025 | Kiểm tra file hỏng/không đọc được — MVP | meetings | meetings.original_filename, stored_filename, audio_path, mime_type, file_size_bytes, duration_seconds, status, error_code, failed_step | R(meetings) | Không crash toàn app.; C(meetings) | app/models/meeting.py |
| F026 | Đổi tên file an toàn — MVP | meetings | meetings.original_filename, stored_filename, audio_path, mime_type, file_size_bytes, duration_seconds, status, error_code, failed_step | R(meetings) | Không chứa ../ hoặc path do user kiểm soát.; C(meetings) | app/models/meeting.py |
| F027 | Hiển thị tiến độ upload — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | 0-100%; tách upload và AI processing. | None — UI/service/config responsibility |
| F028 | Upload video và tách audio — Nâng cao | meetings | meetings.original_filename, stored_filename, audio_path, mime_type, file_size_bytes, duration_seconds, status, error_code, failed_step | R(meetings) | Giới hạn duration/size.; C(meetings) | app/models/meeting.py |
| F030 | Khởi tạo job xử lý — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at; processing_jobs.checkpoint_stage, checkpoint_data, heartbeat_at | R(meetings); R(processing_jobs) | Không giữ request HTTP mở nhiều phút.; C(meetings); C(processing_jobs); D10 meeting-row locking and valid-checkpoint recovery (runtime pending) | app/models/meeting.py; app/models/processing_job.py |
| F031 | Theo dõi trạng thái xử lý — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at; processing_jobs.checkpoint_stage, checkpoint_data, heartbeat_at | R(meetings); R(processing_jobs) | Status enum cố định.; C(meetings); C(processing_jobs); D10 meeting-row locking and valid-checkpoint recovery (runtime pending) | app/models/meeting.py; app/models/processing_job.py |
| F032 | Hiển thị progress theo bước — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at; processing_jobs.checkpoint_stage, checkpoint_data, heartbeat_at | R(meetings); R(processing_jobs) | Không hiển thị % giả quá chi tiết nếu không đo được.; C(meetings); C(processing_jobs); D10 meeting-row locking and valid-checkpoint recovery (runtime pending) | app/models/meeting.py; app/models/processing_job.py |
| F033 | Retry bước lỗi — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at; processing_jobs.checkpoint_stage, checkpoint_data, heartbeat_at | R(meetings); R(processing_jobs) | Không tạo trùng bản ghi kết quả không kiểm soát.; C(meetings); C(processing_jobs); D10 meeting-row locking and valid-checkpoint recovery (runtime pending) | app/models/meeting.py; app/models/processing_job.py |
| F034 | Giữ kết quả trung gian khi bước sau lỗi — MVP | meetings, processing_jobs, transcript_segments | meetings.status, failed_step; processing_jobs.status, current_step; transcript_segments.meeting_id, segment_index, raw_text, start_ms, end_ms; processing_jobs.checkpoint_stage, checkpoint_data, heartbeat_at | R(meetings); R(processing_jobs); R(transcript_segments) | Không rollback toàn pipeline khi summarization fail.; C(meetings); C(processing_jobs); C(transcript_segments) | app/models/meeting.py; app/models/processing_job.py; app/models/transcript.py |
| F040 | Tiền xử lý audio bằng FFmpeg — MVP | meetings | meetings.original_filename, stored_filename, audio_path, mime_type, file_size_bytes, duration_seconds, status, error_code, failed_step | R(meetings) | Chuẩn output 16kHz mono WAV hoặc format model yêu cầu.; C(meetings) | app/models/meeting.py |
| F041 | Chuyển audio thành transcript — MVP | transcript_segments, processing_jobs | transcript_segments.meeting_id, segment_index, raw_text, edited_text, start_ms, end_ms, language, asr_confidence, is_user_edited; processing_jobs.job_type, asr_model_name, asr_model_version | R(transcript_segments); R(processing_jobs) | Ưu tiên tiếng Việt; lưu model/version.; C(transcript_segments); C(processing_jobs); D04 TRANSCRIBE provenance | app/models/transcript.py; app/models/processing_job.py |
| F042 | Sinh timestamp theo segment — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, start_ms, end_ms, language, asr_confidence, is_user_edited | R(transcript_segments) | start < end; thứ tự tăng dần.; C(transcript_segments) | app/models/transcript.py |
| F043 | Lưu raw transcript và clean transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, start_ms, end_ms, language, asr_confidence, is_user_edited | R(transcript_segments) | Không ghi đè raw_text khi user sửa.; C(transcript_segments) | app/models/transcript.py |
| F050 | Speaker diarization — MVP | speakers, transcript_segments | speakers.meeting_id, speaker_label, speaker_name; transcript_segments.meeting_id, speaker_id, segment_index, start_ms, end_ms, raw_text, edited_text | R(speakers); R(transcript_segments) | Không bắt buộc pipeline toàn hệ thống fail nếu bước này fail.; C(speakers); C(transcript_segments) | app/models/participant.py; app/models/transcript.py |
| F051 | Gán tên thật cho speaker — MVP | speakers | speakers.meeting_id, speaker_label, speaker_name, is_user_verified, updated_at | R(speakers) | Đổi tên phải áp dụng toàn transcript hiển thị.; C(speakers) | app/models/participant.py |
| F052 | Sửa gán speaker cho segment — Nâng cao | speakers, transcript_segments | speakers.meeting_id, speaker_label, speaker_name; transcript_segments.meeting_id, speaker_id, segment_index, start_ms, end_ms, raw_text, edited_text | R(speakers); R(transcript_segments) | Speaker phải cùng meeting.; C(speakers); C(transcript_segments) | app/models/participant.py; app/models/transcript.py |
| F060 | Xem transcript đầy đủ — MVP | speakers, transcript_segments | speakers.meeting_id, speaker_label, speaker_name; transcript_segments.meeting_id, speaker_id, segment_index, start_ms, end_ms, raw_text, edited_text | R(speakers); R(transcript_segments) | Chỉ owner meeting xem được.; C(speakers); C(transcript_segments) | app/models/participant.py; app/models/transcript.py |
| F061 | Chỉnh sửa transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, is_user_edited, updated_at | R(transcript_segments) | Không sửa raw_text; lưu updated_at.; C(transcript_segments); D07 confirmed lock; D08 nonblank edits, reset_to_raw, expected_updated_at/409 (API inputs, not columns) | app/models/transcript.py |
| F062 | Tìm kiếm trong transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, is_user_edited, updated_at | R(transcript_segments) | Search không phân biệt hoa thường là đủ.; C(transcript_segments) | app/models/transcript.py |
| F063 | Phát audio tại timestamp — Nâng cao | meetings | meetings.user_id, audio_path, mime_type, audio_deleted_at | R(meetings) | Phải kiểm tra quyền truy cập audio.; C(meetings) | app/models/meeting.py |
| F064 | Tạo lại biên bản từ transcript đã sửa — MVP | transcript_segments, processing_jobs, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | transcript_segments.raw_text, edited_text; processing_jobs.job_type, status; ai_runs.run_type, status; output tables.ai_run_id, is_user_edited; action_item_owners.action_item_id (full field inventories below); ai_runs.is_accepted, accepted_at | R(transcript_segments); R(processing_jobs); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Không chạy lại ASR nếu user không yêu cầu.; C(transcript_segments); C(processing_jobs); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners); D06 per-section accepted eligible run; D07 confirmed lock | app/models/transcript.py; app/models/processing_job.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F070 | Smart Chunking transcript dài — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không cắt giữa câu nếu tránh được; giữ thứ tự và metadata. | None — UI/service/config responsibility |
| F071 | Hierarchical Summarization — MVP | summaries, ai_runs | summaries.meeting_id, ai_run_id, content, is_user_edited, updated_at; ai_runs.model_name, model_version, status | R(summaries); R(ai_runs) | Bước merge phải resolve trùng lặp/mâu thuẫn.; C(summaries); C(ai_runs) | app/models/summary.py; app/models/ai_run.py |
| F072 | Sinh Summary — MVP | summaries, ai_runs | summaries.meeting_id, ai_run_id, content, is_user_edited, updated_at; ai_runs.model_name, model_version, status | R(summaries); R(ai_runs) | Không thêm thông tin ngoài transcript.; C(summaries); C(ai_runs) | app/models/summary.py; app/models/ai_run.py |
| F073 | Trích xuất Key Points — MVP | key_points, ai_runs, transcript_segments | key_points.meeting_id, ai_run_id, content, sort_order, evidence_segment_id, is_user_edited | R(key_points); R(ai_runs); R(transcript_segments) | Phân biệt key point với decision.; C(key_points); C(ai_runs); C(transcript_segments) | app/models/key_point.py; app/models/ai_run.py; app/models/transcript.py |
| F074 | Trích xuất Decision — MVP | decisions, ai_runs, transcript_segments | decisions.meeting_id, ai_run_id, content, decision_status, confidence_level, evidence_segment_id, is_user_edited, updated_at | R(decisions); R(ai_runs); R(transcript_segments) | Hỗ trợ status confirmed/tentative/rejected/superseded.; C(decisions); C(ai_runs); C(transcript_segments) | app/models/decision.py; app/models/ai_run.py; app/models/transcript.py |
| F075 | Trích xuất Action Item — MVP | action_items, ai_runs, transcript_segments, meetings | action_items.meeting_id, ai_run_id, task, deadline_raw, deadline_normalized, task_status, confidence_level, evidence_segment_id; meetings.meeting_date | R(action_items); R(ai_runs); R(transcript_segments); R(meetings) | Một câu nhiều task phải tách đúng.; C(action_items); C(ai_runs); C(transcript_segments); C(meetings) | app/models/action_item.py; app/models/ai_run.py; app/models/transcript.py; app/models/meeting.py |
| F076 | Trích xuất Owner — MVP | action_items, action_item_owners, speakers | action_items.id; action_item_owners.action_item_id, owner_name, speaker_id; speakers.meeting_id, speaker_name, speaker_label | R(action_items); R(action_item_owners); R(speakers) | Không tự bịa owner khi thiếu evidence.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F077 | Trích xuất Deadline raw — MVP | action_items, ai_runs, transcript_segments, meetings | action_items.meeting_id, ai_run_id, task, deadline_raw, deadline_normalized, task_status, confidence_level, evidence_segment_id; meetings.meeting_date | R(action_items); R(ai_runs); R(transcript_segments); R(meetings) | Không suy đoán deadline không được nhắc.; C(action_items); C(ai_runs); C(transcript_segments); C(meetings) | app/models/action_item.py; app/models/ai_run.py; app/models/transcript.py; app/models/meeting.py |
| F078 | Chuẩn hóa Deadline — MVP | action_items, ai_runs, transcript_segments, meetings | action_items.meeting_id, ai_run_id, task, deadline_raw, deadline_normalized, task_status, confidence_level, evidence_segment_id; meetings.meeting_date | R(action_items); R(ai_runs); R(transcript_segments); R(meetings) | Giữ cả raw; không ép normalize khi không chắc.; C(action_items); C(ai_runs); C(transcript_segments); C(meetings) | app/models/action_item.py; app/models/ai_run.py; app/models/transcript.py; app/models/meeting.py |
| F079 | Gắn Evidence — MVP | key_points, decisions, action_items, transcript_segments | key_points/decisions/action_items.evidence_segment_id; transcript_segments.id, meeting_id, start_ms, end_ms, raw_text, edited_text | R(key_points); R(decisions); R(action_items); R(transcript_segments) | Evidence phải thuộc meeting hiện tại.; C(key_points); C(decisions); C(action_items); C(transcript_segments); D09 first trustworthy same-meeting ref in strongest-first order, else NULL | app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/transcript.py |
| F080 | Confidence / đánh dấu không chắc — MVP | decisions, action_items | decisions.confidence_level; action_items.confidence_level | R(decisions); R(action_items) | Không dùng confidence giả làm xác suất tuyệt đối.; C(decisions); C(action_items) | app/models/decision.py; app/models/action_item.py |
| F081 | Trích xuất Risk — Nâng cao | risks | Deferred: risks.meeting_id, ai_run_id, content, risk_status, evidence_segment_id | R(risks) | Không nhầm complaint chung với risk nếu thiếu context.; C(risks) | Deferred: no MVP model |
| F082 | Trích xuất Open Question — Nâng cao | open_questions | Deferred: open_questions.meeting_id, ai_run_id, content, question_status, evidence_segment_id | R(open_questions) | Lấy trạng thái cuối meeting.; C(open_questions) | Deferred: no MVP model |
| F083 | Grounded Output / chống hallucination — MVP | summaries, key_points, decisions, action_items, action_item_owners, transcript_segments | Output content/task, evidence_segment_id where defined; nullable deadline fields; zero owner/decision/task rows allowed | R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners); R(transcript_segments) | Thiếu owner/deadline/decision phải được phép trả null/[].; C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners); C(transcript_segments) | app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py; app/models/transcript.py |
| F084 | Chống prompt injection trong transcript — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không thực thi instruction nằm bên trong transcript. | None — UI/service/config responsibility |
| F085 | Lưu model/version đã xử lý — MVP | ai_runs | ai_runs.meeting_id, run_type, model_name, model_version, dataset_version, prompt_version, status, processing_ms, input_chars, input_tokens, error_code, created_at; ai_runs.schema_version | R(ai_runs) | Version không để trống khi inference.; C(ai_runs); D03 distinct schema/prompt/model/dataset versions | app/models/ai_run.py |
| F090 | Xem biên bản AI dạng Draft — MVP | meetings, summaries, key_points, decisions, action_items, action_item_owners, ai_runs | meetings.review_status; structured output fields and owner relations (full inventories below); ai_runs.is_accepted, accepted_at | R(meetings); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners); R(ai_runs) | Hiển thị rõ trạng thái DRAFT.; C(meetings); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners); D06 per-section accepted eligible run; D07 confirmed lock; C(ai_runs) | app/models/meeting.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py; app/models/ai_run.py |
| F091 | Sửa Summary — MVP | summaries, ai_runs | summaries.meeting_id, ai_run_id, content, is_user_edited, updated_at; ai_runs.model_name, model_version, status | R(summaries); R(ai_runs) | Đánh dấu edited_by_user.; C(summaries); C(ai_runs) | app/models/summary.py; app/models/ai_run.py |
| F092 | Thêm/Sửa/Xóa Decision — MVP | decisions, ai_runs, transcript_segments | decisions.meeting_id, ai_run_id, content, decision_status, confidence_level, evidence_segment_id, is_user_edited, updated_at | R(decisions); R(ai_runs); R(transcript_segments) | Preserve AI original nếu cần audit/version.; C(decisions); C(ai_runs); C(transcript_segments) | app/models/decision.py; app/models/ai_run.py; app/models/transcript.py |
| F093 | Thêm/Sửa/Xóa Action Item — MVP | action_items, action_item_owners, speakers | action_items.meeting_id, task, deadline_raw, deadline_normalized, task_status, evidence_segment_id, is_user_edited; action_item_owners.owner_name, speaker_id | R(action_items); R(action_item_owners); R(speakers) | Deadline normalized phải là ngày hợp lệ nếu có.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F094 | Regenerate riêng một section — MVP | transcript_segments, processing_jobs, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | transcript_segments.raw_text, edited_text; processing_jobs.job_type, status; ai_runs.run_type, status; output tables.ai_run_id, is_user_edited; action_item_owners.action_item_id (full field inventories below); ai_runs.is_accepted, accepted_at | R(transcript_segments); R(processing_jobs); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Không ghi đè user edit nếu chưa xác nhận replace.; C(transcript_segments); C(processing_jobs); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners); D06 per-section accepted eligible run; D07 confirmed lock | app/models/transcript.py; app/models/processing_job.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F095 | Xác nhận biên bản — MVP | meetings, summaries | meetings.review_status; summaries.meeting_id, content (minutes-ready validation) | R(meetings); R(summaries) | Có thể khóa hoặc vẫn cho edit với version mới tùy policy.; C(meetings); C(summaries); D07 blocks content/transcript/regeneration; execution status exception only | app/models/meeting.py; app/models/summary.py |
| F096 | Lưu lịch sử phiên bản biên bản — Nâng cao | minute_versions | Deferred: minute_versions.meeting_id, version_no, source_type, snapshot_json, created_at | R(minute_versions) | Không cần cho MVP nếu phức tạp.; C(minute_versions) | Deferred: no MVP model |
| F100 | Xem danh sách Action Items — MVP | action_items, action_item_owners, speakers | action_items.meeting_id, task, deadline_raw, deadline_normalized, task_status, evidence_segment_id, is_user_edited; action_item_owners.owner_name, speaker_id | R(action_items); R(action_item_owners); R(speakers) | Chỉ task của meeting thuộc user.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F101 | Đánh dấu hoàn thành/chưa hoàn thành — MVP | action_items | action_items.meeting_id, task_status, deadline_normalized, updated_at; overdue is derived, not a column | R(action_items) | Status enum hợp lệ.; C(action_items) | app/models/action_item.py |
| F102 | Cảnh báo quá hạn — MVP | action_items | action_items.meeting_id, task_status, deadline_normalized, updated_at; overdue is derived, not a column | R(action_items) | Không dựa vào deadline_raw mơ hồ.; C(action_items); D11 deadline < today in APP_TIMEZONE AND task_status != DONE; NULL deadline is not overdue | app/models/action_item.py |
| F103 | Lọc task theo owner/status/deadline — Nâng cao | action_items, action_item_owners, speakers | action_items.meeting_id, task, deadline_raw, deadline_normalized, task_status, evidence_segment_id, is_user_edited; action_item_owners.owner_name, speaker_id | R(action_items); R(action_item_owners); R(speakers) | Chỉ dữ liệu user.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F110 | Xem lịch sử cuộc họp — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | Không lộ meeting user khác.; C(meetings) | app/models/meeting.py |
| F111 | Tìm kiếm theo tên cuộc họp — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | Trim input, escape query.; C(meetings) | app/models/meeting.py |
| F112 | Lọc theo ngày/trạng thái — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | from <= to.; C(meetings) | app/models/meeting.py |
| F113 | Sắp xếp mới nhất/cũ nhất — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | Whitelist sort values.; C(meetings) | app/models/meeting.py |
| F114 | Tìm trong transcript/summary — Nâng cao | meetings, transcript_segments, summaries | meetings.user_id, title; transcript_segments.raw_text, edited_text; summaries.content (advanced search) | R(meetings); R(transcript_segments); R(summaries) | Có thể nâng cấp MySQL FULLTEXT.; C(meetings); C(transcript_segments); C(summaries) | app/models/meeting.py; app/models/transcript.py; app/models/summary.py |
| F115 | Xem Meeting Detail — MVP | users, meetings, processing_jobs, speakers, transcript_segments, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | meetings.id, user_id, status; all meeting-child foreign keys; processing_jobs.status; meetings.audio_path, stored_filename (full inventories below) | R(users); R(meetings); R(processing_jobs); R(speakers); R(transcript_segments); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Ownership check.; C(users); C(meetings); C(processing_jobs); C(speakers); C(transcript_segments); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/user.py; app/models/meeting.py; app/models/processing_job.py; app/models/participant.py; app/models/transcript.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F116 | Xóa meeting — MVP | users, meetings, processing_jobs, speakers, transcript_segments, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | meetings.id, user_id, status; all meeting-child foreign keys; processing_jobs.status; meetings.audio_path, stored_filename (full inventories below) | R(users); R(meetings); R(processing_jobs); R(speakers); R(transcript_segments); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Phải confirm; cascade/transaction rõ ràng.; C(users); C(meetings); C(processing_jobs); C(speakers); C(transcript_segments); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/user.py; app/models/meeting.py; app/models/processing_job.py; app/models/participant.py; app/models/transcript.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F117 | Xóa file audio khi xóa meeting — MVP | meetings | meetings.audio_path, stored_filename, audio_deleted_at; retention scheduling policy is deferred | R(meetings) | Không xóa nhầm file ngoài upload dir.; C(meetings); D12 private quarantine, commit/unlink, rollback/restore, startup recovery | app/models/meeting.py |
| F120 | Xuất biên bản PDF — Nâng cao | meetings, summaries, key_points, decisions, action_items, action_item_owners | Deferred export reads: meeting title/date/review_status and structured output fields; no minutes/export table | R(meetings); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Ưu tiên bản CONFIRMED.; C(meetings); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/meeting.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F121 | Xuất biên bản DOCX — Nâng cao | meetings, summaries, key_points, decisions, action_items, action_item_owners | Deferred export reads: meeting title/date/review_status and structured output fields; no minutes/export table | R(meetings); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Ưu tiên bản CONFIRMED.; C(meetings); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/meeting.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F130 | Toast/thông báo thao tác — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không che nội dung chính; message rõ. | None — UI/service/config responsibility |
| F131 | Thông báo lỗi thân thiện — MVP | meetings, processing_jobs, ai_runs | meetings.error_code, failed_step; processing_jobs.error_code, error_message, current_step; ai_runs.error_code (infrastructure errors need no DB row) | R(meetings); R(processing_jobs); R(ai_runs) | Không lộ secret/path/stack trace production.; C(meetings); C(processing_jobs); C(ai_runs) | app/models/meeting.py; app/models/processing_job.py; app/models/ai_run.py |
| F132 | Phân loại mã lỗi theo pipeline — MVP | meetings, processing_jobs, ai_runs | meetings.error_code, failed_step; processing_jobs.error_code, error_message, current_step; ai_runs.error_code (infrastructure errors need no DB row) | R(meetings); R(processing_jobs); R(ai_runs) | Lưu failed_step và error_code.; C(meetings); C(processing_jobs); C(ai_runs) | app/models/meeting.py; app/models/processing_job.py; app/models/ai_run.py |
| F140 | Kiểm tra quyền sở hữu meeting — MVP | meetings | meetings.user_id; child.meeting_id or owner.action_item_id -> action_items.meeting_id | R(meetings) | Không chỉ kiểm tra ở frontend.; C(meetings) | app/models/meeting.py |
| F141 | Lưu password dạng hash — MVP | users | users.id, full_name, email, password_hash, is_active | R(users) | Không log password; không lưu plain text.; C(users) | app/models/user.py |
| F142 | Audio/private files không public trực tiếp — MVP | meetings | meetings.user_id, audio_path, mime_type, audio_deleted_at | R(meetings) | Ownership check trước khi serve.; C(meetings) | app/models/meeting.py |
| F143 | Cấu hình bằng .env — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không commit secret vào Git. | None — UI/service/config responsibility |
| F144 | Chính sách giữ/xóa audio sau N ngày — Nâng cao | meetings | meetings.audio_path, stored_filename, audio_deleted_at; retention scheduling policy is deferred | R(meetings) | Không xóa trước thời hạn.; C(meetings) | app/models/meeting.py |
| F150 | Chuẩn JSON contract analyze_meeting — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Fields chính: summary, decisions[], action_items[]. | None — UI/service/config responsibility |
| F151 | Cho phép đổi base/fine-tuned model qua config — MVP | ai_runs | ai_runs.meeting_id, run_type, model_name, model_version, dataset_version, prompt_version, status, processing_ms, input_chars, input_tokens, error_code, created_at; ai_runs.schema_version | R(ai_runs) | Không hard-code model trong route.; C(ai_runs); D03 distinct schema/prompt/model/dataset versions | app/models/ai_run.py |
| F152 | Ghi metadata inference — MVP | ai_runs | ai_runs.meeting_id, run_type, model_name, model_version, dataset_version, prompt_version, status, processing_ms, input_chars, input_tokens, error_code, created_at; ai_runs.schema_version | R(ai_runs) | Không lưu dữ liệu nhạy cảm không cần thiết trong log.; C(ai_runs); D03 distinct schema/prompt/model/dataset versions | app/models/ai_run.py |

## Field inventories, relationships and constraints

The inventories below describe actual model/migration/live schema, including approved amendments. Nullable fields without an explicit server default are shown as NULL (the implicit SQL default); "-" means no default for a required value. Every id is an auto-increment BIGINT UNSIGNED primary key. MySQL INTEGER/INT and NUMERIC/DECIMAL spellings are synonyms; charset is utf8mb4.

R(table) lists actual incoming/outgoing foreign keys, with all delete actions. C(table) includes actual column constraints and explicit model/migration indexes/unique constraints. MySQL additionally creates supporting FK indexes where needed; these are not extra fields. A required or suggested workbook index is not labeled implemented unless it exists.

### users

Model: `app/models/user.py`. Implemented class: User. Column count: **7**.

C(users) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| full_name | VARCHAR(120) | NO | - | - | - |
| email | VARCHAR(191) | NO | - | UNIQUE(email) | - |
| password_hash | VARCHAR(255) | NO | - | - | - |
| is_active | TINYINT(1) | NO | 1 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(users) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| users | meetings | 1:N | meetings.user_id -> users.id | CASCADE |

C(users) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| uq_users_email | email | UNIQUE |

### meetings

Model: `app/models/meeting.py`. Implemented class: Meeting. Column count: **19**.

C(meetings) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| user_id | BIGINT UNSIGNED | NO | - | INDEX (see below); FK; supporting index | users.id |
| title | VARCHAR(255) | NO | - | INDEX (see below) | - |
| description | TEXT | YES | NULL | - | - |
| meeting_date | DATETIME | YES | NULL | INDEX (see below) | - |
| language | VARCHAR(10) | NO | 'vi' | - | - |
| status | ENUM('DRAFT','UPLOADED','PREPROCESSING','TRANSCRIBING','DIARIZING','ANALYZING','COMPLETED','FAILED') | NO | 'DRAFT' | INDEX (see below) | - |
| review_status | ENUM('DRAFT','CONFIRMED') | NO | 'DRAFT' | INDEX (see below) | - |
| original_filename | VARCHAR(255) | YES | NULL | - | - |
| stored_filename | VARCHAR(255) | YES | NULL | UNIQUE(stored_filename) | - |
| audio_path | VARCHAR(500) | YES | NULL | - | - |
| mime_type | VARCHAR(100) | YES | NULL | - | - |
| file_size_bytes | BIGINT UNSIGNED | YES | NULL | - | - |
| duration_seconds | DECIMAL(10,2) | YES | NULL | - | - |
| error_code | VARCHAR(64) | YES | NULL | INDEX (see below) | - |
| failed_step | VARCHAR(64) | YES | NULL | - | - |
| audio_deleted_at | DATETIME | YES | NULL | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX (see below) | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(meetings) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| users | meetings | 1:N | meetings.user_id -> users.id | CASCADE |
| meetings | processing_jobs | 1:N | processing_jobs.meeting_id -> meetings.id | CASCADE |
| meetings | speakers | 1:N | speakers.meeting_id -> meetings.id | CASCADE |
| meetings | transcript_segments | 1:N | transcript_segments.meeting_id -> meetings.id | CASCADE |
| meetings | ai_runs | 1:N | ai_runs.meeting_id -> meetings.id | CASCADE |
| meetings | summaries | 1:N | summaries.meeting_id -> meetings.id | CASCADE |
| meetings | key_points | 1:N | key_points.meeting_id -> meetings.id | CASCADE |
| meetings | decisions | 1:N | decisions.meeting_id -> meetings.id | CASCADE |
| meetings | action_items | 1:N | action_items.meeting_id -> meetings.id | CASCADE |

C(meetings) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| Unnamed in model/migration (live: stored_filename) | stored_filename | UNIQUE |
| idx_meetings_error_code | error_code | INDEX |
| idx_meetings_review_status | review_status | INDEX |
| idx_meetings_title | title | INDEX |
| idx_meetings_user_created | user_id, created_at | INDEX |
| idx_meetings_user_date | user_id, meeting_date | INDEX |
| idx_meetings_user_status | user_id, status | INDEX |

### processing_jobs

Model: `app/models/processing_job.py`. Implemented class: ProcessingJob. Column count: **16**.

C(processing_jobs) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX (see below); FK; supporting index | meetings.id |
| job_type | ENUM('FULL','TRANSCRIBE','DIARIZE','ANALYZE','REGENERATE') | NO | 'FULL' | INDEX (see below) | - |
| status | ENUM('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED') | NO | 'QUEUED' | INDEX (see below) | - |
| progress_percent | TINYINT UNSIGNED | NO | 0 | - | - |
| current_step | VARCHAR(64) | YES | NULL | - | - |
| error_code | VARCHAR(64) | YES | NULL | - | - |
| error_message | VARCHAR(500) | YES | NULL | - | - |
| started_at | DATETIME | YES | NULL | - | - |
| completed_at | DATETIME | YES | NULL | - | - |
| asr_model_name | VARCHAR(120) | YES | NULL | - | - |
| asr_model_version | VARCHAR(120) | YES | NULL | - | - |
| checkpoint_stage | VARCHAR(64) | YES | NULL | - | - |
| checkpoint_data | JSON | YES | NULL | - | - |
| heartbeat_at | DATETIME | YES | NULL | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX (see below) | - |

R(processing_jobs) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | processing_jobs | 1:N | processing_jobs.meeting_id -> meetings.id | CASCADE |

C(processing_jobs) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_jobs_job_type | job_type | INDEX |
| idx_jobs_meeting_created | meeting_id, created_at | INDEX |
| idx_jobs_status | status | INDEX |

### speakers

Model: `app/models/participant.py`. Implemented class: Speaker. Column count: **7**.

C(speakers) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | UNIQUE(meeting_id,speaker_label); FK; supporting index | meetings.id |
| speaker_label | VARCHAR(50) | NO | - | UNIQUE(meeting_id,speaker_label) | - |
| speaker_name | VARCHAR(120) | YES | NULL | - | - |
| is_user_verified | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(speakers) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | speakers | 1:N | speakers.meeting_id -> meetings.id | CASCADE |
| speakers | transcript_segments | 1:N | transcript_segments.speaker_id -> speakers.id | SET NULL |
| speakers | action_item_owners | 1:N | action_item_owners.speaker_id -> speakers.id | SET NULL |

C(speakers) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| uq_speakers_meeting_label | meeting_id, speaker_label | UNIQUE |

### transcript_segments

Model: `app/models/transcript.py`. Implemented class: TranscriptSegment. Column count: **13**.

C(transcript_segments) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | UNIQUE(meeting_id,segment_index); INDEX (see below); FK; supporting index | meetings.id |
| speaker_id | BIGINT UNSIGNED | YES | NULL | INDEX (see below); FK; supporting index | speakers.id |
| segment_index | INT UNSIGNED | NO | - | UNIQUE(meeting_id,segment_index) | - |
| start_ms | INT UNSIGNED | YES | NULL | INDEX (see below) | - |
| end_ms | INT UNSIGNED | YES | NULL | - | - |
| raw_text | TEXT | NO | - | - | - |
| edited_text | TEXT | YES | NULL | - | - |
| asr_confidence | DECIMAL(5,4) | YES | NULL | - | - |
| language | VARCHAR(10) | YES | NULL | - | - |
| is_user_edited | TINYINT(1) | NO | 0 | INDEX (see below) | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(transcript_segments) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | transcript_segments | 1:N | transcript_segments.meeting_id -> meetings.id | CASCADE |
| speakers | transcript_segments | 1:N | transcript_segments.speaker_id -> speakers.id | SET NULL |
| transcript_segments | key_points | 1:N | key_points.evidence_segment_id -> transcript_segments.id | SET NULL |
| transcript_segments | decisions | 1:N | decisions.evidence_segment_id -> transcript_segments.id | SET NULL |
| transcript_segments | action_items | 1:N | action_items.evidence_segment_id -> transcript_segments.id | SET NULL |

C(transcript_segments) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_segments_is_user_edited | is_user_edited | INDEX |
| idx_segments_meeting_time | meeting_id, start_ms | INDEX |
| idx_segments_speaker_id | speaker_id | INDEX |
| uq_segments_meeting_idx | meeting_id, segment_index | UNIQUE |

### ai_runs

Model: `app/models/ai_run.py`. Implemented class: AIRun. Column count: **16**.

C(ai_runs) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX (see below); FK; supporting index | meetings.id |
| run_type | ENUM('FULL','SUMMARY','DECISIONS','ACTION_ITEMS','RISKS','OPEN_QUESTIONS') | NO | 'FULL' | INDEX (see below) | - |
| model_name | VARCHAR(120) | NO | - | INDEX (see below) | - |
| model_version | VARCHAR(120) | NO | - | INDEX (see below) | - |
| dataset_version | VARCHAR(120) | YES | NULL | - | - |
| prompt_version | VARCHAR(120) | YES | NULL | - | - |
| schema_version | VARCHAR(50) | YES | NULL | - | - |
| status | ENUM('RUNNING','COMPLETED','FAILED') | NO | 'RUNNING' | INDEX (see below) | - |
| processing_ms | INT UNSIGNED | YES | NULL | - | - |
| input_chars | INT UNSIGNED | YES | NULL | - | - |
| input_tokens | INT UNSIGNED | YES | NULL | - | - |
| error_code | VARCHAR(64) | YES | NULL | - | - |
| is_accepted | TINYINT(1) | NO | 0 | - | - |
| accepted_at | DATETIME | YES | NULL | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX (see below) | - |

R(ai_runs) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | ai_runs | 1:N | ai_runs.meeting_id -> meetings.id | CASCADE |
| ai_runs | summaries | 1:N | summaries.ai_run_id -> ai_runs.id | SET NULL |
| ai_runs | key_points | 1:N | key_points.ai_run_id -> ai_runs.id | SET NULL |
| ai_runs | decisions | 1:N | decisions.ai_run_id -> ai_runs.id | SET NULL |
| ai_runs | action_items | 1:N | action_items.ai_run_id -> ai_runs.id | SET NULL |

C(ai_runs) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_airuns_created_at | created_at | INDEX |
| idx_airuns_meeting_created | meeting_id, created_at | INDEX |
| idx_airuns_model_name | model_name | INDEX |
| idx_airuns_model_version | model_version | INDEX |
| idx_airuns_run_type | run_type | INDEX |
| idx_airuns_status | status | INDEX |

### summaries

Model: `app/models/summary.py`. Implemented class: Summary. Column count: **7**.

C(summaries) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX (see below); FK; supporting index | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | ai_runs.id |
| content | LONGTEXT | NO | - | - | - |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX (see below) | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(summaries) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | summaries | 1:N | summaries.meeting_id -> meetings.id | CASCADE |
| ai_runs | summaries | 1:N | summaries.ai_run_id -> ai_runs.id | SET NULL |

C(summaries) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_summaries_meeting | meeting_id, created_at | INDEX |

### key_points

Model: `app/models/key_point.py`. Implemented class: KeyPoint. Column count: **8**.

C(key_points) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | FK; supporting index | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | ai_runs.id |
| content | TEXT | NO | - | - | - |
| sort_order | SMALLINT UNSIGNED | NO | 0 | - | - |
| evidence_segment_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | transcript_segments.id |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |

R(key_points) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | key_points | 1:N | key_points.meeting_id -> meetings.id | CASCADE |
| ai_runs | key_points | 1:N | key_points.ai_run_id -> ai_runs.id | SET NULL |
| transcript_segments | key_points | 1:N | key_points.evidence_segment_id -> transcript_segments.id | SET NULL |

C(key_points) — explicit model/migration indexes and unique constraints:

No additional explicit model/migration indexes; primary/FK support still applies.

### decisions

Model: `app/models/decision.py`. Implemented class: Decision. Column count: **10**.

C(decisions) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | FK; supporting index | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | ai_runs.id |
| content | TEXT | NO | - | - | - |
| decision_status | ENUM('CONFIRMED','TENTATIVE','REJECTED','SUPERSEDED') | NO | 'CONFIRMED' | INDEX (see below) | - |
| confidence_level | ENUM('HIGH','MEDIUM','LOW') | YES | NULL | INDEX (see below) | - |
| evidence_segment_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | transcript_segments.id |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(decisions) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | decisions | 1:N | decisions.meeting_id -> meetings.id | CASCADE |
| ai_runs | decisions | 1:N | decisions.ai_run_id -> ai_runs.id | SET NULL |
| transcript_segments | decisions | 1:N | decisions.evidence_segment_id -> transcript_segments.id | SET NULL |

C(decisions) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_decisions_confidence | confidence_level | INDEX |
| idx_decisions_status | decision_status | INDEX |

### action_items

Model: `app/models/action_item.py`. Implemented class: ActionItem. Column count: **12**.

C(action_items) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX (see below); FK; supporting index | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | ai_runs.id |
| task | TEXT | NO | - | - | - |
| deadline_raw | VARCHAR(255) | YES | NULL | - | - |
| deadline_normalized | DATE | YES | NULL | INDEX (see below) | - |
| task_status | ENUM('TODO','IN_PROGRESS','DONE','CANCELLED') | NO | 'TODO' | INDEX (see below) | - |
| confidence_level | ENUM('HIGH','MEDIUM','LOW') | YES | NULL | INDEX (see below) | - |
| evidence_segment_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | transcript_segments.id |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX (see below) | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(action_items) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | action_items | 1:N | action_items.meeting_id -> meetings.id | CASCADE |
| ai_runs | action_items | 1:N | action_items.ai_run_id -> ai_runs.id | SET NULL |
| transcript_segments | action_items | 1:N | action_items.evidence_segment_id -> transcript_segments.id | SET NULL |
| action_items | action_item_owners | 1:N | action_item_owners.action_item_id -> action_items.id | CASCADE |

C(action_items) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_tasks_confidence | confidence_level | INDEX |
| idx_tasks_created_at | created_at | INDEX |
| idx_tasks_deadline_status | deadline_normalized, task_status | INDEX |
| idx_tasks_meeting_status | meeting_id, task_status | INDEX |

### action_item_owners

Model: `app/models/action_item_owner.py`. Implemented class: ActionItemOwner. Column count: **5**.

C(action_item_owners) — actual columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| action_item_id | BIGINT UNSIGNED | NO | - | FK; supporting index | action_items.id |
| speaker_id | BIGINT UNSIGNED | YES | NULL | FK; supporting index | speakers.id |
| owner_name | VARCHAR(120) | NO | - | INDEX (see below) | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |

R(action_item_owners) — actual relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| action_items | action_item_owners | 1:N | action_item_owners.action_item_id -> action_items.id | CASCADE |
| speakers | action_item_owners | 1:N | action_item_owners.speaker_id -> speakers.id | SET NULL |

C(action_item_owners) — explicit model/migration indexes and unique constraints:

| Index / constraint | Columns | Type |
| --- | --- | --- |
| idx_owner_name | owner_name | INDEX |

## Service constraints and transaction boundaries

The approved runtime rules are summarized in Decisions Required below; their implementation status is stated separately. They are not automatically enforced by the field inventories.

- F005/F140 and BR01: authorize all private access using the session user and meeting ownership. A child FK is not authorization.
- Same-meeting validation applies to evidence, speaker mappings and output-to-run links; simple foreign keys only prove that the referenced row exists.
- F141/BR02: hash passwords and normalize/validate email; authentication core already does this. No session table is required.
- F024/F026/F142: validate upload limits and use generated, private, contained paths. SQL cascades cannot remove media files.
- F030–F034/BR13–BR14 and D10: serialize conflicting job claims using a transactional meeting-row lock. Preserve committed successful stages and validate checkpoints on retry; do not use one transaction for the entire long pipeline.
- F094/D06: accepted results survive failures. Preserve user replacement confirmation before replacing edits, persist each output/task-owner set transactionally, and apply section-specific run eligibility.
- D07 applies to transcript and content mutations/publication, including late pipeline completion, after explicit confirmation. Meeting processing status and review_status remain separate.
- F074/F083 and BR07–BR10: preserve final semantic state, allow grounded empty outputs, reject fabricated owners/deadlines, and treat transcript instructions as untrusted data.
- D12 plus UC25: check ownership/confirmation and reject busy deletion; quarantine audio before transactional deletion, restore on rollback, unlink after commit, and recover quarantine at startup.
- Numeric ranges such as progress 0–100, strict timestamp ordering, nonblank names/text and accepted-run consistency need service validation where SQL types do not enforce them.

## Decisions Required

**All original D01–D12 are RESOLVED: 12 resolved, 0 requiring human decision. S01 is also RESOLVED (13 records total).** D03–D12 are resolved by explicit human approval, not inferred solely from workbook omissions. See [Architecture Decisions](MeetingAI_Architecture_Decisions.md) for source priority, database/API/pipeline impacts and edge cases.

| ID | Status | Approved decision |
| --- | --- | --- |
| D01 | RESOLVED | Use nullable start_ms/end_ms, retaining each known boundary. Require start_ms < end_ms when both are known; never fabricate zero timestamps. A real start of zero is valid with a positive end. |
| D02 | RESOLVED | MVP section-only regeneration supports SUMMARY, DECISIONS and ACTION_ITEMS. Key points come from FULL runs or manual management. Do not add KEY_POINTS or disguise a key-points-only operation as FULL. RISKS and OPEN_QUESTIONS remain advanced even though their enum values exist. |
| D03 | RESOLVED | Store ai_runs.schema_version VARCHAR(50) NULL. prompt_version identifies the prompt, schema_version the input/output schema, model_version the model artifact, and dataset_version the dataset. Never overload one to stand for another. |
| D04 | RESOLVED | Store the actual ASR model name and version on processing_jobs for TRANSCRIBE jobs. Do not represent ASR as an ai_runs NLP run. |
| D05 | RESOLVED | Use ON DELETE SET NULL for key_points.ai_run_id, decisions.ai_run_id and action_items.ai_run_id. summaries.ai_run_id already uses SET NULL. Removing a run preserves output rows; deleting the meeting still cascades through its owned rows. |
| D06 | RESOLVED | Use is_accepted NOT NULL DEFAULT false and nullable accepted_at. Select the newest accepted eligible run separately for each meeting section: summary FULL/SUMMARY; key_points FULL; decisions FULL/DECISIONS; action_items FULL/ACTION_ITEMS. Failed or unaccepted runs never replace current results. Human-created rows with ai_run_id NULL remain independent. |
| D07 | RESOLVED | When meetings.review_status = CONFIRMED, block summary/key-point/decision editing, transcript editing, and AI regeneration/reanalysis. Action-item execution status may still change. Do not silently mutate confirmed content; this status exception does not grant permission to rewrite task content/owners/deadlines. Post-confirmation version editing is advanced scope. |
| D08 | RESOLVED | raw_text is immutable. Effective text = edited_text when edited_text IS NOT NULL, else raw_text. Reject blank/whitespace-only edits. Explicit reset_to_raw=true sets edited_text=NULL and is_user_edited=false. Compare expected_updated_at for optimistic conflicts; stale writes return HTTP 409. Do not add a version column. |
| D09 | RESOLVED | AI evidence refs are ordered strongest-first. Backend validates existence, trustworthiness and same-meeting membership, and persists the first valid same-meeting ref; if none is trustworthy, store NULL. Never fabricate evidence. API evidence text uses current effective transcript text. |
| D10 | RESOLVED | Keep processing_jobs. Use transactional locking of the meeting row to prevent conflicting active jobs. Checkpoint stages: UPLOADED, AUDIO_NORMALIZED, TRANSCRIBED, DIARIZED, ANALYZED. Retry from the nearest valid checkpoint; stale RUNNING jobs become interrupted/failed and may be retried. |
| D11 | RESOLVED | Store application DATETIME values as UTC. API timestamp inputs/outputs use ISO-8601 with offsets. APP_TIMEZONE = Asia/Ho_Chi_Minh for MVP business-time interpretation; relative deadlines and today use that zone. deadline_normalized remains DATE. Overdue = deadline < today AND status != DONE; a null deadline is not overdue. |
| D12 | RESOLVED | Validate every path stays under the configured storage root. Move audio to private storage/temp/deleting before transactional DB deletion. After commit unlink quarantined audio; on rollback restore it. Startup recovery scans quarantine: meeting exists -> restore; meeting absent -> remove quarantined file. No soft-delete/deletion-log table. |
| S01 | RESOLVED | Unknown owner means owners=[] and zero action_item_owners rows. Real owner_name is non-empty; speaker_id may be NULL. Support multiple grounded owners. deadline_raw and deadline_normalized are independently nullable; preserve ambiguous raw deadline phrases even when no normalized date can be grounded. |

For D06, section eligibility is applied before reading section rows. An accepted empty list must not fall back to an older nonempty result. Failed/unaccepted runs never displace accepted output, and human-created NULL-run rows remain independent. No result pointer/version table or new acceptance endpoint is claimed.

For D10, checkpoint_stage is VARCHAR(64), not an enum. UPLOADED / AUDIO_NORMALIZED / TRANSCRIBED / DIARIZED / ANALYZED are allowed application stage values. Interrupted jobs use the existing failure representation: there is no INTERRUPTED database status. The detailed recovery implementation is pending.

For D11, APP_TIMEZONE is configuration, not a database column. The approved overdue condition uses action_items.deadline_normalized and task_status: deadline < today AND task_status != DONE. Null dates are not overdue; CANCELLED is not excluded by an invented rule.

S01 does not make owner_name nullable: the absence of an owner is represented by zero rows. A real owner still needs a non-empty name, with an optional speaker link. No fake Unknown owner is inserted.

## Resolved documentation differences

| Difference | Resolution and authority |
| --- | --- |
| Historical seven model placeholders versus eleven MVP tables | Database Design defines the schema; all eleven mapped model classes now exist in the preserved module architecture. Use Speaker in participant.py and TranscriptSegment in transcript.py. No participants table. |
| editable_text / clean transcript versus edited_text | Preserve raw/edited separation required by F043/F061. Use the concrete edited_text column from DB/API and BR06 effective-text selection. |
| Function route suggestions versus concrete API paths | Function column is explicitly “Route/API gợi ý” (suggested). Use API A030 POST /api/meetings/{meeting_id}/audio and A063 /reanalyze for interfaces; these preserve the higher-priority functions. No routes are added in this phase. |
| Generic pending/completed examples in AGENTS versus DB enums | Use canonical DB enums verbatim, including task TODO/IN_PROGRESS/DONE/CANCELLED and separate job/meeting/review state enums. |
| AI owners array versus a single illustrative owner | BR12 and Database Design require action_item_owners, cardinality 0..N; no scalar owner column in action_items. |
| Model evidence arrays versus one DB evidence FK | Keep the documented MVP primary evidence_segment_id; AI DB_MAPPING expressly allows one primary reference. Do not invent an evidence join table. D09 now selects the first trustworthy same-meeting candidate in strongest-first order, or NULL. |
| AI confidence for key points/risks/questions versus no column | Retain the canonical DB columns. AI contract itself acknowledges that those confidence values need not be stored in this schema. |
| Video, exports, risks/questions and snapshots appear in broader documents | Function Dataset marks F028, F120/F121, F081/F082 and F096 advanced. Do not promote them to MVP. Risks/open_questions keys may remain empty in an AI response without introducing MVP tables. |
| Missing decision/owner/deadline treated as possible error | F083 and BR07 require []/null as valid states. No fabricated task, owner or deadline rows. |
| Corrupt audio state differs between F025 and UC upload exception wording | F025 explicitly expects FAILED for corrupt media; higher-priority function wins for that case. Unsupported extension/oversize remain rejected before processing. Detailed upload timing can be specified in its later phase. |
| Timestamp end equals start allowed in AI input | F042 requires start < end, which takes precedence over AI end_ms >= start_ms. D01 permits nullable missing bounds, now implemented without zero defaults. |


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

## Validation and implementation boundary

- Coverage retained: all 86 canonical Function IDs appear once in the function mapping (74 MVP, 12 advanced).
- Current inventory: 11 application tables, 120 application columns, 19 foreign keys. Model/migration/live table and column names match.
- All 19 live FK targets/delete actions match the model; D05's three formerly omitted relationships are included.
- The repaired summary model uses explicit MySQL LONGTEXT. The original migration uses the historical Text(length=4294967295) variant; live MySQL is LONGTEXT and flask db check reports no model/schema differences.
- No existing model is empty or planned-only. app/extensions.py remains the single SQLAlchemy instance.
- No new migrations, columns or tables are requested by this reconciliation. Runtime gaps above remain for their authorized phases; Phase 3B is not started here.
- The six workbooks are unchanged; approved amendments and remaining workbook differences are explicit.

## Source fingerprints

SHA-256 of all workbooks reread for this reconciliation:

| Workbook | SHA-256 |
| --- | --- |
| MeetingAI_Master_AI_IO_Contract.xlsx | 91D8323D0E5F9A639A4C5378604E2F10DCB231B9797A64FA0807523D78BF8758 |
| MeetingAI_Master_API_Contract.xlsx | 4F40DB01C7679E81BF94416F0F95B44157BF67AFA033EFDEF13714B80B7CB04E |
| MeetingAI_Master_Database_Design.xlsx | 60BD53385B1640F4F06B565DDA1B2B810600523BC15A6B760E5C82C33111E227 |
| MeetingAI_Master_Function_Dataset.xlsx | 32325DC1FD80F6C51FADFD11F95869B4BC4007AB60D7D41D48F84C7C4F27922F |
| MeetingAI_Master_UI_Page_Flow.xlsx | 61E60E0291CAEC9C83FECBC25709DB7030CCBB355E8AAB1C9CAB76B7250CD159 |
| MeetingAI_Master_Use_Case_Specification.xlsx | 28D2AB9FAA489D55A0BCA8B4B9A0AEDA269DF08E68E1758E1A6D37932F883822 |
