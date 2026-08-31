from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.api.controllers import questions as controller
from core.api.dependencies import get_db
from core.schemas.api import QuestionDiscard, QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])


@router.patch("/{question_id}", response_model=QuestionOut)
def update_question_discard(
    question_id: int, body: QuestionDiscard, db: Session = Depends(get_db)
) -> QuestionOut:
    result = controller.update_question_discard(db, question_id, body.discarded)
    if result is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return result
