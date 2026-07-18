from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.attempt import Attempt
from app.models.user import User
from app.schemas.achievements import Badge, CertificateEligibility
from app.services.achievements import compute_badges, is_eligible_for_certificate
from app.services.certificate import generate_certificate_pdf

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("/badges", response_model=list[Badge])
def get_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return compute_badges(db, current_user.id)


@router.get("/certificate/eligibility", response_model=CertificateEligibility)
def get_certificate_eligibility(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eligible, reason = is_eligible_for_certificate(db, current_user.id)
    return CertificateEligibility(eligible=eligible, reason=reason)


@router.get("/certificate/download")
def download_certificate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eligible, reason = is_eligible_for_certificate(db, current_user.id)
    if not eligible:
        raise HTTPException(status_code=403, detail=reason)

    finished_mocks = (
        db.query(Attempt)
        .filter(Attempt.user_id == current_user.id, Attempt.mode == "mock", Attempt.finished_at.isnot(None))
        .all()
    )
    average_score = sum(a.score_percentage or 0 for a in finished_mocks) / len(finished_mocks)

    pdf_bytes = generate_certificate_pdf(
        student_email=current_user.email,
        average_score=average_score,
        mock_count=len(finished_mocks),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=nmcn-cbt-prep-certificate.pdf"},
    )
