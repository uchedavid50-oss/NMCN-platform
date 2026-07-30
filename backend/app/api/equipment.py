from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_admin, get_current_user
from app.core.time import utcnow
from app.db.session import get_db
from app.models.equipment_content import EquipmentContent
from app.models.user import User
from app.schemas.equipment import EquipmentOut, SetEquipmentRequest

router = APIRouter(prefix="/equipment", tags=["equipment"])

MAX_EQUIPMENT_PDF_BYTES = 20 * 1024 * 1024  # 20MB, same cap as textbooks


def _get_or_create(db: Session) -> EquipmentContent:
    equipment = db.query(EquipmentContent).first()
    if not equipment:
        equipment = EquipmentContent()
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
    return equipment


@router.get("", response_model=EquipmentOut)
def get_equipment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create(db)


@router.get("/pdf")
def download_equipment_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    equipment = db.query(EquipmentContent).first()
    if not equipment or not equipment.pdf_data:
        raise HTTPException(status_code=404, detail="No equipment PDF uploaded yet.")
    return Response(
        content=equipment.pdf_data,
        media_type=equipment.pdf_content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{equipment.pdf_filename}"'},
    )


@router.put("", response_model=EquipmentOut)
def set_equipment(
    payload: SetEquipmentRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    equipment = _get_or_create(db)
    equipment.title = payload.title
    equipment.description = payload.description
    equipment.youtube_url = payload.youtube_url
    equipment.updated_at = utcnow()
    db.commit()
    db.refresh(equipment)
    return equipment


@router.post("/pdf", response_model=EquipmentOut)
async def upload_equipment_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = await file.read()
    if len(content) > MAX_EQUIPMENT_PDF_BYTES:
        raise HTTPException(status_code=400, detail="File too large - please keep uploads under 20MB.")

    equipment = _get_or_create(db)
    equipment.pdf_filename = file.filename
    equipment.pdf_content_type = file.content_type or "application/pdf"
    equipment.pdf_data = content
    equipment.pdf_size = len(content)
    equipment.updated_at = utcnow()
    db.commit()
    db.refresh(equipment)
    return equipment
