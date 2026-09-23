
Có. Với project này thì nên đưa thêm các file yêu cầu quan trọng cho Codex, nhưng không cần quăng tất cả file linh tinh vào repo.

Quan trọng nhất là file đã chốt làm nguồn chuẩn:

MeetingAI_Master_Function_Dataset.xlsx
vì đây là bộ 86 chức năng canonical mà mình đã thống nhất. Codex nên đọc file này trước khi build các module lớn để tránh sinh sai chức năng hoặc bỏ sót.

T khuyên tạo thư mục:

C:\Projects\MeetingAI\docs\
rồi để:

docs/
├── MeetingAI_Master_Function_Dataset.xlsx
├── SRS_MeetingAI.docx          # nếu đã có bản SRS ổn
├── Database_Design.xlsx        # nếu có
└── Architecture/
Nhưng có một điểm quan trọng: AGENTS.md là nơi Codex tự đọc instruction dự án trước mỗi task, còn các file Excel/Docx là tài liệu tham chiếu và nên được prompt chỉ rõ cần đọc file nào. Codex chính thức có cơ chế đọc AGENTS.md từ project root và dùng nó làm project instructions. 

Ví dụ sau này prompt:

Read AGENTS.md first.

Then inspect:
docs/MeetingAI_Master_Function_Dataset.xlsx

Treat that Excel file as the canonical functional requirement source.

Current task:
Design the database schema required to support those functions.

Do not implement AI or frontend yet.
Before coding, produce a mapping:
Function -> Required entity/table -> Main fields.
Còn tốt hơn nữa là mình chuyển sheet quan trọng trong Excel sang CSV hoặc Markdown để Codex đọc ổn định hơn:

docs/requirements/
├── MeetingAI_Master_Function_Dataset.xlsx
├── functions.csv
└── FUNCTION_REQUIREMENTS.md
Trong đó .xlsx giữ làm bản gốc, còn .csv/.md để AI tra nhanh. Không nên bỏ file Excel gốc.

Nếu m gửi cho t các file Excel hiện có của MeetingAI, t có thể lọc cho m luôn: file nào cần đưa vào Codex, file nào không cần, và tổ chức lại docs/ thế nào để Codex build đúng nhất.


Hôm nay 20:02
aa5581b9-530a-4727-884b-551d66d4b27f.png

Đúng rồi, Codex extension của m đã cài vào VS Code. Ảnh này chỉ còn vướng bước:

Finish Windows setup to continue

Ở panel Codex bên phải.

Làm theo thứ tự này:

Bấm Continue ở khung Finish Windows setup to continue.

Làm hết phần thiết lập Windows mà Codex yêu cầu. Nếu nó yêu cầu restart VS Code/extension thì bấm Restart Extensions.

Sau khi panel Codex hiện ô chat bình thường, đăng nhập bằng tài khoản ChatGPT này nếu nó hỏi.

Đảm bảo workspace đang là:

C:\Projects\MeetingAI
và terminal có:

(.venv) PS C:\Projects\MeetingAI>
Copy AGENTS.md t đã tạo vào root project, ngang hàng với run.py:

MeetingAI/
├── AGENTS.md
├── run.py
├── config.py
├── requirements.txt
├── app/
└── ...
Tạo thêm:

MeetingAI/docs/
rồi cho MeetingAI_Master_Function_Dataset.xlsx vào đó.

Sau đó prompt đầu tiên cho Codex:

Read AGENTS.md first.

Then inspect the entire current repository without changing anything yet.

Also inspect:
docs/MeetingAI_Master_Function_Dataset.xlsx

Treat that Excel file as the canonical functional requirement source.

Tell me:
1. Current project status
2. What is already implemented
3. What is still empty or incomplete
4. Any architecture problems
5. The next recommended implementation phase

Do not modify files yet.
Chưa bảo Codex build cả project ngay. Để nó đọc và audit project trước, sau đó gửi t kết quả Codex trả về; t sẽ viết prompt tiếp theo để nó bắt đầu build đúng phase.


c903d942-514e-47c7-a567-4b33960d1e77.png
Nnay đủ chưa

Ừ, như ảnh này là gần như đủ bộ tài liệu để Codex build rồi. Thậm chí tốt hơn chỉ đưa mỗi file chức năng, vì trong docs/ m đã có đủ 6 lớp thiết kế:

docs/
├── MeetingAI_Master_Function_Dataset.xlsx       ✅ Chức năng chuẩn
├── MeetingAI_Master_AI_IO_Contract.xlsx         ✅ Input/Output AI
├── MeetingAI_Master_Use_Case_Specification.xlsx ✅ Luồng Use Case
├── MeetingAI_Master_UI_Page_Flow.xlsx           ✅ Luồng giao diện
├── MeetingAI_Master_API_Contract.xlsx           ✅ API
└── MeetingAI_Master_Database_Design.xlsx        ✅ Database
Bộ này rất ổn để Codex hiểu hệ thống từ requirement → use case → UI → API → DB → AI.

Nhưng ảnh hiện tại còn 2 việc cần làm trước khi cho Codex code:

1. Thiếu AGENTS.md ở root
Trong Explorer t chưa thấy AGENTS.md.

Nó phải nằm ngang hàng với:

MeetingAI/
├── AGENTS.md          ← THÊM Ở ĐÂY
├── .env
├── .gitignore
├── config.py
├── README.md
├── requirements.txt
├── run.py
├── app/
├── docs/
└── ...
Không để AGENTS.md trong docs/.

File t tạo lúc trước:

AGENTS.md cho MeetingAI

Copy nó vào:

C:\Projects\MeetingAI\AGENTS.md
2. Codex vẫn chưa setup xong
Bên phải vẫn còn:

Finish Windows setup to continue
→ bấm:

Continue
làm xong bước đó trước.

Khi ô chat Codex hoạt động bình thường thì mới giao task.

Sau khi xong, prompt đầu tiên nên dùng bản này, vì giờ m có đủ 6 Excel:

Read AGENTS.md first.

Then inspect the current MeetingAI repository.

Read and use all canonical documents in /docs:

1. docs/MeetingAI_Master_Function_Dataset.xlsx
2. docs/MeetingAI_Master_Use_Case_Specification.xlsx
3. docs/MeetingAI_Master_UI_Page_Flow.xlsx
4. docs/MeetingAI_Master_API_Contract.xlsx
5. docs/MeetingAI_Master_Database_Design.xlsx
6. docs/MeetingAI_Master_AI_IO_Contract.xlsx

Priority when resolving implementation decisions:

1. Master_Function_Dataset = canonical functional scope
2. Use_Case_Specification = business flows and exceptions
3. Database_Design = data structure
4. API_Contract = backend interface
5. UI_Page_Flow = frontend navigation and screens
6. AI_IO_Contract = AI input/output contracts
7. AGENTS.md = architecture and development rules

Do not modify anything yet.

First perform a project audit and report:

1. Current implementation status
2. Existing files that already contain working code
3. Empty/incomplete files
4. Differences between current code and /docs specifications
5. Missing dependencies
6. Architecture issues
7. Recommended development phases
8. Which module should be implemented next

Do not generate the entire system yet.
Do not change the technology stack.
Do not delete or rename existing architecture.
Cho Codex chạy prompt này trước.

Đừng bảo nó "build full project" ngay. Khi Codex trả bản audit, gửi kết quả sang đây. T sẽ đối chiếu và viết cho m prompt Phase 2 – Database hoặc phase phù hợp để bắt đầu cho Codex code thật.

Với bộ 6 Excel + AGENTS.md này thì context cho Codex đã đủ mạnh để làm project bài bản, không cần thêm tài liệu khác ở thời điểm hiện tại.


AGENTS.md
Tài liệu


Thư viện
/
Hệ Thống Tóm Tắt Nội Dung cuộc họp
/
AGENTS.md



AGENTS.md — MeetingAI
1. Project identity
Project name: MeetingAI
Vietnamese topic: Hệ thống AI tự động ghi nhận và tạo biên bản cuộc họp.

This repository is a student intelligent-system project that processes meeting audio/video into structured meeting notes.

The system must support the pipeline:

Audio / Video
→ FFmpeg preprocessing
→ Faster-Whisper ASR
→ Speaker diarization
→ Transcript normalization
→ Smart / semantic chunking
→ Summarization + information extraction
→ Store results in MySQL
→ Display and manage results through Flask web UI

Expected AI outputs include:

Full transcript

Speaker-separated transcript

Meeting summary

Key points

Decisions

Action items

Owner / assignee

Deadline

Risks

Open questions

2. Canonical requirements
The canonical functional requirement source for the project is:

MeetingAI_Master_Function_Dataset.xlsx

It contains 86 functions and must be treated as the authoritative functional scope.

Rules:

Do not invent major features that conflict with the canonical function dataset.

Do not silently remove or merge required functions.

If a requested implementation conflicts with the canonical requirements, report the conflict first.

Implement incrementally by module.

Avoid generating the entire system in one uncontrolled step.

3. Fixed technology stack
Do not replace this stack unless explicitly instructed.

Backend
Python 3.13

Flask

Flask-SQLAlchemy

Flask-Migrate

PyMySQL

python-dotenv

Database
MySQL 8.x

Database name: meeting_ai

Default local port: 3306

Frontend
HTML

CSS

JavaScript

Jinja2

Bootstrap may be used

Do not migrate the project to React, Vue, Next.js, FastAPI, Django, Node.js, or another framework unless explicitly requested.

Audio / video
FFmpeg

Speech-to-text
Faster-Whisper

Speaker diarization
pyannote.audio

AI / NLP
PyTorch

Hugging Face Transformers

Sentence-Transformers when semantic chunking is needed

Fine-tuning
PEFT

LoRA / QLoRA

Fine-tuning is a later phase. Do not make it a prerequisite for basic system operation.

4. Local development environment
Primary project directory:

C:\Projects\MeetingAI
Python virtual environment:

C:\Projects\MeetingAI\.venv
Expected interpreter:

C:\Projects\MeetingAI\.venv\Scripts\python.exe
Always prefer the project virtual environment.

Typical PowerShell activation:

.\.venv\Scripts\Activate.ps1
Expected prompt:

(.venv) PS C:\Projects\MeetingAI>
Installed system tools:

Git

FFmpeg

MySQL Server

MySQL Workbench

Do not use the old OneDrive copy of the project if it still exists.

5. Current repository structure
The project follows this architecture:

MeetingAI/
│
├── run.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   │
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── meeting_routes.py
│   │   ├── transcript_routes.py
│   │   ├── summary_routes.py
│   │   └── export_routes.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── meeting.py
│   │   ├── participant.py
│   │   ├── transcript.py
│   │   ├── summary.py
│   │   ├── decision.py
│   │   └── action_item.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── meeting_service.py
│   │   ├── audio_service.py
│   │   ├── transcript_service.py
│   │   ├── summary_service.py
│   │   └── export_service.py
│   │
│   ├── ai/
│   │   ├── pipeline.py
│   │   ├── asr/
│   │   │   └── whisper_service.py
│   │   ├── diarization/
│   │   │   └── speaker_service.py
│   │   ├── preprocessing/
│   │   │   ├── text_cleaner.py
│   │   │   └── chunker.py
│   │   ├── summarization/
│   │   │   └── summarizer.py
│   │   └── extraction/
│   │       ├── decision_extractor.py
│   │       ├── action_extractor.py
│   │       └── deadline_extractor.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── seed.py
│   │
│   ├── utils/
│   │   ├── file_utils.py
│   │   ├── audio_utils.py
│   │   └── validators.py
│   │
│   ├── templates/
│   │   ├── auth/
│   │   ├── meetings/
│   │   ├── transcript/
│   │   └── summary/
│   │
│   └── static/
│       ├── css/
│       ├── js/
│       ├── images/
│       └── icons/
│
├── storage/
│   ├── uploads/
│   ├── audio/
│   ├── processed/
│   ├── temp/
│   └── exports/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── gold/
│   ├── silver/
│   └── synthetic/
│
├── trained_models/
│   ├── whisper/
│   ├── diarization/
│   ├── summarization/
│   └── extraction/
│
├── scripts/
│   ├── init_database.py
│   ├── test_database.py
│   ├── test_ffmpeg.py
│   └── test_whisper.py
│
└── tests/
    ├── test_auth.py
    ├── test_meeting.py
    ├── test_asr.py
    ├── test_summary.py
    └── test_pipeline.py
Do not flatten the architecture into a single large app.py.

6. Architecture rules
Use this dependency direction:

Browser / UI
    ↓
Routes
    ↓
Services
    ↓
Models / Database
AI processing should follow:

Services
    ↓
AI Pipeline
    ↓
FFmpeg / ASR / Diarization / NLP
Routes
Routes should:

receive request data

validate basic request shape

call service functions

return HTML or JSON responses

Routes should not contain large AI, database, or business logic.

Services
Services contain:

application business logic

orchestration

transactions

calls to AI modules

calls to model/query layer

Models
Models define database entities and relationships.

AI modules
AI modules should remain independently testable and should not directly depend on Flask request/session objects.

7. Configuration and secrets
Configuration must be loaded from .env.

Never hard-code:

MySQL password

Hugging Face token

API keys

secret keys

credentials

Example environment keys:

FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True

SECRET_KEY=change-me

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=change-me
DB_NAME=meeting_ai

HF_TOKEN=
.env must stay in .gitignore.

8. Flask application pattern
Use Flask application factory.

Expected design:

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints here

    return app
Extensions belong in:

app/extensions.py
Typical extensions:

db = SQLAlchemy()
migrate = Migrate()
9. Database rules
Target database:

meeting_ai
Character set:

utf8mb4
Use SQLAlchemy models and Flask-Migrate for schema evolution.

Do not manually modify production-like schemas when a migration should be used.

Core domain entities currently planned:

User

Meeting

Participant

Transcript

Summary

Decision

ActionItem

Before adding tables, verify the relation against the functional requirements.

Avoid duplicated data where a proper relationship is available.

Use foreign keys intentionally.

Use timestamps where useful, such as:

created_at

updated_at

started_at

ended_at

10. AI pipeline design
Target pipeline:

Input file
→ validation
→ storage
→ FFmpeg normalization
→ Faster-Whisper transcription
→ diarization
→ speaker-transcript alignment
→ text cleaning
→ chunking
→ summarization
→ structured extraction
→ database persistence
→ UI
Each stage should produce an inspectable intermediate result where practical.

Do not make the pipeline one monolithic function.

Suggested stages:

validate_input()

normalize_media()

transcribe()

diarize()

align_speakers()

clean_transcript()

chunk_transcript()

summarize_chunks()

merge_summary()

extract_decisions()

extract_action_items()

extract_deadlines()

persist_results()

11. Long-meeting requirements
The system must be designed for long meetings.

Do not pass arbitrarily long transcripts directly into one model call.

Use chunking.

Preferred strategy:

Transcript
→ semantic / length-aware chunks
→ summarize each chunk
→ merge chunk summaries
→ final summary
Preserve timestamps and speaker references where possible.

Do not split text in the middle of a sentence merely to hit a token count unless necessary.

12. Speaker diarization requirements
Expected result format should support:

[00:00:05 - 00:00:12] Speaker 1: ...
[00:00:13 - 00:00:21] Speaker 2: ...
Speaker labels may initially be:

Speaker 1

Speaker 2

Speaker 3

A later user-facing step may allow mapping anonymous speaker labels to participant names.

Do not assume diarization automatically knows real participant identities.

13. Summarization output structure
The summary layer should be capable of producing structured data similar to:

{
  "summary": "...",
  "key_points": [],
  "decisions": [],
  "action_items": [],
  "risks": [],
  "open_questions": []
}
An action item should be structured when possible:

{
  "task": "...",
  "owner": "...",
  "deadline": "...",
  "status": "pending"
}
Do not force a field value when the transcript does not contain enough information.

Use null / empty values instead of hallucinating an owner or deadline.

14. Dataset strategy
The project may use multiple dataset tiers:

data/raw
data/processed
data/gold
data/silver
data/synthetic
Meaning:

raw: unprocessed source data

processed: normalized or transformed data

gold: manually reviewed, high-quality examples

silver: automatically generated or weakly supervised examples

synthetic: generated examples for augmentation

Do not treat synthetic or silver labels as equivalent to manually reviewed gold data.

15. Model strategy
Do not train a large model from scratch.

Preferred student-project strategy:

Start with pretrained models.

Build a working end-to-end baseline.

Evaluate baseline.

Prepare domain-specific meeting dataset.

Fine-tune only the component that gives meaningful benefit.

Prefer LoRA / QLoRA when fine-tuning large transformer models.

Possible summarization models may include Vietnamese-capable encoder-decoder or instruction models, but model choice should be evaluated before locking.

16. Development phases
Follow this order unless explicitly instructed otherwise.

Phase 1 — Foundation
Python virtual environment

Flask app factory

configuration

MySQL connection

health check

project structure

Phase 2 — Database
schema design

SQLAlchemy models

relationships

migrations

seed/test data

Phase 3 — Authentication
register

login

logout

session handling

authorization where required

Phase 4 — Meeting management
create meeting

update meeting

delete/archive where required

meeting list/history

meeting details

Phase 5 — Media handling
upload audio/video

validate extension and size

save safely

FFmpeg normalization

Phase 6 — ASR
Faster-Whisper integration

timestamps

language handling

transcript persistence

Phase 7 — Speaker diarization
pyannote.audio

speaker segments

speaker-ASR alignment

Phase 8 — NLP
cleaning

smart chunking

summaries

decisions

action items

deadlines

risks

open questions

Phase 9 — UI
dashboard

meeting pages

transcript page

summary page

editing

history/search

Phase 10 — Export
meeting minutes

DOCX/PDF where required

structured export

Phase 11 — Dataset and evaluation
gold/silver/synthetic sets

evaluation metrics

human review

baseline comparison

Phase 12 — Fine-tuning
LoRA / QLoRA

experiment tracking

model comparison

Phase 13 — Testing and hardening
unit tests

integration tests

long meeting tests

invalid file tests

missing speaker/deadline tests

error recovery

17. Coding rules
When editing the repository:

Read the relevant existing files first.

Do not overwrite unrelated work.

Do not rename folders without a clear reason.

Keep functions reasonably small.

Prefer clear names over abbreviations.

Add comments only where logic is non-obvious.

Avoid duplicate logic.

Avoid circular imports.

Validate user-provided file paths and uploads.

Use pathlib or safe path utilities where practical.

Handle exceptions at appropriate boundaries.

Do not expose raw secrets or credentials in error output.

Do not silently swallow exceptions.

Keep AI/model loading reusable rather than loading a model for every request.

Preserve Vietnamese Unicode correctly.

18. Security rules
At minimum:

Never commit .env.

Validate uploaded file extension and MIME/type where possible.

Generate safe server-side filenames.

Do not execute uploaded files.

Prevent path traversal.

Store passwords hashed, never plain text.

Do not expose full tracebacks to end users in production mode.

Restrict file size.

Restrict supported media types.

Validate IDs from routes before database access.

19. Performance rules
AI models are expensive to load.

Do not load Faster-Whisper or summarization models once per HTTP request if avoidable.

Use reusable service/model instances or a controlled lazy-loading strategy.

Long-running AI jobs should be designed so the UI can represent:

pending

processing

completed

failed

Do not assume transcription of a long meeting completes instantly.

20. Testing requirements
Each major layer should be testable independently.

Minimum categories:

configuration test

database connection test

model tests

route tests

upload validation

FFmpeg test

ASR test

summarization test

pipeline test

Do not consider a feature complete only because its happy path works manually.

21. Git rules
Before large changes:

git status
After a coherent milestone, create a commit.

Do not commit:

.venv/
.env
trained_models/*
storage/uploads/*
storage/audio/*
storage/temp/*
large datasets
Do not use destructive Git commands unless explicitly requested.

22. Codex operating instructions
When given a task:

Inspect relevant files first.

State a short implementation plan.

Modify only files required for the current task.

Run relevant tests or validation commands.

Report:

files changed

commands executed

test results

unresolved issues

Stop after the requested phase.

Do not automatically continue into later phases.

If a task is ambiguous, preserve the existing architecture and choose the least disruptive implementation.

23. Current development status
Environment prepared:

Python 3.13 virtual environment: ready

Flask: installed

Flask-SQLAlchemy: installed

Flask-Migrate: installed

PyMySQL: installed

python-dotenv: installed

Git: ready

FFmpeg: ready

MySQL 8: ready

Current immediate milestone:

Flask
→ configuration
→ MySQL connection
→ / endpoint
→ /health endpoint
Do not implement Whisper, diarization, summarization, or model training until the basic backend/database foundation is confirmed stable.

24. First Codex task
Use the following initial task if the foundation is not yet fully verified:

Read AGENTS.md and inspect the current MeetingAI repository.

Do not change the technology stack or folder architecture.

Current task only:
1. Inspect run.py, config.py, app/__init__.py, app/extensions.py and .env usage.
2. Fix the Flask application factory if necessary.
3. Confirm SQLAlchemy and Flask-Migrate initialization.
4. Ensure GET / returns a simple backend-running response.
5. Ensure GET /health executes SELECT 1 against MySQL and returns whether the database is connected.
6. Do not implement models, authentication, AI, Whisper, diarization, UI or migrations yet.
7. Do not hard-code credentials.
8. Run the project using the existing .venv interpreter.
9. Test the endpoints.
10. Report exactly what changed and any remaining issue.

Before editing, show a brief plan.
After editing, run the required checks.
25. Core principle
Build the system vertically and incrementally.

A small end-to-end feature that works is preferred over a large amount of generated code that has not been integrated or tested.

The target is not merely to generate code. The target is to produce a stable, demonstrable MeetingAI system whose implementation remains traceable to the canonical 86-function requirement dataset.

