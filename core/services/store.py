from sqlalchemy.orm import Session

from core.db.models import Document, Question, Sentence
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
    session: Session, sentence_id: int, cloze: GeneratedCloze, validation: ValidationResult
) -> int:
    question = Question(
        sentence_id=sentence_id,
        text=cloze.text,
        answer=cloze.answer,
        reason=cloze.reason,
        is_valid=validation.is_valid,
        validation_reasons=",".join(validation.reasons),
    )
    session.add(question)
    session.flush()
    return question.id


def store_questions(
    session: Session,
    items: list[tuple[int, GeneratedCloze, ValidationResult]],
) -> list[int]:
    return [store_question(session, sentence_id, cloze, validation) for sentence_id, cloze, validation in items]
