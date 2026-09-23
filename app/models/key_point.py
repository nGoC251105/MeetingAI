from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    SMALLINT,
    TIMESTAMP,
    TINYINT,
)

from app.extensions import db


class KeyPoint(db.Model):
    __tablename__ = "key_points"

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

    sort_order = db.Column(
        SMALLINT(unsigned=True),
        nullable=False,
        server_default=text("0")
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

    meeting = db.relationship(
        "Meeting",
        back_populates="key_points"
    )

    ai_run = db.relationship(
        "AIRun",
        back_populates="key_points"
    )

    evidence_segment = db.relationship(
        "TranscriptSegment",
        back_populates="evidence_key_points"
    )

    def __repr__(self):
        return (
            f"<KeyPoint id={self.id} "
            f"meeting_id={self.meeting_id}>"
        )