from sqlalchemy import func
from sqlalchemy.orm import Session

from core.models import Document, Question, Sentence
from core.services.generate import GeneratedCloze
from core.services.score import ScoredSentence
from core.services.validate import ValidationResult


def store_document(session: Session, filename: str) -> int:
    document = Document(filename=filename)
    session.add(document)
    session.flush()
    return document.id


def store_sentence(
    session: Session, document_id: int, position: int, scored: ScoredSentence
) -> int:
    sentence = Sentence(
        document_id=document_id,
        position=position,
        text=scored.text,
        worth_question=scored.worth_question,
        score_reason=scored.reason,
    )
    session.add(sentence)
    session.flush()
    return sentence.id


def store_sentences(
    session: Session, document_id: int, sentences: list[ScoredSentence]
) -> list[int]:
    return [
        store_sentence(session, document_id, position, scored)
        for position, scored in enumerate(sentences)
    ]


def store_question(
    session: Session,
    sentence_id: int,
    cloze: GeneratedCloze,
    validation: ValidationResult,
    discarded: bool = False,
) -> int:
    question = Question(
        sentence_id=sentence_id,
        text=cloze.text,
        answer=cloze.answer,
        reason=cloze.reason,
        is_valid=validation.is_valid,
        validation_reasons=",".join(validation.reasons),
        discarded=discarded,
    )
    session.add(question)
    session.flush()
    return question.id


def store_questions(
    session: Session,
    items: list[
        tuple[int, GeneratedCloze, ValidationResult]
        | tuple[int, GeneratedCloze, ValidationResult, bool]
    ],
) -> list[int]:
    ids = []
    for item in items:
        if len(item) == 4:
            sentence_id, cloze, validation, discarded = item
            ids.append(
                store_question(session, sentence_id, cloze, validation, discarded=discarded)
            )
        else:
            sentence_id, cloze, validation = item
            ids.append(store_question(session, sentence_id, cloze, validation))
    return ids


def get_document(session: Session, document_id: int) -> Document | None:
    return session.get(Document, document_id)


def list_documents(session: Session) -> list[Document]:
    return session.query(Document).order_by(Document.id).all()


def list_valid_questions(session: Session, document_id: int) -> list[Question]:
    return (
        session.query(Question)
        .join(Sentence, Question.sentence_id == Sentence.id)
        .filter(
            Sentence.document_id == document_id,
            Question.is_valid.is_(True),
            Question.discarded.is_(False),
        )
        .order_by(Sentence.position, Question.id)
        .all()
    )


def count_valid_questions(session: Session, document_id: int) -> int:
    return (
        session.query(func.count(Question.id))
        .join(Sentence, Question.sentence_id == Sentence.id)
        .filter(
            Sentence.document_id == document_id,
            Question.is_valid.is_(True),
            Question.discarded.is_(False),
        )
        .scalar()
    )


def get_question(session: Session, question_id: int) -> Question | None:
    return session.get(Question, question_id)


def set_question_discarded(
    session: Session, question_id: int, discarded: bool
) -> Question | None:
    question = session.get(Question, question_id)
    if question is None:
        return None
    question.discarded = discarded
    session.flush()
    return question
