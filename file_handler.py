# Saving student records to CSV file
import csv
import os

def save_student(student, subjects):
    file_exists = os.path.isfile("students.csv")
    with open("students.csv", "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name"] + subjects)
           
        if not file_exists:
            writer.writeheader()
        writer.writerow(student)

#  Loading student records from the CSV file.
def load_students():
    students = []
    if not os.path.isfile("students.csv"):
        return students
    with open("students.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            student = {"name": row["name"]}
            for subject in row:
                if subject != "name":
                    student[subject] = float(row[subject])
            students.append(student)
    return students
    
