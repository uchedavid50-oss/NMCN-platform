"""
Generates AI study notes for every topic that doesn't already have one.
Safe to re-run -- skips topics that already have a note.
Includes pacing between requests to avoid rate limits.
"""

import time
from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.topic import Topic
from app.models.topic_note import TopicNote
from app.api.tutor import _call_gemini

EXAM_FRAMING = {
    "NMCN": "the NMCN (Nursing and Midwifery Council of Nigeria) Professional Qualifying Examination",
    "NCLEX": "the NCLEX (National Council Licensure Examination) for nursing licensure",
}


def generate_note_for_topic(topic):
    exam_type = topic.subject.exam_type if topic.subject else "NMCN"
    exam_framing = EXAM_FRAMING.get(exam_type, EXAM_FRAMING["NMCN"])

    system_prompt = (
        f"You write comprehensive study notes for a nursing student preparing for "
        f"{exam_framing}, on the topic '{topic.name}' (subject: "
        f"{topic.subject.name if topic.subject else 'General'}).\n\n"
        "Write a thorough, well-organized study note covering the key concepts, "
        "definitions, clinical relevance, and any important nursing considerations "
        "for this topic. Use Markdown formatting: headings, bullet points, and bold "
        "for key terms. Where a diagram would genuinely help understanding (e.g. a "
        "process, cycle, anatomical relationship, or classification), include ONE "
        "Mermaid diagram in a ```mermaid code block using flowchart or graph syntax. "
        "Do not overuse diagrams -- only include one if it adds real value. "
        "Respond with ONLY the markdown content, no preamble or meta-commentary."
    )

    return _call_gemini(
        system_prompt,
        f"Topic: {topic.name}",
        max_output_tokens=4000,
    )


def run():
    db = SessionLocal()
    created = 0
    skipped = 0
    failed = 0
    try:
        topics = db.query(Topic).all()
        print(f"Found {len(topics)} topics total.")

        for i, topic in enumerate(topics, start=1):
            existing = db.query(TopicNote).filter(TopicNote.topic_id == topic.id).first()
            if existing:
                skipped += 1
                continue

            print(f"[{i}/{len(topics)}] Generating note for: {topic.name}")
            try:
                content = generate_note_for_topic(topic)
                if not content or not content.strip():
                    print(f"  -> empty response, skipping")
                    failed += 1
                    continue

                note = TopicNote(topic_id=topic.id, content=content.strip())
                db.add(note)
                db.commit()
                created += 1
            except Exception as exc:
                print(f"  -> failed: {exc}")
                failed += 1
                db.rollback()

            time.sleep(2)  # pace requests to avoid rate limits

        print(f"\nDone. Created {created}, skipped {skipped} (already had notes), failed {failed}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()