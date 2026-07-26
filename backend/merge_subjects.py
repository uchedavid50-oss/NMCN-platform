"""
Merges numbered course variants (e.g. "Anatomy and Physiology I", "II", "III")
into a single combined subject, moving all their topics underneath it.
Safe to run once. If a target subject with the same base name already
exists (e.g. your original "Anatomy & Physiology" or "Pharmacology"),
topics get added into that existing subject instead of creating a new one.
"""

from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.subject import Subject
from app.models.topic import Topic

# target subject name -> list of existing subject names to merge into it
MERGE_GROUPS = {
    "Anatomy & Physiology": [
        "Anatomy and Physiology I",
        "Anatomy and Physiology II",
        "Anatomy and Physiology III",
        "Anatomy and Physiology IV",
    ],
    "Foundation of Nursing": [
        "Foundation of Nursing I",
        "Foundation of Nursing II",
        "Foundation of Nursing III",
        "Foundation of Nursing IV",
    ],
    "Medical/Surgical Nursing": [
        "Medical/Surgical Nursing I",
        "Medical/Surgical Nursing II",
        "Medical/Surgical Nursing III",
        "Medical/Surgical Nursing IV",
        "Medical Surgical Nursing V",
    ],
    "Primary Health Care": [
        "Primary Health Care I",
        "Primary Health Care II",
    ],
    "Pharmacology": [
        "Pharmacology I",
        "Pharmacology II",
    ],
    "Reproductive Health": [
        "Reproductive Health I",
        "Reproductive Health II",
        "Reproductive Health III",
        "Reproductive Health IV",
    ],
    "Research Methodology": [
        "Research Methodology I",
        "Research Methodology II",
    ],
    "Community Health Nursing": [
        "Community Health Nursing I",
        "Community Health Nursing II",
    ],
}


def run():
    db = SessionLocal()
    moved_topics = 0
    removed_subjects = 0
    try:
        for target_name, source_names in MERGE_GROUPS.items():
            target = db.query(Subject).filter(Subject.name == target_name).first()
            if not target:
                target = Subject(name=target_name)
                db.add(target)
                db.flush()
                print(f"Created target subject: {target_name}")
            else:
                print(f"Using existing target subject: {target_name}")

            existing_topic_names = {
                t.name for t in db.query(Topic).filter(Topic.subject_id == target.id).all()
            }

            for source_name in source_names:
                source = db.query(Subject).filter(Subject.name == source_name).first()
                if not source:
                    continue
                topics = db.query(Topic).filter(Topic.subject_id == source.id).all()
                for topic in topics:
                    if topic.name in existing_topic_names:
                        # duplicate topic name -- drop it, target already has it
                        db.delete(topic)
                        continue
                    topic.subject_id = target.id
                    existing_topic_names.add(topic.name)
                    moved_topics += 1
                db.flush()
                db.delete(source)
                removed_subjects += 1
                print(f"  Merged and removed: {source_name}")

        db.commit()
        print(f"\nDone. Moved {moved_topics} topic(s), removed {removed_subjects} old subject(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()