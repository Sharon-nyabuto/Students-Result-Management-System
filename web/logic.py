"""Grading logic: averages, grades and class ranking."""

SUBJECTS = ["Mathematics", "English", "Science", "History", "Kiswahili", "Physics"]


PASS_MARK = 50        # below this in a subject: remedial classes recommended
REPEAT_BELOW = 40     # overall average below this (grade F): repeats the class


def grade_for(average):
    if average >= 80:
        return "A"
    if average >= 70:
        return "B"
    if average >= 60:
        return "C"
    if average >= 50:
        return "D"
    if average >= REPEAT_BELOW:
        return "E"
    return "F"


def calculate_results(marks):
    """marks: dict of subject -> mark. Returns (average, grade)."""
    values = [marks[s] for s in SUBJECTS if marks.get(s) is not None]
    if not values:
        return 0.0, "F"
    average = sum(values) / len(values)
    return average, grade_for(average)


def validate_mark(value):
    """Return a float between 0 and 100, or raise ValueError."""
    mark = float(value)
    if mark < 0 or mark > 100:
        raise ValueError("Marks must be between 0 and 100.")
    return mark


def remedial_subjects(marks):
    """Subjects where the mark is below the pass mark."""
    return [s for s in SUBJECTS if marks.get(s) is not None and marks[s] < PASS_MARK]


def outcome(marks):
    """End-of-term outcome: 'Repeats class', 'Promoted, remedial needed' or 'Promoted'."""
    average, _ = calculate_results(marks)
    if average < REPEAT_BELOW:
        return "Repeats class"
    if remedial_subjects(marks):
        return "Promoted, remedial needed"
    return "Promoted"
