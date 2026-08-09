# Functions used to calculate student averages and grades.
def calculate_results(student):
    marks = [
            student["Mathematics"],
            student["English"],
            student["Science"],
            student["History"],
            student["Kiswahili"],
            student["Physics"]]
    average = sum(marks) / len(marks)
    if average >= 80:
        grade = "A"
    elif average >= 70:
        grade = "B"
    elif average >= 60:
        grade = "C"
    elif average >= 50:
        grade = "D"
    else:
        grade = "E"
    return average, grade
    