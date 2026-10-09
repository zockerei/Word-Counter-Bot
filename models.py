"""
SQLAlchemy models for the word counter bot.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Word(Base):
    """A tracked word or phrase, stored normalized (lowercase ASCII)."""

    __tablename__ = 'words'

    name: Mapped[str] = mapped_column(primary_key=True)

    def __repr__(self):
        return f"<Word(name='{self.name}')>"


class WordCount(Base):
    """How often a user has said a word."""

    __tablename__ = 'word_counts'
    __table_args__ = (Index('idx_word_counts_word', 'word'),)

    # No users table: a count belongs to whoever said the word, even after they leave.
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    word: Mapped[str] = mapped_column(
        ForeignKey('words.name', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True
    )
    count: Mapped[int] = mapped_column(default=0)

    def __repr__(self):
        return f"<WordCount(user_id={self.user_id}, word='{self.word}', count={self.count})>"
