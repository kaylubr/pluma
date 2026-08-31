from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.api.controllers import reviewers as controller
from core.api.dependencies import get_db
from core.schemas.api import QuestionOut, ReviewerDetail, ReviewerSummary

router = APIRouter(prefix="/reviewers", tags=["reviewers"])


@router.post("", response_model=ReviewerDetail, status_code=201)
def create_reviewer(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> ReviewerDetail:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    contents = file.file.read()
    try:
        return controller.create_reviewer(db, file.filename, contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ReviewerSummary])
def list_reviewers(db: Session = Depends(get_db)) -> list[ReviewerSummary]:
    return controller.list_reviewers(db)


@router.get("/{reviewer_id}/questions", response_model=list[QuestionOut])
def get_reviewer_questions(
    reviewer_id: int, db: Session = Depends(get_db)
) -> list[QuestionOut]:
    result = controller.get_reviewer_questions(db, reviewer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Reviewer not found")
    return result
