"""Idempotent creation of the first admin user from INITIAL_ADMIN_* env vars."""

import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main() -> int:
    email = settings.INITIAL_ADMIN_EMAIL
    password = settings.INITIAL_ADMIN_PASSWORD
    if not email or not password:
        print(
            "INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD must both be set.",
            file=sys.stderr,
        )
        return 1

    normalized = email.lower().strip()
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == normalized))
        if existing is not None:
            print("Admin user already exists; nothing to do.")
            return 0

        user = User(
            email=normalized,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        print("Initial admin user created.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
