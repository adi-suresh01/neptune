from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """
    Smart database selection:
    - Development: PostgreSQL (your current setup)
    - Desktop App: SQLite (bundled, zero-config)
    """
    
    # Check if we're in a PyInstaller bundle (desktop app)
    if getattr(sys, 'frozen', False):
        # Desktop app mode - use SQLite for zero-config reliability
        db_dir = os.path.join(os.path.expanduser("~"), ".neptune")
        os.makedirs(db_dir, exist_ok=True)
        sqlite_path = os.path.join(db_dir, 'neptune.db')
        sqlite_url = f"sqlite:///{sqlite_path}"
        
        print(f"📱 Desktop app mode: Using SQLite")
        print(f"📁 Database location: {sqlite_path}")
        return sqlite_url
    
    else:
        # Development mode - use PostgreSQL from .env
        pg_url = os.getenv("DATABASE_URL")
        if pg_url and pg_url.startswith("postgresql://"):
            try:
                # Test PostgreSQL connection
                test_engine = create_engine(pg_url)
                test_engine.connect().close()
                print(f"🔧 Development mode: Using PostgreSQL")
                print(f"🗄️  Database: {pg_url.split('@')[1] if '@' in pg_url else pg_url}")
                return pg_url
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                print("🔄 Falling back to SQLite for development...")
        
        # Fallback to SQLite even in development if PostgreSQL fails
        fallback_path = os.path.join(os.getcwd(), "neptune_dev.db")
        fallback_url = f"sqlite:///{fallback_path}"
        print(f"📁 Development fallback: Using SQLite at {fallback_path}")
        return fallback_url

# Get the appropriate database URL
DATABASE_URL = get_database_url()

# Create SQLAlchemy engine
# Add check_same_thread=False for SQLite to work with FastAPI
if DATABASE_URL.startswith("sqlite:"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

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
    print("🏗️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")