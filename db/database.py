from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_PATH
from db.models import Base

engine = create_engine(DB_PATH)

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Provides a database session for use in database operations.

    This function is a dependency that yields a database session.
    It ensures that the session is properly closed after use.

    Yields:
        Session: A SQLAlchemy database session.

    Example:
        with get_db() as db:
            # perform database operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
