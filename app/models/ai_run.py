from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    ENUM,
    INTEGER,
    TIMESTAMP,
    TINYINT,
)

from app.extensions import db


class AIRun(db.Model):
    __tablename__ = "ai_runs"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    meeting_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "meetings.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    run_type = db.Column(
        ENUM(
            "FULL",
            "SUMMARY",
            "DECISIONS",
            "ACTION_ITEMS",
            "RISKS",
            "OPEN_QUESTIONS"
        ),
        nullable=False,
        server_default=text("'FULL'")
    )

    model_name = db.Column(
        db.String(120),
        nullable=False
    )

    model_version = db.Column(
        db.String(120),
        nullable=False
    )

    dataset_version = db.Column(
        db.String(120),
        nullable=True
    )

    prompt_version = db.Column(
        db.String(120),
        nullable=True
    )

    # D03 - lưu schema AI riêng biệt
    schema_version = db.Column(
        db.String(50),
        nullable=True
    )

    status = db.Column(
        ENUM(
            "RUNNING",
            "COMPLETED",
            "FAILED"
        ),
        nullable=False,
        server_default=text("'RUNNING'")
    )

    processing_ms = db.Column(
        INTEGER(unsigned=True),
        nullable=True
    )

    input_chars = db.Column(
        INTEGER(unsigned=True),
        nullable=True
    )

    input_tokens = db.Column(
        INTEGER(unsigned=True),
        nullable=True
    )

    error_code = db.Column(
        db.String(64),
        nullable=True
    )

    # D06 - run đã được chấp nhận làm kết quả hiện tại hay chưa
    is_accepted = db.Column(
        TINYINT(display_width=1),
        nullable=False,
        server_default=text("0")
    )

    accepted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    meeting = db.relationship(
        "Meeting",
        back_populates="ai_runs"
    )
    summaries = db.relationship(
        "Summary",
        back_populates="ai_run",
        passive_deletes=True
    )

    key_points = db.relationship(
        "KeyPoint",
        back_populates="ai_run",
        passive_deletes=True
    )

    decisions = db.relationship(
        "Decision",
        back_populates="ai_run",
        passive_deletes=True
    )
    action_items = db.relationship(
        "ActionItem",
        back_populates="ai_run",
        passive_deletes=True
    )

    __table_args__ = (
        db.Index(
            "idx_airuns_meeting_created",
            "meeting_id",
            "created_at"
        ),
        db.Index(
            "idx_airuns_run_type",
            "run_type"
        ),
        db.Index(
            "idx_airuns_model_name",
            "model_name"
        ),
        db.Index(
            "idx_airuns_model_version",
            "model_version"
        ),
        db.Index(
            "idx_airuns_status",
            "status"
        ),
        db.Index(
            "idx_airuns_created_at",
            "created_at"
        ),
    )

    def __repr__(self):
        return (
            f"<AIRun id={self.id} "
            f"meeting_id={self.meeting_id} "
            f"run_type={self.run_type} "
            f"status={self.status}>"
        )