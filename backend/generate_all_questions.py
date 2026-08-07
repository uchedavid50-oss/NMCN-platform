"""
Generates AI practice questions (rich format: rationale, why_others_wrong,
clinical_tip, exam_specific_tip, cognitive_level) for every topic in the
database, landing them in the pending-review queue.

Usage:
    python generate_all_questions.py <count_per_topic> [--exam-type=nmcn|nclex] [--limit=N]

    --exam-type   Forces NMCN or NCLEX framing for every topic, regardless of
                  that topic's subject.exam_type. Omit to use each topic's own
                  exam_type (the normal per-topic behavior).
    --limit       Only process the first N topics -- for a quick preview run
                  before committing to the full topic list.

Includes pacing between requests to avoid rate limits. Commits per topic, so
a crash partway through still keeps everything generated up to that point.
Continues past per-topic failures (logged) rather than aborting the run.
"""
import argparse
import time

from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.topic import Topic
from app.models.user import User
from app.api.admin_content import _generate_questions_for_topic, EXAM_FRAMING


def run(count: int, exam_type_override: str | None, limit: int | None):
    db = SessionLocal()
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        print("No admin user found, aborting")
        db.close()
        return

    created_total = 0
    failed = 0
    try:
        query = db.query(Topic).order_by(Topic.name)
        if limit:
            query = query.limit(limit)
        topics = query.all()
        print(f"Processing {len(topics)} topic(s), {count} question(s) each"
              f"{f', forced exam_type={exam_type_override}' if exam_type_override else ''}.")

        for i, topic in enumerate(topics, start=1):
            print(f"[{i}/{len(topics)}] Generating for: {topic.name}")
            try:
                created, exam_type = _generate_questions_for_topic(
                    db, topic, count, exam_type_override=exam_type_override
                )
                if not created:
                    print("  -> no well-formed questions returned, skipping")
                    failed += 1
                    db.rollback()
                    continue

                db.commit()
                for q in created:
                    db.refresh(q)
                created_total += len(created)
                print(f"  -> created {len(created)} pending questions ({exam_type} framing)")
            except Exception as exc:
                print(f"  -> failed: {exc}")
                failed += 1
                db.rollback()

            time.sleep(2)  # pace requests to avoid rate limits

        print(f"\nDone. Created {created_total} pending questions across "
              f"{len(topics)} topics, {failed} topic(s) failed/skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int, help="Questions to generate per topic")
    parser.add_argument(
        "--exam-type",
        type=str,
        default=None,
        help=f"Force framing regardless of topic exam_type: one of {list(EXAM_FRAMING)} (case-insensitive)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N topics")
    args = parser.parse_args()

    exam_type_override = args.exam_type.upper() if args.exam_type else None
    if exam_type_override and exam_type_override not in EXAM_FRAMING:
        parser.error(f"--exam-type must be one of {list(EXAM_FRAMING)}")

    run(args.count, exam_type_override, args.limit)
