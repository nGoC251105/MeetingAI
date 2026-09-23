from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    ENUM,
    TIMESTAMP,
)

from app.extensions import db


class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    meeting_date = db.Column(
        db.DateTime,
        nullable=True
    )

    language = db.Column(
        db.String(10),
        nullable=False,
        server_default=text("'vi'")
    )

    status = db.Column(
        ENUM(
            "DRAFT",
            "UPLOADED",
            "PREPROCESSING",
            "TRANSCRIBING",
            "DIARIZING",
            "ANALYZING",
            "COMPLETED",
            "FAILED"
        ),
        nullable=False,
        server_default=text("'DRAFT'")
    )

    review_status = db.Column(
        ENUM(
            "DRAFT",
            "CONFIRMED"
        ),
        nullable=False,
        server_default=text("'DRAFT'")
    )

    original_filename = db.Column(
        db.String(255),
        nullable=True
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=True,
        unique=True
    )

    audio_path = db.Column(
        db.String(500),
        nullable=True
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True
    )

    file_size_bytes = db.Column(
        BIGINT(unsigned=True),
        nullable=True
    )

    duration_seconds = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    error_code = db.Column(
        db.String(64),
        nullable=True
    )

    failed_step = db.Column(
        db.String(64),
        nullable=True
    )

    audio_deleted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = db.Column(
        TIMESTAMP,
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )
    )

    user = db.relationship(
        "User",
        back_populates="meetings"
    )
    processing_jobs = db.relationship(
        "ProcessingJob",
        back_populates="meeting",
        passive_deletes=True
    )

    speakers = db.relationship(
        "Speaker",
        back_populates="meeting",
        passive_deletes=True
    )
    transcript_segments = db.relationship(
        "TranscriptSegment",
        back_populates="meeting",
        passive_deletes=True
    )

    ai_runs = db.relationship(
        "AIRun",
        back_populates="meeting",
        passive_deletes=True
    )
    summaries = db.relationship(
        "Summary",
        back_populates="meeting",
        passive_deletes=True
    )

    key_points = db.relationship(
        "KeyPoint",
        back_populates="meeting",
        passive_deletes=True
    )

    decisions = db.relationship(
        "Decision",
        back_populates="meeting",
        passive_deletes=True
    )
    action_items = db.relationship(
        "ActionItem",
        back_populates="meeting",
        passive_deletes=True
    )

    __table_args__ = (
        db.Index(
            "idx_meetings_user_created",
            "user_id",
            "created_at"
        ),
        db.Index(
            "idx_meetings_user_status",
            "user_id",
            "status"
        ),
        db.Index(
            "idx_meetings_user_date",
            "user_id",
            "meeting_date"
        ),
        db.Index(
            "idx_meetings_title",
            "title"
        ),
        db.Index(
            "idx_meetings_error_code",
            "error_code"
        ),
        db.Index(
            "idx_meetings_review_status",
            "review_status"
        ),
    )

    def __repr__(self):
        return (
            f"<Meeting id={self.id} "
            f"title={self.title!r} "
            f"status={self.status}>"
        )