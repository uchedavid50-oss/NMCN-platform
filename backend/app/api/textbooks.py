import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.textbook import Textbook
from app.models.textbook_folder import TextbookFolder
from app.models.user import User
from app.schemas.textbook import TextbookFolderCreate, TextbookFolderOut, TextbookOut

router = APIRouter(prefix="/textbooks", tags=["textbooks"])

MAX_TEXTBOOK_BYTES = 20 * 1024 * 1024  # 20MB - textbooks are naturally larger than study notes


@router.post("/folders", response_model=TextbookFolderOut, status_code=201)
def create_folder(
    payload: TextbookFolderCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = db.query(TextbookFolder).filter(TextbookFolder.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="A folder with this name already exists")
    folder = TextbookFolder(name=payload.name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("/folders", response_model=list[TextbookFolderOut])
def list_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(TextbookFolder).order_by(TextbookFolder.name.asc()).all()


@router.post("/folders/{folder_id}/upload", response_model=TextbookOut, status_code=201)
async def upload_textbook(
    folder_id: uuid.UUID,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    folder = db.query(TextbookFolder).filter(TextbookFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    content = await file.read()
    if len(content) > MAX_TEXTBOOK_BYTES:
        raise HTTPException(status_code=400, detail="File too large - please keep uploads under 20MB.")

    textbook = Textbook(
        folder_id=folder.id,
        title=title,
        filename=file.filename,
        content_type=file.content_type or "application/pdf",
        file_size=len(content),
        file_data=content,
        uploaded_by=admin.id,
    )
    db.add(textbook)
    db.commit()
    db.refresh(textbook)
    return textbook


@router.get("/folders/{folder_id}/textbooks", response_model=list[TextbookOut])
def list_textbooks_in_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folder = db.query(TextbookFolder).filter(TextbookFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return (
        db.query(Textbook)
        .filter(Textbook.folder_id == folder_id)
        .order_by(Textbook.title.asc())
        .all()
    )


@router.get("/{textbook_id}/download")
def download_textbook(
    textbook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")

    return Response(
        content=textbook.file_data,
        media_type=textbook.content_type,
        headers={"Content-Disposition": f'inline; filename="{textbook.filename}"'},
    )


@router.delete("/{textbook_id}", status_code=204)
def delete_textbook(
    textbook_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    db.delete(textbook)
    db.commit()
    return None
