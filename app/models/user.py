from sqlalchemy import text
from sqlalchemy.dialects.mysql import BIGINT, TINYINT, TIMESTAMP

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(191),
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_active = db.Column(
        TINYINT(display_width=1),
        nullable=False,
        server_default=text("1")
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

    meetings = db.relationship(
        "Meeting",
        back_populates="user",
        passive_deletes=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "email",
            name="uq_users_email"
        ),
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"