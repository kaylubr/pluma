from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base


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

    document: Mapped["Document"] = relationship(back_populates="sentences")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="sentence", cascade="all, delete-orphan"
    )
