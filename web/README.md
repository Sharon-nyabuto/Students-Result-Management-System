# Student Results Management System (web version)

A web app for recording student marks, calculating averages and grades, ranking a class and producing report cards. It grew out of my command-line version, keeping the same grading rules.

**Demo data only.** Every student, name and mark is fictional.

## What it does

- Three roles: **admin** (everything, plus CSV import, delete and PIN resets), **teacher** (view, add and edit marks) and **student** (view only)
- Students sign in with their student ID and a personal PIN, and see only their own marks next to the class average for each subject, with their position in class and a PDF report card. PINs are stored hashed; new students get a random 6-digit PIN that the admin sees once
- Dashboard: class average, pass rate, top student, average by subject, grade distribution
- Search students, edit marks, validate input (0 to 100, unique admission numbers)
- Class report ranked by average, downloadable as CSV
- Per-student report card as PDF
- Bulk import from CSV with row-by-row error messages
- Data stored in SQLite, so it survives restarts

## Grading

Average of the six subjects: A 80+, B 70-79, C 60-69, D 50-59, E below 50.

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```

Demo logins: `admin` / `admin-demo` and `teacher` / `teacher-demo`. Demo student: ID `DEMO-001` (up to `DEMO-040`), PIN `123456`.
To change them, set `SRMS_ADMIN_PASSWORD` and `SRMS_TEACHER_PASSWORD` before starting.

## Structure

- `app.py` the web interface
- `logic.py` averages, grades and mark validation
- `db.py` SQLite storage and demo data
- `auth.py` hashed-password login with roles
- `report.py` class table and PDF report cards
- `test_logic.py`, `test_db.py` tests for grading, storage and PIN checks

## Limits

- Staff use two shared demo accounts; only students have individual logins
- Student PINs are a light check, not strong security: login is locked after 5 failed tries per visit, but there is no password recovery or per-IP limit
- Free hosting tiers may reset the database, which is fine for a demo but not for real records
- Real student data needs proper accounts, backups and a data protection plan before use
