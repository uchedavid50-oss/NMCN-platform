"""
Seeds OSCE (clinical skills) subjects and topics from the NMCN OSCE syllabus.
Safe to run once. Skips creating a subject if one with the same name
already exists -- it will just add any missing topics to it instead.
"""

from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.subject import Subject
from app.models.topic import Topic

OSCE_SYLLABUS = {
    "OSCE: Personal Hygiene and Basic Care": [
        "Bed Bath (Complete and Partial)",
        "Bed Making (Occupied and Unoccupied Bed)",
        "Oral Hygiene and Mouth Care",
        "Hair Care and Back Care",
        "Pressure Ulcer Prevention and Care",
        "Patient Positioning (Supine, Lateral, Prone, Fowler's, Trendelenburg)",
    ],
    "OSCE: Wound Care": [
        "Aseptic Technique and Sterile Field Preparation",
        "Simple Wound Dressing",
        "Surgical Wound Dressing",
        "Suture and Staple Removal",
        "Burns Dressing",
    ],
    "OSCE: Medication Administration": [
        "Oral Medication Administration",
        "Intramuscular Injection",
        "Subcutaneous Injection",
        "Intradermal Injection",
        "Intravenous Drug Administration",
        "Drug Dosage Calculation",
    ],
    "OSCE: Fluid and Nutritional Support": [
        "Setting Up Intravenous Infusion",
        "Monitoring and Adjusting IV Fluid Rate",
        "Nasogastric Tube Insertion and Management",
        "Nasogastric Tube Feeding",
        "Blood Transfusion Procedure and Monitoring",
    ],
    "OSCE: Elimination": [
        "Female and Male Urinary Catheterisation",
        "Catheter Care and Management",
        "Enema Administration",
        "Colostomy Care",
        "Serving of Bedpan",
    ],
    "OSCE: Respiratory Care": [
        "Oxygen Therapy (Masks, Nasal Cannula, Flow Rates)",
        "Suctioning of Airways",
        "Inhalation Therapy Administration",
        "Chest Physiotherapy Basics",
    ],
    "OSCE: Vital Signs and Monitoring": [
        "Temperature, Pulse, Respiration, and Blood Pressure Measurement",
        "Oxygen Saturation Monitoring",
        "Neurological Observations (Glasgow Coma Scale)",
        "Blood Glucose Monitoring",
    ],
    "OSCE: Obstetric and Gynaecological Procedures": [
        "Antenatal Abdominal Examination",
        "Fundal Height Measurement",
        "Fetal Heart Auscultation",
        "Vulval Swabbing and Perineal Care",
    ],
}


def run():
    db = SessionLocal()
    created_subjects = 0
    created_topics = 0
    try:
        for subject_name, topic_names in OSCE_SYLLABUS.items():
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