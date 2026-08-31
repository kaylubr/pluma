from sqlalchemy.orm import Session

from core.api.controllers import mapping
from core.schemas.api import QuestionOut
from core.services import store


def update_question_discard(
    session: Session, question_id: int, discarded: bool
) -> QuestionOut | None:
    question = store.set_question_discarded(session, question_id, discarded)
    if question is None:
        return None
    return mapping.question_to_out(question)
