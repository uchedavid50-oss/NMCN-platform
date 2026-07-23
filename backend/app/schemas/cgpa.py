import uuid
from typing import List

from pydantic import BaseModel, Field, field_validator

VALID_GRADES = {"A", "B", "C", "D", "E", "F"}


class CourseCreate(BaseModel):
    semester: str
    course_name: str
    credit_units: int = Field(ge=1, le=10)
    grade: str

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in VALID_GRADES:
            raise ValueError(f"grade must be one of {sorted(VALID_GRADES)}")
        return v


class CourseOut(BaseModel):
    id: uuid.UUID
    semester: str
    course_name: str
    credit_units: int
    grade: str

    class Config:
        from_attributes = True


class SemesterSummary(BaseModel):
    semester: str
    total_units: int
    grade_points: float
    gpa: float


class CGPASummary(BaseModel):
    cgpa: float
    total_units: int
    semesters: List[SemesterSummary]
    courses: List[CourseOut]
