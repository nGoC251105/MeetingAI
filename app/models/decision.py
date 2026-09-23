from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    ENUM,
    TIMESTAMP,
    TINYINT,
)

from app.extensions import db


class Decision(db.Model):
    __tablename__ = "decisions"

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

    ai_run_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "ai_runs.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    decision_status = db.Column(
        ENUM(
            "CONFIRMED",
            "TENTATIVE",
            "REJECTED",
            "SUPERSEDED"
        ),
        nullable=False,
        server_default=text("'CONFIRMED'")
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
        back_populates="decisions"
    )

    ai_run = db.relationship(
        "AIRun",
        back_populates="decisions"
    )

    evidence_segment = db.relationship(
        "TranscriptSegment",
        back_populates="evidence_decisions"
    )

    __table_args__ = (
        db.Index(
            "idx_decisions_status",
            "decision_status"
        ),
        db.Index(
            "idx_decisions_confidence",
            "confidence_level"
        ),
    )

    def __repr__(self):
        return (
            f"<Decision id={self.id} "
            f"meeting_id={self.meeting_id} "
            f"status={self.decision_status}>"
        )