# MeetingAI database mapping — Phase 1.5

Status: review document only. No models, tables, migrations, seed data, or business endpoints are implemented by this phase.

## Sources and precedence

Read on 2026-09-23, including all 54 worksheets. Resolve functional scope before implementation detail:

1. [Master Function Dataset](MeetingAI_Master_Function_Dataset.xlsx) — FUNCTION_DATASET: 86 functions, 74 MVP and 12 advanced.
2. [Use Case Specification](MeetingAI_Master_Use_Case_Specification.xlsx) — business flows, BUSINESS_RULES, EXCEPTION_MATRIX.
3. [Database Design](MeetingAI_Master_Database_Design.xlsx) — TABLES_OVERVIEW, COLUMNS, RELATIONSHIPS, ENUMS, INDEXES, MIGRATION_ORDER.
4. [API Contract](MeetingAI_Master_API_Contract.xlsx) — API_ENDPOINTS, REQUEST_FIELDS, RESPONSE_SCHEMAS, STATE_TRANSITIONS.
5. [UI Page Flow](MeetingAI_Master_UI_Page_Flow.xlsx) — page/component actions and states.
6. [AI IO Contract](MeetingAI_Master_AI_IO_Contract.xlsx) — inputs, outputs, validation, mapping and versioning.

[AGENTS.md](../AGENTS.md) governs the fixed stack and existing layered architecture. This document is derived guidance, not a replacement for the canonical workbooks. Source hashes appear below.

## Model-file mapping and schema boundary

Only the following 11 tables belong to the canonical MVP. Model paths are planned destinations, not implemented files. Existing files are preserved. In particular, Speaker belongs in the existing participant.py module with table name speakers; this does not introduce a participants table. TranscriptSegment belongs in transcript.py.

| Order | Table | Planned class | Model file | File status |
| --- | --- | --- | --- | --- |
| 1 | users | User | app/models/user.py | Existing empty module; retained |
| 2 | meetings | Meeting | app/models/meeting.py | Existing empty module; retained |
| 3 | processing_jobs | ProcessingJob | app/models/processing_job.py | Future addition; not created |
| 4 | speakers | Speaker | app/models/participant.py | Existing empty module; retained |
| 5 | transcript_segments | TranscriptSegment | app/models/transcript.py | Existing empty module; retained |
| 6 | ai_runs | AIRun | app/models/ai_run.py | Future addition; not created |
| 7 | summaries | Summary | app/models/summary.py | Existing empty module; retained |
| 8 | key_points | KeyPoint | app/models/key_point.py | Future addition; not created |
| 9 | decisions | Decision | app/models/decision.py | Existing empty module; retained |
| 10 | action_items | ActionItem | app/models/action_item.py | Existing empty module; retained |
| 11 | action_item_owners | ActionItemOwner | app/models/action_item_owner.py | Future addition; not created |

All future models import db from app/extensions.py. app/database/db.py must not instantiate SQLAlchemy. Future model registration belongs in app/models/__init__.py and must be wired into the factory before migration discovery.

Advanced tables risks, open_questions, minute_versions and password_reset_tokens are deferred. No participants, minutes, chunks, uploads, exports, sessions, logs, or separate deadlines table is added by inference from a feature name.

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
| F030 | Khởi tạo job xử lý — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at | R(meetings); R(processing_jobs) | Không giữ request HTTP mở nhiều phút.; C(meetings); C(processing_jobs) | app/models/meeting.py; app/models/processing_job.py |
| F031 | Theo dõi trạng thái xử lý — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at | R(meetings); R(processing_jobs) | Status enum cố định.; C(meetings); C(processing_jobs) | app/models/meeting.py; app/models/processing_job.py |
| F032 | Hiển thị progress theo bước — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at | R(meetings); R(processing_jobs) | Không hiển thị % giả quá chi tiết nếu không đo được.; C(meetings); C(processing_jobs) | app/models/meeting.py; app/models/processing_job.py |
| F033 | Retry bước lỗi — MVP | meetings, processing_jobs | meetings.status, failed_step, error_code; processing_jobs.meeting_id, job_type, status, progress_percent, current_step, error_code, error_message, started_at, completed_at, created_at | R(meetings); R(processing_jobs) | Không tạo trùng bản ghi kết quả không kiểm soát.; C(meetings); C(processing_jobs) | app/models/meeting.py; app/models/processing_job.py |
| F034 | Giữ kết quả trung gian khi bước sau lỗi — MVP | meetings, processing_jobs, transcript_segments | meetings.status, failed_step; processing_jobs.status, current_step; transcript_segments.meeting_id, segment_index, raw_text, start_ms, end_ms | R(meetings); R(processing_jobs); R(transcript_segments) | Không rollback toàn pipeline khi summarization fail.; C(meetings); C(processing_jobs); C(transcript_segments) | app/models/meeting.py; app/models/processing_job.py; app/models/transcript.py |
| F040 | Tiền xử lý audio bằng FFmpeg — MVP | meetings | meetings.original_filename, stored_filename, audio_path, mime_type, file_size_bytes, duration_seconds, status, error_code, failed_step | R(meetings) | Chuẩn output 16kHz mono WAV hoặc format model yêu cầu.; C(meetings) | app/models/meeting.py |
| F041 | Chuyển audio thành transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, start_ms, end_ms, language, asr_confidence, is_user_edited | R(transcript_segments) | Ưu tiên tiếng Việt; lưu model/version.; C(transcript_segments) | app/models/transcript.py |
| F042 | Sinh timestamp theo segment — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, start_ms, end_ms, language, asr_confidence, is_user_edited | R(transcript_segments) | start < end; thứ tự tăng dần.; C(transcript_segments) | app/models/transcript.py |
| F043 | Lưu raw transcript và clean transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, start_ms, end_ms, language, asr_confidence, is_user_edited | R(transcript_segments) | Không ghi đè raw_text khi user sửa.; C(transcript_segments) | app/models/transcript.py |
| F050 | Speaker diarization — MVP | speakers, transcript_segments | speakers.meeting_id, speaker_label, speaker_name; transcript_segments.meeting_id, speaker_id, segment_index, start_ms, end_ms, raw_text, edited_text | R(speakers); R(transcript_segments) | Không bắt buộc pipeline toàn hệ thống fail nếu bước này fail.; C(speakers); C(transcript_segments) | app/models/participant.py; app/models/transcript.py |
| F051 | Gán tên thật cho speaker — MVP | speakers | speakers.meeting_id, speaker_label, speaker_name, is_user_verified, updated_at | R(speakers) | Đổi tên phải áp dụng toàn transcript hiển thị.; C(speakers) | app/models/participant.py |
| F052 | Sửa gán speaker cho segment — Nâng cao | speakers, transcript_segments | speakers.meeting_id, speaker_label, speaker_name; transcript_segments.meeting_id, speaker_id, segment_index, start_ms, end_ms, raw_text, edited_text | R(speakers); R(transcript_segments) | Speaker phải cùng meeting.; C(speakers); C(transcript_segments) | app/models/participant.py; app/models/transcript.py |
| F060 | Xem transcript đầy đủ — MVP | speakers, transcript_segments | speakers.meeting_id, speaker_label, speaker_name; transcript_segments.meeting_id, speaker_id, segment_index, start_ms, end_ms, raw_text, edited_text | R(speakers); R(transcript_segments) | Chỉ owner meeting xem được.; C(speakers); C(transcript_segments) | app/models/participant.py; app/models/transcript.py |
| F061 | Chỉnh sửa transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, is_user_edited, updated_at | R(transcript_segments) | Không sửa raw_text; lưu updated_at.; C(transcript_segments) | app/models/transcript.py |
| F062 | Tìm kiếm trong transcript — MVP | transcript_segments | transcript_segments.meeting_id, segment_index, raw_text, edited_text, is_user_edited, updated_at | R(transcript_segments) | Search không phân biệt hoa thường là đủ.; C(transcript_segments) | app/models/transcript.py |
| F063 | Phát audio tại timestamp — Nâng cao | meetings | meetings.user_id, audio_path, mime_type, audio_deleted_at | R(meetings) | Phải kiểm tra quyền truy cập audio.; C(meetings) | app/models/meeting.py |
| F064 | Tạo lại biên bản từ transcript đã sửa — MVP | transcript_segments, processing_jobs, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | transcript_segments.raw_text, edited_text; processing_jobs.job_type, status; ai_runs.run_type, status; output tables.ai_run_id, is_user_edited; action_item_owners.action_item_id (full field inventories below) | R(transcript_segments); R(processing_jobs); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Không chạy lại ASR nếu user không yêu cầu.; C(transcript_segments); C(processing_jobs); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/transcript.py; app/models/processing_job.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F070 | Smart Chunking transcript dài — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không cắt giữa câu nếu tránh được; giữ thứ tự và metadata. | None — UI/service/config responsibility |
| F071 | Hierarchical Summarization — MVP | summaries, ai_runs | summaries.meeting_id, ai_run_id, content, is_user_edited, updated_at; ai_runs.model_name, model_version, status | R(summaries); R(ai_runs) | Bước merge phải resolve trùng lặp/mâu thuẫn.; C(summaries); C(ai_runs) | app/models/summary.py; app/models/ai_run.py |
| F072 | Sinh Summary — MVP | summaries, ai_runs | summaries.meeting_id, ai_run_id, content, is_user_edited, updated_at; ai_runs.model_name, model_version, status | R(summaries); R(ai_runs) | Không thêm thông tin ngoài transcript.; C(summaries); C(ai_runs) | app/models/summary.py; app/models/ai_run.py |
| F073 | Trích xuất Key Points — MVP | key_points, ai_runs, transcript_segments | key_points.meeting_id, ai_run_id, content, sort_order, evidence_segment_id, is_user_edited | R(key_points); R(ai_runs); R(transcript_segments) | Phân biệt key point với decision.; C(key_points); C(ai_runs); C(transcript_segments) | app/models/key_point.py; app/models/ai_run.py; app/models/transcript.py |
| F074 | Trích xuất Decision — MVP | decisions, ai_runs, transcript_segments | decisions.meeting_id, ai_run_id, content, decision_status, confidence_level, evidence_segment_id, is_user_edited, updated_at | R(decisions); R(ai_runs); R(transcript_segments) | Hỗ trợ status confirmed/tentative/rejected/superseded.; C(decisions); C(ai_runs); C(transcript_segments) | app/models/decision.py; app/models/ai_run.py; app/models/transcript.py |
| F075 | Trích xuất Action Item — MVP | action_items, ai_runs, transcript_segments, meetings | action_items.meeting_id, ai_run_id, task, deadline_raw, deadline_normalized, task_status, confidence_level, evidence_segment_id; meetings.meeting_date | R(action_items); R(ai_runs); R(transcript_segments); R(meetings) | Một câu nhiều task phải tách đúng.; C(action_items); C(ai_runs); C(transcript_segments); C(meetings) | app/models/action_item.py; app/models/ai_run.py; app/models/transcript.py; app/models/meeting.py |
| F076 | Trích xuất Owner — MVP | action_items, action_item_owners, speakers | action_items.id; action_item_owners.action_item_id, owner_name, speaker_id; speakers.meeting_id, speaker_name, speaker_label | R(action_items); R(action_item_owners); R(speakers) | Không tự bịa owner khi thiếu evidence.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F077 | Trích xuất Deadline raw — MVP | action_items, ai_runs, transcript_segments, meetings | action_items.meeting_id, ai_run_id, task, deadline_raw, deadline_normalized, task_status, confidence_level, evidence_segment_id; meetings.meeting_date | R(action_items); R(ai_runs); R(transcript_segments); R(meetings) | Không suy đoán deadline không được nhắc.; C(action_items); C(ai_runs); C(transcript_segments); C(meetings) | app/models/action_item.py; app/models/ai_run.py; app/models/transcript.py; app/models/meeting.py |
| F078 | Chuẩn hóa Deadline — MVP | action_items, ai_runs, transcript_segments, meetings | action_items.meeting_id, ai_run_id, task, deadline_raw, deadline_normalized, task_status, confidence_level, evidence_segment_id; meetings.meeting_date | R(action_items); R(ai_runs); R(transcript_segments); R(meetings) | Giữ cả raw; không ép normalize khi không chắc.; C(action_items); C(ai_runs); C(transcript_segments); C(meetings) | app/models/action_item.py; app/models/ai_run.py; app/models/transcript.py; app/models/meeting.py |
| F079 | Gắn Evidence — MVP | key_points, decisions, action_items, transcript_segments | key_points/decisions/action_items.evidence_segment_id; transcript_segments.id, meeting_id, start_ms, end_ms, raw_text, edited_text | R(key_points); R(decisions); R(action_items); R(transcript_segments) | Evidence phải thuộc meeting hiện tại.; C(key_points); C(decisions); C(action_items); C(transcript_segments) | app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/transcript.py |
| F080 | Confidence / đánh dấu không chắc — MVP | decisions, action_items | decisions.confidence_level; action_items.confidence_level | R(decisions); R(action_items) | Không dùng confidence giả làm xác suất tuyệt đối.; C(decisions); C(action_items) | app/models/decision.py; app/models/action_item.py |
| F081 | Trích xuất Risk — Nâng cao | risks | Deferred: risks.meeting_id, ai_run_id, content, risk_status, evidence_segment_id | R(risks) | Không nhầm complaint chung với risk nếu thiếu context.; C(risks) | Deferred: no MVP model |
| F082 | Trích xuất Open Question — Nâng cao | open_questions | Deferred: open_questions.meeting_id, ai_run_id, content, question_status, evidence_segment_id | R(open_questions) | Lấy trạng thái cuối meeting.; C(open_questions) | Deferred: no MVP model |
| F083 | Grounded Output / chống hallucination — MVP | summaries, key_points, decisions, action_items, action_item_owners, transcript_segments | Output content/task, evidence_segment_id where defined; nullable deadline fields; zero owner/decision/task rows allowed | R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners); R(transcript_segments) | Thiếu owner/deadline/decision phải được phép trả null/[].; C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners); C(transcript_segments) | app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py; app/models/transcript.py |
| F084 | Chống prompt injection trong transcript — MVP | None | No persistent fields required by this function itself; validation, session, UI, configuration, or in-memory contract behavior. | None | Không thực thi instruction nằm bên trong transcript. | None — UI/service/config responsibility |
| F085 | Lưu model/version đã xử lý — MVP | ai_runs | ai_runs.meeting_id, run_type, model_name, model_version, dataset_version, prompt_version, status, processing_ms, input_chars, input_tokens, error_code, created_at | R(ai_runs) | Version không để trống khi inference.; C(ai_runs) | app/models/ai_run.py |
| F090 | Xem biên bản AI dạng Draft — MVP | meetings, summaries, key_points, decisions, action_items, action_item_owners | meetings.review_status; structured output fields and owner relations (full inventories below) | R(meetings); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Hiển thị rõ trạng thái DRAFT.; C(meetings); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/meeting.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F091 | Sửa Summary — MVP | summaries, ai_runs | summaries.meeting_id, ai_run_id, content, is_user_edited, updated_at; ai_runs.model_name, model_version, status | R(summaries); R(ai_runs) | Đánh dấu edited_by_user.; C(summaries); C(ai_runs) | app/models/summary.py; app/models/ai_run.py |
| F092 | Thêm/Sửa/Xóa Decision — MVP | decisions, ai_runs, transcript_segments | decisions.meeting_id, ai_run_id, content, decision_status, confidence_level, evidence_segment_id, is_user_edited, updated_at | R(decisions); R(ai_runs); R(transcript_segments) | Preserve AI original nếu cần audit/version.; C(decisions); C(ai_runs); C(transcript_segments) | app/models/decision.py; app/models/ai_run.py; app/models/transcript.py |
| F093 | Thêm/Sửa/Xóa Action Item — MVP | action_items, action_item_owners, speakers | action_items.meeting_id, task, deadline_raw, deadline_normalized, task_status, evidence_segment_id, is_user_edited; action_item_owners.owner_name, speaker_id | R(action_items); R(action_item_owners); R(speakers) | Deadline normalized phải là ngày hợp lệ nếu có.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F094 | Regenerate riêng một section — MVP | transcript_segments, processing_jobs, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | transcript_segments.raw_text, edited_text; processing_jobs.job_type, status; ai_runs.run_type, status; output tables.ai_run_id, is_user_edited; action_item_owners.action_item_id (full field inventories below) | R(transcript_segments); R(processing_jobs); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Không ghi đè user edit nếu chưa xác nhận replace.; C(transcript_segments); C(processing_jobs); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/transcript.py; app/models/processing_job.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F095 | Xác nhận biên bản — MVP | meetings, summaries | meetings.review_status; summaries.meeting_id, content (minutes-ready validation) | R(meetings); R(summaries) | Có thể khóa hoặc vẫn cho edit với version mới tùy policy.; C(meetings); C(summaries) | app/models/meeting.py; app/models/summary.py |
| F096 | Lưu lịch sử phiên bản biên bản — Nâng cao | minute_versions | Deferred: minute_versions.meeting_id, version_no, source_type, snapshot_json, created_at | R(minute_versions) | Không cần cho MVP nếu phức tạp.; C(minute_versions) | Deferred: no MVP model |
| F100 | Xem danh sách Action Items — MVP | action_items, action_item_owners, speakers | action_items.meeting_id, task, deadline_raw, deadline_normalized, task_status, evidence_segment_id, is_user_edited; action_item_owners.owner_name, speaker_id | R(action_items); R(action_item_owners); R(speakers) | Chỉ task của meeting thuộc user.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F101 | Đánh dấu hoàn thành/chưa hoàn thành — MVP | action_items | action_items.meeting_id, task_status, deadline_normalized, updated_at; overdue is derived, not a column | R(action_items) | Status enum hợp lệ.; C(action_items) | app/models/action_item.py |
| F102 | Cảnh báo quá hạn — MVP | action_items | action_items.meeting_id, task_status, deadline_normalized, updated_at; overdue is derived, not a column | R(action_items) | Không dựa vào deadline_raw mơ hồ.; C(action_items) | app/models/action_item.py |
| F103 | Lọc task theo owner/status/deadline — Nâng cao | action_items, action_item_owners, speakers | action_items.meeting_id, task, deadline_raw, deadline_normalized, task_status, evidence_segment_id, is_user_edited; action_item_owners.owner_name, speaker_id | R(action_items); R(action_item_owners); R(speakers) | Chỉ dữ liệu user.; C(action_items); C(action_item_owners); C(speakers) | app/models/action_item.py; app/models/action_item_owner.py; app/models/participant.py |
| F110 | Xem lịch sử cuộc họp — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | Không lộ meeting user khác.; C(meetings) | app/models/meeting.py |
| F111 | Tìm kiếm theo tên cuộc họp — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | Trim input, escape query.; C(meetings) | app/models/meeting.py |
| F112 | Lọc theo ngày/trạng thái — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | from <= to.; C(meetings) | app/models/meeting.py |
| F113 | Sắp xếp mới nhất/cũ nhất — MVP | meetings | meetings.user_id, title, meeting_date, status, created_at | R(meetings) | Whitelist sort values.; C(meetings) | app/models/meeting.py |
| F114 | Tìm trong transcript/summary — Nâng cao | meetings, transcript_segments, summaries | meetings.user_id, title; transcript_segments.raw_text, edited_text; summaries.content (advanced search) | R(meetings); R(transcript_segments); R(summaries) | Có thể nâng cấp MySQL FULLTEXT.; C(meetings); C(transcript_segments); C(summaries) | app/models/meeting.py; app/models/transcript.py; app/models/summary.py |
| F115 | Xem Meeting Detail — MVP | users, meetings, processing_jobs, speakers, transcript_segments, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | meetings.id, user_id, status; all meeting-child foreign keys; processing_jobs.status; meetings.audio_path, stored_filename (full inventories below) | R(users); R(meetings); R(processing_jobs); R(speakers); R(transcript_segments); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Ownership check.; C(users); C(meetings); C(processing_jobs); C(speakers); C(transcript_segments); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/user.py; app/models/meeting.py; app/models/processing_job.py; app/models/participant.py; app/models/transcript.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F116 | Xóa meeting — MVP | users, meetings, processing_jobs, speakers, transcript_segments, ai_runs, summaries, key_points, decisions, action_items, action_item_owners | meetings.id, user_id, status; all meeting-child foreign keys; processing_jobs.status; meetings.audio_path, stored_filename (full inventories below) | R(users); R(meetings); R(processing_jobs); R(speakers); R(transcript_segments); R(ai_runs); R(summaries); R(key_points); R(decisions); R(action_items); R(action_item_owners) | Phải confirm; cascade/transaction rõ ràng.; C(users); C(meetings); C(processing_jobs); C(speakers); C(transcript_segments); C(ai_runs); C(summaries); C(key_points); C(decisions); C(action_items); C(action_item_owners) | app/models/user.py; app/models/meeting.py; app/models/processing_job.py; app/models/participant.py; app/models/transcript.py; app/models/ai_run.py; app/models/summary.py; app/models/key_point.py; app/models/decision.py; app/models/action_item.py; app/models/action_item_owner.py |
| F117 | Xóa file audio khi xóa meeting — MVP | meetings | meetings.audio_path, stored_filename, audio_deleted_at; retention scheduling policy is deferred | R(meetings) | Không xóa nhầm file ngoài upload dir.; C(meetings) | app/models/meeting.py |
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
| F151 | Cho phép đổi base/fine-tuned model qua config — MVP | ai_runs | ai_runs.meeting_id, run_type, model_name, model_version, dataset_version, prompt_version, status, processing_ms, input_chars, input_tokens, error_code, created_at | R(ai_runs) | Không hard-code model trong route.; C(ai_runs) | app/models/ai_run.py |
| F152 | Ghi metadata inference — MVP | ai_runs | ai_runs.meeting_id, run_type, model_name, model_version, dataset_version, prompt_version, status, processing_ms, input_chars, input_tokens, error_code, created_at | R(ai_runs) | Không lưu dữ liệu nhạy cảm không cần thiết trong log.; C(ai_runs) | app/models/ai_run.py |

## Field inventories, relationships and constraints

The following field rows are transcribed from Database Design / COLUMNS, not newly designed fields. Defaults and enum spelling are preserved. Each table's id is an auto-increment BIGINT UNSIGNED primary key. Database charset is utf8mb4; exact collation is not fixed by the workbooks.

R(table) lists all incoming/outgoing relationship rows from RELATIONSHIPS; C(table) includes the column constraints and named indexes. Foreign keys listed in COLUMNS but absent from RELATIONSHIPS remain real references; their unspecified deletion policy is recorded in Decisions Required.

### users

Model: `app/models/user.py`.

C(users) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| full_name | VARCHAR(120) | NO | - | - | - |
| email | VARCHAR(191) | NO | - | UNIQUE | - |
| password_hash | VARCHAR(255) | NO | - | - | - |
| is_active | TINYINT(1) | NO | 1 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(users) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| users | meetings | 1:N | meetings.user_id -> users.id | CASCADE |

C(users) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| uq_users_email | email | UNIQUE |

### meetings

Model: `app/models/meeting.py`.

C(meetings) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| user_id | BIGINT UNSIGNED | NO | - | INDEX, FK | users.id |
| title | VARCHAR(255) | NO | - | INDEX | - |
| description | TEXT | YES | NULL | - | - |
| meeting_date | DATETIME | YES | NULL | INDEX | - |
| language | VARCHAR(10) | NO | 'vi' | - | - |
| status | ENUM('DRAFT','UPLOADED','PREPROCESSING','TRANSCRIBING','DIARIZING','ANALYZING','COMPLETED','FAILED') | NO | 'DRAFT' | INDEX | - |
| review_status | ENUM('DRAFT','CONFIRMED') | NO | 'DRAFT' | INDEX | - |
| original_filename | VARCHAR(255) | YES | NULL | - | - |
| stored_filename | VARCHAR(255) | YES | NULL | UNIQUE | - |
| audio_path | VARCHAR(500) | YES | NULL | - | - |
| mime_type | VARCHAR(100) | YES | NULL | - | - |
| file_size_bytes | BIGINT UNSIGNED | YES | NULL | - | - |
| duration_seconds | DECIMAL(10,2) | YES | NULL | - | - |
| error_code | VARCHAR(64) | YES | NULL | INDEX | - |
| failed_step | VARCHAR(64) | YES | NULL | - | - |
| audio_deleted_at | DATETIME | YES | NULL | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(meetings) — canonical relationships:

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

C(meetings) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| idx_meetings_user_created | user_id, created_at | INDEX |
| idx_meetings_user_status | user_id, status | INDEX |
| idx_meetings_user_date | user_id, meeting_date | INDEX |
| idx_meetings_title | title | INDEX |

### processing_jobs

Model: `app/models/processing_job.py`.

C(processing_jobs) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| job_type | ENUM('FULL','TRANSCRIBE','DIARIZE','ANALYZE','REGENERATE') | NO | 'FULL' | INDEX | - |
| status | ENUM('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED') | NO | 'QUEUED' | INDEX | - |
| progress_percent | TINYINT UNSIGNED | NO | 0 | - | - |
| current_step | VARCHAR(64) | YES | NULL | - | - |
| error_code | VARCHAR(64) | YES | NULL | - | - |
| error_message | VARCHAR(500) | YES | NULL | - | - |
| started_at | DATETIME | YES | NULL | - | - |
| completed_at | DATETIME | YES | NULL | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX | - |

R(processing_jobs) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | processing_jobs | 1:N | processing_jobs.meeting_id -> meetings.id | CASCADE |

C(processing_jobs) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| idx_jobs_meeting_created | meeting_id, created_at | INDEX |

### speakers

Model: `app/models/participant.py`.

C(speakers) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| speaker_label | VARCHAR(50) | NO | - | UNIQUE(meeting_id,speaker_label) | - |
| speaker_name | VARCHAR(120) | YES | NULL | - | - |
| is_user_verified | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(speakers) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | speakers | 1:N | speakers.meeting_id -> meetings.id | CASCADE |
| speakers | transcript_segments | 1:N | transcript_segments.speaker_id -> speakers.id | SET NULL |
| speakers | action_item_owners | 1:N | action_item_owners.speaker_id -> speakers.id | SET NULL |

C(speakers) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| uq_speakers_meeting_label | meeting_id, speaker_label | UNIQUE |

### transcript_segments

Model: `app/models/transcript.py`.

C(transcript_segments) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| speaker_id | BIGINT UNSIGNED | YES | NULL | INDEX, FK | speakers.id |
| segment_index | INT UNSIGNED | NO | - | UNIQUE(meeting_id,segment_index) | - |
| start_ms | INT UNSIGNED | NO | 0 | INDEX | - |
| end_ms | INT UNSIGNED | NO | 0 | - | - |
| raw_text | TEXT | NO | - | FULLTEXT candidate | - |
| edited_text | TEXT | YES | NULL | FULLTEXT candidate | - |
| asr_confidence | DECIMAL(5,4) | YES | NULL | - | - |
| language | VARCHAR(10) | YES | NULL | - | - |
| is_user_edited | TINYINT(1) | NO | 0 | INDEX | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(transcript_segments) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | transcript_segments | 1:N | transcript_segments.meeting_id -> meetings.id | CASCADE |
| speakers | transcript_segments | 1:N | transcript_segments.speaker_id -> speakers.id | SET NULL |
| transcript_segments | key_points | 1:N | key_points.evidence_segment_id -> transcript_segments.id | SET NULL |
| transcript_segments | decisions | 1:N | decisions.evidence_segment_id -> transcript_segments.id | SET NULL |
| transcript_segments | action_items | 1:N | action_items.evidence_segment_id -> transcript_segments.id | SET NULL |

C(transcript_segments) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| uq_segments_meeting_idx | meeting_id, segment_index | UNIQUE |
| idx_segments_meeting_time | meeting_id, start_ms | INDEX |
| ft_segments_text | raw_text, edited_text | FULLTEXT (optional) |

### ai_runs

Model: `app/models/ai_run.py`.

C(ai_runs) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| run_type | ENUM('FULL','SUMMARY','DECISIONS','ACTION_ITEMS','RISKS','OPEN_QUESTIONS') | NO | 'FULL' | INDEX | - |
| model_name | VARCHAR(120) | NO | - | INDEX | - |
| model_version | VARCHAR(120) | NO | - | INDEX | - |
| dataset_version | VARCHAR(120) | YES | NULL | - | - |
| prompt_version | VARCHAR(120) | YES | NULL | - | - |
| status | ENUM('RUNNING','COMPLETED','FAILED') | NO | 'RUNNING' | INDEX | - |
| processing_ms | INT UNSIGNED | YES | NULL | - | - |
| input_chars | INT UNSIGNED | YES | NULL | - | - |
| input_tokens | INT UNSIGNED | YES | NULL | - | - |
| error_code | VARCHAR(64) | YES | NULL | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX | - |

R(ai_runs) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | ai_runs | 1:N | ai_runs.meeting_id -> meetings.id | CASCADE |
| ai_runs | summaries | 1:N | summaries.ai_run_id -> ai_runs.id | SET NULL |

C(ai_runs) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| idx_airuns_meeting_created | meeting_id, created_at | INDEX |

### summaries

Model: `app/models/summary.py`.

C(summaries) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | INDEX, FK | ai_runs.id |
| content | LONGTEXT | NO | - | FULLTEXT candidate | - |
| is_user_edited | TINYINT(1) | NO | 0 | INDEX | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(summaries) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | summaries | 1:N | summaries.meeting_id -> meetings.id | CASCADE |
| ai_runs | summaries | 1:N | summaries.ai_run_id -> ai_runs.id | SET NULL |

C(summaries) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| idx_summaries_meeting | meeting_id, created_at | INDEX |

### key_points

Model: `app/models/key_point.py`.

C(key_points) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK | ai_runs.id |
| content | TEXT | NO | - | - | - |
| sort_order | SMALLINT UNSIGNED | NO | 0 | INDEX | - |
| evidence_segment_id | BIGINT UNSIGNED | YES | NULL | FK | transcript_segments.id |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |

R(key_points) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | key_points | 1:N | key_points.meeting_id -> meetings.id | CASCADE |
| transcript_segments | key_points | 1:N | key_points.evidence_segment_id -> transcript_segments.id | SET NULL |

C(key_points) — indexes from INDEXES (column-level keys above also apply):

No additional named indexes specified.

### decisions

Model: `app/models/decision.py`.

C(decisions) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK | ai_runs.id |
| content | TEXT | NO | - | - | - |
| decision_status | ENUM('CONFIRMED','TENTATIVE','REJECTED','SUPERSEDED') | NO | 'CONFIRMED' | INDEX | - |
| confidence_level | ENUM('HIGH','MEDIUM','LOW') | YES | NULL | INDEX | - |
| evidence_segment_id | BIGINT UNSIGNED | YES | NULL | FK | transcript_segments.id |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(decisions) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | decisions | 1:N | decisions.meeting_id -> meetings.id | CASCADE |
| transcript_segments | decisions | 1:N | decisions.evidence_segment_id -> transcript_segments.id | SET NULL |

C(decisions) — indexes from INDEXES (column-level keys above also apply):

No additional named indexes specified.

### action_items

Model: `app/models/action_item.py`.

C(action_items) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| meeting_id | BIGINT UNSIGNED | NO | - | INDEX, FK | meetings.id |
| ai_run_id | BIGINT UNSIGNED | YES | NULL | FK | ai_runs.id |
| task | TEXT | NO | - | - | - |
| deadline_raw | VARCHAR(255) | YES | NULL | - | - |
| deadline_normalized | DATE | YES | NULL | INDEX | - |
| task_status | ENUM('TODO','IN_PROGRESS','DONE','CANCELLED') | NO | 'TODO' | INDEX | - |
| confidence_level | ENUM('HIGH','MEDIUM','LOW') | YES | NULL | INDEX | - |
| evidence_segment_id | BIGINT UNSIGNED | YES | NULL | FK | transcript_segments.id |
| is_user_edited | TINYINT(1) | NO | 0 | - | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | INDEX | - |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | - | - |

R(action_items) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| meetings | action_items | 1:N | action_items.meeting_id -> meetings.id | CASCADE |
| action_items | action_item_owners | 1:N | action_item_owners.action_item_id -> action_items.id | CASCADE |
| transcript_segments | action_items | 1:N | action_items.evidence_segment_id -> transcript_segments.id | SET NULL |

C(action_items) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| idx_tasks_meeting_status | meeting_id, task_status | INDEX |
| idx_tasks_deadline_status | deadline_normalized, task_status | INDEX |

### action_item_owners

Model: `app/models/action_item_owner.py`.

C(action_item_owners) — canonical columns:

| Field | MySQL type | Nullable | Default | Key / constraint | FK target |
| --- | --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK | - |
| action_item_id | BIGINT UNSIGNED | NO | - | INDEX, FK | action_items.id |
| speaker_id | BIGINT UNSIGNED | YES | NULL | INDEX, FK | speakers.id |
| owner_name | VARCHAR(120) | NO | - | INDEX | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | - | - |

R(action_item_owners) — canonical relationships:

| Parent | Child | Cardinality | Foreign key | ON DELETE |
| --- | --- | --- | --- | --- |
| action_items | action_item_owners | 1:N | action_item_owners.action_item_id -> action_items.id | CASCADE |
| speakers | action_item_owners | 1:N | action_item_owners.speaker_id -> speakers.id | SET NULL |

C(action_item_owners) — indexes from INDEXES (column-level keys above also apply):

| Index | Columns | Type |
| --- | --- | --- |
| idx_owner_name | owner_name | INDEX |

## Service constraints and transaction boundaries

These rules are requirements for later implementation, not implemented SQL CHECK constraints or new columns.

- F005/F140 and BR01: enforce session user_id ownership on all private access. A valid child FK alone is not authorization.
- F079 and EX12: evidence must belong to the same meeting as its output item. F052 and EX13: speaker mappings must remain within the meeting. Output ai_run_id must also identify the corresponding meeting.
- F141 and BR02: store password hashes only; validate/normalize email before uniqueness checks. Session logout does not require a new session table.
- F024: configured upload limit is not a database column. F026/F142: server-generated paths and private serving. Filesystem deletion needs safe containment checks; a SQL cascade does not delete files.
- F030–F034, BR13–BR14: one conflicting active job per meeting; preserve checkpoints and successful transcript data when later AI fails. Persist stages independently, not one transaction for the entire pipeline.
- F116–F117, BR16 and UC25: block meeting deletion while processing; execute database deletion transactionally and handle associated files safely. File/DB recovery details remain a decision below.
- F043/F061 and BR05–BR06: never overwrite raw_text on user edits. Effective text uses edited_text when non-null, otherwise raw_text. An empty edit is not automatically equivalent to null.
- F076 and BR12: one task may have zero or many owner rows. Owner text can exist without a speaker FK. Do not create an extra user-owner relationship.
- F077–F078 and BR11: retain deadline_raw; normalize only when grounded. deadline_normalized remains nullable. Overdue is computed from date and task status, not persisted as a new field.
- F074/F083 and BR07–BR10: preserve final semantic state, allow empty structured outputs, reject hallucinated owners/deadlines, and treat transcript instructions as untrusted data.
- F094: regeneration must not overwrite user edits without confirmation. Save validated output atomically, including task-owner rows. Do not rerun ASR for text-only reanalysis.
- F095 and BR15: AI-created minutes are DRAFT until explicit user confirmation; meeting processing status and review_status are separate fields.
- API numeric constraints such as progress 0–100 and text lengths must be validated even where unsigned types do not enforce the full business range. Whether to add DB CHECK constraints is not prescribed.
- No database schema or seed writes are necessary for Phase 1.5 foundation health checks.

## Resolved documentation differences

| Difference | Resolution and authority |
| --- | --- |
| Seven model placeholders versus eleven MVP tables | Database Design defines the schema; preserve existing modules and plan four additional modules. Use Speaker in participant.py and TranscriptSegment in transcript.py. No participants table. |
| editable_text / clean transcript versus edited_text | Preserve raw/edited separation required by F043/F061. Use the concrete edited_text column from DB/API and BR06 effective-text selection. |
| Function route suggestions versus concrete API paths | Function column is explicitly “Route/API gợi ý” (suggested). Use API A030 POST /api/meetings/{meeting_id}/audio and A063 /reanalyze for interfaces; these preserve the higher-priority functions. No routes are added in this phase. |
| Generic pending/completed examples in AGENTS versus DB enums | Use canonical DB enums verbatim, including task TODO/IN_PROGRESS/DONE/CANCELLED and separate job/meeting/review state enums. |
| AI owners array versus a single illustrative owner | BR12 and Database Design require action_item_owners, cardinality 0..N; no scalar owner column in action_items. |
| Model evidence arrays versus one DB evidence FK | Keep the documented MVP primary evidence_segment_id; AI DB_MAPPING expressly allows one primary reference. Do not invent an evidence join table. Primary-reference selection remains a decision below. |
| AI confidence for key points/risks/questions versus no column | Retain the canonical DB columns. AI contract itself acknowledges that those confidence values need not be stored in this schema. |
| Video, exports, risks/questions and snapshots appear in broader documents | Function Dataset marks F028, F120/F121, F081/F082 and F096 advanced. Do not promote them to MVP. Risks/open_questions keys may remain empty in an AI response without introducing MVP tables. |
| Missing decision/owner/deadline treated as possible error | F083 and BR07 require []/null as valid states. No fabricated task, owner or deadline rows. |
| Corrupt audio state differs between F025 and UC upload exception wording | F025 explicitly expects FAILED for corrupt media; higher-priority function wins for that case. Unsupported extension/oversize remain rejected before processing. Detailed upload timing can be specified in its later phase. |
| Timestamp end equals start allowed in AI input | F042 requires start < end, which takes precedence over AI end_ms >= start_ms. Missing timestamps remain unresolved below. |

## Decisions Required

No field, enum, persistence mechanism, or workflow policy below is invented or implemented here.

| ID | Source discrepancy / omission | Decision needed before dependent implementation |
| --- | --- | --- |
| D01 | F042 permits missing timestamp nullable/fallback; DB COLUMNS requires non-null start_ms/end_ms with zero defaults. | Choose an explicit missing-timestamp fallback or authorize nullable columns. Do not fabricate 0/0 as a valid timed segment; start < end remains required. |
| D02 | API A080/REQUEST_FIELDS allows key_points regeneration; ai_runs.run_type has FULL/SUMMARY/DECISIONS/ACTION_ITEMS/RISKS/OPEN_QUESTIONS only. | Specify how a key-points-only run is represented; do not silently use FULL or add KEY_POINTS. |
| D03 | AI README describes schema_version provenance via ai_runs, but DB has no schema_version or metadata JSON column; AI VERSIONING also names input/output JSON and config. | Specify durable schema-version storage, if required per inference. Do not overload prompt_version. |
| D04 | F041 asks to preserve ASR model/version; transcript_segments has no such fields and ai_runs.run_type describes NLP output types. | Specify where ASR model/version is recorded without pretending an NLP run type represents ASR. |
| D05 | COLUMNS has key_points.ai_run_id, decisions.ai_run_id and action_items.ai_run_id FKs, but RELATIONSHIPS states ON DELETE only for summaries.ai_run_id. | Specify ON DELETE for these three FKs. Nullability alone does not establish SET NULL. |
| D06 | F064/F094 require preserving previous results/user edits; summaries and other outputs can have many runs, but there is no active-result pointer and mixed section regeneration is allowed. | Define current-result selection across sections, human-created rows with null ai_run_id, replacement confirmation, and rollback behavior. Do not assume max(id) or latest run solves all sections. |
| D07 | F095 permits locking or continued editing after confirmation; API transitions do not define edit/regenerate after CONFIRMED. | Choose whether edits reset review_status, are rejected, or require a version workflow. |
| D08 | F061 mentions empty/concurrent edits; API A061 permits empty only if a business rule allows it; UI supplies an editor but no complete conflict policy. | Decide empty text acceptance, how to restore raw text, and stale-edit conflict behavior. No optimistic-lock column is added here. |
| D09 | AI OUTPUT_SCHEMA supports multiple evidence refs. DB_MAPPING says first ref for key points and strongest task/final-state ref for actions; long-meeting merge needs correction evidence too. | Define a deterministic primary-evidence selection rule and whether/how full refs or snapshots are retained. No log-storage format is prescribed. |
| D10 | F030–F034/BR14 require no conflicting jobs and checkpoint retry; schema has no unique active-job constraint, checkpoint table, or explicit normalized-file path. | Specify concurrency enforcement, durable checkpoint/artifact identification and restart recovery using or amending the canonical schema. Do not invent columns or a queue technology. |
| D11 | F078/F102 need dates relative to meeting_date/today; DB DATETIME has no timezone, API uses ISO datetime, and no user timezone policy exists. | Define storage/API timezone convention and “today” for overdue/relative dates. Do not assume the developer machine timezone. |
| D12 | F116/F117 require both database and file deletion; UC25 describes success but not partial filesystem failure recovery. | Define deletion ordering and recovery if file removal fails or the DB transaction fails. No outbox/soft-delete fields are added here. |

D01, D02, D03, D04 and D05 are direct schema-mapping blockers for the affected fields/relationships. D06–D12 must be resolved before their services are implemented and may affect schema choices. They do not block the foundation changes in this phase.

## Review and later implementation gate

- Coverage: all 86 Function IDs appear exactly once in the function mapping (74 MVP, 12 advanced).
- Scope: exactly 11 MVP table inventories; all canonical MVP columns are retained.
- Keep app/extensions.py as the sole SQLAlchemy instance.
- Resolve affected Decisions Required entries before creating corresponding schema or services.
- A future database phase may implement models, register metadata, and create migrations in the canonical order only when requested.
- No canonical workbook is edited by this mapping.

## Source fingerprints

SHA-256 of the workbooks read for this phase:

| Workbook | SHA-256 |
| --- | --- |
| MeetingAI_Master_AI_IO_Contract.xlsx | 91D8323D0E5F9A639A4C5378604E2F10DCB231B9797A64FA0807523D78BF8758 |
| MeetingAI_Master_API_Contract.xlsx | 4F40DB01C7679E81BF94416F0F95B44157BF67AFA033EFDEF13714B80B7CB04E |
| MeetingAI_Master_Database_Design.xlsx | 60BD53385B1640F4F06B565DDA1B2B810600523BC15A6B760E5C82C33111E227 |
| MeetingAI_Master_Function_Dataset.xlsx | 32325DC1FD80F6C51FADFD11F95869B4BC4007AB60D7D41D48F84C7C4F27922F |
| MeetingAI_Master_UI_Page_Flow.xlsx | 61E60E0291CAEC9C83FECBC25709DB7030CCBB355E8AAB1C9CAB76B7250CD159 |
| MeetingAI_Master_Use_Case_Specification.xlsx | 28D2AB9FAA489D55A0BCA8B4B9A0AEDA269DF08E68E1758E1A6D37932F883822 |
