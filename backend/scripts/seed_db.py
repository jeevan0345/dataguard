"""
DataGuard Database Seeder
Safely ensures default enterprise demo accounts exist in PostgreSQL.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.auth.service import AuthService
from app.auth.schemas import UserRegister


def seed_database():
    print("=" * 60)
    print("DATAGUARD 2.0 DATABASE SEEDER")
    print("=" * 60)

    db = SessionLocal()
    try:
        demo_accounts = [
            ("admin@dataguard.ai", "System Administrator", "admin123", "ADMIN"),
            ("engineer@dataguard.ai", "Lead Data Engineer", "engineer123", "DATA_ENGINEER"),
            ("viewer@dataguard.ai", "Business Stakeholder", "viewer123", "VIEWER"),
        ]

        seeded_count = 0
        for email, name, pwd, role in demo_accounts:
            existing = AuthService.get_by_email(db, email)
            if not existing:
                user = AuthService.register_user(
                    db,
                    UserRegister(email=email, full_name=name, password=pwd, role=role),
                )
                print(f"[+] Created user: {user.email} (Role: {user.role})")
                seeded_count += 1
            else:
                print(f"[*] User already exists: {existing.email} (Role: {existing.role})")

        print("=" * 60)
        print(f"Seeding completed. {seeded_count} user(s) created.")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
