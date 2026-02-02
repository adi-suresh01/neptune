from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import os
import sys
from app.core.settings import settings
import logging
from app.db.models import Base

logger = logging.getLogger(__name__)

def _sqlite_url(sqlite_path: str) -> str:
    sqlite_path = os.path.abspath(sqlite_path)
    return f"sqlite:///{sqlite_path}"


def _desktop_sqlite_url() -> str:
    os.makedirs(settings.desktop_data_dir, exist_ok=True)
    sqlite_path = os.path.join(settings.desktop_data_dir, "neptune.db")
    logger.info("Desktop app mode: Using SQLite")
    logger.info("Database location: %s", sqlite_path)
    return _sqlite_url(sqlite_path)


def _postgres_url() -> str | None:
    pg_url = settings.database_url
    if not pg_url:
        return None
    if not pg_url.startswith("postgresql://"):
        logger.warning("Unsupported DATABASE_URL format: %s", pg_url)
        return None
    return pg_url


def _test_postgres(pg_url: str) -> bool:
    try:
        test_engine = create_engine(
            pg_url,
            connect_args={"connect_timeout": settings.db_connect_timeout_seconds},
            pool_pre_ping=settings.db_pool_pre_ping,
        )
        test_engine.connect().close()
        return True
    except Exception as e:
        logger.warning("PostgreSQL connection failed: %s", e)
        return False


def get_database_url():
    """
    Smart database selection:
    - Desktop app: SQLite (zero-config, local)
    - Server: PostgreSQL preferred, SQLite fallback when configured
    """
    if settings.db_backend == "sqlite":
        if settings.app_mode == "desktop" or getattr(sys, "frozen", False):
            return _desktop_sqlite_url()
        fallback_path = os.path.join(os.getcwd(), "neptune_dev.db")
        logger.info("SQLite forced: Using %s", fallback_path)
        return _sqlite_url(fallback_path)

    if settings.db_backend == "postgres":
        pg_url = _postgres_url()
        if not pg_url:
            raise RuntimeError("DB_BACKEND=postgres but DATABASE_URL is missing or invalid")
        logger.info("PostgreSQL forced: Using configured DATABASE_URL")
        return pg_url

    # auto
    if settings.app_mode == "desktop" or getattr(sys, "frozen", False):
        return _desktop_sqlite_url()

    pg_url = _postgres_url()
    if pg_url and _test_postgres(pg_url):
        logger.info("Server mode: Using PostgreSQL")
        return pg_url

    fallback_path = os.path.join(os.getcwd(), "neptune_dev.db")
    logger.info("Server fallback: Using SQLite at %s", fallback_path)
    return _sqlite_url(fallback_path)

# Get the appropriate database URL
DATABASE_URL = get_database_url()

# Create SQLAlchemy engine
# Add check_same_thread=False for SQLite to work with FastAPI
if DATABASE_URL.startswith("sqlite:"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": settings.db_connect_timeout_seconds},
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for database sessions
def get_db():
    """
    Dependency function to get a database session.
    This will be used in FastAPI endpoints with Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database tables
def init_db():
    """
    Create all database tables.
    This should be called when the app starts.
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    try:
        from app.services.search import ensure_fts
        from app.services.embeddings import load_embeddings_map
        from app.services.vector_index_faiss import rebuild_index
        db = SessionLocal()
        try:
            ensure_fts(db)
            embeddings = (
                db.query(Base.metadata.tables["note_embeddings"].c.file_id,
                         Base.metadata.tables["note_embeddings"].c.vector)
                .all()
            )
            parsed = []
            dim = None
            for file_id, vector_json in embeddings:
                try:
                    vec = json.loads(vector_json)
                except Exception:
                    continue
                if not vec:
                    continue
                dim = dim or len(vec)
                parsed.append((file_id, vec))
            if dim:
                rebuild_index(parsed, dim)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning("FTS setup skipped: %s", e)
    logger.info("Database tables created successfully")
