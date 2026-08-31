from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sentences: Mapped[list["Sentence"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    worth_question: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score_reason: Mapped[str] = mapped_column(String, nullable=False)

    document: Mapped[Document] = relationship(back_populates="sentences")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="sentence", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    validation_reasons: Mapped[str] = mapped_column(Text, nullable=False)
    discarded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    sentence: Mapped[Sentence] = relationship(back_populates="questions")
