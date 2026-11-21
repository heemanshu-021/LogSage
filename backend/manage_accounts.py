"""Offline maintenance for local LogSage accounts."""
from __future__ import annotations

import argparse
import asyncio
import getpass

from sqlalchemy import select

from backend.core.auth import hash_password
from backend.db.database import AsyncSessionLocal
from backend.db.models import User


async def reset_password(username: str, new_password: str) -> bool:
    if len(new_password) < 12:
        raise ValueError("The new password must contain at least 12 characters")
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if user is None:
            return False
        user.password_hash = await asyncio.to_thread(hash_password, new_password)
        user.session_version += 1
        await db.commit()
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage a LogSage local account")
    subparsers = parser.add_subparsers(dest="command", required=True)
    reset_parser = subparsers.add_parser("reset-password", help="Reset a local account password")
    reset_parser.add_argument("username")
    args = parser.parse_args()

    new_password = getpass.getpass("New password (at least 12 characters): ")
    confirmation = getpass.getpass("Confirm new password: ")
    if new_password != confirmation:
        parser.error("Passwords do not match")
    try:
        updated = asyncio.run(reset_password(args.username, new_password))
    except ValueError as exc:
        parser.error(str(exc))
    if not updated:
        parser.error(f"No local account found for username: {args.username}")
    print(f"Password reset for {args.username}; existing sessions were revoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
