import pytest

import db
from logic import SUBJECTS

MARKS = {s: 60 for s in SUBJECTS}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()


def test_demo_data_loads():
    assert len(db.load_students()) == 40


def test_add_student_returns_pin_and_it_works():
    sid, pin = db.add_student("T-1", "Test Person", "Form 3 East", MARKS)
    assert len(pin) == 6
    assert db.verify_student_pin("T-1", pin) == sid
    assert db.verify_student_pin("T-1", "000000" if pin != "000000" else "111111") is None


def test_unknown_student_and_wrong_pin_fail():
    assert db.verify_student_pin("NOPE", "123456") is None
    assert db.verify_student_pin("DEMO-001", "wrong") is None
    assert db.verify_student_pin("DEMO-001", db.DEMO_PIN) is not None


def test_students_never_expose_pin_fields():
    s = db.load_students()[0]
    assert "pin_hash" not in s and "pin_salt" not in s


def test_reset_pin_changes_login():
    sid = db.verify_student_pin("DEMO-002", db.DEMO_PIN)
    new = db.reset_pin(sid)
    assert db.verify_student_pin("DEMO-002", new) == sid
    if new != db.DEMO_PIN:
        assert db.verify_student_pin("DEMO-002", db.DEMO_PIN) is None


def test_duplicate_and_range_rejected():
    with pytest.raises(ValueError):
        db.add_student("DEMO-001", "Dup", "Form 3 East", MARKS)
    with pytest.raises(ValueError):
        db.add_student("X-1", "Bad", "Form 3 East", {**MARKS, "Physics": 120})


def test_issues_flow():
    sid = db.verify_student_pin("DEMO-020", db.DEMO_PIN)
    db.add_issue(sid, "My English mark is missing.")
    mine = db.load_issues(student_id=sid)
    assert mine[0]["status"] == "Open"
    db.resolve_issue(mine[0]["id"], "Fixed")
    assert db.load_issues(student_id=sid)[0]["status"] == "Resolved"
    with pytest.raises(ValueError):
        db.add_issue(sid, "  ")


def test_open_issue_limit():
    sid = db.verify_student_pin("DEMO-021", db.DEMO_PIN)
    for _ in range(db.MAX_OPEN_ISSUES):
        db.add_issue(sid, "Something is wrong.")
    with pytest.raises(ValueError):
        db.add_issue(sid, "One more problem.")
