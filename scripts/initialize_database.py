"""Initialize NagarNexus database tables and seed initial metadata."""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import engine, SessionLocal
from app.models import Base
from app.services.seeder import seed_initial_data


def main():
    print("[NagarNexus] Creating database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = seed_initial_data(db)
        print(f"[NagarNexus] Database initialization complete: {result}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

