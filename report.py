# Summary report of student performance.
from logic import calculate_results

def generate_report(students):
    if not students:
        print("\nNo student records found.")
        return
    print("      EASTSIDE HIGH SCHOOL - REPORT")
    print("="*50)
    print(f"{'Name':<20} {'Average':<10} {'Grade':<5}")
    print("-"*40)

    class_total = 0
    highest_average = -1
    highest_student = ""

    for student in students:
        average, grade = calculate_results(student)
        print(f"{student['name']:<20} {average:<10.1f} {grade:<5}")
        class_total += average

        if average > highest_average:
            highest_average = average
            highest_student = student["name"]
    class_average = class_total / len(students)

    print("-"*40)
    print(f"Class Average: {class_average:.1f}")
    print(f"Top Student: {highest_student} ({highest_average:.1f})")
    print("="*40)