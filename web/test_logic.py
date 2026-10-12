import pytest
from logic import SUBJECTS, calculate_results, grade_for, validate_mark


def test_grade_boundaries():
    assert grade_for(80) == "A" and grade_for(79.9) == "B"
    assert grade_for(70) == "B" and grade_for(60) == "C"
    assert grade_for(50) == "D" and grade_for(49.9) == "E"


def test_average():
    avg, grade = calculate_results({s: 70 for s in SUBJECTS})
    assert avg == 70 and grade == "B"


def test_validate_mark():
    assert validate_mark("55") == 55.0
    with pytest.raises(ValueError):
        validate_mark(101)
    with pytest.raises(ValueError):
        validate_mark(-1)
