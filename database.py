"""
Async PostgreSQL access for the word counter bot.
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models import Base, Word, WordCount

logger = logging.getLogger('bot.database')


class Database:
    """Async PostgreSQL access through SQLAlchemy and asyncpg."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            asyncpg_url(database_url),
            pool_size=5,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        """Create missing tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info('Database ready')

    async def get_words(self) -> list[str]:
        async with self.sessions() as session:
            return list(await session.scalars(select(Word.name).order_by(Word.name)))

    async def add_word(self, word: str) -> bool:
        """Returns False if the word was already tracked."""
        stmt = insert(Word).values(name=word).on_conflict_do_nothing().returning(Word.name)
        async with self.sessions.begin() as session:
            return await session.scalar(stmt) is not None

    async def remove_word(self, word: str) -> bool:
        """Removes the word and all its counts. Returns False if it wasn't tracked."""
        stmt = delete(Word).where(Word.name == word).returning(Word.name)
        async with self.sessions.begin() as session:
            return await session.scalar(stmt) is not None

    async def add_count(self, user_id: int, word: str, amount: int) -> int:
        """Adds to a user's count and returns the new total."""
        stmt = insert(WordCount).values(user_id=user_id, word=word, count=amount)
        stmt = stmt.on_conflict_do_update(
            index_elements=[WordCount.user_id, WordCount.word],
            set_={'count': WordCount.count + stmt.excluded.count},
        ).returning(WordCount.count)
        async with self.sessions.begin() as session:
            return await session.scalar(stmt)

    async def raise_counts(self, counts: dict[tuple[int, str], int]) -> None:
        """Stores counts from a history scan. Existing counts are only ever raised, never lowered."""
        if not counts:
            return
        stmt = insert(WordCount).values([
            {'user_id': user_id, 'word': word, 'count': count}
            for (user_id, word), count in counts.items()
        ])
        stmt = stmt.on_conflict_do_update(
            index_elements=[WordCount.user_id, WordCount.word],
            set_={'count': func.greatest(WordCount.count, stmt.excluded.count)},
        )
        async with self.sessions.begin() as session:
            await session.execute(stmt)

    async def get_count(self, user_id: int, word: str) -> int:
        stmt = select(WordCount.count).where(WordCount.user_id == user_id, WordCount.word == word)
        async with self.sessions() as session:
            return await session.scalar(stmt) or 0

    async def user_counts(self, user_id: int) -> list[tuple[str, int]]:
        """All (word, count) pairs of a user, highest first."""
        stmt = (
            select(WordCount.word, WordCount.count)
            .where(WordCount.user_id == user_id, WordCount.count > 0)
            .order_by(WordCount.count.desc(), WordCount.word)
        )
        async with self.sessions() as session:
            return [tuple(row) for row in await session.execute(stmt)]

    async def word_ranking(self, word: str) -> list[tuple[int, int]]:
        """All (user_id, count) pairs for a word, highest first."""
        stmt = (
            select(WordCount.user_id, WordCount.count)
            .where(WordCount.word == word, WordCount.count > 0)
            .order_by(WordCount.count.desc(), WordCount.user_id)
        )
        async with self.sessions() as session:
            return [tuple(row) for row in await session.execute(stmt)]

    async def top_counts(self, limit: int = 10) -> list[tuple[int, str, int]]:
        """The highest (user_id, word, count) rows across all words."""
        stmt = (
            select(WordCount.user_id, WordCount.word, WordCount.count)
            .where(WordCount.count > 0)
            .order_by(WordCount.count.desc(), WordCount.user_id)
            .limit(limit)
        )
        async with self.sessions() as session:
            return [tuple(row) for row in await session.execute(stmt)]

    async def close(self) -> None:
        await self.engine.dispose()
        logger.info('Database connections closed')


def asyncpg_url(raw: str) -> URL:
    """Accept the usual postgresql:// URLs and point them at the asyncpg driver.

    Raises ValueError if the URL cannot be used.
    """
    try:
        url = make_url(raw.replace('postgres://', 'postgresql://', 1))
    except ArgumentError:
        raise ValueError('expected postgresql://user:password@host:port/database') from None
    if url.get_backend_name() != 'postgresql':
        raise ValueError(f'expected a PostgreSQL URL, not {url.drivername}')
    url = url.set(drivername='postgresql+asyncpg')
    # asyncpg calls libpq's sslmode "ssl".
    sslmode = url.query.get('sslmode')
    if sslmode is not None:
        url = url.difference_update_query(['sslmode']).update_query_dict({'ssl': sslmode})
    return url
