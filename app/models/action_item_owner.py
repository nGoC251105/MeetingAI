from sqlalchemy import text
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP

from app.extensions import db


class ActionItemOwner(db.Model):
    __tablename__ = "action_item_owners"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    action_item_id = db.Column(
        BIGINT(unsigned=True),
        db.ForeignKey(
            "action_items.id",
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

    owner_name = db.Column(
        db.String(120),
        nullable=False
    )

    created_at = db.Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    action_item = db.relationship(
        "ActionItem",
        back_populates="owners"
    )

    speaker = db.relationship(
        "Speaker",
        back_populates="action_item_owners"
    )

    __table_args__ = (
        db.Index(
            "idx_owner_name",
            "owner_name"
        ),
    )

    def __repr__(self):
        return (
            f"<ActionItemOwner id={self.id} "
            f"owner_name={self.owner_name!r}>"
        )