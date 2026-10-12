"""Grading logic: averages, grades and class ranking."""

SUBJECTS = ["Mathematics", "English", "Science", "History", "Kiswahili", "Physics"]


def grade_for(average):
    if average >= 80:
        return "A"
    if average >= 70:
        return "B"
    if average >= 60:
        return "C"
    if average >= 50:
        return "D"
    return "E"


def calculate_results(marks):
    """marks: dict of subject -> mark. Returns (average, grade)."""
    values = [marks[s] for s in SUBJECTS if marks.get(s) is not None]
    if not values:
        return 0.0, "E"
    average = sum(values) / len(values)
    return average, grade_for(average)


def validate_mark(value):
    """Return a float between 0 and 100, or raise ValueError."""
    mark = float(value)
    if mark < 0 or mark > 100:
        raise ValueError("Marks must be between 0 and 100.")
    return mark
