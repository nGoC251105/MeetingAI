"""Live MySQL regressions; fixtures are flushed, never committed or migrated."""

import unittest
import uuid

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, select

from app import create_app
from app.extensions import db
from app.models import (
    ActionItem, ActionItemOwner, AIRun, Decision, KeyPoint, Meeting,
    ProcessingJob, Speaker, Summary, TranscriptSegment, User,
)


class DatabaseModelTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        self.addCleanup(db.engine.dispose)
        self.addCleanup(db.session.remove)
        self.addCleanup(db.session.rollback)

    def make_graph(self):
        user = User(
            full_name="Database regression fixture",
            email=f"model-test-{uuid.uuid4().hex}@meetingai.local",
            password_hash="non-login-test-fixture",
        )
        meeting = Meeting(user=user, title="Database regression fixture")
        speaker = Speaker(meeting=meeting, speaker_label="SPEAKER_00")
        segment = TranscriptSegment(
            meeting=meeting, speaker=speaker, segment_index=0,
            raw_text="Nội dung cuộc họp.",
        )
        run = AIRun(meeting=meeting, model_name="fixture", model_version="1")
        task = ActionItem(meeting=meeting, ai_run=run, task="Test cascade",
                          evidence_segment=segment)
        rows = [
            user, meeting, speaker, segment, run, task,
            ProcessingJob(meeting=meeting),
            Summary(meeting=meeting, ai_run=run, content="Tóm tắt."),
            KeyPoint(meeting=meeting, ai_run=run, content="Ý chính.",
                     evidence_segment=segment),
            Decision(meeting=meeting, ai_run=run, content="Quyết định.",
                     evidence_segment=segment),
            ActionItemOwner(action_item=task, speaker=speaker, owner_name="Owner"),
        ]
        db.session.add_all(rows)
        db.session.flush()
        return {type(row): row.id for row in rows}

    def assert_cascade(self, parent_model, loaded):
        ids = self.make_graph()
        # Remove objects populated by fixture relationship assignment. Reload
        # only the parent, then explicitly test either relationship load state.
        db.session.expunge_all()
        parent = db.session.get(parent_model, ids[parent_model])
        collections = [rel.key for rel in inspect(parent_model).relationships
                       if rel.uselist]
        if loaded:
            for name in collections:
                self.assertTrue(getattr(parent, name))
        else:
            self.assertTrue(set(collections) <= inspect(parent).unloaded)

        db.session.delete(parent)
        db.session.flush()
        removed = set(ids)
        if parent_model is Meeting:
            removed.remove(User)
        elif parent_model is ActionItem:
            removed = {ActionItem, ActionItemOwner}

        # Query database rows directly: database cascades can leave loaded ORM
        # instances stale until expiration/commit, which must not mask results.
        for model, row_id in ids.items():
            with self.subTest(table=model.__tablename__):
                actual = db.session.execute(
                    select(model.id).where(model.id == row_id)
                ).scalar_one_or_none()
                self.assertEqual(actual, None if model in removed else row_id)

    def test_user_delete_loaded_children(self):
        self.assert_cascade(User, loaded=True)

    def test_user_delete_unloaded_children(self):
        self.assert_cascade(User, loaded=False)

    def test_meeting_delete_loaded_children(self):
        self.assert_cascade(Meeting, loaded=True)

    def test_meeting_delete_unloaded_children(self):
        self.assert_cascade(Meeting, loaded=False)

    def test_action_item_delete_loaded_owners(self):
        self.assert_cascade(ActionItem, loaded=True)

    def test_action_item_delete_unloaded_owners(self):
        self.assert_cascade(ActionItem, loaded=False)

    def test_live_schema_matches_models(self):
        connection = db.session.connection()
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        self.assertEqual(compare_metadata(context, db.metadata), [])
        expected = {
            "users", "meetings", "processing_jobs", "speakers",
            "transcript_segments", "ai_runs", "summaries", "key_points",
            "decisions", "action_items", "action_item_owners",
        }
        self.assertEqual(set(db.metadata.tables), expected)
        inspector = inspect(connection)
        self.assertEqual(set(inspector.get_table_names()), expected | {"alembic_version"})
        self.assertEqual(sum(len(inspector.get_columns(t)) for t in expected), 120)

    def test_summary_round_trips_beyond_text_capacity(self):
        ids = self.make_graph()
        summary = db.session.get(Summary, ids[Summary])
        content = "Nội dung cuộc họp. " * 5000
        self.assertGreater(len(content.encode("utf-8")), 65535)
        summary.content = content
        db.session.flush()
        db.session.expire(summary)
        self.assertEqual(summary.content, content)


if __name__ == "__main__":
    unittest.main()
