import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Get database URL from environment variables or use SQLite as default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app/data/llm_shell.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

# Create session factory
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(session_factory)

# Create declarative base
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    from app.models.task import Task
    from app.models.filesystem_state import FilesystemState
    
    # Create data directory if using SQLite
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if db_path:  # Only create directories if there's an actual path
            directory = os.path.dirname(db_path)
            if directory:  # Only attempt to create if directory is not empty
                os.makedirs(directory, exist_ok=True)
        else:
            # Default to a safe location if no path is specified
            os.makedirs("app/data", exist_ok=True)
            # Update the database URL to use the default path
            global engine
            engine = create_engine(
                "sqlite:///app/data/llm_shell.db",
                connect_args={"check_same_thread": False},
                echo=False
            )
    
    # Create tables
    Base.metadata.create_all(bind=engine) 