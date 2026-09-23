from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    ENUM,
    JSON,
    TIMESTAMP,
    TINYINT,
)

from app.extensions import db


class ProcessingJob(db.Model):
    __tablename__ = "processing_jobs"

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

    job_type = db.Column(
        ENUM(
            "FULL",
            "TRANSCRIBE",
            "DIARIZE",
            "ANALYZE",
            "REGENERATE"
        ),
        nullable=False,
        server_default=text("'FULL'")
    )

    status = db.Column(
        ENUM(
            "QUEUED",
            "RUNNING",
            "COMPLETED",
            "FAILED",
            "CANCELLED"
        ),
        nullable=False,
        server_default=text("'QUEUED'")
    )

    progress_percent = db.Column(
        TINYINT(unsigned=True),
        nullable=False,
        server_default=text("0")
    )

    current_step = db.Column(
        db.String(64),
        nullable=True
    )

    error_code = db.Column(
        db.String(64),
        nullable=True
    )

    error_message = db.Column(
        db.String(500),
        nullable=True
    )

    started_at = db.Column(
        db.DateTime,
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # D04 - ASR provenance
    asr_model_name = db.Column(
        db.String(120),
        nullable=True
    )

    asr_model_version = db.Column(
        db.String(120),
        nullable=True
    )

    # D10 - checkpoint / recovery
    checkpoint_stage = db.Column(
        db.String(64),
        nullable=True
    )

    checkpoint_data = db.Column(
        JSON,
        nullable=True
    )

    heartbeat_at = db.Column(
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
        back_populates="processing_jobs"
    )

    __table_args__ = (
        db.Index(
            "idx_jobs_meeting_created",
            "meeting_id",
            "created_at"
        ),
        db.Index(
            "idx_jobs_job_type",
            "job_type"
        ),
        db.Index(
            "idx_jobs_status",
            "status"
        ),
    )

    def __repr__(self):
        return (
            f"<ProcessingJob id={self.id} "
            f"meeting_id={self.meeting_id} "
            f"status={self.status}>"
        )