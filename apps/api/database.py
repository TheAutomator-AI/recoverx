import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from apps.api.config import PROJECT_ROOT, settings
from core.domain.models import Base

# SQLite connect_args for concurrent access
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    if os.getenv("VERCEL") and "/tmp/recoverx.db" in settings.database_url:
        tmp_db = Path("/tmp/recoverx.db")
        seed_db = PROJECT_ROOT / "recoverx.db"
        if not tmp_db.exists() and seed_db.exists():
            try:
                shutil.copyfile(seed_db, tmp_db)
            except Exception as e:
                print(f"Notice: Could not copy seed db: {e}")

    Base.metadata.create_all(bind=engine)


# Auto-initialize DB tables on load
init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
