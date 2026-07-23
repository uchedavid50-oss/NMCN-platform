from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.tutor import _call_gemini, _check_tutor_available
from app.db.session import get_db
from app.models.mnemonic import Mnemonic
from app.models.tutor_request import TutorRequest
from app.models.user import User
from app.schemas.mnemonic import MnemonicGenerateRequest, MnemonicOut

router = APIRouter(prefix="/mnemonics", tags=["mnemonics"])


@router.post("/generate", response_model=MnemonicOut, status_code=201)
def generate_mnemonic(
    payload: MnemonicGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_tutor_available(db, current_user.id)

    system_prompt = (
        "You create short, memorable mnemonics to help a Nigerian nursing student remember "
        "nursing/medical terms, lists, or sequences for the NMCN Professional Qualifying "
        "Examination. Given a term or list, respond with ONLY the mnemonic itself (a short "
        "phrase, acronym, or rhyme) plus a one-line explanation of what each part stands for. "
        "Keep it under 60 words total. No preamble, no extra commentary."
    )

    reply_text = _call_gemini(system_prompt, payload.term, max_output_tokens=300)

    mnemonic = Mnemonic(user_id=current_user.id, term=payload.term, mnemonic_text=reply_text)
    db.add(mnemonic)
    db.add(TutorRequest(user_id=current_user.id))
    db.commit()
    db.refresh(mnemonic)
    return mnemonic


@router.get("", response_model=list[MnemonicOut])
def list_mnemonics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Mnemonic)
        .filter(Mnemonic.user_id == current_user.id)
        .order_by(Mnemonic.created_at.desc())
        .all()
    )
