"""Give an existing Supabase Auth user a staff role. Usage (from pipeline/):

    ../.venv/Scripts/python.exe set_staff.py someone@example.com clerk
    ../.venv/Scripts/python.exe set_staff.py demo@example.com demo

The account itself is created by a person in the Supabase dashboard
(Authentication -> Users -> Add user); this script never sees a password.
"""
import os
import sys

from draft_item import load_env


def main(email, role):
    if role not in ("clerk", "demo"):
        sys.exit("role must be clerk or demo")
    load_env()
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    users = db.auth.admin.list_users(per_page=1000)
    match = [u for u in users if (u.email or "").lower() == email.lower()]
    if not match:
        sys.exit(f"No Auth user with email {email}. Create it in the Supabase dashboard first.")
    db.table("staff_profiles").upsert({"user_id": match[0].id, "role": role}).execute()
    print(f"{email}: role set to {role}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
