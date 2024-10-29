from sqlalchemy import (
    Column, Integer, String, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    permission = Column(String(10), nullable=False)

    __table_args__ = (CheckConstraint(permission.in_(['admin', 'user']), name='chk_permission'),)

    words = relationship("UserHasWord", back_populates="user", cascade="all, delete-orphan")


class Word(Base):
    __tablename__ = 'word'

    name = Column(String(45), primary_key=True)

    users = relationship("UserHasWord", back_populates="word", cascade="all, delete-orphan")


class UserHasWord(Base):
    __tablename__ = 'user_has_word'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    word_name = Column(String(45), ForeignKey('word.name'), primary_key=True)
    count = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="words")
    word = relationship("Word", back_populates="users")

    __table_args__ = (UniqueConstraint('user_id', 'word_name', name='uq_user_word'),)
