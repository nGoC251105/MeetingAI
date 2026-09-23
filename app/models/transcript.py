from sqlalchemy import text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    INTEGER,
    TIMESTAMP,
    TINYINT,
)

from app.extensions import db


class TranscriptSegment(db.Model):
    __tablename__ = "transcript_segments"

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

    speaker_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "speakers.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    segment_index = db.Column(
        INTEGER(unsigned=True),
        nullable=False
    )

    # D01:
    # timestamp không biết -> NULL
    # không dùng 0 để giả lập timestamp bị thiếu
    start_ms = db.Column(
        INTEGER(unsigned=True),
        nullable=True
    )

    end_ms = db.Column(
        INTEGER(unsigned=True),
        nullable=True
    )

    raw_text = db.Column(
        db.Text,
        nullable=False
    )

    edited_text = db.Column(
        db.Text,
        nullable=True
    )

    asr_confidence = db.Column(
        db.Numeric(5, 4),
        nullable=True
    )

    language = db.Column(
        db.String(10),
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
        back_populates="transcript_segments"
    )

    speaker = db.relationship(
        "Speaker",
        back_populates="transcript_segments"
    )
    evidence_key_points = db.relationship(
        "KeyPoint",
        back_populates="evidence_segment",
        passive_deletes=True
    )

    evidence_decisions = db.relationship(
        "Decision",
        back_populates="evidence_segment",
        passive_deletes=True
    )
    evidence_action_items = db.relationship(
        "ActionItem",
        back_populates="evidence_segment",
        passive_deletes=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "meeting_id",
            "segment_index",
            name="uq_segments_meeting_idx"
        ),
        db.Index(
            "idx_segments_meeting_time",
            "meeting_id",
            "start_ms"
        ),
        db.Index(
            "idx_segments_speaker_id",
            "speaker_id"
        ),
        db.Index(
            "idx_segments_is_user_edited",
            "is_user_edited"
        ),
    )

    @property
    def effective_text(self):
        """
        D08:
        edited_text được ưu tiên nếu khác NULL.
        Không dùng `edited_text or raw_text`
        vì empty string và NULL có ý nghĩa khác nhau.
        """
        if self.edited_text is not None:
            return self.edited_text
        return self.raw_text

    def __repr__(self):
        return (
            f"<TranscriptSegment id={self.id} "
            f"meeting_id={self.meeting_id} "
            f"segment_index={self.segment_index}>"
        )