"""
CLI Script to seed the RecoverX demo database with Case A, Case B, Case C and synthetic transactions.
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.database import SessionLocal, init_db
from apps.api.routers.demo import seed_demo_dataset


def main():
    print("Initializing RecoverX Database schema...")
    init_db()
    db = SessionLocal()
    try:
        print("Seeding deterministic demo scenarios (Case A, Case B, Case C)...")
        result = seed_demo_dataset(db)
        print(f"Success! {result['total_seeded_records']} payments seeded.")
        print(f" - Case A (Autonomous): {result['case_a_autonomous']['order_id']} | Status: {result['case_a_autonomous']['status']}")
        print(f" - Case B (Assisted):   {result['case_b_assisted']['order_id']} | Status: {result['case_b_assisted']['status']}")
        print(f" - Case C (Escalated):  {result['case_c_escalated']['order_id']} | Status: {result['case_c_escalated']['status']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
