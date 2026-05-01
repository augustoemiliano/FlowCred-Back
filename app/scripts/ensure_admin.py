"""Cria ou sincroniza o utilizador admin a partir de INITIAL_ADMIN_* no ambiente."""

import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal
from app.models.user import User


def main() -> int:
    username = (settings.INITIAL_ADMIN_USERNAME or "").strip().lower()
    password = (settings.INITIAL_ADMIN_PASSWORD or "").strip()
    if not username or not password:
        print(
            "INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD must both be set.",
            file=sys.stderr,
        )
        return 1

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            if verify_password(password, existing.hashed_password):
                print("Admin user already exists; password matches INITIAL_ADMIN_PASSWORD.")
                return 0
            existing.hashed_password = hash_password(password)
            existing.is_active = True
            existing.is_superuser = True
            db.commit()
            print("Admin password synced from INITIAL_ADMIN_PASSWORD.")
            return 0

        user = User(
            username=username,
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
