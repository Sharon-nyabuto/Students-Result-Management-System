"""Simple role-based login. Demo accounts only; swap for real accounts before real use."""
import hashlib
import hmac
import os
import secrets

ITERATIONS = 120_000


def hash_secret(secret, salt):
    return hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, ITERATIONS)


def new_salt():
    return os.urandom(16)


def new_pin():
    """Random 6-digit PIN for a student."""
    return f"{secrets.randbelow(1_000_000):06d}"


_hash = hash_secret


def _make_user(role, password):
    salt = hashlib.sha256(("srms-" + role).encode()).digest()[:16]
    return {"role": role, "salt": salt, "hash": _hash(password, salt)}


# Demo credentials. Override with environment variables when hosting.
USERS = {
    "admin": _make_user("admin", os.environ.get("SRMS_ADMIN_PASSWORD", "admin-demo")),
    "teacher": _make_user("teacher", os.environ.get("SRMS_TEACHER_PASSWORD", "teacher-demo")),
}


def check_login(username, password):
    """Return the role for valid credentials, otherwise None."""
    user = USERS.get(username.strip().lower())
    if not user:
        return None
    if hmac.compare_digest(user["hash"], _hash(password, user["salt"])):
        return user["role"]
    return None
