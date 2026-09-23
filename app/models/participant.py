from sqlalchemy import text
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP, TINYINT

from app.extensions import db


class Speaker(db.Model):
    __tablename__ = "speakers"

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

    speaker_label = db.Column(
        db.String(50),
        nullable=False
    )

    speaker_name = db.Column(
        db.String(120),
        nullable=True
    )

    is_user_verified = db.Column(
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
        back_populates="speakers"
    )

    transcript_segments = db.relationship(
        "TranscriptSegment",
        back_populates="speaker",
        passive_deletes=True
    )
    action_item_owners = db.relationship(
        "ActionItemOwner",
        back_populates="speaker",
        passive_deletes=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "meeting_id",
            "speaker_label",
            name="uq_speakers_meeting_label"
        ),
    )

    def __repr__(self):
        return (
            f"<Speaker id={self.id} "
            f"label={self.speaker_label!r}>"
        )