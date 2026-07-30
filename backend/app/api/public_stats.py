from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entrance_exam_question import EntranceExamQuestion
from app.models.question import Question
from app.models.subject import Subject
from app.models.user import User

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)):
    """No auth -- aggregate marketing-page counts only, no PII. Real
    numbers from the database, not placeholder marketing copy."""
    students = db.query(User).filter(User.role == "student").count()
    questions = db.query(Question).count() + db.query(EntranceExamQuestion).count()
    subjects = db.query(Subject).count()
    return {"students": students, "questions": questions, "subjects": subjects}
