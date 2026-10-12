"""SQLite storage for students and marks."""
import os
import random
from datetime import datetime, timezone
import sqlite3

import hmac

from auth import hash_secret, new_pin, new_salt
from logic import SUBJECTS, validate_mark

DEMO_PIN = "123456"

DB_PATH = os.environ.get("SRMS_DB", "results.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adm_no TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                pin_hash BLOB,
                pin_salt BLOB
            );
            CREATE TABLE IF NOT EXISTS marks (
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                subject TEXT NOT NULL,
                mark REAL NOT NULL CHECK (mark >= 0 AND mark <= 100),
                PRIMARY KEY (student_id, subject)
            );
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                reply TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            );
            """
        )
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(students)")]
        for col in ("pin_hash", "pin_salt"):  # upgrade older databases
            if col not in cols:
                conn.execute(f"ALTER TABLE students ADD COLUMN {col} BLOB")
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if count == 0:
        seed_demo_data()
    with connect() as conn:  # demo students from older databases get the demo PIN
        for r in conn.execute("SELECT id FROM students WHERE pin_hash IS NULL AND adm_no LIKE 'DEMO-%'").fetchall():
            _set_pin(conn, r["id"], DEMO_PIN)
    _seed_sample_issues()


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


MAX_OPEN_ISSUES = 3


def add_issue(student_id, message):
    """A student raises an issue (for example a missing mark). Raises ValueError on bad input."""
    message = (message or "").strip()
    if len(message) < 5:
        raise ValueError("Please describe the issue in a few words.")
    if len(message) > 500:
        raise ValueError("Please keep it under 500 characters.")
    with connect() as conn:
        open_count = conn.execute("SELECT COUNT(*) FROM issues WHERE student_id = ? AND status = 'Open'",
                                  (student_id,)).fetchone()[0]
        if open_count >= MAX_OPEN_ISSUES:
            raise ValueError("You already have 3 open issues. Please wait for the admin to respond.")
        conn.execute("INSERT INTO issues (student_id, message, created_at) VALUES (?, ?, ?)",
                     (student_id, message, _now()))


def load_issues(status=None, student_id=None):
    """Issues newest first, with the student's name and admission number."""
    sql = ("SELECT i.id, i.student_id, s.adm_no, s.name, s.class_name, i.message, i.status, i.reply, "
           "i.created_at, i.resolved_at FROM issues i JOIN students s ON s.id = i.student_id WHERE 1=1")
    args = []
    if status:
        sql += " AND i.status = ?"
        args.append(status)
    if student_id:
        sql += " AND i.student_id = ?"
        args.append(student_id)
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql + " ORDER BY i.id DESC", args)]


def resolve_issue(issue_id, reply=""):
    with connect() as conn:
        conn.execute("UPDATE issues SET status = 'Resolved', reply = ?, resolved_at = ? WHERE id = ?",
                     ((reply or "").strip() or None, _now(), issue_id))


def _seed_sample_issues():
    with connect() as conn:
        if conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]:
            return
        ids = {r["adm_no"]: r["id"] for r in conn.execute("SELECT id, adm_no FROM students")}
    if "DEMO-004" in ids and "DEMO-011" in ids:
        add_issue(ids["DEMO-004"], "My Kiswahili mark looks too low. I think my second paper was not added.")
        add_issue(ids["DEMO-011"], "There is no History mark for me on my results.")


def _set_pin(conn, student_id, pin):
    salt = new_salt()
    conn.execute("UPDATE students SET pin_hash = ?, pin_salt = ? WHERE id = ?",
                 (hash_secret(pin, salt), salt, student_id))


def reset_pin(student_id):
    """Give a student a new random PIN and return it (shown once to the admin)."""
    pin = new_pin()
    with connect() as conn:
        _set_pin(conn, student_id, pin)
    return pin


def verify_student_pin(adm_no, pin):
    """Return the student's id if the admission number and PIN match, otherwise None."""
    with connect() as conn:
        row = conn.execute("SELECT id, pin_hash, pin_salt FROM students WHERE adm_no = ?",
                           (adm_no.strip(),)).fetchone()
    if not row or row["pin_hash"] is None:
        return None
    if hmac.compare_digest(row["pin_hash"], hash_secret(pin.strip(), row["pin_salt"])):
        return row["id"]
    return None


def add_student(adm_no, name, class_name, marks, pin=None):
    """Insert a student with marks and a PIN. Returns (id, pin). Raises ValueError on bad input or duplicate admission number."""
    adm_no, name, class_name = adm_no.strip(), name.strip(), class_name.strip()
    if not adm_no or not name or not class_name:
        raise ValueError("Admission number, name and class are required.")
    clean = {s: validate_mark(marks[s]) for s in SUBJECTS}
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO students (adm_no, name, class_name) VALUES (?, ?, ?)",
                (adm_no, name, class_name),
            )
            conn.executemany(
                "INSERT INTO marks (student_id, subject, mark) VALUES (?, ?, ?)",
                [(cur.lastrowid, s, m) for s, m in clean.items()],
            )
            pin = pin or new_pin()
            _set_pin(conn, cur.lastrowid, pin)
            return cur.lastrowid, pin
    except sqlite3.IntegrityError:
        raise ValueError(f"Admission number {adm_no} already exists.")


def update_student(student_id, name, class_name, marks):
    clean = {s: validate_mark(marks[s]) for s in SUBJECTS}
    with connect() as conn:
        conn.execute(
            "UPDATE students SET name = ?, class_name = ? WHERE id = ?",
            (name.strip(), class_name.strip(), student_id),
        )
        conn.executemany(
            "INSERT INTO marks (student_id, subject, mark) VALUES (?, ?, ?) "
            "ON CONFLICT(student_id, subject) DO UPDATE SET mark = excluded.mark",
            [(student_id, s, m) for s, m in clean.items()],
        )


def delete_student(student_id):
    with connect() as conn:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))


def load_students():
    """Return a list of dicts: id, adm_no, name, class_name and one key per subject."""
    with connect() as conn:
        students = [dict(r) for r in conn.execute("SELECT id, adm_no, name, class_name FROM students ORDER BY adm_no")]
        by_id = {s["id"]: s for s in students}
        for r in conn.execute("SELECT student_id, subject, mark FROM marks"):
            by_id[r["student_id"]][r["subject"]] = r["mark"]
    return students


FIRST = ["Amani", "Baraka", "Neema", "Zawadi", "Imani", "Tumaini", "Furaha", "Subira", "Jabali",
         "Wema", "Pendo", "Upendo", "Rehema", "Sifa", "Faraja", "Heri", "Jasiri", "Nuru",
         "Tabu", "Zuri"]
LAST = ["Mwangi", "Otieno", "Wanjiru", "Kamau", "Achieng", "Njoroge", "Odhiambo", "Wambui",
        "Kiptoo", "Mutua", "Chebet", "Omondi", "Nyambura", "Barasa", "Mohamed", "Atieno"]


def seed_demo_data(n=40):
    """Fictional students only. Names are randomly combined and do not refer to real people."""
    rng = random.Random(2026)
    used = set()
    for i in range(n):
        while True:
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            if name not in used:
                used.add(name)
                break
        ability = rng.gauss(64, 11)
        marks = {s: min(100, max(18, round(rng.gauss(ability, 9)))) for s in SUBJECTS}
        add_student(f"DEMO-{i + 1:03d}", name, "Form 3 East" if i % 2 == 0 else "Form 3 West", marks, pin=DEMO_PIN)
