from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    ENUM,
    TIMESTAMP,
    TINYINT,
)

from app.extensions import db


class ActionItem(db.Model):
    __tablename__ = "action_items"

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

    # D05: giữ task nếu AI run bị xóa
    ai_run_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "ai_runs.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    task = db.Column(
        db.Text,
        nullable=False
    )

    deadline_raw = db.Column(
        db.String(255),
        nullable=True
    )

    deadline_normalized = db.Column(
        db.Date,
        nullable=True
    )

    task_status = db.Column(
        ENUM(
            "TODO",
            "IN_PROGRESS",
            "DONE",
            "CANCELLED"
        ),
        nullable=False,
        server_default=text("'TODO'")
    )

    confidence_level = db.Column(
        ENUM(
            "HIGH",
            "MEDIUM",
            "LOW"
        ),
        nullable=True
    )

    evidence_segment_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "transcript_segments.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    is_user_edited = db.Column(
        TINYINT(display_width=1),
        nullable=False,
        server_default=text("0")
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

    meeting = db.relationship(
        "Meeting",
        back_populates="action_items"
    )

    ai_run = db.relationship(
        "AIRun",
        back_populates="action_items"
    )

    evidence_segment = db.relationship(
        "TranscriptSegment",
        back_populates="evidence_action_items"
    )

    owners = db.relationship(
        "ActionItemOwner",
        back_populates="action_item",
        passive_deletes=True
    )

    __table_args__ = (
        db.Index(
            "idx_tasks_meeting_status",
            "meeting_id",
            "task_status"
        ),
        db.Index(
            "idx_tasks_deadline_status",
            "deadline_normalized",
            "task_status"
        ),
        db.Index(
            "idx_tasks_confidence",
            "confidence_level"
        ),
        db.Index(
            "idx_tasks_created_at",
            "created_at"
        ),
    )

    def __repr__(self):
        return (
            f"<ActionItem id={self.id} "
            f"meeting_id={self.meeting_id} "
            f"status={self.task_status}>"
        )