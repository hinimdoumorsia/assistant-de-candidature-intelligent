"""
database/db_manager.py - Gestion de la session SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from database.models import Base
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Crée toutes les tables si elles n'existent pas."""
    Base.metadata.create_all(engine)
    logger.info("Base de données initialisée.")


@contextmanager
def get_session() -> Session:
    """Context manager pour une session DB avec rollback automatique."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"DB error: {e}")
        raise
    finally:
        session.close()
