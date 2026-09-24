import uuid

from sqlalchemy.orm import configure_mappers

from app import create_app
from app.extensions import db
from app.models import (
    User,
    Meeting,
    ProcessingJob,
    Speaker,
    TranscriptSegment,
    AIRun,
    Summary,
    KeyPoint,
    Decision,
    ActionItem,
    ActionItemOwner,
)


app = create_app()


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main():
    with app.app_context():
        configure_mappers()

        print("\n=== MEETINGAI DATABASE INTEGRATION TEST ===\n")

        test_email = f"db-test-{uuid.uuid4().hex[:8]}@meetingai.local"

        user = None

        try:
            # =========================================================
            # 1. USERS
            # =========================================================
            user = User(
                full_name="Database Test User",
                email=test_email,
                password_hash="test-password-hash",
                is_active=1,
            )

            db.session.add(user)
            db.session.commit()

            check(user.id is not None, "Create user")


            # =========================================================
            # 2. MEETINGS
            # =========================================================
            meeting = Meeting(
                user_id=user.id,
                title="MeetingAI Database Test",
                description="Integration test meeting",
                language="vi",
            )

            db.session.add(meeting)
            db.session.commit()

            meeting_id = meeting.id

            check(meeting.id is not None, "Create meeting")
            check(meeting.user_id == user.id, "Meeting belongs to user")
            check(meeting in user.meetings, "User -> meetings relationship")


            # =========================================================
            # 3. PROCESSING JOB
            # =========================================================
            job = ProcessingJob(
                meeting_id=meeting.id,
                job_type="TRANSCRIBE",
                status="COMPLETED",
                progress_percent=100,
                current_step="TRANSCRIBED",

                # D04
                asr_model_name="faster-whisper",
                asr_model_version="test",

                # D10
                checkpoint_stage="TRANSCRIBED",
                checkpoint_data={
                    "test": True,
                    "segment_count": 1,
                },
            )

            db.session.add(job)


            # =========================================================
            # 4. SPEAKER
            # =========================================================
            speaker = Speaker(
                meeting_id=meeting.id,
                speaker_label="SPEAKER_00",
                speaker_name="Người nói thử nghiệm",
                is_user_verified=1,
            )

            db.session.add(speaker)

            # cần flush để có speaker.id
            db.session.flush()


            # =========================================================
            # 5. TRANSCRIPT SEGMENT
            # =========================================================
            segment = TranscriptSegment(
                meeting_id=meeting.id,
                speaker_id=speaker.id,
                segment_index=0,

                # D01:
                # test timestamp NULL hợp lệ
                start_ms=None,
                end_ms=None,

                raw_text="Đây là nội dung transcript gốc.",
                edited_text=None,
                asr_confidence=0.9500,
                language="vi",
                is_user_edited=0,
            )

            db.session.add(segment)
            db.session.flush()


            # =========================================================
            # 6. AI RUN
            # =========================================================
            ai_run = AIRun(
                meeting_id=meeting.id,
                run_type="FULL",
                model_name="meetingai-test-model",
                model_version="1.0",
                dataset_version="test-dataset-v1",
                prompt_version="prompt-v1",

                # D03
                schema_version="schema-v1",

                status="COMPLETED",
                processing_ms=100,
                input_chars=100,
                input_tokens=30,

                # D06
                is_accepted=1,
            )

            db.session.add(ai_run)
            db.session.flush()


            # =========================================================
            # 7. SUMMARY
            # =========================================================
            summary = Summary(
                meeting_id=meeting.id,
                ai_run_id=ai_run.id,
                content="Đây là nội dung tóm tắt thử nghiệm.",
                is_user_edited=0,
            )

            db.session.add(summary)


            # =========================================================
            # 8. KEY POINT
            # =========================================================
            key_point = KeyPoint(
                meeting_id=meeting.id,
                ai_run_id=ai_run.id,
                content="Đây là một ý chính.",
                sort_order=1,
                evidence_segment_id=segment.id,
                is_user_edited=0,
            )

            db.session.add(key_point)


            # =========================================================
            # 9. DECISION
            # =========================================================
            decision = Decision(
                meeting_id=meeting.id,
                ai_run_id=ai_run.id,
                content="Nhóm thống nhất tiếp tục phát triển hệ thống.",
                decision_status="CONFIRMED",
                confidence_level="HIGH",
                evidence_segment_id=segment.id,
                is_user_edited=0,
            )

            db.session.add(decision)


            # =========================================================
            # 10. ACTION ITEM
            # =========================================================
            action_item = ActionItem(
                meeting_id=meeting.id,
                ai_run_id=ai_run.id,
                task="Hoàn thiện kiểm thử database.",
                deadline_raw="tuần sau",
                deadline_normalized=None,
                task_status="TODO",
                confidence_level="HIGH",
                evidence_segment_id=segment.id,
                is_user_edited=0,
            )

            db.session.add(action_item)
            db.session.flush()


            # =========================================================
            # 11. ACTION ITEM OWNER
            # =========================================================
            owner = ActionItemOwner(
                action_item_id=action_item.id,
                speaker_id=speaker.id,
                owner_name="Người nói thử nghiệm",
            )

            db.session.add(owner)

            db.session.commit()

            speaker_id = speaker.id
            segment_id = segment.id
            ai_run_id = ai_run.id
            summary_id = summary.id
            key_point_id = key_point.id
            decision_id = decision.id
            action_item_id = action_item.id
            owner_id = owner.id
            job_id = job.id


            # =========================================================
            # RELATIONSHIP TEST
            # =========================================================
            check(
                len(meeting.processing_jobs) == 1,
                "Meeting -> processing_jobs relationship"
            )

            check(
                len(meeting.speakers) == 1,
                "Meeting -> speakers relationship"
            )

            check(
                len(meeting.transcript_segments) == 1,
                "Meeting -> transcript_segments relationship"
            )

            check(
                len(meeting.ai_runs) == 1,
                "Meeting -> ai_runs relationship"
            )

            check(
                len(meeting.summaries) == 1,
                "Meeting -> summaries relationship"
            )

            check(
                len(meeting.key_points) == 1,
                "Meeting -> key_points relationship"
            )

            check(
                len(meeting.decisions) == 1,
                "Meeting -> decisions relationship"
            )

            check(
                len(meeting.action_items) == 1,
                "Meeting -> action_items relationship"
            )

            check(
                segment.effective_text == segment.raw_text,
                "Effective transcript uses raw_text when edited_text is NULL"
            )

            check(
                segment.start_ms is None and segment.end_ms is None,
                "Nullable transcript timestamps work"
            )

            check(
                len(action_item.owners) == 1,
                "ActionItem -> owners relationship"
            )


            # =========================================================
            # TEST SPEAKER ON DELETE SET NULL
            # =========================================================
            db.session.delete(speaker)
            db.session.commit()

            db.session.expire_all()

            refreshed_segment = db.session.get(
                TranscriptSegment,
                segment_id
            )

            refreshed_owner = db.session.get(
                ActionItemOwner,
                owner_id
            )

            check(
                refreshed_segment is not None,
                "Deleting speaker does not delete transcript segment"
            )

            check(
                refreshed_segment.speaker_id is None,
                "Speaker deletion SET NULL on transcript_segments.speaker_id"
            )

            check(
                refreshed_owner is not None,
                "Deleting speaker does not delete action owner"
            )

            check(
                refreshed_owner.speaker_id is None,
                "Speaker deletion SET NULL on action_item_owners.speaker_id"
            )


            # =========================================================
            # TEST AI RUN ON DELETE SET NULL
            # =========================================================
            run_to_delete = db.session.get(
                AIRun,
                ai_run_id
            )

            db.session.delete(run_to_delete)
            db.session.commit()

            db.session.expire_all()

            check(
                db.session.get(Summary, summary_id).ai_run_id is None,
                "AI run deletion SET NULL on summaries.ai_run_id"
            )

            check(
                db.session.get(KeyPoint, key_point_id).ai_run_id is None,
                "AI run deletion SET NULL on key_points.ai_run_id"
            )

            check(
                db.session.get(Decision, decision_id).ai_run_id is None,
                "AI run deletion SET NULL on decisions.ai_run_id"
            )

            check(
                db.session.get(ActionItem, action_item_id).ai_run_id is None,
                "AI run deletion SET NULL on action_items.ai_run_id"
            )


            # =========================================================
            # TEST MEETING CASCADE
            # =========================================================
            meeting_to_delete = db.session.get(
                Meeting,
                meeting_id
            )

            db.session.delete(meeting_to_delete)
            db.session.commit()

            db.session.expire_all()

            check(
                db.session.get(Meeting, meeting_id) is None,
                "Meeting deleted"
            )

            check(
                db.session.get(ProcessingJob, job_id) is None,
                "Meeting deletion CASCADE -> processing_jobs"
            )

            check(
                db.session.get(TranscriptSegment, segment_id) is None,
                "Meeting deletion CASCADE -> transcript_segments"
            )

            check(
                db.session.get(Summary, summary_id) is None,
                "Meeting deletion CASCADE -> summaries"
            )

            check(
                db.session.get(KeyPoint, key_point_id) is None,
                "Meeting deletion CASCADE -> key_points"
            )

            check(
                db.session.get(Decision, decision_id) is None,
                "Meeting deletion CASCADE -> decisions"
            )

            check(
                db.session.get(ActionItem, action_item_id) is None,
                "Meeting deletion CASCADE -> action_items"
            )

            check(
                db.session.get(ActionItemOwner, owner_id) is None,
                "Action item CASCADE -> action_item_owners"
            )


            # =========================================================
            # CLEAN USER
            # =========================================================
            db.session.delete(user)
            db.session.commit()

            check(
                db.session.get(User, user.id) is None,
                "Clean test user"
            )

            print("\n======================================")
            print("DATABASE INTEGRATION TEST: SUCCESS")
            print("11 MVP TABLES + RELATIONSHIPS OK")
            print("======================================\n")

        except Exception:
            db.session.rollback()

            # cleanup nếu test dừng giữa chừng
            if user is not None and user.id is not None:
                cleanup_user = db.session.get(
                    User,
                    user.id
                )

                if cleanup_user is not None:
                    db.session.delete(cleanup_user)
                    db.session.commit()

            raise


if __name__ == "__main__":
    main()