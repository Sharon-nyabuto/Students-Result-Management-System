# Import the functions needed to run the student results system.
from logic import calculate_results
from file_handler import save_student
from file_handler import load_students
from report import generate_report

students = load_students()
subjects = ["Mathematics", "English", "Science", "History", "Kiswahili", "Physics"]

print("\n===== STUDENT RESULTS MANAGEMENT SYSTEM =====")
print("1. Add Student")
print("2. View Students")
print("3. Generate Report")
print("4. Exit")

while True:
    choice = input("Select an option: ")
    if choice == "1":
        print("\n===== Add Student =====")
        name = input("Enter student name: ")
        student = {"name": name}
        for subject in subjects:
            mark = float(input(f"Enter {subject} marks: "))
            while mark < 0 or mark > 100:
                print("Mark must be between 0 and 100.")
                mark = float(input(f"Enter {subject} marks: "))
            student[subject] = mark
        students.append(student)
        save_student(student, subjects)       
        print(f"\n{name} has been added successfully!")

    elif choice == "2": 
        print("\n===== View Student Records =====")
        if not students:
            print("\nNo student records found.")
        else:
            for student in students:
                average, grade = calculate_results(student)
                print(f"\nStudent: {student['name']}")
                for subject in subjects:
                     print(f"{subject:<12}: {student[subject]:>6.1f}")
                print(f"{'Average':<12}: {average:>6.2f}")
                print(f"{'Grade':<12}: {grade:>6}")
            
    elif choice == "3":
         generate_report(students)
    elif choice == "4":
        break
    else:
        print("Invalid choice. Please try again.")


