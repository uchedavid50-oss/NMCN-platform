"""
Seeds the Organ list for the Viva > Organs page.
Safe to run once. Skips any organ whose name already exists.
"""

from app.main import app  # noqa: F401  (ensures all models are registered)
from app.db.session import SessionLocal
from app.models.organ import Organ

ORGANS = {
    "Heart": "A four-chambered muscular pump that circulates blood through the body, "
    "delivering oxygen and nutrients to tissues and removing waste products via the "
    "pulmonary and systemic circuits.",
    "Lungs": "A pair of spongy, air-filled organs where gas exchange takes place -- "
    "oxygen is absorbed into the blood and carbon dioxide is expelled during breathing.",
    "Liver": "The body's largest internal organ; metabolizes nutrients and drugs, "
    "detoxifies harmful substances, produces bile for fat digestion, and stores "
    "glycogen, vitamins, and iron.",
    "Kidneys": "A pair of bean-shaped organs that filter waste and excess fluid from "
    "the blood to form urine, while regulating electrolyte balance, blood pressure, "
    "and red blood cell production.",
    "Brain": "The central organ of the nervous system, housed in the skull; controls "
    "thought, memory, emotion, movement, and the body's vital involuntary functions "
    "such as breathing and heart rate.",
    "Stomach": "A muscular, J-shaped sac that stores swallowed food, mixes it with "
    "acid and digestive enzymes, and breaks it down into a semi-liquid form (chyme) "
    "before it moves into the small intestine.",
    "Small Intestine": "A long, coiled tube (duodenum, jejunum, ileum) where most "
    "digestion and nutrient absorption occurs, aided by enzymes from the pancreas "
    "and bile from the liver/gallbladder.",
    "Large Intestine": "Absorbs water and electrolytes from indigestible food matter, "
    "forms and stores feces, and hosts bacteria that produce certain vitamins, before "
    "waste is eliminated through the rectum and anus.",
    "Pancreas": "A gland behind the stomach with two roles: an exocrine function "
    "producing digestive enzymes released into the small intestine, and an endocrine "
    "function secreting insulin and glucagon to regulate blood sugar.",
    "Spleen": "Filters and recycles old or damaged red blood cells, stores platelets, "
    "and helps the immune system fight infection by producing white blood cells and "
    "antibodies.",
    "Gallbladder": "A small sac beneath the liver that stores and concentrates bile, "
    "releasing it into the small intestine to help digest and absorb dietary fats.",
    "Urinary Bladder": "A muscular, expandable sac that stores urine produced by the "
    "kidneys until it is voluntarily released from the body through the urethra.",
    "Uterus": "A muscular, pear-shaped reproductive organ where a fertilized egg "
    "implants and a fetus develops during pregnancy, and which sheds its lining "
    "monthly as menstruation if pregnancy does not occur.",
    "Ovaries": "A pair of female reproductive glands that produce eggs (ova) and "
    "secrete the hormones estrogen and progesterone, which regulate the menstrual "
    "cycle and secondary sexual characteristics.",
    "Testes": "A pair of male reproductive glands that produce sperm and secrete "
    "testosterone, the hormone responsible for male secondary sexual characteristics "
    "and reproductive function.",
    "Thyroid Gland": "A butterfly-shaped gland in the neck that produces hormones "
    "(T3 and T4) regulating metabolism, growth, body temperature, and energy use.",
    "Adrenal Glands": "A pair of small glands sitting atop each kidney that produce "
    "hormones such as cortisol (stress response, metabolism) and adrenaline "
    "(fight-or-flight response), plus aldosterone for salt/water balance.",
    "Pituitary Gland": "A pea-sized gland at the base of the brain often called the "
    "\"master gland\" -- it releases hormones that control growth, metabolism, "
    "reproduction, and the activity of other endocrine glands.",
    "Skin": "The body's largest organ; forms a protective barrier against injury, "
    "infection, and fluid loss, regulates temperature, and provides the sense of "
    "touch through its nerve receptors.",
    "Eyes": "The organs of vision -- light entering through the cornea and lens is "
    "focused onto the retina, which converts it into nerve signals sent to the brain "
    "via the optic nerve.",
    "Ears": "The organs of hearing and balance -- the outer and middle ear channel "
    "and amplify sound to the inner ear, which converts vibrations into nerve "
    "signals and also senses head position and movement.",
}


def run():
    db = SessionLocal()
    created = 0
    try:
        existing_names = {o.name for o in db.query(Organ).all()}
        for name, description in ORGANS.items():
            if name in existing_names:
                print(f"Organ already exists, skipping: {name}")
                continue
            db.add(Organ(name=name, description=description))
            created += 1
            print(f"Created organ: {name}")

        db.commit()
        print(f"\nDone. Created {created} new organ(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
