import argparse
import getpass
import sys

from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Reset the Blombooru admin password and/or username."
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Prompt securely for a new password without exposing it in command arguments.",
    )
    parser.add_argument(
        "--password",
        help="The new admin password (6-50 characters). WARNING: Exposes password in shell history and process lists.",
    )
    parser.add_argument(
        "--username",
        help="The new admin username (1-50 characters).",
    )
    args = parser.parse_args()

    if not args.reset_password and not args.password and not args.username:
        parser.error("At least one of --reset-password, --password, or --username is required.")

    if args.reset_password and args.password:
        parser.error("Use either --reset-password or --password, not both.")

    new_password = None
    new_username = None

    if args.reset_password:
        try:
            pw1 = getpass.getpass("New password: ")
            pw2 = getpass.getpass("Confirm password: ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.", file=sys.stderr)
            sys.exit(1)

        if pw1 != pw2:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)
        new_password = pw1.strip()
    elif args.password is not None:
        new_password = args.password.strip()

    if new_password is not None:
        if not new_password:
            print("Error: Password cannot be empty or whitespace-only.", file=sys.stderr)
            sys.exit(1)

        if len(new_password) < 6:
            print("Error: Password must be at least 6 characters.", file=sys.stderr)
            sys.exit(1)

        if len(new_password) > 50:
            print("Error: Password is too long (max 50 characters).", file=sys.stderr)
            sys.exit(1)

    if args.username is not None:
        new_username = args.username.strip()

        if not new_username:
            print("Error: Username cannot be empty or whitespace-only.", file=sys.stderr)
            sys.exit(1)

        if len(new_username) > 50:
            print("Error: Username is too long (max 50 characters).", file=sys.stderr)
            sys.exit(1)

    from backend.app.config import settings

    if settings.IS_FIRST_RUN:
        print(
            "Error: Initial setup has not been completed yet. "
            "Please complete first-run onboarding before using this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    from backend.app import database
    from backend.app.models import User

    database.init_engine()

    if database.SessionLocal is None:
        print(
            "Error: Could not connect to the database. "
            "Make sure the database is running and settings are configured.",
            file=sys.stderr,
        )
        sys.exit(1)

    db = database.SessionLocal()
    try:
        # TODO: If a guest account is implemented, filter by is_admin == True
        user = db.query(User).order_by(User.id).first()

        if user is None:
            print("Error: No admin user found in the database.", file=sys.stderr)
            sys.exit(1)

        if new_password is not None:
            from backend.app.auth import get_password_hash
            user.password_hash = get_password_hash(new_password)
            print(f"Password successfully reset for user: {user.username}")

        if new_username is not None:
            old_username = user.username
            user.username = new_username
            print(f"Username changed from '{old_username}' to '{new_username}'")

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
