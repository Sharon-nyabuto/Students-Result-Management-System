"""Class report table and PDF report cards."""
import pandas as pd
from fpdf import FPDF

from logic import SUBJECTS, calculate_results

SCHOOL = "EASTSIDE HIGH SCHOOL"


def class_table(students):
    """Ranked DataFrame of averages and grades."""
    rows = []
    for s in students:
        avg, grade = calculate_results(s)
        rows.append({"Adm No": s["adm_no"], "Name": s["name"], "Class": s["class_name"],
                     **{sub: s.get(sub) for sub in SUBJECTS}, "Average": round(avg, 1), "Grade": grade})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("Average", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    return df


def report_card_pdf(student, position, class_size, scope="school"):
    avg, grade = calculate_results(student)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, SCHOOL, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, "Student Report Card (demo data)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 7, "Name:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, student["name"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 7, "Admission no:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, student["adm_no"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 7, "Class:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, student["class_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(100, 8, "Subject", border="B")
    pdf.cell(40, 8, "Marks", border="B", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for sub in SUBJECTS:
        pdf.cell(100, 8, sub)
        pdf.cell(40, 8, f"{student[sub]:.0f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(100, 8, "Average", border="T")
    pdf.cell(40, 8, f"{avg:.1f}", border="T", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(100, 8, "Grade")
    pdf.cell(40, 8, grade, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(100, 8, f"Position in {scope}")
    pdf.cell(40, 8, f"{position} of {class_size}", align="R", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
