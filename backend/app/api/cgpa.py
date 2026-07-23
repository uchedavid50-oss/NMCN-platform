import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.course import Course, GRADE_POINTS
from app.models.user import User
from app.schemas.cgpa import CGPASummary, CourseCreate, CourseOut, SemesterSummary

router = APIRouter(prefix="/cgpa", tags=["cgpa"])


@router.post("/courses", response_model=CourseOut, status_code=201)
def add_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = Course(
        user_id=current_user.id,
        semester=payload.semester,
        course_name=payload.course_name,
        credit_units=payload.credit_units,
        grade=payload.grade,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = (
        db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return None


@router.get("/summary", response_model=CGPASummary)
def get_cgpa_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    courses = (
        db.query(Course)
        .filter(Course.user_id == current_user.id)
        .order_by(Course.created_at.asc())
        .all()
    )

    by_semester = defaultdict(list)
    for c in courses:
        by_semester[c.semester].append(c)

    semester_summaries = []
    total_units_all = 0
    total_points_all = 0.0

    for semester, semester_courses in by_semester.items():
        total_units = sum(c.credit_units for c in semester_courses)
        grade_points = sum(c.credit_units * GRADE_POINTS[c.grade] for c in semester_courses)
        gpa = round(grade_points / total_units, 2) if total_units else 0.0
        semester_summaries.append(
            SemesterSummary(
                semester=semester,
                total_units=total_units,
                grade_points=round(grade_points, 2),
                gpa=gpa,
            )
        )
        total_units_all += total_units
        total_points_all += grade_points

    cgpa = round(total_points_all / total_units_all, 2) if total_units_all else 0.0

    return CGPASummary(
        cgpa=cgpa,
        total_units=total_units_all,
        semesters=semester_summaries,
        courses=courses,
    )
