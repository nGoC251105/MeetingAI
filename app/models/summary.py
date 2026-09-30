from sqlalchemy import text
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT, TIMESTAMP, TINYINT

from app.extensions import db


class Summary(db.Model):
    __tablename__ = "summaries"

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
        db.Text().with_variant(LONGTEXT(), "mysql"),
        nullable=False
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
        back_populates="summaries"
    )

    ai_run = db.relationship(
        "AIRun",
        back_populates="summaries"
    )

    __table_args__ = (
        db.Index(
            "idx_summaries_meeting",
            "meeting_id",
            "created_at"
        ),
    )

    def __repr__(self):
        return (
            f"<Summary id={self.id} "
            f"meeting_id={self.meeting_id}>"
        )
