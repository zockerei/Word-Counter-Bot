from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Create an engine that stores data in the specified database file.
engine = create_engine('sqlite:///word_counter.db')

# Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
Base.metadata.create_all(engine)

# Bind the engine to the sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get the database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
