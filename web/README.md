# Student Results Management System (web version)

A web app for recording student marks, calculating averages and grades, ranking a class and producing report cards. It grew out of my command-line version, keeping the same grading rules.

**Demo data only.** Every student, name and mark is fictional.

## What it does

- Separate Student, Teacher and Admin logins on a centred sign-in page, with the demo credentials shown as placeholders
- Students can raise an issue (for example a missing mark); the admin sees it under **Issues** and can reply and resolve it
- Edits and imports confirm with a success message
- Charts are static, so scrolling over them never rescales them
- Three roles: **admin** (everything, plus CSV import, delete and PIN resets), **teacher** (view, add and edit marks) and **student** (view only)
- Students sign in with their student ID and a personal PIN, and see only their own marks next to the class average for each subject, with their position in class and a PDF report card. PINs are stored hashed; new students get a random 6-digit PIN that the admin sees once
- Dashboard: class average, pass rate, top student, average by subject, grade distribution
- Search students, edit marks, validate input (0 to 100, unique admission numbers)
- Class report ranked by average, downloadable as CSV
- Per-student report card as PDF
- Bulk import from CSV with row-by-row error messages
- Data stored in SQLite, so it survives restarts

## Grading

Average of the six subjects (and each subject mark): A 80+, B 70-79, C 60-69, D 50-59, E 40-49, F below 40.

- **Remedial:** any subject below 50 is flagged, for students, teachers and on the PDF report card.
- **Repeats the class:** an overall average below 40 (grade F). Both thresholds are constants at the top of `logic.py`.

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

- Free hosting tiers such as streamlit may reset the database, which is fine for a demo but not for real records. So when working with actual data you'll need proper accounts, backups and a data protection plan before use.
