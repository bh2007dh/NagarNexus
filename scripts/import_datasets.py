"""Generate and import sample urban datasets into NagarNexus."""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import engine, SessionLocal
from app.models import Base
from app.services.seeder import generate_sample_csv_files, seed_initial_data


def main():
    files = generate_sample_csv_files()
    print(f"[NagarNexus] Generated {len(files)} sample CSV datasets:")
    for title, path in files.items():
        print(f"  - {title}: {path}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        res = seed_initial_data(db)
        print(f"[NagarNexus] Dataset import status: {res}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

