"""
Seeds subjects/topics from the official NMCN General Nursing Curriculum PDF.
Safe to run once. Skips creating a subject if one with the same name
already exists -- it will just add any missing topics to it instead.
"""

from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.subject import Subject
from app.models.topic import Topic

CURRICULUM = {
    "Anatomy and Physiology I": [
        "Introduction to Anatomy and Physiology",
        "The Musculoskeletal System",
        "Blood and Cardiovascular System",
    ],
    "Foundation of Nursing I": [
        "Health Care Institutions",
        "Ethico-Legal Issues",
        "Tools of Nursing",
        "Basic Client/Patient Care",
        "Diagnostic Measures",
        "First Aid",
    ],
    "Nutrition": [
        "Nutritional Needs",
        "Nutritional Management for Health",
        "Nutrition in Health/Disease",
    ],
    "Use of English": [
        "Grammatical Convention",
        "Techniques of Writing",
        "Reading Skills, Summary and Art of Debate",
    ],
    "Applied Physics": [
        "Molecular Phenomena and Applications",
        "Measurements and Units",
        "Forces and Their Application in Nursing Practice",
        "Machines",
        "Heat",
        "Elasticity",
        "Optics and Waves",
        "Electricity, Magnetism and Sound Waves",
        "Practical: Measurement of Physical Properties",
    ],
    "Applied Chemistry": [
        "Nature of Matter",
        "Acids, Bases and Salts",
        "Electrolysis",
        "Carbon and Carbon Compounds",
        "Organic and Inorganic Compounds",
        "Atomic Nucleus and Nuclear Energy",
        "Practical",
    ],
    "Sociology": [
        "Nature and Scope of Sociology",
        "Social Process/Adaptive Processes",
        "Health Illness Behavior",
        "Relationships in Health Care Organizations",
    ],
    "Introduction to Information Communication Technology": [
        "Components of the Computer System",
        "Computer Files",
        "Data Collection and Control",
        "Computer Networking",
        "ICT in Health Care",
    ],
    "Anatomy and Physiology II": [
        "The Integumentary System",
        "The Endocrine System",
    ],
    "Foundation of Nursing II": [
        "Administration of Drugs",
        "Legal Aspects of Nursing",
        "Aseptic Techniques",
        "Injection Safety",
        "Unsafe Injection Practices",
        "Introduction to Healthcare Waste",
    ],
    "Medical/Surgical Nursing I": [
        "Concepts and Terms in Medical Surgical Nursing",
        "Diagnostic Measures",
        "Common Situations that Threaten Adaptation",
        "Management of Patients with Infectious Diseases",
        "Principles of Operating Room Nursing",
        "Principles and Practice of Rehabilitation",
    ],
    "Primary Health Care I": [
        "Introduction to Primary Health Care",
        "The Community: Structure and Functions",
        "Community Diagnosis",
        "Community Mobilization",
        "Information, Education and Communication (IEC)",
        "Clinical Skills in Primary Health Care",
    ],
    "Microbiology": [
        "Infectious Process and Infectious Disease Control",
        "Microorganisms of Clinical Importance",
        "Introduction to Immunology and Immune Response",
        "Diagnostic Microbiology",
        "Environmental Aspects of Microbiology",
    ],
    "Pharmacology I": [
        "Sources and Classification of Drugs",
        "Preparation of Drugs",
        "Routes of Drug Administration",
        "Safety in Drug Administration",
        "Mechanism of Drug Action",
    ],
    "Psychology": [
        "Human Growth and Development",
        "Psychological Testing Methods",
    ],
    "Anatomy and Physiology III": [
        "The Female Reproductive System",
        "Affiliated Organs",
    ],
    "Foundation of Nursing III": [
        "Nursing Care of Patients with Feeding/Elimination Problems",
    ],
    "Medical/Surgical Nursing II": [
        "Management of Clients with Problems of the Respiratory System",
        "Management of Clients with Problems of the Digestive System",
        "Management of Patients with Problems of Genito-Urinary System",
        "Management of Patients with Problems of Integumentary System",
    ],
    "Primary Health Care II": [
        "Components of Primary Health Care",
        "Training",
        "Management in Primary Health Care",
    ],
    "Pharmacology II": [
        "Pharmacovigilance",
        "Drug Revolving Fund",
        "Patient Education and Counseling",
        "Drugs Used for Conditions Apart from Systemic Disorders",
    ],
    "Reproductive Health I": [
        "Human Sexuality",
        "Review of Reproductive Organs",
        "Investigations, Procedures and Surgical Interventions",
        "Gynaecological Conditions",
        "Reproductive Tract Infections and Infertility",
        "HIV Infection and Acquired Immune Deficiency Syndrome (AIDS)",
        "Issues in Reproductive Health",
        "Information, Education and Communication (IEC)",
    ],
    "Biostatistics": [
        "Statistical Measurement",
        "Statistical Analysis",
    ],
    "Research Methodology I": [
        "Overview of Research",
        "Nature and Functions of Research",
        "Preliminary Steps in Research Process",
    ],
    "Anatomy and Physiology IV": [
        "The Nervous System",
        "The Special Senses",
    ],
    "Foundation of Nursing IV": [
        "Nursing Care of Patients with Musculo-Skeletal Injuries",
        "Special Diagnostic Measures",
        "The Dying Patient",
    ],
    "Medical/Surgical Nursing III": [
        "Management of Clients with Musculoskeletal Problems",
        "Management of Clients with Problems of the Metabolic and Endocrine System",
        "Management of Clients with Neurologic Disorders",
        "Management of Clients with Problems of the Cardiovascular System",
        "Inherited Degenerative Diseases",
        "Respiratory System",
        "Gastrointestinal System",
        "Musculo-skeletal System",
        "Central Nervous System",
        "Endocrine System",
    ],
    "Research Methodology II": [
        "Steps in Research Process",
        "Proposal Writing",
    ],
    "Community Health Nursing I": [
        "Basic Concepts and Tools in Community Health Nursing",
        "Maternal and Child Health Services",
        "School Health Programme",
        "Nursing Needs and Management of Special Groups in the Community",
    ],
    "Reproductive Health II": [
        "Concept of Safe Motherhood",
        "Child-Bearing Cycle",
        "Labour",
        "Abnormalities in Labour",
        "Family Planning",
        "Abortion and Post Abortion Care",
        "Quality of Care",
    ],
    "Dietetics": [
        "Dietary Guidelines for Healthy Living",
        "Modifications of Diet in Critical Periods of the Life Span",
        "Therapeutic Diets for Management of Medical-Surgical Conditions",
        "Dietary Education and Supplementation",
    ],
    "Introduction to Medical Sociology": [
        "Societal Response to Common Tropical Diseases",
        "Social Class/Disease Relationship",
        "Modern and Traditional Health Care Delivery",
        "Social Planning and Health Care",
        "Health Care Problems in Nigeria",
    ],
    "Introduction to Seminar Presentation/Writing of Term Paper": [
        "Development and Validation of Seminar Papers",
        "Ethical and Legal Frameworks in Seminar Papers",
    ],
    "Medical/Surgical Nursing IV": [
        "Reproductive Disorders",
        "Management of Clients with Problems of the Haematological System",
        "Special Senses",
        "Medical and Surgical Procedures",
    ],
    "Reproductive Health III": [
        "Nutritional Requirements of a Child",
        "Vaccines and Immunization Schedule",
        "Common Childhood Developmental Problems",
        "The Adolescent/Youth",
    ],
    "Community Health Nursing II": [
        "Introduction to Epidemiology and Control of Communicable Diseases",
        "Epidemiology and Control of Non-Communicable Diseases",
        "Principles of Epidemiologic Data Collection and Utilization",
    ],
    "Mental Health/Psychiatric Nursing": [
        "Introduction to Mental Health Concepts",
        "Mental Disorders",
        "Community Mental Health",
    ],
    "Emergency and Disaster Nursing": [
        "Concepts and Principles of Emergency Care",
        "Emergencies and Life-Threatening Situations",
        "Management of Patient in Hospital Emergency Department",
        "Disaster Management (Basic)",
    ],
    "Principles of Management and Teaching": [
        "Management",
        "Objectives in Health Administration",
        "Leadership Dynamics",
        "Management of Resources",
        "Conflict Management and Resolution",
        "Application of Principles of Management to Nursing Practice",
        "Quality Assurance and Risk Management",
        "Contemporary Issues in Nursing",
        "Teaching and Learning Process",
        "Evaluation Process",
        "Administrative Laws Relevant to Nursing",
    ],
    "Medical Surgical Nursing V": [
        "Oncology",
        "Critical Care Nursing",
        "Gerontology",
        "Palliative Care",
    ],
    "Reproductive Health IV": [
        "Hospitalized Child",
        "Management of Congenital Abnormalities",
        "Neonatal Conditions",
        "Integrated Management of Neonatal and Childhood Illness (IMNCI)",
        "HIV & AIDS in Children",
        "Tuberculosis in Children",
    ],
    "Health Economics": [
        "Introduction to Health Economics",
        "Nigeria's Economy and its Influences on Health Care Delivery",
        "National Health Policy and National Development",
        "Health Care Financing and Insurance Scheme",
        "Economic Influences on Health Care",
    ],
    "Entrepreneurship": [
        "Meaning and Scope of Enterprise and Entrepreneurship",
        "History and Government Policy Measures Promoting Entrepreneurship in Nigeria",
        "Types, Characteristics and Rationale of Entrepreneurship",
        "Role of Entrepreneurship in Economic Development",
        "Entrepreneurial Characteristics and Attitude",
        "Competencies and Determining Factors for Success in Entrepreneurship",
        "Motivational Pattern of Entrepreneurs",
    ],
}


def run():
    db = SessionLocal()
    created_subjects = 0
    created_topics = 0
    try:
        for subject_name, topic_names in CURRICULUM.items():
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