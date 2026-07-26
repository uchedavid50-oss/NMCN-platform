"""
Seeds the 12 NMCN theory subjects and their topics.
Safe to run once. Skips creating a subject if one with the same
name already exists (so "Anatomy & Physiology" won't be duplicated) --
it will just add any missing topics to it instead.
"""

from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.subject import Subject
from app.models.topic import Topic

SYLLABUS = {
    "Anatomy & Physiology": [
        "Cardiovascular system",
        "Respiratory system",
        "Gastrointestinal system",
        "Renal and urinary system",
        "Nervous system",
        "Musculoskeletal system",
        "Reproductive system",
        "Endocrine system",
    ],
    "Fundamentals of Nursing": [
        "The nursing process",
        "Patient assessment",
        "Nursing care plans",
        "Basic nursing procedures",
        "Infection prevention and control",
        "Documentation and reporting",
        "Patient safety",
    ],
    "Medical-Surgical Nursing": [
        "Cardiovascular conditions",
        "Respiratory conditions",
        "Gastrointestinal conditions",
        "Renal conditions",
        "Endocrine conditions",
        "Neurological conditions",
        "Surgical nursing",
        "Oncology nursing",
    ],
    "Obstetrics and Gynaecology": [
        "Antenatal care",
        "Labour and delivery",
        "Postnatal care",
        "Gynaecological conditions",
        "Family planning",
        "Newborn care",
    ],
    "Paediatric Nursing": [
        "Growth and development",
        "Immunisation",
        "Common childhood illnesses",
        "Nutritional disorders",
        "Paediatric nursing procedures",
        "Child health programmes",
    ],
    "Community Health Nursing": [
        "Primary healthcare",
        "Epidemiology",
        "Disease prevention and control",
        "Health promotion",
        "Maternal and child health",
        "Environmental health",
        "School health nursing",
        "Occupational health nursing",
    ],
    "Pharmacology": [
        "Pharmacokinetics and pharmacodynamics",
        "Drug classifications",
        "Routes of drug administration",
        "Drug calculations",
        "Side effects and adverse reactions",
        "Nursing responsibilities in drug administration",
    ],
    "Mental Health Nursing": [
        "Mental health disorders",
        "Therapeutic communication",
        "Psychiatric assessment",
        "Psychotropic medications",
        "Legal and ethical issues in mental health",
        "Rehabilitation and recovery",
    ],
    "Nursing Ethics and Professional Practice": [
        "Nursing as a profession",
        "NMCN Act",
        "Ethical principles in nursing",
        "Patients' rights",
        "Legal aspects of nursing practice",
        "Professional conduct",
    ],
    "Nutrition and Biochemistry": [
        "Macronutrients and micronutrients",
        "Metabolism",
        "Therapeutic diets",
        "Nutritional assessment",
        "Nutrition across the lifecycle",
        "Common nutritional disorders in Nigeria",
    ],
    "Nursing Research": [
        "The research process",
        "Types of research",
        "Data collection methods",
        "Ethics in nursing research",
        "Application of research to practice",
    ],
    "Management and Leadership in Nursing": [
        "Nursing administration",
        "Leadership styles",
        "Management functions",
        "Staff supervision and development",
        "Quality assurance in healthcare",
        "Change management",
    ],
}


def run():
    db = SessionLocal()
    created_subjects = 0
    created_topics = 0
    try:
        for subject_name, topic_names in SYLLABUS.items():
            subject = db.query(Subject).filter(Subject.name == subject_name).first()
            if not subject:
                subject = Subject(name=subject_name)
                db.add(subject)
                db.flush()
                created_subjects += 1
                print(f"Created subject: {subject_name}")
            else:
                print(f"Subject already exists, reusing: {subject_name}")

            existing_topic_names = {
                t.name for t in db.query(Topic).filter(Topic.subject_id == subject.id).all()
            }

            for topic_name in topic_names:
                if topic_name in existing_topic_names:
                    continue
                db.add(Topic(subject_id=subject.id, name=topic_name))
                created_topics += 1

        db.commit()
        print(f"\nDone. Created {created_subjects} new subject(s), {created_topics} new topic(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()